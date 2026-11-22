"""
Tests de exportación de reportes CSV y JSON.
"""

import copy
import csv
import io
import json

from src.core import reports
from src.core.result import AnalysisResult


def _sample_results():
    return [
        AnalysisResult(
            file_name="buena.flac", file_path="/music/buena.flac", format=".flac",
            classification="legitimate", reason="Contenido por encima de 20 kHz",
            bitrate=1094000, sample_rate=44100, cutoff_frequency=22050.0,
            spectral_presence=100.0, dynamic_range=70.5, file_size=1234,
        ).to_dict(),
        AnalysisResult(
            file_name="mala.flac", file_path="/music/mala.flac", format=".flac",
            classification="fake", reason="Sin contenido en altas frecuencias",
            bitrate=998000, cutoff_frequency=16000.0, spectral_presence=0.0,
        ).to_dict(),
    ]


def test_csv_then_json_does_not_mutate_results():
    results = _sample_results()
    original = copy.deepcopy(results)

    reports.to_csv(results, io.StringIO())
    json_output = io.StringIO()
    reports.to_json(results, json_output)

    assert results == original
    exported = json.loads(json_output.getvalue())
    assert exported[0]["bitrate"] == 1094000


def test_csv_has_header_one_row_per_result_and_kbps():
    output = io.StringIO()

    reports.to_csv(_sample_results(), output)

    rows = list(csv.DictReader(io.StringIO(output.getvalue())))
    assert len(rows) == 2
    assert list(rows[0]) == reports.CSV_FIELDS
    assert rows[0]["bitrate"] == "1094 kbps"
    assert rows[0]["spectral_presence"] == "100.0"
    # Un valor ausente se escribe como celda vacía
    assert rows[1]["sample_rate"] == ""


def test_accepts_analysis_result_objects():
    result = AnalysisResult(
        file_name="a.mp3", file_path="a.mp3", format=".mp3",
        classification="suspicious", reason="dudoso", bitrate=320000,
    )
    output = io.StringIO()

    reports.to_json([result], output)

    assert json.loads(output.getvalue())[0]["classification"] == "suspicious"
