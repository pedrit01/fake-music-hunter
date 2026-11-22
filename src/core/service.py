"""
Servicio de análisis: analiza archivos y los clasifica.

Es el único punto de entrada al análisis; lo usan la CLI y la API web.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Optional

from src.analyzer import AudioAnalyzer
from src.config import CLASS_ERROR
from src.core.result import AnalysisResult
from src.detector import FakeDetector

logger = logging.getLogger(__name__)


@dataclass
class Progress:
    """Aviso de progreso que se emite tras analizar cada archivo."""

    processed: int
    total: int
    result: AnalysisResult


def analyze_file(path: Path, display_path: Optional[str] = None) -> AnalysisResult:
    """Analiza un archivo y devuelve su resultado.

    Nunca lanza excepciones: cualquier fallo se devuelve como un resultado
    con clasificación 'error', para que un archivo malo no pare un lote.

    Args:
        path: Ruta real del archivo en disco.
        display_path: Ruta que se mostrará en el resultado. Sirve para no
            exponer rutas internas (por ejemplo, en archivos subidos).
    """
    path = Path(path)
    shown_path = display_path or str(path)

    try:
        analysis = AudioAnalyzer(path).analyze()
        classification, reason = FakeDetector.detect(analysis)
    except Exception as error:
        logger.exception("Fallo inesperado analizando %s", path)
        return AnalysisResult(
            file_name=path.name,
            file_path=shown_path,
            format=path.suffix.lower(),
            classification=CLASS_ERROR,
            reason=f"Error inesperado durante el análisis: {error}",
        )

    return AnalysisResult(
        file_name=path.name,
        file_path=shown_path,
        # Si mutagen no pudo leer los metadatos, el formato sale de la extensión
        format=analysis.get("format") or path.suffix.lower(),
        classification=classification,
        reason=reason,
        bitrate=_to_int(analysis.get("bitrate")),
        sample_rate=_to_int(analysis.get("sample_rate")),
        channels=_to_int(analysis.get("channels")),
        duration=_to_float(analysis.get("length")),
        file_size=_to_int(analysis.get("file_size")),
        cutoff_frequency=_to_float(analysis.get("cutoff_frequency")),
        spectral_presence=_to_float(analysis.get("spectral_presence")),
        high_freq_energy=_to_float(analysis.get("high_freq_energy")),
        has_content_above_20k=_to_bool(analysis.get("has_content_above_20k")),
        dynamic_range=_to_float(analysis.get("dynamic_range")),
    )


def analyze_many(
    paths: Iterable[Path],
    on_progress: Optional[Callable[[Progress], None]] = None,
    should_cancel: Optional[Callable[[], bool]] = None,
) -> list[AnalysisResult]:
    """Analiza varios archivos uno tras otro.

    Args:
        paths: Archivos a analizar.
        on_progress: Se llama tras cada archivo con el progreso acumulado.
        should_cancel: Se consulta antes de cada archivo; si devuelve True,
            se detiene y se devuelven los resultados obtenidos hasta ahí.
    """
    paths = list(paths)
    results: list[AnalysisResult] = []

    for path in paths:
        if should_cancel is not None and should_cancel():
            break

        result = analyze_file(path)
        results.append(result)

        if on_progress is not None:
            on_progress(Progress(processed=len(results), total=len(paths), result=result))

    return results


# Las métricas llegan como tipos de numpy; las pasamos a tipos de Python
# para que se puedan serializar a JSON sin sorpresas.

def _to_int(value) -> Optional[int]:
    return None if value is None else int(value)


def _to_float(value) -> Optional[float]:
    return None if value is None else float(value)


def _to_bool(value) -> Optional[bool]:
    return None if value is None else bool(value)
