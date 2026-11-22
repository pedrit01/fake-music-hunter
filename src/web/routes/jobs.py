"""
Trabajos de análisis: creación, progreso, resultados, reportes y cancelación.
"""

import asyncio
import io
import json
import shutil
from pathlib import Path, PurePath
from typing import Literal, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import Response, StreamingResponse

from src.config import SUPPORTED_FORMATS
from src.core import reports
from src.web.dependencies import get_job_or_404, get_manager, get_settings, get_store
from src.web.jobs import FileToAnalyze, JobManager
from src.web.paths import iter_library_files, relative_to_library
from src.web.routes.library import resolve_library_folder
from src.web.schemas import Job, JobPage, LibraryJobRequest, ResultPage
from src.web.settings import Settings
from src.web.store import SOURCE_LIBRARY, SOURCE_UPLOAD, JobStore, new_job_id

router = APIRouter(prefix="/jobs", tags=["trabajos"])

# Tamaño de cada bloque al guardar una subida en disco
UPLOAD_CHUNK_BYTES = 1024 * 1024
# Valores admitidos para filtrar y ordenar resultados (FastAPI responde 422 con otros)
ClassificationParam = Literal["legitimate", "fake", "suspicious", "error"]
SortParam = Literal["severity", "file_name", "format", "bitrate", "cutoff_frequency", "spectral_presence"]
# Cada cuánto se manda un comentario por SSE para que los proxies no corten
SSE_KEEPALIVE_SECONDS = 15


# --- Creación -------------------------------------------------------------

# Las rutas que lanzan trabajos son async: el trabajo se crea como tarea del
# bucle de eventos, y eso solo se puede hacer desde el propio bucle.
@router.post("", response_model=Job, status_code=201, summary="Analizar una carpeta de la biblioteca")
async def create_library_job(
    request: LibraryJobRequest,
    settings: Settings = Depends(get_settings),
    store: JobStore = Depends(get_store),
    manager: JobManager = Depends(get_manager),
) -> dict:
    folder = resolve_library_folder(settings, request.path)
    formats = _normalize_formats(request.formats)
    library_root = settings.library_root

    def list_files():
        for path in iter_library_files(library_root, folder, request.recursive, formats):
            yield FileToAnalyze(path=path, display_path=relative_to_library(library_root, path))

    params = {"path": relative_to_library(library_root, folder),
              "recursive": request.recursive, "formats": formats}
    job = store.create_job(SOURCE_LIBRARY, params)
    manager.start(job["id"], list_files)
    return job


@router.post("/upload", response_model=Job, status_code=201, summary="Analizar archivos subidos")
async def create_upload_job(
    files: list[UploadFile] = File(description="Archivos .mp3, .flac o .wav"),
    settings: Settings = Depends(get_settings),
    store: JobStore = Depends(get_store),
    manager: JobManager = Depends(get_manager),
) -> dict:
    # Validamos todas las extensiones antes de escribir nada en disco
    names = [_safe_upload_name(upload.filename) for upload in files]
    for name in names:
        if Path(name).suffix.lower() not in SUPPORTED_FORMATS:
            allowed = ", ".join(SUPPORTED_FORMATS)
            raise HTTPException(status_code=400,
                                detail=f"Formato no soportado: {name}. Formatos admitidos: {allowed}")

    job_id = new_job_id()
    upload_dir = settings.uploads_dir / job_id
    upload_dir.mkdir(parents=True)

    to_analyze = []
    try:
        for index, (upload, name) in enumerate(zip(files, names)):
            # El prefijo evita colisiones si dos archivos se llaman igual
            destination = upload_dir / f"{index:04d}_{name}"
            await _save_upload(upload, destination, name, settings.max_upload_bytes)
            to_analyze.append(FileToAnalyze(path=destination, display_path=name))
    except BaseException:
        shutil.rmtree(upload_dir, ignore_errors=True)
        raise

    job = store.create_job(SOURCE_UPLOAD, {"files": names}, job_id=job_id)
    manager.start(job_id, lambda: to_analyze, cleanup_dir=upload_dir)
    return job


# --- Consulta ---------------------------------------------------------------

@router.get("", response_model=JobPage, summary="Historial de trabajos")
def list_jobs(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    store: JobStore = Depends(get_store),
) -> JobPage:
    jobs, total = store.list_jobs(offset=offset, limit=limit)
    return JobPage(items=jobs, total=total, offset=offset, limit=limit)


@router.get("/{job_id}", response_model=Job, summary="Estado y progreso de un trabajo")
def get_job(job_id: str, store: JobStore = Depends(get_store)) -> dict:
    return get_job_or_404(store, job_id)


@router.get("/{job_id}/results", response_model=ResultPage, summary="Resultados de un trabajo")
def list_results(
    job_id: str,
    classification: Optional[list[ClassificationParam]] = Query(
        None, description="Una o varias clasificaciones: ?classification=fake&classification=suspicious"),
    format: Optional[str] = Query(None, description="Extensión, p. ej. flac o .flac"),
    q: Optional[str] = Query(None, description="Texto a buscar en el nombre del archivo"),
    sort: Optional[SortParam] = Query(
        None, description="Orden en el servidor; severity = fake, suspicious, error, legitimate. "
                          "Sin él, orden de llegada"),
    order: Literal["asc", "desc"] = Query("asc", description="Sentido del orden"),
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    store: JobStore = Depends(get_store),
) -> ResultPage:
    get_job_or_404(store, job_id)
    file_format = _normalize_formats([format])[0] if format else None
    items, total = store.list_results(job_id, classification=classification, file_format=file_format,
                                      search=q, offset=offset, limit=limit, sort=sort, order=order)
    return ResultPage(items=items, total=total, offset=offset, limit=limit)


@router.get("/{job_id}/events", summary="Progreso en tiempo real (Server-Sent Events)")
async def job_events(
    job_id: str,
    store: JobStore = Depends(get_store),
    manager: JobManager = Depends(get_manager),
) -> StreamingResponse:
    get_job_or_404(store, job_id)
    # Nos suscribimos antes de mirar el estado, para no perder el aviso final
    queue = manager.subscribe(job_id)

    async def stream():
        try:
            yield _sse("progress", {"job": store.get_job(job_id)})
            if not manager.is_active(job_id):
                yield _sse("done", {"job": store.get_job(job_id)})
                return

            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), SSE_KEEPALIVE_SECONDS)
                except TimeoutError:
                    yield ": keep-alive\n\n"
                    continue
                yield _sse(event.name, {"job": event.job, "last_result": event.last_result})
                if event.name == "done":
                    return
        finally:
            manager.unsubscribe(job_id, queue)

    return StreamingResponse(stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


# --- Reportes y cancelación ---------------------------------------------------

@router.get("/{job_id}/report.csv", summary="Descargar el reporte en CSV")
def download_csv(job_id: str, store: JobStore = Depends(get_store)) -> Response:
    get_job_or_404(store, job_id)
    results, _ = store.list_results(job_id)
    output = io.StringIO()
    reports.to_csv(results, output)
    return _download(output.getvalue(), "text/csv; charset=utf-8", f"fake-music-hunter-{job_id[:8]}.csv")


@router.get("/{job_id}/report.json", summary="Descargar el reporte en JSON")
def download_json(job_id: str, store: JobStore = Depends(get_store)) -> Response:
    get_job_or_404(store, job_id)
    results, _ = store.list_results(job_id)
    output = io.StringIO()
    reports.to_json(results, output)
    return _download(output.getvalue(), "application/json", f"fake-music-hunter-{job_id[:8]}.json")


@router.post("/{job_id}/cancel", response_model=Job, summary="Cancelar un trabajo en curso")
def cancel_job(
    job_id: str,
    store: JobStore = Depends(get_store),
    manager: JobManager = Depends(get_manager),
) -> dict:
    get_job_or_404(store, job_id)
    if not manager.is_active(job_id):
        raise HTTPException(status_code=409, detail="El trabajo ya ha terminado")
    manager.cancel(job_id)
    return store.get_job(job_id)


# --- Utilidades ---------------------------------------------------------------

def _normalize_formats(formats: list[str]) -> list[str]:
    """Acepta 'flac', '.flac' o 'FLAC' y devuelve '.flac'. Rechaza los no soportados."""
    normalized = []
    for fmt in formats:
        extension = "." + fmt.strip().lower().lstrip(".")
        if extension not in SUPPORTED_FORMATS:
            allowed = ", ".join(SUPPORTED_FORMATS)
            raise HTTPException(status_code=400,
                                detail=f"Formato no soportado: {fmt}. Formatos admitidos: {allowed}")
        normalized.append(extension)
    return normalized


def _safe_upload_name(filename: Optional[str]) -> str:
    """Se queda solo con el nombre, sin carpetas (evita escribir fuera de la subida)."""
    name = PurePath((filename or "").replace("\\", "/")).name.strip()
    if not name or name in (".", ".."):
        raise HTTPException(status_code=400, detail="Archivo sin nombre")
    return name


async def _save_upload(upload: UploadFile, destination: Path, name: str, max_bytes: int) -> None:
    written = 0
    with open(destination, "wb") as output:
        while chunk := await upload.read(UPLOAD_CHUNK_BYTES):
            written += len(chunk)
            if written > max_bytes:
                limit_mb = max_bytes / (1024 * 1024)
                raise HTTPException(status_code=413,
                                    detail=f"{name} supera el tamaño máximo de {limit_mb:g} MB")
            output.write(chunk)


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _download(content: str, media_type: str, filename: str) -> Response:
    return Response(content=content, media_type=media_type,
                    headers={"Content-Disposition": f'attachment; filename="{filename}"'})
