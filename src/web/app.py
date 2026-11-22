"""
Aplicación FastAPI de Fake Music Hunter.

Arranque local:
    uvicorn src.web.app:create_app --factory --host 0.0.0.0 --port 8000
"""

import asyncio
import logging
import multiprocessing
from concurrent.futures import Executor, ProcessPoolExecutor
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI

from src import __version__
from src.core.service import analyze_file
from src.web.cleanup import run_cleanup
from src.web.jobs import AnalyzeFunction, JobManager
from src.web.routes import jobs, library, system
from src.web.settings import Settings
from src.web.spa import mount_spa
from src.web.store import JobStore

logger = logging.getLogger(__name__)

CLEANUP_INTERVAL_SECONDS = 60 * 60


def create_app(settings: Optional[Settings] = None, executor: Optional[Executor] = None,
               analyze: AnalyzeFunction = analyze_file) -> FastAPI:
    """Crea la aplicación.

    Args:
        settings: Configuración; por defecto se lee de las variables FMH_*.
        executor: Pool donde se analizan los archivos. Por defecto, un pool
            de procesos con FMH_WORKERS procesos. Los tests pasan uno propio.
        analyze: Función de análisis de un archivo (los tests la sustituyen).
    """
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        settings.data_dir.mkdir(parents=True, exist_ok=True)
        store = JobStore(settings.database_path)
        interrupted = store.mark_interrupted_jobs()
        if interrupted:
            logger.warning("%d trabajos quedaron interrumpidos por un reinicio", interrupted)

        # 'spawn' arranca procesos limpios: hacer fork de un servidor con
        # hilos puede dejar bloqueos heredados en el proceso hijo.
        pool = executor or ProcessPoolExecutor(
            max_workers=settings.workers, mp_context=multiprocessing.get_context("spawn"))
        manager = JobManager(store, pool, max_in_flight=settings.workers, analyze=analyze)

        app.state.settings = settings
        app.state.store = store
        app.state.manager = manager

        cleanup_task = asyncio.create_task(_cleanup_periodically(store, manager, settings))
        try:
            yield
        finally:
            cleanup_task.cancel()
            await manager.shutdown()
            if executor is None:
                pool.shutdown(cancel_futures=True)
            store.close()

    app = FastAPI(title="Fake Music Hunter", version=__version__, lifespan=lifespan,
                  description="Detección de archivos de audio falsos o upscaleados.")
    app.include_router(system.router, prefix="/api")
    app.include_router(library.router, prefix="/api")
    app.include_router(jobs.router, prefix="/api")

    # La interfaz web va al final: su ruta comodín no debe tapar la API
    if settings.static_dir is not None:
        if (settings.static_dir / "index.html").is_file():
            mount_spa(app, settings.static_dir)
        else:
            logger.warning("FMH_STATIC_DIR=%s no contiene index.html; solo se sirve la API",
                           settings.static_dir)
    return app


async def _cleanup_periodically(store: JobStore, manager: JobManager, settings: Settings) -> None:
    while True:
        try:
            run_cleanup(store, manager, settings.uploads_dir, settings.retention_days)
        except Exception:
            logger.exception("Fallo en la limpieza periódica")
        await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)
