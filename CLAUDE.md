# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Working rules

- **Languages:**
  - Always reply to the user in **Spanish**.
  - Write commit messages in **English**.
  - Write code comments and docstrings in **Spanish**, as the existing code does.
- **Docker only, nothing installed on the host Mac.** Don't install Python, pip packages, npm packages, uv, Homebrew formulas or anything else on the host, and don't create a local venv or `node_modules`. Run tests, the CLI, the API and frontend builds inside Docker containers. The user starts OrbStack (the Docker daemon) themselves, so if it isn't running, ask them to start it.
- **Write code for humans.** Prefer clear names, small functions and straightforward control flow over clever or compact code. Add comments only where the *why* isn't obvious. Keep it maintainable: no needless abstractions, and follow the existing structure and style.
- **Never commit automatically.** Don't run `git commit` (or push) unless the user explicitly asks. At the end of each iteration, give a suggested commit message the user can run themselves, for example:

  ```
  git add <files>
  git commit -m "[add] <short summary>" -m "<optional details>"
  ```

- **Commit message format:** start the subject with a tag in square brackets, then a short summary in English. Tags:
  - `[add]`: new feature or files.
  - `[fix]`: bug fix.
  - `[update]`: change or improvement to something that already exists.
  - `[refactor]`: restructuring with no change in behaviour.
  - `[docs]`: documentation only.
  - `[test]`: tests only.
  - `[ci]`: CI workflows.
  - `[chore]`: maintenance, such as dependencies, config or tooling.

  Example: `[add] GitHub Actions workflow for tests and Docker image`.

## Project

Fake Music Hunter is a Python 3.13+ CLI, plus a web UI and API packaged as a Docker image, that detects fake or upscaled audio files (FLAC/WAV transcoded from lossy MP3, or MP3s labelled 320 kbps that came from lower bitrates) by spectral analysis. All docs, docstrings, comments, CLI help and user-facing messages are in **Spanish**. Keep new strings in Spanish.

## Commands

Everything runs in Docker (see Working rules). The dev image holds the dependencies; the repo is mounted at `/app`, so rebuild only when `requirements*.txt` change.

```bash
docker build -f docker/dev.Dockerfile -t fmh-dev .

docker run --rm -v "$PWD":/app fmh-dev pytest            # pytest.ini sets testpaths=tests, -v, --tb=short
docker run --rm -v "$PWD":/app fmh-dev pytest tests/test_service.py::test_low_passed_audio_is_fake
docker run --rm -v "$PWD":/app fmh-dev pytest --cov=src --cov-report=term-missing

# Web API (OpenAPI at http://localhost:8000/docs)
docker run --rm -p 127.0.0.1:8000:8000 -v "$PWD":/app \
  -v "$HOME/Soulseek Downloads/complete/ogalla/MUSICA":/music:ro -e FMH_DATA_DIR=/tmp/fmh-data \
  fmh-dev uvicorn src.web.app:create_app --factory --host 0.0.0.0 --port 8000

# CLI against the test music library (read-only mount)
docker run --rm -v "$PWD":/app -v "$HOME/Soulseek Downloads/complete/ogalla/MUSICA":/music:ro \
  fmh-dev python -m src.main -p /music -v
```

Frontend (`frontend/`, React + TypeScript + Vite). `node_modules` lives in the `fmh-node-modules` Docker volume, never on the host:

```bash
docker run --rm -v "$PWD/frontend":/app -v fmh-node-modules:/app/node_modules -w /app node:22-alpine npm install
docker run --rm -v "$PWD/frontend":/app -v fmh-node-modules:/app/node_modules -w /app node:22-alpine npm run build   # tsc + vite → frontend/dist
```

`frontend/README.md` has the hot-reload dev setup (Vite proxying `/api` to an API container on a shared Docker network). To serve the built UI from FastAPI, add `-e FMH_STATIC_DIR=/app/frontend/dist` to the API command above.

Production image (root `Dockerfile`): a multi-stage build that compiles the frontend in `node:22-alpine` and copies `dist/` into `python:3.13-slim` at `/app/static`. It installs only `requirements-web.txt`, runs as user `app` (UID 1000), declares `VOLUME /data` and has a Python healthcheck on `/api/health`. `docker/entrypoint.sh` takes `web` (the default: uvicorn with `--workers 1`), `cli <args>` (`python -m src.main`), or any other command, which it runs with `exec`. `.dockerignore` keeps tests, docs and openspec out of the build context.

```bash
docker build -t fake-music-hunter .
MUSIC_DIR="$HOME/Soulseek Downloads/complete/ogalla/MUSICA" docker compose up -d     # http://localhost:8000, history in ./data (gitignored)
docker run --rm -v "$HOME/Soulseek Downloads/complete/ogalla/MUSICA":/music:ro -v "$PWD/output":/data \
  fake-music-hunter cli -p /music -o /data/r.csv
docker buildx build --platform linux/amd64,linux/arm64 -t fake-music-hunter .   # both build on 3.13
```

CI (`.github/workflows/ci.yml`) is manual-only (`workflow_dispatch`) for now, because the account has no Actions minutes. The commented-out `on:` block in the file restores the push/PR triggers. It runs three jobs: pytest inside the `docker/dev.Dockerfile` image (the same command as locally), `npm ci && npm run build` for the frontend, and a `docker buildx` build for amd64/arm64 without pushing. Lint the workflow with `docker run --rm -v "$PWD":/repo -w /repo rhysd/actionlint:latest`.

Dependencies are layered: `requirements.txt` (CLI runtime, the only one PyInstaller needs) ← `requirements-web.txt` (FastAPI, uvicorn, python-multipart, pydantic-settings) ← `requirements-dev.txt` (pytest, pytest-cov, httpx).

Run the CLI as `python -m src.main` from the repo root. Modules import each other as `from src.x import ...`, so `python src/main.py` fails with an import error.

**Test music library:** `~/Soulseek Downloads/complete/ogalla/MUSICA` has about 80 real files (mostly WAV, plus MP3 and a few FLAC). Use it for end-to-end checks, such as comparing CLI and web classifications. Always mount it read-only (`:ro`) and never write to it. It's a local path on the user's Mac, so keep it out of public docs like the README.

There is no linter or formatter configured.

Windows build (see BUILD_RELEASE.md): `python -m PyInstaller --onefile --name fake-music-hunter src\main.py --noconfirm`. It must use the venv's Python, or the bundled exe will be missing dependencies. Output goes to `dist/fake-music-hunter.exe`.

## Architecture

`src/core/service.py` is the single entry point to analysis, shared by the CLI and the web API:

`AudioScanner.scan()` → `core.service.analyze_file(path)` (wraps `AudioAnalyzer(path).analyze()` + `FakeDetector.detect()`) → `AnalysisResult` dataclass (`core/result.py`) → `Reporter` (console) / `core.reports.to_csv|to_json` (export).

- **core/service.py**: `analyze_file` never raises. Unexpected failures become a result with classification `error`. It also converts numpy types to plain Python. `analyze_many(paths, on_progress, should_cancel)` runs a batch with a progress callback and cooperative cancellation.
- **core/reports.py**: pure CSV/JSON writers that work on copies, so exporting never mutates the results. The CSV shows bitrate in kbps; the JSON keeps it as an int in bps.
- **web/** (FastAPI, `create_app()` factory in `app.py`). The CLI must never import it, so the PyInstaller exe stays free of web dependencies.
  - `jobs.JobManager` runs each job as an asyncio task. It sends at most `FMH_WORKERS` files at a time to a shared `ProcessPoolExecutor` (spawn context), stores each result as it arrives and publishes `progress`/`done` events to SSE subscribers. Cancellation stops sending new files; files already in flight finish. Only one uvicorn worker is supported, because in-flight job state lives in memory.
  - `store.JobStore` keeps `jobs` and `results` in SQLite at `$FMH_DATA_DIR/fmh.sqlite3`. On startup, jobs left `queued`/`running` are marked `failed`.
  - `paths.safe_resolve` confines every client path to `FMH_LIBRARY_ROOT`, rejecting `..`, absolute paths and symlinks that leave it. Library results show paths relative to the root.
  - Uploads stream to `$FMH_DATA_DIR/uploads/<job_id>/` with a per-file size limit and are deleted when the job ends. `cleanup.run_cleanup` (hourly) deletes jobs past `FMH_RETENTION_DAYS` and orphaned upload folders.
  - `settings.Settings` reads `FMH_*` env vars (pydantic-settings).
  - `spa.mount_spa` serves `FMH_STATIC_DIR` (the built frontend) with an `index.html` fallback. It's registered after the API routers, and `/api/*` misses still return a JSON 404.
  - Routes that start jobs must be `async def`, because `JobManager.start` creates an asyncio task on the running loop.
- **frontend/src**: `api/types.ts` mirrors `src/web/schemas.py` and `AnalysisResult` by hand, so update it when an API model changes. `hooks/useLiveJob` follows a job over SSE and falls back to polling every 2 s. `hooks/useHealth` polls `/api/health` every 10 s and drives the "Sin conexión" banner. Requests time out (5 s for health, 15 s otherwise) so a dead server is detected. All UI text is Spanish, and numbers are formatted with the `es-ES` locale in `format.ts`.
- **analyzer.py** loads only the first `ANALYSIS_DURATION` (30 s), resampled to mono at 44.1 kHz with librosa. It averages the STFT magnitude over time, converts it to dB relative to the peak, and returns a flat dict: mutagen metadata (`format`, `bitrate` in bps, …) plus `cutoff_frequency`, `spectral_presence` (% of bins in 18–22 kHz above −70 dB), `high_freq_energy`, `has_content_above_20k` (any bin in 20–22 kHz above −65 dB) and `dynamic_range`. If loading fails it sets an `error` key instead of raising. Errors are logged with `logging`, not `print`.
- **detector.py** holds only static methods that dispatch on `format`:
  - FLAC/WAV use the "hybrid" algorithm. The fast path is `has_content_above_20k` → legitimate. Otherwise it classifies by `spectral_presence`: >30 legitimate, 15–30 checks energy > −60 dB, 5–15 suspicious, <5 is fake only if the cutoff is < 16500 Hz and suspicious otherwise. WAV reuses `detect_flac`.
  - MP3 compares `cutoff_frequency` with the expected cutoff for the declared bitrate, using `CUTOFF_THRESHOLDS` ± `SUSPICIOUS_THRESHOLD`.
  - It returns `(classification, reason)`, where classification is one of the `CLASS_*` constants in config.py (`legitimate`/`fake`/`suspicious`/`error`).
- **reporter.py** renders the console output with rich and delegates export to `core.reports`. Console markers come from `EMOJI_MAP` (`[OK]`, `[X]`, `[!]`, `[ERR]`). They are ASCII on purpose, so the Windows exe console can show them.
- **config.py** holds the MP3 cutoff thresholds, STFT params and class constants. Several FLAC thresholds are **hardcoded rather than in config**: the −70 dB and −65 dB bin thresholds and the 18/20/22 kHz bands in `analyzer.calculate_spectral_stats`, and the 30/15/5 %, −60 dB and 16500 Hz checks in `detector.detect_flac`. Tuning the algorithm means editing those files directly.

Adding a metric touches three places: return it from `analyzer.calculate_spectral_stats`, read it with `.get()` in `detector`, and add it as a field to `AnalysisResult` and fill it in `core.service.analyze_file`, then display it in `reporter` (and add it to `CSV_FIELDS` in `core/reports.py` if it should go in the CSV).

Tests: `test_detector.py` uses hand-built analysis dicts. `test_service.py` generates synthetic WAVs in `tmp_path` (full-band noise → legitimate, noise low-passed at 16 kHz → fake, garbage bytes → error), so no audio fixtures are committed. `test_reports.py` covers the exporters. `tests/web/` builds the app with `create_app(settings, executor=ThreadPoolExecutor(...), analyze=<fake>)`. The fakes in `tests/web/fakes.py` classify by file name, so API tests are fast and need no real audio. `wait_for_job` polls until a job finishes. The detector reads every key with `.get()` and a default (for example, a missing `spectral_presence` counts as 0), so tests can pass minimal dicts.

## Reference docs

- `openspec/specs/` holds the current specs (analysis-jobs, audio-analysis-core, container-runtime, web-ui). Plan new changes with OpenSpec under `openspec/changes/`. Finished changes go to `openspec/changes/archive/`.
- `ALGORITHM.md` has the algorithm rationale, diagrams and pseudocode.
- `TESTING.md` covers how to check results against Spek spectrograms.
- `CHANGELOG.md` records the v1 → v2 accuracy figures.
