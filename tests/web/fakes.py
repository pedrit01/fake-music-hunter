"""
Sustitutos del análisis real para los tests de la API.

Clasifican por el nombre del archivo, así los tests son rápidos y no
dependen de librosa ni de audio de verdad.
"""

import threading
import time
from pathlib import Path
from typing import Optional

from src.core.result import AnalysisResult


def quick_analyze(path: Path, display_path: Optional[str] = None) -> AnalysisResult:
    name = Path(display_path or path).name
    if "fake" in name:
        classification = "fake"
    elif "sospechoso" in name:
        classification = "suspicious"
    else:
        classification = "legitimate"

    return AnalysisResult(
        file_name=name,
        file_path=display_path or str(path),
        format=Path(name).suffix.lower(),
        classification=classification,
        reason=f"clasificado como {classification} por el nombre",
        bitrate=320000,
    )


def slow_analyze(path: Path, display_path: Optional[str] = None) -> AnalysisResult:
    time.sleep(0.05)
    return quick_analyze(path, display_path)


class ConcurrencyTracker:
    """Mide cuántos análisis se ejecutan a la vez."""

    def __init__(self):
        self._lock = threading.Lock()
        self._running = 0
        self.max_running = 0

    def __call__(self, path: Path, display_path: Optional[str] = None) -> AnalysisResult:
        with self._lock:
            self._running += 1
            self.max_running = max(self.max_running, self._running)
        try:
            time.sleep(0.02)
            return quick_analyze(path, display_path)
        finally:
            with self._lock:
                self._running -= 1
