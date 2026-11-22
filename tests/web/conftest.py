"""
Fixtures comunes: biblioteca de prueba, configuración y cliente de la API.
"""

import time
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from src.web.app import create_app
from src.web.settings import Settings
from tests.web.fakes import quick_analyze

FINISHED = {"completed", "failed", "cancelled"}


@pytest.fixture
def library(tmp_path):
    """Biblioteca falsa: el contenido de los archivos da igual con quick_analyze."""
    root = tmp_path / "music"
    (root / "Albums" / "2024").mkdir(parents=True)
    (root / "Vacia").mkdir()
    (root / "Albums" / "2024" / "buena.flac").write_bytes(b"x")
    (root / "Albums" / "2024" / "fake.flac").write_bytes(b"x")
    (root / "Albums" / "2024" / "sospechoso.mp3").write_bytes(b"x")
    (root / "Albums" / "notas.txt").write_text("no es audio")
    (root / "suelta.wav").write_bytes(b"x")
    return root


@pytest.fixture
def settings(tmp_path, library):
    return Settings(library_root=library, data_dir=tmp_path / "data", workers=2, max_upload_mb=1)


@pytest.fixture
def make_client(settings):
    """Crea un cliente con la función de análisis y el pool que pida cada test."""
    clients = []

    def _make(analyze=quick_analyze, app_settings=None, max_workers=4):
        app = create_app(app_settings or settings, executor=ThreadPoolExecutor(max_workers=max_workers),
                         analyze=analyze)
        client = TestClient(app)
        client.__enter__()   # arranca el lifespan (store, manager…)
        clients.append(client)
        return client

    yield _make
    for client in clients:
        client.__exit__(None, None, None)


@pytest.fixture
def client(make_client):
    return make_client()


def wait_for_job(client, job_id, timeout=10):
    """Espera a que un trabajo termine y devuelve su estado final."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        job = client.get(f"/api/jobs/{job_id}").json()
        if job["status"] in FINISHED:
            return job
        time.sleep(0.02)
    raise AssertionError(f"El trabajo {job_id} no terminó en {timeout} s")
