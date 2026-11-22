"""
Exportación de resultados a CSV y JSON.

Las funciones no modifican los resultados que reciben, así que se pueden
exportar los mismos datos a varios formatos y en cualquier orden.
"""

import csv
import json
from typing import Any, Iterable, TextIO, Union

from src.core.result import AnalysisResult

# Columnas del CSV, en orden
CSV_FIELDS = [
    "file_name",
    "file_path",
    "classification",
    "reason",
    "format",
    "bitrate",
    "sample_rate",
    "cutoff_frequency",
    "spectral_presence",
    "dynamic_range",
    "file_size",
]

ResultLike = Union[AnalysisResult, dict[str, Any]]


def to_csv(results: Iterable[ResultLike], output: TextIO) -> None:
    """Escribe los resultados como CSV (bitrate en kbps para que sea legible)."""
    writer = csv.DictWriter(output, fieldnames=CSV_FIELDS, extrasaction="ignore")
    writer.writeheader()

    for result in results:
        row = _as_dict(result)
        if row.get("bitrate"):
            row["bitrate"] = f"{row['bitrate'] / 1000:.0f} kbps"
        writer.writerow(row)


def to_json(results: Iterable[ResultLike], output: TextIO) -> None:
    """Escribe los resultados como una lista JSON (bitrate numérico en bps)."""
    rows = [_as_dict(result) for result in results]
    json.dump(rows, output, indent=2, ensure_ascii=False)


def _as_dict(result: ResultLike) -> dict[str, Any]:
    """Devuelve siempre una copia, para no tocar los datos originales."""
    if isinstance(result, AnalysisResult):
        return result.to_dict()
    return dict(result)
