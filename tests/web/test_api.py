"""
Tests de la API: biblioteca, trabajos, resultados, SSE, reportes y limpieza.
"""

import csv
import io
import json
import os
import sqlite3
import time

from src.core import reports
from src.web.cleanup import ORPHAN_UPLOAD_AGE_SECONDS, run_cleanup
from src.web.settings import Settings
from tests.web.conftest import wait_for_job
from tests.web.fakes import ConcurrencyTracker, slow_analyze


# --- Salud y biblioteca -------------------------------------------------------

def test_health(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["version"] == "2.1.0"
    assert body["library_available"] is True
    assert body["max_upload_mb"] == 1


def test_health_and_library_without_library(make_client, tmp_path):
    no_library = Settings(library_root=tmp_path / "no-existe", data_dir=tmp_path / "data2")
    client = make_client(app_settings=no_library)

    assert client.get("/api/health").json()["library_available"] is False
    assert client.get("/api/library").status_code == 503


def test_browse_library_root(client):
    body = client.get("/api/library").json()

    assert body["path"] == ""
    assert body["parent"] is None
    assert [d["name"] for d in body["directories"]] == ["Albums", "Vacia"]
    assert body["audio_files"] == {".mp3": 0, ".flac": 0, ".wav": 1}


def test_browse_subfolder(client):
    body = client.get("/api/library", params={"path": "Albums/2024"}).json()

    assert body["path"] == "Albums/2024"
    assert body["parent"] == "Albums"
    assert body["audio_files"] == {".mp3": 1, ".flac": 2, ".wav": 0}


def test_browse_rejects_path_traversal(client):
    assert client.get("/api/library", params={"path": "../../etc"}).status_code == 400
    assert client.get("/api/library", params={"path": "no-existe"}).status_code == 404


# --- Trabajos de carpeta --------------------------------------------------------

def test_library_job_full_cycle(client):
    response = client.post("/api/jobs", json={"path": "Albums", "recursive": True})
    assert response.status_code == 201
    assert response.json()["status"] in ("queued", "running")

    job = wait_for_job(client, response.json()["id"])

    assert job["status"] == "completed"
    assert job["total"] == job["processed"] == 3
    assert job["counts"] == {"legitimate": 1, "fake": 1, "suspicious": 1, "error": 0}
    assert job["finished_at"] is not None
    assert job["params"] == {"path": "Albums", "recursive": True, "formats": []}


def test_library_job_with_format_filter_and_no_recursion(client):
    job_id = client.post("/api/jobs", json={"path": "", "recursive": False, "formats": ["WAV"]}).json()["id"]
    job = wait_for_job(client, job_id)

    assert job["total"] == 1
    results = client.get(f"/api/jobs/{job_id}/results").json()["items"]
    # Las rutas se muestran relativas a la biblioteca, nunca la ruta del contenedor
    assert results[0]["file_path"] == "suelta.wav"


def test_library_job_on_empty_folder_completes_with_no_results(client):
    job_id = client.post("/api/jobs", json={"path": "Vacia"}).json()["id"]
    job = wait_for_job(client, job_id)

    assert job["status"] == "completed"
    assert job["total"] == 0
    assert client.get(f"/api/jobs/{job_id}/results").json()["total"] == 0


def test_library_job_rejects_bad_input(client):
    assert client.post("/api/jobs", json={"path": "../../etc"}).status_code == 400
    assert client.post("/api/jobs", json={"path": "", "formats": ["ogg"]}).status_code == 400
    assert client.get("/api/jobs").json()["total"] == 0


def test_concurrency_never_exceeds_workers(make_client, library):
    for i in range(12):
        (library / f"extra_{i}.flac").write_bytes(b"x")
    tracker = ConcurrencyTracker()
    client = make_client(analyze=tracker, max_workers=8)   # el pool permitiría 8

    wait_for_job(client, client.post("/api/jobs", json={"path": ""}).json()["id"])

    assert 1 <= tracker.max_running <= 2   # settings.workers == 2


# --- Subidas -----------------------------------------------------------------------

def _files(*names, size=10):
    return [("files", (name, b"x" * size, "application/octet-stream")) for name in names]


def test_upload_job(client, settings):
    response = client.post("/api/jobs/upload", files=_files("uno.flac", "fake.flac", "tres.mp3"))
    assert response.status_code == 201
    job_id = response.json()["id"]

    job = wait_for_job(client, job_id)

    assert job["status"] == "completed"
    assert job["source"] == "upload"
    assert job["total"] == 3
    results = client.get(f"/api/jobs/{job_id}/results").json()["items"]
    # Se muestra el nombre original, no la ruta interna con prefijo
    assert sorted(r["file_path"] for r in results) == ["fake.flac", "tres.mp3", "uno.flac"]
    # Los archivos subidos se borran al terminar
    assert not (settings.uploads_dir / job_id).exists()


def test_upload_sanitizes_file_names(client):
    job_id = client.post("/api/jobs/upload", files=_files("../../evil.flac")).json()["id"]
    wait_for_job(client, job_id)

    results = client.get(f"/api/jobs/{job_id}/results").json()["items"]
    assert results[0]["file_name"] == "evil.flac"


def test_upload_rejects_unsupported_format(client, settings):
    response = client.post("/api/jobs/upload", files=_files("ok.flac", "cancion.ogg"))

    assert response.status_code == 400
    assert ".flac" in response.json()["detail"]
    assert client.get("/api/jobs").json()["total"] == 0
    assert not settings.uploads_dir.exists() or not any(settings.uploads_dir.iterdir())


def test_upload_too_large_leaves_nothing_on_disk(client, settings):
    too_big = settings.max_upload_bytes + 1
    response = client.post("/api/jobs/upload", files=_files("enorme.flac", size=too_big))

    assert response.status_code == 413
    assert client.get("/api/jobs").json()["total"] == 0
    assert not any(settings.uploads_dir.iterdir())


# --- Consulta, filtros y cancelación ------------------------------------------------

def test_unknown_job_returns_404(client):
    assert client.get("/api/jobs/no-existe").status_code == 404
    assert client.get("/api/jobs/no-existe/results").status_code == 404
    assert client.post("/api/jobs/no-existe/cancel").status_code == 404


def test_results_filters_and_pagination(client):
    job_id = client.post("/api/jobs", json={"path": ""}).json()["id"]
    wait_for_job(client, job_id)
    url = f"/api/jobs/{job_id}/results"

    fakes = client.get(url, params={"classification": "fake"}).json()
    assert fakes["total"] == 1 and fakes["items"][0]["file_name"] == "fake.flac"

    flacs = client.get(url, params={"format": "flac"}).json()
    assert {r["file_name"] for r in flacs["items"]} == {"buena.flac", "fake.flac"}

    found = client.get(url, params={"q": "suel"}).json()
    assert [r["file_name"] for r in found["items"]] == ["suelta.wav"]

    page = client.get(url, params={"limit": 2, "offset": 2}).json()
    assert page["total"] == 4 and len(page["items"]) == 2


def test_job_history(client):
    first = client.post("/api/jobs", json={"path": "Vacia"}).json()["id"]
    second = client.post("/api/jobs", json={"path": "Albums"}).json()["id"]
    wait_for_job(client, first)
    wait_for_job(client, second)

    history = client.get("/api/jobs").json()

    assert history["total"] == 2
    assert [job["id"] for job in history["items"]] == [second, first]


def test_cancel_keeps_partial_results(make_client, library, settings):
    for i in range(40):
        (library / f"extra_{i:02d}.flac").write_bytes(b"x")
    client = make_client(analyze=slow_analyze)
    job_id = client.post("/api/jobs", json={"path": ""}).json()["id"]

    while client.get(f"/api/jobs/{job_id}").json()["processed"] < 1:
        time.sleep(0.01)
    assert client.post(f"/api/jobs/{job_id}/cancel").status_code == 200
    job = wait_for_job(client, job_id)

    assert job["status"] == "cancelled"
    assert 1 <= job["processed"] < job["total"]
    assert client.get(f"/api/jobs/{job_id}/results").json()["total"] == job["processed"]
    # Cancelar un trabajo ya terminado no tiene sentido
    assert client.post(f"/api/jobs/{job_id}/cancel").status_code == 409


def test_cancelled_upload_is_cleaned_up(make_client, settings):
    client = make_client(analyze=slow_analyze)
    names = [f"cancion_{i}.flac" for i in range(30)]
    job_id = client.post("/api/jobs/upload", files=_files(*names)).json()["id"]

    client.post(f"/api/jobs/{job_id}/cancel")
    job = wait_for_job(client, job_id)

    assert job["status"] == "cancelled"
    assert not (settings.uploads_dir / job_id).exists()


def test_failed_job_is_cleaned_up(make_client, settings):
    def broken_analyze(path, display_path=None):
        raise RuntimeError("fallo simulado")

    client = make_client(analyze=broken_analyze)
    job_id = client.post("/api/jobs/upload", files=_files("a.flac")).json()["id"]
    job = wait_for_job(client, job_id)

    assert job["status"] == "failed"
    assert "fallo simulado" in job["error"]
    assert not (settings.uploads_dir / job_id).exists()


# --- Progreso por SSE -------------------------------------------------------------

def _read_events(response):
    events = []
    name = None
    for line in response.iter_lines():
        if line.startswith("event: "):
            name = line.removeprefix("event: ")
        elif line.startswith("data: "):
            events.append((name, json.loads(line.removeprefix("data: "))))
            if name == "done":
                break
    return events


def test_events_stream_progress_and_done(make_client):
    client = make_client(analyze=slow_analyze)
    job_id = client.post("/api/jobs", json={"path": ""}).json()["id"]

    with client.stream("GET", f"/api/jobs/{job_id}/events") as response:
        assert response.headers["content-type"].startswith("text/event-stream")
        events = _read_events(response)

    names = [name for name, _ in events]
    assert names.count("done") == 1 and names[-1] == "done"
    processed = [data["job"]["processed"] for name, data in events if name == "progress"]
    assert processed == sorted(processed)          # nunca retrocede
    assert len(processed) > 1                      # llegan avisos intermedios
    assert events[-1][1]["job"]["processed"] == 4
    assert events[-1][1]["job"]["status"] == "completed"


def test_events_for_finished_job_end_immediately(client):
    job_id = client.post("/api/jobs", json={"path": "Vacia"}).json()["id"]
    wait_for_job(client, job_id)

    with client.stream("GET", f"/api/jobs/{job_id}/events") as response:
        events = _read_events(response)

    assert [name for name, _ in events] == ["progress", "done"]


# --- Reportes -----------------------------------------------------------------------

def test_reports_match_cli_export(client):
    job_id = client.post("/api/jobs", json={"path": ""}).json()["id"]
    wait_for_job(client, job_id)
    results = client.get(f"/api/jobs/{job_id}/results").json()["items"]

    csv_response = client.get(f"/api/jobs/{job_id}/report.csv")
    json_response = client.get(f"/api/jobs/{job_id}/report.json")

    assert csv_response.headers["content-type"].startswith("text/csv")
    assert "attachment" in csv_response.headers["content-disposition"]
    assert json_response.headers["content-type"] == "application/json"
    # Mismo contenido que generan las funciones que usa la CLI
    expected_csv = io.StringIO()
    reports.to_csv(results, expected_csv)
    assert csv_response.text == expected_csv.getvalue()
    assert json_response.json() == results
    rows = list(csv.DictReader(io.StringIO(csv_response.text)))
    assert len(rows) == 4 and rows[0]["bitrate"] == "320 kbps"


# --- Limpieza ---------------------------------------------------------------------

def test_cleanup_removes_expired_jobs_and_orphan_uploads(client, settings):
    job_id = client.post("/api/jobs", json={"path": "Vacia"}).json()["id"]
    wait_for_job(client, job_id)
    store = client.app.state.store
    manager = client.app.state.manager

    orphan = settings.uploads_dir / "huerfana"
    orphan.mkdir(parents=True)
    recent = settings.uploads_dir / "recien-subida"
    recent.mkdir()
    old_time = time.time() - ORPHAN_UPLOAD_AGE_SECONDS - 10
    os.utime(orphan, (old_time, old_time))

    # Con la retención normal el trabajo recién terminado se conserva
    run_cleanup(store, manager, settings.uploads_dir, retention_days=30)
    assert store.get_job(job_id) is not None
    assert not orphan.exists()
    assert recent.exists()   # puede ser una subida que aún se está recibiendo

    # Envejecemos el trabajo para que supere el periodo de retención
    with sqlite3.connect(settings.database_path) as connection:
        connection.execute("UPDATE jobs SET finished_at = ? WHERE id = ?",
                           ("2000-01-01T00:00:00+00:00", job_id))
    run_cleanup(store, manager, settings.uploads_dir, retention_days=30)
    assert client.get(f"/api/jobs/{job_id}").status_code == 404


# --- Interfaz web (SPA) -------------------------------------------------------------

def test_spa_is_served_with_fallback(make_client, settings, tmp_path):
    static = tmp_path / "dist"
    (static / "assets").mkdir(parents=True)
    (static / "index.html").write_text("<!doctype html><title>Fake Music Hunter</title>")
    (static / "assets" / "app.js").write_text("console.log('hola')")
    client = make_client(app_settings=settings.model_copy(update={"static_dir": static}))

    root = client.get("/")
    assert root.status_code == 200 and "Fake Music Hunter" in root.text
    # Una ruta interna de la SPA devuelve index.html para que funcione al recargar
    job_page = client.get("/jobs/abc")
    assert job_page.status_code == 200 and job_page.headers["content-type"].startswith("text/html")
    assert client.get("/assets/app.js").text == "console.log('hola')"
    # La API sigue respondiendo JSON, también para rutas que no existen
    assert client.get("/api/health").json()["status"] == "ok"
    unknown = client.get("/api/unknown")
    assert unknown.status_code == 404 and unknown.json()["detail"]
    # No se puede salir de la carpeta estática
    assert "Fake Music Hunter" in client.get("/../../etc/passwd").text


def test_without_static_dir_only_api_is_served(client):
    assert client.get("/").status_code == 404
