"""
Navegación por la biblioteca de música montada.
"""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from src.web.dependencies import get_settings
from src.web.paths import PathOutsideLibrary, describe_folder, safe_resolve
from src.web.schemas import LibraryFolder
from src.web.settings import Settings

router = APIRouter(tags=["biblioteca"])


def resolve_library_folder(settings: Settings, relative_path: str) -> Path:
    """Valida una carpeta pedida por el cliente y devuelve su ruta real.

    Lo usan tanto la navegación como la creación de trabajos.
    """
    if not settings.library_available:
        raise HTTPException(status_code=503, detail="No hay ninguna biblioteca de música configurada")

    try:
        folder = safe_resolve(settings.library_root, relative_path)
    except PathOutsideLibrary:
        raise HTTPException(status_code=400, detail="La ruta está fuera de la biblioteca")

    if not folder.is_dir():
        raise HTTPException(status_code=404, detail="La carpeta no existe")
    return folder


@router.get("/library", response_model=LibraryFolder, summary="Contenido de una carpeta de la biblioteca")
def browse_library(path: str = "", settings: Settings = Depends(get_settings)) -> LibraryFolder:
    folder = resolve_library_folder(settings, path)
    return LibraryFolder(**describe_folder(settings.library_root, folder))
