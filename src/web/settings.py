"""
Configuración del servicio web, leída de variables de entorno FMH_*.
"""

import os
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_workers() -> int:
    return min(2, os.cpu_count() or 1)


class Settings(BaseSettings):
    """Cada campo se puede sobrescribir con FMH_<NOMBRE>, p. ej. FMH_WORKERS=4."""

    model_config = SettingsConfigDict(env_prefix="FMH_")

    # Carpeta de música que se puede navegar y analizar (solo lectura)
    library_root: Path = Path("/music")
    # Carpeta escribible para la base de datos, subidas y reportes
    data_dir: Path = Path("/data")
    port: int = 8000
    # Número máximo de archivos analizándose a la vez
    workers: int = Field(default_factory=_default_workers, ge=1)
    # Tamaño máximo de cada archivo subido, en megabytes
    max_upload_mb: float = Field(default=500, gt=0)
    # Días que se conservan los trabajos terminados
    retention_days: int = Field(default=30, ge=1)
    # Carpeta con la interfaz web compilada; si no existe, solo se sirve la API
    static_dir: Optional[Path] = None

    @property
    def library_available(self) -> bool:
        return self.library_root.is_dir()

    @property
    def database_path(self) -> Path:
        return self.data_dir / "fmh.sqlite3"

    @property
    def uploads_dir(self) -> Path:
        return self.data_dir / "uploads"

    @property
    def max_upload_bytes(self) -> int:
        return int(self.max_upload_mb * 1024 * 1024)
