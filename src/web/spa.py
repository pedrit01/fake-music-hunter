"""
Sirve la interfaz web compilada (frontend/dist) desde la propia API.

La SPA gestiona sus rutas en el navegador (/jobs/abc…), así que cualquier
ruta que no sea de la API ni un archivo estático devuelve index.html.
"""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse


def mount_spa(app: FastAPI, static_dir: Path) -> None:
    root = static_dir.resolve()
    index = root / "index.html"

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_spa(full_path: str) -> FileResponse:
        # Una ruta de la API inexistente debe dar 404 en JSON, no la SPA
        if full_path == "api" or full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Ruta no encontrada")

        candidate = (root / full_path).resolve()
        if candidate.is_relative_to(root) and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(index)
