"""
Persistencia de trabajos y resultados en SQLite.

Guardamos cada resultado en cuanto llega, para poder consultarlo mientras
el trabajo sigue en marcha y no perderlo si el servicio se cae.
"""

import json
import sqlite3
import threading
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

from src.config import CLASS_ERROR, CLASS_FAKE, CLASS_LEGITIMATE, CLASS_SUSPICIOUS

# Estados de un trabajo
STATUS_QUEUED = "queued"
STATUS_RUNNING = "running"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"
STATUS_CANCELLED = "cancelled"

ACTIVE_STATUSES = (STATUS_QUEUED, STATUS_RUNNING)
FINISHED_STATUSES = (STATUS_COMPLETED, STATUS_FAILED, STATUS_CANCELLED)

# Origen de los archivos de un trabajo
SOURCE_LIBRARY = "library"
SOURCE_UPLOAD = "upload"

INTERRUPTED_REASON = "Interrumpido por un reinicio del servicio"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id          TEXT PRIMARY KEY,
    source      TEXT NOT NULL,
    params      TEXT NOT NULL,
    status      TEXT NOT NULL,
    total       INTEGER NOT NULL DEFAULT 0,
    processed   INTEGER NOT NULL DEFAULT 0,
    counts      TEXT NOT NULL,
    error       TEXT,
    created_at  TEXT NOT NULL,
    finished_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs (created_at);

CREATE TABLE IF NOT EXISTS results (
    job_id         TEXT NOT NULL REFERENCES jobs (id) ON DELETE CASCADE,
    idx            INTEGER NOT NULL,
    classification TEXT NOT NULL,
    format         TEXT NOT NULL,
    file_name      TEXT NOT NULL,
    data           TEXT NOT NULL,
    PRIMARY KEY (job_id, idx)
);

CREATE INDEX IF NOT EXISTS idx_results_classification ON results (job_id, classification);
"""


def empty_counts() -> dict[str, int]:
    return {CLASS_LEGITIMATE: 0, CLASS_FAKE: 0, CLASS_SUSPICIOUS: 0, CLASS_ERROR: 0}


def new_job_id() -> str:
    return str(uuid.uuid4())


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class JobStore:
    """Acceso a la base de datos. Seguro para usar desde varios hilos."""

    def __init__(self, database_path: Path):
        database_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(database_path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._lock = threading.Lock()

        with self._lock, self._connection:
            self._connection.execute("PRAGMA foreign_keys = ON")
            self._connection.execute("PRAGMA journal_mode = WAL")
            self._connection.executescript(_SCHEMA)

    def close(self) -> None:
        with self._lock:
            self._connection.close()

    # --- Trabajos -------------------------------------------------------

    def create_job(self, source: str, params: dict[str, Any],
                   job_id: Optional[str] = None) -> dict[str, Any]:
        """Crea un trabajo en estado 'queued'.

        Se puede pasar el id cuando hace falta conocerlo antes (p. ej. para
        nombrar la carpeta de los archivos subidos).
        """
        job_id = job_id or new_job_id()
        with self._lock, self._connection:
            self._connection.execute(
                "INSERT INTO jobs (id, source, params, status, counts, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (job_id, source, json.dumps(params), STATUS_QUEUED,
                 json.dumps(empty_counts()), _now()),
            )
        return self.get_job(job_id)

    def get_job(self, job_id: str) -> Optional[dict[str, Any]]:
        with self._lock:
            row = self._connection.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        return _job_from_row(row) if row else None

    def list_jobs(self, offset: int = 0, limit: int = 50) -> tuple[list[dict[str, Any]], int]:
        """Devuelve una página de trabajos (los más recientes primero) y el total."""
        with self._lock:
            rows = self._connection.execute(
                "SELECT * FROM jobs ORDER BY created_at DESC LIMIT ? OFFSET ?", (limit, offset)
            ).fetchall()
            total = self._connection.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
        return [_job_from_row(row) for row in rows], total

    def start_job(self, job_id: str, total: int) -> None:
        with self._lock, self._connection:
            self._connection.execute(
                "UPDATE jobs SET status = ?, total = ? WHERE id = ?",
                (STATUS_RUNNING, total, job_id),
            )

    def finish_job(self, job_id: str, status: str, error: Optional[str] = None) -> None:
        with self._lock, self._connection:
            self._connection.execute(
                "UPDATE jobs SET status = ?, error = ?, finished_at = ? WHERE id = ?",
                (status, error, _now(), job_id),
            )

    def mark_interrupted_jobs(self) -> int:
        """Marca como fallidos los trabajos que quedaron a medias.

        Se llama al arrancar: si un trabajo seguía activo, es que el servicio
        se paró mientras lo procesaba.
        """
        with self._lock, self._connection:
            cursor = self._connection.execute(
                f"UPDATE jobs SET status = ?, error = ?, finished_at = ? "
                f"WHERE status IN ({_placeholders(ACTIVE_STATUSES)})",
                (STATUS_FAILED, INTERRUPTED_REASON, _now(), *ACTIVE_STATUSES),
            )
        return cursor.rowcount

    def delete_jobs_finished_before(self, cutoff: datetime) -> list[str]:
        """Borra los trabajos terminados antes de la fecha dada y sus resultados."""
        with self._lock, self._connection:
            rows = self._connection.execute(
                f"SELECT id FROM jobs WHERE finished_at < ? "
                f"AND status IN ({_placeholders(FINISHED_STATUSES)})",
                (cutoff.isoformat(), *FINISHED_STATUSES),
            ).fetchall()
            job_ids = [row["id"] for row in rows]
            self._connection.executemany("DELETE FROM jobs WHERE id = ?", [(i,) for i in job_ids])
        return job_ids

    def delete_jobs_older_than(self, days: int) -> list[str]:
        return self.delete_jobs_finished_before(datetime.now(timezone.utc) - timedelta(days=days))

    # --- Resultados -----------------------------------------------------

    def add_result(self, job_id: str, idx: int, result: dict[str, Any],
                   processed: int, counts: dict[str, int]) -> None:
        """Guarda un resultado y actualiza el progreso del trabajo a la vez."""
        with self._lock, self._connection:
            self._connection.execute(
                "INSERT INTO results (job_id, idx, classification, format, file_name, data) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (job_id, idx, result["classification"], result["format"],
                 result["file_name"], json.dumps(result, ensure_ascii=False)),
            )
            self._connection.execute(
                "UPDATE jobs SET processed = ?, counts = ? WHERE id = ?",
                (processed, json.dumps(counts), job_id),
            )

    def list_results(self, job_id: str, classification: Optional[str] = None,
                     file_format: Optional[str] = None, search: Optional[str] = None,
                     offset: int = 0, limit: Optional[int] = None) -> tuple[list[dict[str, Any]], int]:
        """Devuelve una página de resultados filtrados y el total que cumple el filtro."""
        conditions = ["job_id = ?"]
        values: list[Any] = [job_id]
        if classification:
            conditions.append("classification = ?")
            values.append(classification)
        if file_format:
            conditions.append("format = ?")
            values.append(file_format)
        if search:
            conditions.append("file_name LIKE ?")
            values.append(f"%{search}%")
        where = " AND ".join(conditions)

        with self._lock:
            total = self._connection.execute(
                f"SELECT COUNT(*) FROM results WHERE {where}", values
            ).fetchone()[0]
            rows = self._connection.execute(
                f"SELECT data FROM results WHERE {where} ORDER BY idx LIMIT ? OFFSET ?",
                (*values, -1 if limit is None else limit, offset),
            ).fetchall()
        return [json.loads(row["data"]) for row in rows], total


def _job_from_row(row: sqlite3.Row) -> dict[str, Any]:
    job = dict(row)
    job["params"] = json.loads(job["params"])
    job["counts"] = json.loads(job["counts"])
    return job


def _placeholders(values: tuple) -> str:
    return ", ".join("?" for _ in values)
