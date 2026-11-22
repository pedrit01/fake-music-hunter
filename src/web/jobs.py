"""
Ejecución de trabajos de análisis en segundo plano.

El análisis consume mucha CPU, así que cada archivo se manda a un pool de
procesos (compartido por todos los trabajos). El bucle de eventos solo
coordina: envía archivos, guarda resultados y avisa a quien esté
escuchando el progreso.
"""

import asyncio
import logging
import shutil
from concurrent.futures import Executor
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Optional

from src.core.result import AnalysisResult
from src.core.service import analyze_file
from src.web.store import (
    STATUS_CANCELLED, STATUS_COMPLETED, STATUS_FAILED, JobStore, empty_counts,
)

logger = logging.getLogger(__name__)

# Firma de la función que analiza un archivo (inyectable en los tests)
AnalyzeFunction = Callable[[Path, Optional[str]], AnalysisResult]


@dataclass
class FileToAnalyze:
    path: Path               # ruta real en disco
    display_path: str        # ruta que verá el usuario


@dataclass
class JobEvent:
    """Aviso que reciben los suscriptores de un trabajo (vía SSE)."""

    name: str                # "progress" o "done"
    job: dict[str, Any]
    last_result: Optional[dict[str, Any]] = None


class JobManager:
    def __init__(self, store: JobStore, executor: Executor, max_in_flight: int,
                 analyze: AnalyzeFunction = analyze_file):
        """
        Args:
            store: Persistencia de trabajos y resultados.
            executor: Pool donde se ejecuta el análisis de cada archivo.
            max_in_flight: Archivos de un mismo trabajo analizándose a la vez.
                Mandarlos poco a poco (y no todos de golpe) permite que la
                cancelación sea inmediata.
            analyze: Función de análisis; los tests la sustituyen.
        """
        self._store = store
        self._executor = executor
        self._max_in_flight = max_in_flight
        self._analyze = analyze
        self._tasks: dict[str, asyncio.Task] = {}
        self._cancel_requested: set[str] = set()
        self._subscribers: dict[str, set[asyncio.Queue]] = {}

    # --- API pública ------------------------------------------------------

    def start(self, job_id: str, list_files: Callable[[], Iterable[FileToAnalyze]],
              cleanup_dir: Optional[Path] = None) -> None:
        """Lanza un trabajo ya creado en el store.

        Args:
            list_files: Devuelve los archivos a analizar. Se llama en un hilo
                aparte, porque recorrer una biblioteca grande puede tardar.
            cleanup_dir: Carpeta que se borra al terminar (archivos subidos).
        """
        task = asyncio.create_task(self._run(job_id, list_files, cleanup_dir))
        self._tasks[job_id] = task
        task.add_done_callback(lambda _: self._tasks.pop(job_id, None))

    def is_active(self, job_id: str) -> bool:
        return job_id in self._tasks

    def cancel(self, job_id: str) -> None:
        """Pide parar un trabajo. Los archivos que ya se están analizando terminan."""
        self._cancel_requested.add(job_id)

    def subscribe(self, job_id: str) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue()
        self._subscribers.setdefault(job_id, set()).add(queue)
        return queue

    def unsubscribe(self, job_id: str, queue: asyncio.Queue) -> None:
        subscribers = self._subscribers.get(job_id)
        if subscribers is not None:
            subscribers.discard(queue)
            if not subscribers:
                del self._subscribers[job_id]

    async def shutdown(self) -> None:
        """Cancela los trabajos en curso (al parar el servicio)."""
        for task in list(self._tasks.values()):
            task.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks.values(), return_exceptions=True)

    # --- Ejecución --------------------------------------------------------

    async def _run(self, job_id: str, list_files: Callable[[], Iterable[FileToAnalyze]],
                   cleanup_dir: Optional[Path]) -> None:
        try:
            files = await asyncio.to_thread(lambda: list(list_files()))
            self._store.start_job(job_id, total=len(files))
            self._publish(job_id, "progress")

            await self._analyze_files(job_id, files)

            final_status = STATUS_CANCELLED if job_id in self._cancel_requested else STATUS_COMPLETED
            self._store.finish_job(job_id, final_status)
        except asyncio.CancelledError:
            self._store.finish_job(job_id, STATUS_FAILED, "El servicio se detuvo durante el análisis")
            raise
        except Exception as error:
            logger.exception("El trabajo %s ha fallado", job_id)
            self._store.finish_job(job_id, STATUS_FAILED, str(error))
        finally:
            self._cancel_requested.discard(job_id)
            if cleanup_dir is not None:
                shutil.rmtree(cleanup_dir, ignore_errors=True)
            self._publish(job_id, "done")

    async def _analyze_files(self, job_id: str, files: list[FileToAnalyze]) -> None:
        loop = asyncio.get_running_loop()
        pending = iter(files)
        in_flight: set[asyncio.Future] = set()
        processed = 0
        counts = empty_counts()

        while True:
            # Rellenamos la ventana de archivos en análisis, salvo si nos han cancelado
            while job_id not in self._cancel_requested and len(in_flight) < self._max_in_flight:
                next_file = next(pending, None)
                if next_file is None:
                    break
                in_flight.add(loop.run_in_executor(
                    self._executor, self._analyze, next_file.path, next_file.display_path))

            if not in_flight:
                return

            finished, in_flight = await asyncio.wait(in_flight, return_when=asyncio.FIRST_COMPLETED)
            for future in finished:
                result = future.result().to_dict()
                processed += 1
                counts[result["classification"]] = counts.get(result["classification"], 0) + 1
                self._store.add_result(job_id, processed, result, processed, counts)
                self._publish(job_id, "progress", last_result=result)

    def _publish(self, job_id: str, name: str, last_result: Optional[dict] = None) -> None:
        subscribers = self._subscribers.get(job_id)
        if not subscribers:
            return
        event = JobEvent(name=name, job=self._store.get_job(job_id), last_result=last_result)
        for queue in subscribers:
            queue.put_nowait(event)
