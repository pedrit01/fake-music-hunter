"""
Resultado estructurado del análisis de un archivo de audio.
"""

from dataclasses import asdict, dataclass
from typing import Any, Optional


@dataclass
class AnalysisResult:
    """Todo lo que sabemos de un archivo tras analizarlo y clasificarlo.

    Las métricas que no se han podido calcular valen None.
    """

    file_name: str
    file_path: str
    format: str
    classification: str
    reason: str
    bitrate: Optional[int] = None            # bps, tal como lo da mutagen
    sample_rate: Optional[int] = None
    channels: Optional[int] = None
    duration: Optional[float] = None         # segundos
    file_size: Optional[int] = None          # bytes
    cutoff_frequency: Optional[float] = None
    spectral_presence: Optional[float] = None
    high_freq_energy: Optional[float] = None
    has_content_above_20k: Optional[bool] = None
    dynamic_range: Optional[float] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
