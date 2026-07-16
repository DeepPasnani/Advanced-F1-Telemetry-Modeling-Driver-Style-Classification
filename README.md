# F1 Telemetry — Driver Style Classification

Analyze F1 driver behavior using telemetry data. Classifies driving styles (Aggressive, Smooth Cornering, Late Braker), predicts lap times, and generates visual reports — all through a FastAPI backend + React dashboard.

## Quick Start

### Development (hot-reload, two terminals)

```bash
# Terminal 1 — backend
uvicorn server.main:app --host 0.0.0.0 --port 8080 --reload

# Terminal 2 — frontend
cd frontend && npm install && npx vite --host 0.0.0.0

# Open http://localhost:5173
```

### Production (Docker, single command)

```bash
docker compose up --build
# Open http://localhost:8080
```

### Tests

```bash
python -m pytest tests/ -v
# 24 tests, all passing
```

## Architecture

```
├── server/main.py          FastAPI app (REST + WebSocket)
├── data_loader.py          FastF1 session loading & telemetry
├── feature_engineering.py  Feature extraction from telemetry
├── clustering.py           KMeans style classification + PCA
├── prediction.py           MLPRegressor lap time prediction
├── report.py               Text report generation
├── visualization.py        Plot generation (matplotlib + seaborn)
├── frontend/               React + Vite + Tailwind dashboard
│   ├── src/pages/          Home → SessionDetail → AnalysisResults → Report → LiveTelemetry
│   └── src/hooks/          useApi.js + useWebSocket.js
├── Dockerfile              Multi-stage: Node build → Python serve
├── docker-compose.yml      One-command production startup
└── tests/                  24 pytest tests
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/sessions` | List loaded sessions |
| `POST` | `/sessions/load` | Load a session (year, grand_prix, session_type) |
| `GET` | `/sessions/{id}/drivers` | List drivers in a session |
| `GET` | `/sessions/{id}/drivers/{code}/telemetry` | Fastest-lap telemetry |
| `GET` | `/sessions/{id}/drivers/{code}/sectors` | Sector times |
| `POST` | `/sessions/{id}/analyze` | Run full analysis pipeline |
| `GET` | `/analysis/{id}/report` | Analysis text report |
| `GET` | `/analysis/{id}/plots` | List generated plots |
| `GET` | `/analysis/{id}/plots/{name}.png` | Get a plot image |
| `WS` | `/ws/telemetry/{session_id}/{driver_code}` | Real-time telemetry stream |

## Features

- **Weather-aware** — track/air temperature and rainfall in feature set
- **Multi-lap aggregation** — features computed across all 57 race laps (mean + std)
- **DRS analysis** — DRS usage rate as a driving style feature
- **Neural network prediction** — MLPRegressor for lap time estimation
- **Real-time streaming** — WebSocket replay of fastest-lap telemetry
- **UI dashboard** — dark-themed React app with driver cards, plots, and live view

## Data Source

Uses [FastF1](https://github.com/theOehrly/FastF1) (v3.8.3) to load Formula 1 session data. Cache is stored in `cache/`. Tested with 2023 Bahrain Grand Prix.
