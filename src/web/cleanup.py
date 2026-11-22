"""
Limpieza periódica: trabajos caducados y subidas huérfanas.
"""

import logging
import shutil
import time
from pathlib import Path

from src.web.jobs import JobManager
from src.web.store import JobStore

logger = logging.getLogger(__name__)

# Una carpeta de subida sin trabajo activo se considera huérfana pasado este
# tiempo. El margen evita borrar una subida que todavía se está recibiendo.
ORPHAN_UPLOAD_AGE_SECONDS = 60 * 60


def run_cleanup(store: JobStore, manager: JobManager, uploads_dir: Path, retention_days: int) -> None:
    deleted = store.delete_jobs_older_than(retention_days)
    if deleted:
        logger.info("Borrados %d trabajos caducados", len(deleted))

    if not uploads_dir.is_dir():
        return

    now = time.time()
    for upload_dir in uploads_dir.iterdir():
        is_old = now - upload_dir.stat().st_mtime > ORPHAN_UPLOAD_AGE_SECONDS
        if upload_dir.is_dir() and is_old and not manager.is_active(upload_dir.name):
            logger.info("Borrando subida huérfana %s", upload_dir.name)
            shutil.rmtree(upload_dir, ignore_errors=True)
