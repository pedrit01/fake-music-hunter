"""
Acceso a los objetos compartidos de la aplicación desde las rutas.
"""

from fastapi import HTTPException, Request

from src.web.jobs import JobManager
from src.web.settings import Settings
from src.web.store import JobStore


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_store(request: Request) -> JobStore:
    return request.app.state.store


def get_manager(request: Request) -> JobManager:
    return request.app.state.manager


def get_job_or_404(store: JobStore, job_id: str) -> dict:
    job = store.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Trabajo no encontrado")
    return job
