# F1 Telemetry API — Phase 1 Design

## Overview

Build a FastAPI REST server exposing the existing F1 telemetry analysis pipeline (driver style classification, lap time prediction, visualization) through HTTP endpoints. This is Phase 1 of a multi-phase effort: API → Frontend → Model Improvements.

## Project State

- Only `visualization.py` and `Dockerfile` survived binary corruption.
- Core modules (`data_loader.py`, `feature_engineering.py`, `clustering.py`, `prediction.py`, `report.py`) must be recreated based on what `visualization.py` imports and what the README describes.
- FastF1 cache at `cache/` contains real session data (2018, 2023) — salvageable.
- `server/` and `frontend/` directories are empty.

## Architecture

```
FastAPI Server (server/main.py)
  ├── /sessions/*        — session listing & loading
  ├── /drivers/*         — driver telemetry & sectors
  ├── /analysis/*        — full analysis pipeline (features → cluster → predict → report)
  └── Core Modules (root)
      ├── data_loader.py        — FastF1 session loading, telemetry extraction
      ├── feature_engineering.py — driver feature computation
      ├── clustering.py          — KMeans clustering + PCA
      ├── prediction.py          — RandomForest lap time regression
      ├── report.py              — text report generation
      └── visualization.py       — plot generation (surviving file, unchanged)
```

Core modules stay at root level so they remain runnable as standalone CLI scripts. The `server/` package contains only the FastAPI app — a thin router layer that calls core modules.

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/sessions` | List cached sessions |
| `POST` | `/sessions/load` | Load session by year/grand_prix/session_type |
| `GET` | `/sessions/{id}/drivers` | List drivers in session |
| `GET` | `/sessions/{id}/drivers/{code}/telemetry` | Fastest lap telemetry |
| `GET` | `/sessions/{id}/drivers/{code}/sectors` | Sector times |
| `POST` | `/sessions/{id}/analyze` | Run full analysis pipeline |
| `GET` | `/analysis/{id}/report` | Get text report |
| `GET` | `/analysis/{id}/plots/{name}.png` | Get generated plot |

Response envelope: `{ "data": ..., "status": "ok" }` or `{ "error": "...", "status": "error" }`.

## Core Module Contracts

### data_loader.py
- `load_session(year, grand_prix, session_type)` → session object
- `get_driver_telemetry(session, driver_code)` → DataFrame[Distance, Speed, Throttle, Brake, RPM, Gear, nGear]
- `get_sector_times(session, driver_code)` → tuple(s1, s2, s3) in seconds
- `get_result(session, driver_code)` → dict with position, status, etc.

### feature_engineering.py
- `extract_features(driver_telemetry_dict)` → DataFrame indexed by driver code, columns: mean_speed, mean_throttle, brake_frequency, aggression_index, mean_gear
- `get_target_times(feature_df, session)` → Series of lap times per driver

### clustering.py
- `perform_clustering(feature_df, n_clusters=3)` → (labels, model)
- `perform_pca(feature_df, n_components=2)` → (X_pca, model)

### prediction.py
- `train_lap_time_predictor(feature_df, target_times)` → model
- `predict_lap_time(model, features)` → float

### report.py
- `generate_report(feature_df, style_labels, sector_times_dict)` → str

### visualization.py (existing, unchanged)
- `generate_all_visualizations(driver_telemetry_dict, sector_times_dict, feature_df, style_labels)` → saves PNGs to `output/`

## Analysis Storage

Analysis results (reports, plot paths) are stored in-memory via a dict keyed by a UUID generated at `POST /sessions/{id}/analyze` time. No database — YAGNI until persistence is needed.

## Error Handling

- Custom exceptions: `SessionNotFound`, `DriverNotFound`, `AnalysisError`
- FastAPI exception handlers convert to JSON error responses
- All user-facing errors are caught; 500 only on unexpected failures

## Testing

- One test file: `tests/test_api.py`
- Uses FastAPI `TestClient` with the existing cache data
- Covers: session listing, session loading, driver telemetry fetch, full analysis pipeline
- Run via: `pytest tests/ -v`

## Out of Scope

These are intentionally deferred to later phases:

- Frontend UI (Phase 2)
- Deep learning models, weather/track conditions (Phase 3)
- Real-time telemetry streaming
- Authentication/authorization (add when deployed publicly)
