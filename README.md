<div align="center">

# 🏎️ F1 Telemetry — Advanced Driver Style Classification & Lap Time Modeling

**Turn raw Formula 1 telemetry into driver insight.** Classifies driving styles, predicts lap times, and streams live telemetry — powered by a FastAPI backend and a React dashboard.

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react)](https://react.dev/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-Educational-lightgrey)](#license)

</div>

---

## Overview

This project ingests real Formula 1 session telemetry (via [FastF1](https://github.com/theOehrly/FastF1)) — speed, throttle, brake, gear, DRS, and weather — and turns it into actionable driver insight:

- **Classifies** each driver's style as `Aggressive`, `Smooth Cornering`, or `Late Braker` using KMeans clustering + PCA
- **Predicts** lap times with a small neural net (`MLPRegressor`, 32→16)
- **Visualizes** results with cluster scatter plots, radar charts, speed traces, and sector comparisons
- **Streams** fastest-lap telemetry in real time over WebSocket
- Ships as a single Docker container, with a ready-to-use `render.yaml` for one-click deployment on Render

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Running Locally](#running-locally)
- [Deployment](#deployment)
  - [Docker / docker-compose](#docker--docker-compose)
  - [Render (one-click)](#render-one-click)
  - [Other platforms](#other-platforms)
- [API Reference](#api-reference)
- [WebSocket Streaming](#websocket-streaming)
- [Testing](#testing)
- [Configuration](#configuration)
- [Data Source & Limitations](#data-source--limitations)
- [Troubleshooting](#troubleshooting)
- [Roadmap](#roadmap)
- [License](#license)

---

## Features

| Feature | Details |
|---|---|
| **Driver Style Classification** | KMeans clustering + PCA on telemetry features → `Aggressive`, `Smooth Cornering`, `Late Braker` |
| **Lap Time Prediction** | `MLPRegressor` (32→16 neural net) predicts lap times from style features |
| **Weather-Aware** | Track temp, air temp, and rainfall folded into the feature set |
| **Multi-Lap Aggregation** | Features computed across all race laps (mean + std per driver) |
| **DRS Analysis** | DRS usage rate extracted as a driving-style signal |
| **Real-Time Streaming** | WebSocket endpoint replays fastest-lap telemetry at original timing |
| **Visual Reports** | 5 matplotlib/seaborn plots — cluster scatter, radar chart, speed trace, throttle/brake, sector comparison |
| **Web Dashboard** | Dark-themed React + Vite + Tailwind app, 5 pages |
| **Dockerized** | Multi-stage build serves API + frontend from a single container |
| **PWA Ready** | Manifest, icon set, theme color — installable as a web app |

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.12+, FastAPI, Uvicorn |
| **Data** | FastF1 3.8.3, Pandas, NumPy |
| **ML** | scikit-learn (KMeans, PCA, MLPRegressor) |
| **Visualization** | Matplotlib, Seaborn |
| **Frontend** | React 18, Vite 5, Tailwind CSS 3 |
| **Fonts** | Inter (UI), JetBrains Mono (data) |
| **Streaming** | WebSocket (async replay) |
| **Deployment** | Docker, docker-compose, Render |

---

## Project Structure

```
.
├── server/
│   └── main.py                FastAPI app (REST + WebSocket + SPA serving)
├── data_loader.py             FastF1 session loading & driver telemetry
├── feature_engineering.py     Feature extraction from raw telemetry
├── clustering.py              KMeans style classification + PCA reduction
├── prediction.py              MLPRegressor lap time prediction
├── report.py                  Text report generation from analysis
├── visualization.py           Plot generation (matplotlib + seaborn)
├── frontend/
│   ├── index.html             HTML entry with favicon + manifest links
│   ├── vite.config.js         Vite config with API/WS proxy
│   ├── tailwind.config.js     Custom F1 design system theme
│   ├── src/
│   │   ├── main.jsx           React mount
│   │   ├── App.jsx            Router setup (5 routes)
│   │   ├── index.css          Design tokens + component classes + motion
│   │   ├── components/        Breadcrumbs, EmptyState, ErrorMessage,
│   │   │                      LoadingSkeleton, LoadingSpinner, PlotCard
│   │   ├── pages/              Home, SessionDetail, AnalysisResults, Report,
│   │   │                      LiveTelemetry
│   │   └── hooks/              useApi.js, useWebSocket.js
│   └── public/                 Favicons, site.webmanifest
├── scripts/
│   └── generate-favicons.py    Pillow script to regenerate favicon set
├── tests/                      24 tests across 6 modules (pytest)
├── cache/                      FastF1 session cache (gitignored)
├── output/                     Generated plots (gitignored)
├── Dockerfile                  Multi-stage: Node 20 build → Python slim runtime
├── docker-compose.yml          One-command production startup
├── render.yaml                 Render Blueprint for one-click deployment
├── requirements.txt            Python dependencies
└── README.md
```

---

## Getting Started

### Prerequisites

- **Python 3.12+**
- **Node.js 20+** (frontend development only)
- **Docker + docker-compose** (recommended for deployment)
- **Pillow** (only if regenerating favicons: `pip install Pillow`)

### 1. Clone the repo

```bash
git clone https://github.com/DeepPasnani/Advanced-F1-Telemetry-Modeling-Driver-Style-Classification.git
cd Advanced-F1-Telemetry-Modeling-Driver-Style-Classification
```

### 2. Backend setup

```bash
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

pip install -r requirements.txt

# Pre-populate the FastF1 cache (downloads 2023 Bahrain GP data)
python -c "import data_loader; data_loader.load_session(2023, 'Bahrain', 'R')"
```

> **Note:** the repo currently ships both `requirement.txt` and `requirements.txt`. Keep them in sync, or delete the one you're not using — `render.yaml` currently points at `requirement.txt`.

### 3. Frontend setup (development only)

```bash
cd frontend
npm install
cd ..
```

---

## Running Locally

### Development mode (hot-reload, two terminals)

```bash
# Terminal 1 — backend
uvicorn server.main:app --host 0.0.0.0 --port 1212 --reload

# Terminal 2 — frontend
cd frontend && npx vite --host 0.0.0.0
```

Open **http://localhost:5173**. The Vite dev server proxies `/api/*` → `http://localhost:1212/api/*` and `/ws/*` → `ws://localhost:1212/ws/*`.

### Production mode (single container)

```bash
docker compose up --build
```

Open **http://localhost:1212** — the FastAPI backend serves the built React app directly.

### Walkthrough

1. **Home** — click "Load Session", enter Year `2023`, Grand Prix `Bahrain`, Session `R`, then Load
2. **Session Detail** — select 2–5 drivers, click "Run Analysis"
3. **Analysis Results** — view style classification, speed, brake frequency, aggression, DRS usage
4. **Report** — read the generated text report and browse the plots
5. **Live Telemetry** — pick a driver and watch speed/throttle/brake/DRS/gear stream in real time

---

## Deployment

### Docker / docker-compose

The `Dockerfile` is a multi-stage build:

1. **Stage 1 (Node 20)** — installs frontend dependencies and builds the Vite app
2. **Stage 2 (Python slim)** — copies the built frontend + Python app and installs `requirements.txt`

```bash
docker compose up --build -d
```

The app is served on **port 1212**. Two volumes persist state across restarts:

| Host path | Container path | Purpose |
|---|---|---|
| `./cache` | `/app/cache` | Persistent FastF1 session cache |
| `./output` | `/app/output` | Generated plot images |

To deploy this container on any Docker-friendly host (a VPS, Fly.io, Railway, AWS ECS/App Runner, Azure Container Apps, etc.), build the image and push it to your registry of choice:

```bash
docker build -t f1-telemetry:latest .
docker tag f1-telemetry:latest <your-registry>/f1-telemetry:latest
docker push <your-registry>/f1-telemetry:latest
```

Then point your host at the image, expose port `1212` (or remap it via the `PORT` env var if your platform injects one), and mount persistent storage for `cache/` if you want FastF1 downloads to survive restarts.

### Render (one-click)

The repo includes a `render.yaml` Blueprint, so Render can stand up the API directly from GitHub:

1. Push this repo to your own GitHub account
2. In the Render dashboard, choose **New → Blueprint** and select the repo
3. Render reads `render.yaml` and provisions:

   | Setting | Value |
   |---|---|
   | Type | Web Service |
   | Environment | Python |
   | Build command | `pip install -r requirement.txt` |
   | Start command | `uvicorn server.main:app --host 0.0.0.0 --port $PORT` |
   | `CACHE_TTL_MINUTES` | `30` |
   | `MAX_DRIVERS` | `6` |
   | `ALLOWED_ORIGIN` | `*` |

4. Click **Apply** — Render builds and deploys automatically on every push to `main`

**Before deploying, double-check:**
- `render.yaml`'s build command references `requirement.txt` — rename/align it with `requirements.txt` if you consolidate the two dependency files
- This Blueprint deploys the **API only**. If you want the bundled frontend + API in one Render service the way `docker-compose` runs it locally, either set Render's environment to **Docker** (so it builds the multi-stage `Dockerfile` instead) or build the frontend separately as a Render **Static Site** and point `ALLOWED_ORIGIN` at its URL
- Tighten `ALLOWED_ORIGIN` from `*` to your actual frontend origin before going to production

### Other platforms

Because the whole app is a single Docker image, it also deploys cleanly to:

- **Fly.io** — `fly launch` detects the Dockerfile automatically
- **Railway** — "Deploy from GitHub", Railway detects the Dockerfile
- **Google Cloud Run** — `gcloud run deploy --source .`
- **Azure Container Apps / AWS App Runner** — point at the built image

For any of these, keep in mind FastF1 needs outbound internet access on first load (to fetch session data) and benefits from a persistent volume or bucket for `cache/`.

---

## API Reference

All routes are prefixed with `/api`. Full OpenAPI/Swagger docs are available at `/docs` while the server is running.

### Session endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/sessions` | List all loaded session IDs |
| `POST` | `/api/sessions/load` | Load a session from FastF1 |
| `GET` | `/api/sessions/{id}` | Get session metadata |
| `GET` | `/api/sessions/{id}/drivers` | List driver codes in a session |
| `GET` | `/api/sessions/{id}/drivers/{code}/telemetry` | Fastest-lap telemetry for a driver |
| `GET` | `/api/sessions/{id}/drivers/{code}/sectors` | Sector times (S1, S2, S3) for a driver |

### Analysis endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/sessions/{id}/analyze` | Run the full analysis pipeline on selected drivers |
| `GET` | `/api/analysis/{id}/report` | Get the text report for an analysis |
| `GET` | `/api/analysis/{id}/plots` | List available plot names |
| `GET` | `/api/analysis/{id}/plots/{name}.png` | Get a specific plot image |

**Load session — request body**
```json
{
  "year": 2023,
  "grand_prix": "Bahrain",
  "session_type": "R"
}
```

**Analyze — request body**
```json
{
  "driver_codes": ["VER", "HAM", "LEC"]
}
```

**Analyze — response**
```json
{
  "status": "ok",
  "data": {
    "analysis_id": "uuid",
    "styles": { "VER": "Aggressive", "HAM": "Smooth Cornering" },
    "predictions": { "VER": 95.3, "HAM": 96.1 },
    "features": { "VER": { "mean_speed": 210.5 } }
  }
}
```

---

## WebSocket Streaming

```
ws://localhost:1212/ws/telemetry/{session_id}/{driver_code}
```

The server replays a driver's fastest-lap telemetry at its original timing deltas. Each message:

```json
{
  "speed": 298,
  "throttle": 85,
  "brake": 0,
  "drs": 1,
  "rpm": 10500,
  "gear": 7,
  "lap_progress": 0.45
}
```

The frontend's `useWebSocket` hook manages connection lifecycle, reconnects on driver change, and exposes `data`, `connected`, and `error` state.

---

## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run one module
python -m pytest tests/test_api.py -v

# With coverage
pip install pytest-cov
python -m pytest tests/ --cov=. --cov-report=term
```

| Module | Tests | Scope |
|---|---|---|
| `test_api.py` | 3 | FastAPI endpoint integration (load → analyze → report) |
| `test_data_loader.py` | 4 | Session loading, driver list, telemetry, sectors |
| `test_feature_engineering.py` | 4 | Feature extraction with multi-lap and weather |
| `test_clustering.py` | 5 | KMeans clustering, PCA, cluster count validation |
| `test_prediction.py` | 4 | MLPRegressor training, prediction, feature count |
| `test_report.py` | 4 | Report format, weather inclusion, lap count |

---

## Configuration

### Port

The app runs on port **1212** in both development and Docker.

- **Docker** — edit `ports:` in `docker-compose.yml`
- **Dev** — change `--port` in the uvicorn command and update `target` in `frontend/vite.config.js`

### Driving style labels

```
0 → Aggressive
1 → Smooth Cornering
2 → Late Braker
```

`KMeans(n_clusters=3)` is fixed; the label-to-name mapping lives in `server/main.py`.

### Environment variables

| Variable | Default | Description |
|---|---|---|
| `FASTF1_CACHE_DIR` | `/app/cache` | FastF1 cache directory inside the container |
| `CACHE_TTL_MINUTES` | `30` | (Render) cache lifetime |
| `MAX_DRIVERS` | `6` | (Render) max drivers per analysis |
| `ALLOWED_ORIGIN` | `*` | (Render) CORS origin — restrict this in production |

### Favicon regeneration

Favicons are generated from `favicon-source.png` (1024×1024 RGBA) via Pillow:

```bash
python3 scripts/generate-favicons.py
```

Produces `favicon.ico`, 16×16/32×32 PNGs, an Apple touch icon, Android Chrome icons, and `site.webmanifest` (theme `#e8002d`, background `#050505`).

---

## Data Source & Limitations

Telemetry is loaded via [FastF1](https://github.com/theOehrly/FastF1) v3.8.3 from official F1 timing data.

- **Cache**: `cache/` (gitignored)
- **Tested session**: 2023 Bahrain Grand Prix
- **Required columns**: `Speed`, `Throttle`, `Brake`, `RPM`, `nGear`, `DRS`, `SessionTime`
- **Not available**: Steering and ERS data aren't exposed by FastF1 v3.8.3 for 2023 sessions, so those features are skipped

---

## Troubleshooting

**Port 1212 already in use**
```bash
lsof -ti:1212 | xargs kill -9
```

**Module not found / import errors**
```bash
pip install -r requirements.txt --upgrade
```

**FastF1 fails to load a session** — ensure a stable internet connection on first load; results are cached afterward.

**WebSocket connection fails in Docker** — the WebSocket shares port `1212` with the API; make sure any reverse proxy or load balancer in front of it supports WebSocket upgrade headers.

**Frontend proxy errors in development** — confirm the backend is running on port 1212 and that `frontend/vite.config.js`'s proxy target matches.

---

## Roadmap

- [ ] Support additional seasons/sessions beyond 2023 Bahrain
- [ ] Add authentication for multi-user deployments
- [ ] Persist analyses to a database instead of in-memory/cache storage
- [ ] Add CI (GitHub Actions) to run the pytest suite on every push

---

## License

This project is for educational and research purposes. Formula 1 data is provided by [FastF1](https://github.com/theOehrly/FastF1) and originates from official F1 timing feeds. The F1 logo and related trademarks are owned by Formula One World Championship Limited.

---

<div align="center">

Built by [DeepPasnani](https://github.com/DeepPasnani)

</div>
