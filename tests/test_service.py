"""
Tests del servicio de análisis con audio sintético.
"""

import dataclasses

import numpy as np
import pytest
import soundfile as sf

from src.core.result import AnalysisResult
from src.core.service import analyze_file, analyze_many

SAMPLE_RATE = 44100
DURATION_SECONDS = 3


def _white_noise() -> np.ndarray:
    rng = np.random.default_rng(seed=42)
    return rng.uniform(-0.5, 0.5, SAMPLE_RATE * DURATION_SECONDS)


def _low_pass(signal: np.ndarray, cutoff_hz: float) -> np.ndarray:
    """Filtro ideal: anula todo el espectro por encima del corte.

    Imita lo que hace un MP3 de baja calidad con las altas frecuencias.
    """
    spectrum = np.fft.rfft(signal)
    frequencies = np.fft.rfftfreq(len(signal), d=1 / SAMPLE_RATE)
    spectrum[frequencies > cutoff_hz] = 0
    return np.fft.irfft(spectrum, n=len(signal))


@pytest.fixture
def full_band_wav(tmp_path):
    """WAV con contenido hasta Nyquist, como un lossless auténtico."""
    path = tmp_path / "full_band.wav"
    sf.write(path, _white_noise(), SAMPLE_RATE)
    return path


@pytest.fixture
def low_passed_wav(tmp_path):
    """WAV sin nada por encima de 16 kHz, como un MP3 de 128 kbps convertido."""
    path = tmp_path / "low_passed.wav"
    sf.write(path, _low_pass(_white_noise(), 16000), SAMPLE_RATE)
    return path


@pytest.fixture
def corrupt_wav(tmp_path):
    path = tmp_path / "corrupt.wav"
    path.write_bytes(b"esto no es audio")
    return path


def test_to_dict_includes_every_field():
    result = AnalysisResult(
        file_name="a.flac", file_path="/music/a.flac", format=".flac",
        classification="legitimate", reason="ok",
    )

    expected_keys = {field.name for field in dataclasses.fields(AnalysisResult)}
    assert set(result.to_dict()) == expected_keys
    # Las métricas no calculadas se mantienen como None, no se omiten
    assert result.to_dict()["cutoff_frequency"] is None


def test_full_band_audio_is_legitimate(full_band_wav):
    result = analyze_file(full_band_wav)

    assert result.classification == "legitimate"
    assert result.format == ".wav"
    assert result.has_content_above_20k is True
    assert result.sample_rate == SAMPLE_RATE


def test_low_passed_audio_is_fake(low_passed_wav):
    result = analyze_file(low_passed_wav)

    assert result.classification == "fake"
    assert result.cutoff_frequency < 16500
    assert result.spectral_presence < 5


def test_corrupt_file_is_error(corrupt_wav):
    result = analyze_file(corrupt_wav)

    assert result.classification == "error"
    assert result.reason


def test_display_path_hides_real_path(full_band_wav):
    result = analyze_file(full_band_wav, display_path="mi_cancion.wav")

    assert result.file_path == "mi_cancion.wav"


def test_analyze_many_reports_progress_and_survives_errors(full_band_wav, corrupt_wav, low_passed_wav):
    events = []

    results = analyze_many([full_band_wav, corrupt_wav, low_passed_wav], on_progress=events.append)

    assert [r.classification for r in results] == ["legitimate", "error", "fake"]
    assert [e.processed for e in events] == [1, 2, 3]
    assert all(e.total == 3 for e in events)
    assert events[-1].result is results[-1]


def test_analyze_many_stops_when_cancelled(full_band_wav, low_passed_wav):
    events = []

    def cancel_after_first():
        return len(events) >= 1

    results = analyze_many(
        [full_band_wav, low_passed_wav, full_band_wav],
        on_progress=events.append,
        should_cancel=cancel_after_first,
    )

    assert len(results) == 1
