# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Working rules

- **Languages:**
  - Always reply to the user in **Spanish**.
  - Write commit messages in **English**.
  - Write code comments and docstrings in **Spanish**, as the existing code does.
- **Write code for humans.** Prefer clear names, small functions and straightforward control flow over clever or compact code. Add comments only where the *why* isn't obvious. Keep it maintainable: no needless abstractions, and follow the existing structure and style.
- **Never commit automatically.** Don't run `git commit` (or push) unless the user explicitly asks. At the end of each iteration, give a suggested commit message the user can run themselves, for example:

  ```
  git add <files>
  git commit -m "<type>: <short summary>" -m "<optional details>"
  ```

## Project

Fake Music Hunter is a Python 3.13+ CLI that detects fake or upscaled audio files (FLAC/WAV transcoded from lossy MP3, or MP3s labelled 320 kbps that came from lower bitrates) by spectral analysis. All docs, docstrings, comments, CLI help and user-facing messages are in **Spanish**. Keep new strings in Spanish.

## Commands

```bash
pip install -r requirements.txt            # runtime deps (librosa, numpy, scipy, mutagen, rich, click, pandas, soundfile)
pip install pytest pytest-cov              # test deps (not in requirements.txt)

python -m src.main -p <dir> [-f flac] [--no-recursive] [-v] [-o report.csv] [-j report.json]

pytest                                     # pytest.ini sets testpaths=tests, -v, --tb=short
pytest tests/test_detector.py::TestFakeDetector::test_detect_flac_fake
pytest --cov=src --cov-report=term-missing
```

Run from the repo root with `python -m src.main`. Modules import each other as `from src.x import ...`, so `python src/main.py` (shown in parts of the README) fails with an import error unless the repo root is on `PYTHONPATH`.

There is no linter or formatter configured.

Windows build (see BUILD_RELEASE.md): `python -m PyInstaller --onefile --name fake-music-hunter src\main.py --noconfirm`. It must use the venv's Python, or the bundled exe will be missing dependencies. Output goes to `dist/fake-music-hunter.exe`.

## Architecture

The pipeline runs in `src/main.py`, one file at a time:

`AudioScanner.scan()` → `AudioAnalyzer(path).analyze()` → `FakeDetector.detect(results)` → `Reporter.add_result/print_result` → summary + optional CSV/JSON export.

- **analyzer.py** loads only the first `ANALYSIS_DURATION` (30 s), resampled to mono at 44.1 kHz with librosa. It averages the STFT magnitude over time, converts it to dB relative to the peak, and returns a flat dict: mutagen metadata (`format`, `bitrate` in bps, …) plus `cutoff_frequency`, `spectral_presence` (% of bins in 18–22 kHz above −70 dB), `high_freq_energy`, `has_content_above_20k` (any bin in 20–22 kHz above −65 dB) and `dynamic_range`. If loading fails it sets an `error` key instead of raising.
- **detector.py** holds only static methods that dispatch on `format`:
  - FLAC/WAV use the "hybrid" algorithm. The fast path is `has_content_above_20k` → legitimate. Otherwise it classifies by `spectral_presence`: >30 legitimate, 15–30 checks energy > −60 dB, 5–15 suspicious, <5 is fake only if the cutoff is < 16500 Hz and suspicious otherwise. WAV reuses `detect_flac`.
  - MP3 compares `cutoff_frequency` with the expected cutoff for the declared bitrate, using `CUTOFF_THRESHOLDS` ± `SUSPICIOUS_THRESHOLD`.
  - It returns `(classification, reason)`, where classification is one of the `CLASS_*` constants in config.py (`legitimate`/`fake`/`suspicious`/`error`).
- **reporter.py** renders the console output with rich and exports CSV/JSON. Console markers come from `EMOJI_MAP` (`[OK]`, `[X]`, `[!]`, `[ERR]`). They are ASCII on purpose, so the Windows exe console can show them.
- **config.py** holds the MP3 cutoff thresholds, STFT params and class constants. Several FLAC thresholds are **hardcoded rather than in config**: the −70 dB and −65 dB bin thresholds and the 18/20/22 kHz bands in `analyzer.calculate_spectral_stats`, and the 30/15/5 %, −60 dB and 16500 Hz checks in `detector.detect_flac`. Tuning the algorithm means editing those files directly.

Adding a metric touches three places: return it from `analyzer.calculate_spectral_stats`, read it with `.get()` in `detector`, and display or export it in `reporter`.

Tests (`tests/test_detector.py`) cover only `FakeDetector`, using hand-built analysis dicts. No audio fixtures are needed. The detector reads every key with `.get()` and a default (for example, a missing `spectral_presence` counts as 0), so tests can pass minimal dicts.

## Reference docs

- `ALGORITHM.md` has the algorithm rationale, diagrams and pseudocode.
- `TESTING.md` covers how to check results against Spek spectrograms.
- `CHANGELOG.md` records the v1 → v2 accuracy figures.
