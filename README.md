# F1 Telemetry — Driver Style Classification

**Analyze Formula 1 driver behavior using telemetry data.** Classifies driving styles (Aggressive, Smooth Cornering, Late Braker), predicts lap times, and generates visual reports — all through a FastAPI backend + React dashboard.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [WebSocket Streaming](#websocket-streaming)
- [Testing](#testing)
- [Docker Deployment](#docker-deployment)
- [Favicon Generation](#favicon-generation)
- [Configuration](#configuration)
- [Data Source](#data-source)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Features

| Feature | Details |
|---|---|
| **Driver Style Classification** | KMeans clustering + PCA on telemetry features — classifies as Aggressive, Smooth Cornering, or Late Braker |
| **Lap Time Prediction** | MLPRegressor (32→16 neural net) predicts lap times from driving style features |
| **Weather-Aware** | Track temperature, air temperature, and rainfall incorporated into feature set |
| **Multi-Lap Aggregation** | Features computed across all race laps (mean + std per driver) |
| **DRS Analysis** | DRS usage rate extracted as a driving style signal |
| **Real-Time Streaming** | WebSocket endpoint replays fastest-lap telemetry at original timing |
| **Visual Reports** | 5 matplotlib/seaborn plots: cluster scatter, radar chart, speed trace, throttle/brake, sector comparison |
| **Web Dashboard** | Dark-themed React + Vite + Tailwind app with 5 pages |
| **Dockerized** | Multi-stage build serves API + frontend from a single container |
| **PWA Ready** | Manifest, serviceable icons, and theme-color for installable web app |

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.14, FastAPI, Uvicorn |
| **Data** | FastF1 3.8.3, Pandas, NumPy |
| **ML** | Scikit-learn (KMeans, PCA, MLPRegressor) |
| **Visualization** | Matplotlib, Seaborn |
| **Frontend** | React 18, Vite 5, Tailwind CSS 3 |
| **Fonts** | Inter (UI), JetBrains Mono (data) |
| **Streaming** | WebSocket (async replay) |
| **Deployment** | Docker, docker-compose |

---

## Project Structure

```
.
├── server/
│   └── main.py               FastAPI app (REST + WebSocket + SPA serving)
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
│   │   ├── components/        Shared: Breadcrumbs, EmptyState, ErrorMessage,
│   │   │                      LoadingSkeleton, LoadingSpinner, PlotCard
│   │   ├── pages/             Home, SessionDetail, AnalysisResults, Report,
│   │   │                      LiveTelemetry
│   │   └── hooks/             useApi.js, useWebSocket.js
│   └── public/                Favicons, site.webmanifest
├── scripts/
│   └── generate-favicons.py   Pillow script to regenerate favicon set
├── tests/
│   ├── test_api.py            FastAPI TestClient integration tests
│   ├── test_data_loader.py    Session loading & telemetry extraction
│   ├── test_feature_engineering.py  Feature extraction correctness
│   ├── test_clustering.py     KMeans clustering sanity
│   ├── test_prediction.py     MLPRegressor training/prediction
│   └── test_report.py         Report generation format
├── cache/                     FastF1 session cache (gitignored)
├── output/                    Generated plots (gitignored)
├── favicon-source.png         1024×1024 source for favicon generation
├── Dockerfile                 Multi-stage: Node 20 build → Python 3.12-slim
├── docker-compose.yml         One-command production startup
├── requirements.txt           Python dependencies
└── README.md                  This file
```

---

## Prerequisites

- **Python 3.12+** (3.14 recommended)
- **Node.js 20+** (for frontend development)
- **Docker + docker-compose** (for production deployment)
- **Pillow** (for favicon regeneration: `pip install Pillow`)

---

## Installation

### 1. Clone and enter the repo

```bash
git clone <repo-url>
cd Advanced-F1-Telemetry-Modeling-Driver-Style-Classification-main
```

### 2. Backend

```bash
# Create a virtual environment (optional but recommended)
python3 -m venv venv && source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Pre-populate FastF1 cache (downloads 2023 Bahrain GP data)
python -c "import data_loader; data_loader.load_session(2023, 'Bahrain', 'R')"
```

### 3. Frontend (development only)

```bash
cd frontend && npm install && cd ..
```

---

## Usage

### Development (hot-reload, two terminals)

```bash
# Terminal 1 — backend
uvicorn server.main:app --host 0.0.0.0 --port 1212 --reload

# Terminal 2 — frontend
cd frontend && npx vite --host 0.0.0.0

# Open http://localhost:5173
```

The Vite dev server proxies `/api/*` → `http://localhost:1212/api/*` and `/ws/*` → `ws://localhost:1212/ws/*`.

### Production (Docker, single command)

```bash
docker compose up --build
# Open http://localhost:1212
```

### Walkthrough

1. **Home** — Click "Load Session", enter Year `2023`, Grand Prix `Bahrain`, Session `R`, click Load
2. **Session Detail** — Select 2–5 drivers from the grid, click "Run Analysis"
3. **Analysis Results** — View style classification cards with speed, brake frequency, aggression bars, DRS usage
4. **Report** — Read the full text report and scroll through generated plots
5. **Live Telemetry** — Switch to a driver, watch speed/throttle/brake/DRS/gear in real time

---

## API Documentation

All API routes are prefixed with `/api`. The full OpenAPI schema is available at `/docs` when the server is running.

### Session Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/sessions` | List all loaded session IDs |
| `POST` | `/api/sessions/load` | Load a session from FastF1 |
| `GET` | `/api/sessions/{id}` | Get session metadata |
| `GET` | `/api/sessions/{id}/drivers` | List driver codes in a session |
| `GET` | `/api/sessions/{id}/drivers/{code}/telemetry` | Get fastest-lap telemetry for a driver |
| `GET` | `/api/sessions/{id}/drivers/{code}/sectors` | Get sector times (S1, S2, S3) for a driver |

### Analysis Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/sessions/{id}/analyze` | Run full analysis pipeline on selected drivers |
| `GET` | `/api/analysis/{id}/report` | Get the text report for an analysis |
| `GET` | `/api/analysis/{id}/plots` | List available plot names |
| `GET` | `/api/analysis/{id}/plots/{name}.png` | Get a specific plot image |

### Load Session Request Body

```json
{
  "year": 2023,
  "grand_prix": "Bahrain",
  "session_type": "R"
}
```

### Analyze Request Body

```json
{
  "driver_codes": ["VER", "HAM", "LEC"]
}
```

### Analyze Response

```json
{
  "status": "ok",
  "data": {
    "analysis_id": "uuid",
    "styles": { "VER": "Aggressive", "HAM": "Smooth Cornering" },
    "predictions": { "VER": 95.3, "HAM": 96.1 },
    "features": { "VER": { "mean_speed": 210.5, ... }, ... }
  }
}
```

---

## WebSocket Streaming

Connect to a real-time telemetry replay via WebSocket:

```
ws://localhost:1212/ws/telemetry/{session_id}/{driver_code}
```

The server replays the driver's fastest-lap telemetry at original timing deltas. Each message is a JSON object:

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

The frontend `useWebSocket` hook handles connection lifecycle, reconnection on driver change, and exposes `data`, `connected`, and `error` states.

---

## Testing

```bash
# Run all 24 tests
python -m pytest tests/ -v

# Run a specific test module
python -m pytest tests/test_api.py -v

# Run with coverage (optional)
pip install pytest-cov
python -m pytest tests/ --cov=. --cov-report=term
```

All 24 tests currently pass across 6 test modules:

| Module | Tests | Scope |
|--------|-------|-------|
| `test_api.py` | 3 | FastAPI endpoint integration (load → analyze → report) |
| `test_data_loader.py` | 4 | Session loading, driver list, telemetry, sectors |
| `test_feature_engineering.py` | 4 | Feature extraction with multi-lap and weather |
| `test_clustering.py` | 5 | KMeans clustering, PCA, cluster count validation |
| `test_prediction.py` | 4 | MLPRegressor training, prediction, feature count |
| `test_report.py` | 4 | Report format, weather inclusion, lap count |

---

## Docker Deployment

### Build and run

```bash
docker compose up --build
# Open http://localhost:1212
```

The multi-stage `Dockerfile`:
1. **Stage 1 (Node 20)** — Installs npm dependencies and builds the Vite frontend
2. **Stage 2 (Python 3.12-slim)** — Copies built frontend + Python app, installs requirements

### Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FASTF1_CACHE_DIR` | `/app/cache` | FastF1 cache directory inside container |

### Volumes

| Host path | Container path | Purpose |
|-----------|---------------|---------|
| `./cache` | `/app/cache` | Persistent FastF1 data cache |
| `./output` | `/app/output` | Generated plot images |

---

## Favicon Generation

The favicon set was generated from `favicon-source.png` (1024×1024 RGBA) using Pillow.

**Regenerate:**

```bash
# Replace favicon-source.png with your source, then:
python3 scripts/generate-favicons.py
```

This produces:
- `frontend/public/favicon.ico` — multi-res (16×16, 32×32, 48×48)
- `frontend/public/favicon-16x16.png`
- `frontend/public/favicon-32x32.png`
- `frontend/public/apple-touch-icon.png` — 180×180 (iOS home screen)
- `frontend/public/android-chrome-192x192.png`
- `frontend/public/android-chrome-512x512.png`
- `frontend/public/site.webmanifest` — theme `#e8002d`, bg `#050505`

---

## Configuration

### Port

The application uses port **1212** in both development and Docker configurations.

- **Docker**: edit `ports:` in `docker-compose.yml`
- **Dev**: change `--port` in the uvicorn command and update `target` in `frontend/vite.config.js`

### Analysis

The clustered driving styles are mapped as:

| Label | Index |
|-------|-------|
| Aggressive | 0 |
| Smooth Cornering | 1 |
| Late Braker | 2 |

KMeans `n_clusters=3` is fixed. The label-to-name mapping lives in `server/main.py`.

### Design System

The frontend uses a custom dark F1 theme defined in `frontend/tailwind.config.js`:

- **Colors**: near-black `#050505` bg, Ferrari red `#e8002d` accent, carbon-fiber `#121214` / `#1a1a1e` surfaces
- **Fonts**: Inter (UI labels/body), JetBrains Mono (data/code)
- **Motion**: `ease-out-quart` easing, 150–500ms durations, stagger entrance, reduced-motion support
- **Components**: `f1-card`, `f1-btn-primary`, `f1-btn-secondary`, `f1-input`, `f1-select`, `f1-badge`, `f1-progress`, with full hover/focus/active/disabled states

---

## Data Source

Uses [FastF1](https://github.com/theOehrly/FastF1) (v3.8.3) to load official Formula 1 session data from the Ergast API.

- **Cache**: `cache/` directory (add to `.gitignore`)
- **Tested session**: 2023 Bahrain Grand Prix
- **Required columns**: Speed, Throttle, Brake, RPM, nGear, DRS, SessionTime
- **Steering/ERS**: Not available in FastF1 v3.8.3 for 2023 sessions — these features are skipped

---

## Troubleshooting

### Port 1212 already in use

```bash
# Find and kill the process
lsof -ti:1212 | xargs kill -9
```

### Module not found / import errors

```bash
pip install -r requirements.txt --upgrade
```

### FastF1 fails to load session

Ensure you have a stable internet connection for the first load (data is cached afterward).

### WebSocket connection fails in Docker

The WebSocket endpoint uses the same port as the API (`1212`). Ensure your proxy/load balancer supports WebSocket upgrade headers.

### Frontend proxy errors in development

Make sure the backend is running on port 1212 before starting the Vite dev server. Check `frontend/vite.config.js` matches.

---

## License

This project is for educational and research purposes. Formula 1 data is provided by [FastF1](https://github.com/theOehrly/FastF1) and originates from the official F1 timing feeds. The F1 logo and related trademarks are owned by Formula One World Championship Limited.
