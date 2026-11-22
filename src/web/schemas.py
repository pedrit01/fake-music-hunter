"""
Modelos de entrada y salida de la API (los que aparecen en /docs).
"""

from typing import Any, Optional

from pydantic import BaseModel, Field


class Health(BaseModel):
    status: str
    version: str
    library_available: bool
    max_upload_mb: float


class LibraryDirectory(BaseModel):
    name: str
    path: str


class LibraryFolder(BaseModel):
    path: str = Field(description="Ruta relativa a la raíz de la biblioteca ('' es la raíz)")
    parent: Optional[str]
    directories: list[LibraryDirectory]
    audio_files: dict[str, int] = Field(description="Archivos de audio en esta carpeta, por formato")


class LibraryJobRequest(BaseModel):
    path: str = Field(default="", description="Carpeta relativa a la raíz de la biblioteca")
    recursive: bool = True
    formats: list[str] = Field(default_factory=list, description="Vacío = todos (mp3, flac, wav)")


class Job(BaseModel):
    id: str
    source: str
    params: dict[str, Any]
    status: str
    total: int
    processed: int
    counts: dict[str, int]
    error: Optional[str]
    created_at: str
    finished_at: Optional[str]


class JobPage(BaseModel):
    items: list[Job]
    total: int
    offset: int
    limit: int


class ResultPage(BaseModel):
    items: list[dict[str, Any]]
    total: int
    offset: int
    limit: int
