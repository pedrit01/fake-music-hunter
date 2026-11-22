"""
Tests de configuración, persistencia y confinamiento de rutas.
"""

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.web.paths import PathOutsideLibrary, iter_library_files, safe_resolve
from src.web.settings import Settings
from src.web.store import JobStore


# --- Configuración ----------------------------------------------------------

def test_settings_defaults(monkeypatch):
    for name in list(os.environ):
        if name.startswith("FMH_"):
            monkeypatch.delenv(name)

    settings = Settings()

    assert settings.library_root == Path("/music")
    assert settings.data_dir == Path("/data")
    assert settings.port == 8000
    assert settings.max_upload_mb == 500
    assert settings.retention_days == 30
    assert settings.workers >= 1


def test_settings_from_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("FMH_LIBRARY_ROOT", str(tmp_path))
    monkeypatch.setenv("FMH_WORKERS", "4")
    monkeypatch.setenv("FMH_MAX_UPLOAD_MB", "50")
    monkeypatch.setenv("FMH_RETENTION_DAYS", "7")

    settings = Settings()

    assert settings.library_root == tmp_path
    assert settings.workers == 4
    assert settings.max_upload_bytes == 50 * 1024 * 1024
    assert settings.retention_days == 7
    assert settings.library_available


# --- Persistencia -------------------------------------------------------------

def _result(name, classification):
    return {"file_name": name, "format": Path(name).suffix, "classification": classification}


def test_store_saves_results_and_progress(tmp_path):
    store = JobStore(tmp_path / "db.sqlite3")
    job = store.create_job("library", {"path": ""})
    store.start_job(job["id"], total=2)

    store.add_result(job["id"], 1, _result("a.flac", "fake"), processed=1, counts={"fake": 1})
    store.add_result(job["id"], 2, _result("b.mp3", "legitimate"), processed=2,
                     counts={"fake": 1, "legitimate": 1})

    saved = store.get_job(job["id"])
    assert saved["status"] == "running"
    assert saved["processed"] == 2
    assert saved["counts"] == {"fake": 1, "legitimate": 1}

    fakes, total = store.list_results(job["id"], classification="fake")
    assert total == 1 and fakes[0]["file_name"] == "a.flac"
    mp3s, _ = store.list_results(job["id"], file_format=".mp3")
    assert [r["file_name"] for r in mp3s] == ["b.mp3"]


def test_store_survives_restart_and_marks_interrupted_jobs(tmp_path):
    database = tmp_path / "db.sqlite3"
    store = JobStore(database)
    finished = store.create_job("library", {})
    store.finish_job(finished["id"], "completed")
    running = store.create_job("library", {})
    store.start_job(running["id"], total=10)
    store.close()

    reopened = JobStore(database)
    assert reopened.mark_interrupted_jobs() == 1

    assert reopened.get_job(finished["id"])["status"] == "completed"
    interrupted = reopened.get_job(running["id"])
    assert interrupted["status"] == "failed"
    assert "reinicio" in interrupted["error"]


def test_store_deletes_only_old_finished_jobs(tmp_path):
    store = JobStore(tmp_path / "db.sqlite3")
    old = store.create_job("library", {})
    store.finish_job(old["id"], "completed")
    store.add_result(old["id"], 1, _result("a.flac", "fake"), processed=1, counts={})
    active = store.create_job("library", {})

    deleted = store.delete_jobs_finished_before(datetime.now(timezone.utc) + timedelta(seconds=1))

    assert deleted == [old["id"]]
    assert store.get_job(old["id"]) is None
    assert store.list_results(old["id"])[1] == 0
    assert store.get_job(active["id"]) is not None


# --- Rutas ----------------------------------------------------------------------

@pytest.mark.parametrize("bad_path", ["..", "../../etc", "Albums/../../etc", "/etc", "/"])
def test_safe_resolve_rejects_paths_outside_library(library, bad_path):
    with pytest.raises(PathOutsideLibrary):
        safe_resolve(library, bad_path)


def test_safe_resolve_rejects_symlink_leaving_library(library, tmp_path):
    outside = tmp_path / "fuera"
    outside.mkdir()
    (library / "enlace").symlink_to(outside)

    with pytest.raises(PathOutsideLibrary):
        safe_resolve(library, "enlace")


def test_safe_resolve_accepts_paths_inside(library):
    assert safe_resolve(library, "") == library.resolve()
    assert safe_resolve(library, "Albums/2024") == (library / "Albums" / "2024").resolve()


def test_scan_skips_files_linked_from_outside(library, tmp_path):
    secret = tmp_path / "secreto.flac"
    secret.write_bytes(b"x")
    (library / "enlace.flac").symlink_to(secret)

    found = [p.name for p in iter_library_files(library, library, recursive=True, formats=[])]

    assert "enlace.flac" not in found
    assert sorted(found) == ["buena.flac", "fake.flac", "sospechoso.mp3", "suelta.wav"]
