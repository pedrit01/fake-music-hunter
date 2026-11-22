"""
Estado del servicio.
"""

from fastapi import APIRouter, Depends

from src import __version__
from src.web.dependencies import get_settings
from src.web.schemas import Health
from src.web.settings import Settings

router = APIRouter(tags=["sistema"])


@router.get("/health", response_model=Health, summary="Estado del servicio")
def health(settings: Settings = Depends(get_settings)) -> Health:
    return Health(status="ok", version=__version__, library_available=settings.library_available,
                  max_upload_mb=settings.max_upload_mb)
