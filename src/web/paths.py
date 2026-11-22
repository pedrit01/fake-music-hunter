"""
Acceso seguro a la biblioteca de música.

Toda ruta que llega de un cliente es relativa a la raíz de la biblioteca y
nunca puede salir de ella (ni con '..', ni con rutas absolutas, ni
siguiendo enlaces simbólicos).
"""

from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Iterator

from src.config import SUPPORTED_FORMATS
from src.scanner import AudioScanner


class PathOutsideLibrary(ValueError):
    """La ruta pedida apunta fuera de la biblioteca."""


def safe_resolve(library_root: Path, relative_path: str) -> Path:
    """Convierte una ruta relativa del cliente en una ruta real dentro de la biblioteca.

    Raises:
        PathOutsideLibrary: si la ruta es absoluta, usa '..' o, una vez
            resueltos los enlaces simbólicos, queda fuera de la raíz.
    """
    relative = PurePosixPath(relative_path.strip() or ".")
    if relative.is_absolute() or ".." in relative.parts:
        raise PathOutsideLibrary(relative_path)

    root = library_root.resolve()
    resolved = (root / relative).resolve()
    if not resolved.is_relative_to(root):
        raise PathOutsideLibrary(relative_path)
    return resolved


def is_inside(library_root: Path, path: Path) -> bool:
    return path.resolve().is_relative_to(library_root.resolve())


def relative_to_library(library_root: Path, path: Path) -> str:
    """Ruta que se muestra al cliente, siempre relativa y con '/'."""
    relative = path.resolve().relative_to(library_root.resolve())
    return relative.as_posix() if relative.parts else ""


def iter_library_files(library_root: Path, folder: Path, recursive: bool,
                       formats: list[str]) -> Iterator[Path]:
    """Archivos de audio de una carpeta, descartando los que salen de la biblioteca."""
    scanner = AudioScanner(str(folder), recursive=recursive, formats=formats or SUPPORTED_FORMATS)
    for path in sorted(scanner.scan()):
        if is_inside(library_root, path):
            yield path


def describe_folder(library_root: Path, folder: Path) -> dict:
    """Subcarpetas y número de archivos de audio (por formato) de una carpeta."""
    directories = []
    counts = Counter({fmt: 0 for fmt in SUPPORTED_FORMATS})

    for entry in sorted(folder.iterdir(), key=lambda p: p.name.lower()):
        # Saltamos ocultos y cualquier cosa que apunte fuera de la biblioteca
        if entry.name.startswith(".") or not is_inside(library_root, entry):
            continue
        if entry.is_dir():
            directories.append({"name": entry.name, "path": relative_to_library(library_root, entry)})
        elif entry.is_file() and entry.suffix.lower() in SUPPORTED_FORMATS:
            counts[entry.suffix.lower()] += 1

    current = relative_to_library(library_root, folder)
    parent = None if current == "" else relative_to_library(library_root, folder.parent)

    return {
        "path": current,
        "parent": parent,
        "directories": directories,
        "audio_files": dict(counts),
    }
