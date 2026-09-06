# F1 Telemetry — Driver Style Classification

**Analyze Formula 1 driver behavior using telemetry data.** Classifies driving styles (Aggressive, Smooth Cornering, Late Braker), predicts lap times, and generates visual reports — all through a FastAPI backend + React dashboard.

🔗 **Live demo:** [f1.deadpan.qzz.io](https://f1.deadpan.qzz.io/) — frontend on Vercel, backend on Render's free tier (the first request after a period of inactivity can take 30-60s to wake up — see [Troubleshooting](#troubleshooting)).

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
- [Split Deployment (Vercel + a backend host)](#split-deployment-vercel--a-backend-host)
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
| **Real-Time Streaming** | WebSocket endpoint replays fastest-lap telemetry paced to the original timing deltas |
| **Visual Reports** | 5 matplotlib/seaborn plots — cluster scatter, radar chart, speed trace, throttle/brake, sector comparison — each generated in the background so results appear immediately |
| **Data-Driven Plot Captions** | Each plot is annotated with a short, computed interpretation of that specific analysis (e.g. who set the fastest sector, who carried the most speed) — not a generic description of the chart type |
| **Season Calendar Picker** | Year and Grand Prix are populated from FastF1's real event schedule, not free text |
| **Full-Grid Analysis** | Select any 3+ drivers, or one click to select the entire field |
| **Web Dashboard** | Dark-themed React + Vite + Tailwind app, self-hosted Formula1 display font, with 5 pages |
| **Dockerized** | Multi-stage build serves API + frontend from a single container, runs as a non-root user |
| **Split-Deployable** | Frontend deploys to Vercel, backend to Railway/Render/Fly.io, wired together via env vars |
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
| **Fonts** | Formula1 (self-hosted, UI/headings), JetBrains Mono (data/telemetry) |
| **Streaming** | WebSocket (async, real-time-paced replay) |
| **Deployment** | Docker/docker-compose (single host), or Vercel (frontend) + Railway/Render/Fly.io (backend) |

---

## Project Structure

```
.
├── server/
│   └── main.py               FastAPI app (REST + WebSocket + SPA serving)
├── data_loader.py             FastF1 session loading & driver telemetry
├── feature_engineering.py     Feature extraction from raw telemetry
├── clustering.py              KMeans style classification + dynamic cluster labeling + PCA reduction
├── prediction.py              MLPRegressor lap time prediction
├── report.py                  Text report generation from analysis
├── visualization.py           Plot generation (matplotlib + seaborn)
├── insights.py                Per-analysis, data-driven plot captions
├── frontend/
│   ├── index.html             HTML entry with favicon + manifest links
│   ├── vite.config.js         Vite config with API/WS proxy
│   ├── tailwind.config.js     Custom F1 design system theme
│   ├── src/
│   │   ├── main.jsx           React mount
│   │   ├── App.jsx            Router setup (5 routes)
│   │   ├── index.css          Design tokens, @font-face, component classes, motion
│   │   ├── components/        Shared: Breadcrumbs, EmptyState, ErrorMessage,
│   │   │                      LoadingSkeleton, LoadingSpinner, PlotCard
│   │   ├── pages/             Home, SessionDetail, AnalysisResults, Report,
│   │   │                      LiveTelemetry
│   │   ├── hooks/             useApi.js, useWebSocket.js
│   │   └── lib/                plotInfo.js — shared plot titles/fallback descriptions
│   └── public/
│       ├── fonts/              Self-hosted Formula1 display font (Regular/Bold/Wide)
│       └── ...                 Favicons, site.webmanifest
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
├── output/                    Generated plots + store.json persistence (gitignored)
├── favicon-source.png         1024×1024 source for favicon generation
├── Dockerfile                 Multi-stage: Node 20 build → Python 3.12-slim, runs as non-root
├── docker-compose.yml         One-command production startup
├── .dockerignore               Keeps cache/, node_modules/, .git/, etc. out of the build context
├── vercel.json                 Frontend-only build config for a split Vercel deployment
├── render.yaml                 Free-tier backend blueprint for Render
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

1. **Home** — Click "Load Session", pick a Year and Grand Prix from the dropdowns (populated from FastF1's real event schedule) and a session type, click Load
2. **Session Detail** — Select at least 3 drivers from the grid (or click "Select All" for the whole field), click "Run Analysis" (3 minimum is required — KMeans clusters into 3 driving styles)
3. **Analysis Results** — View style classification cards (speed, brake frequency, aggression, sector times, estimated lap time) alongside the race/year context, then scroll to plots — each annotated with a caption computed from that specific analysis, not a generic description
4. **Report** — Read the full text report and scroll through the same annotated plots
5. **Live Telemetry** — Switch to a driver, watch speed/throttle/brake/DRS/gear replay paced to the actual lap timing

---

## API Documentation

All API routes are prefixed with `/api`. The full OpenAPI schema is available at `/docs` when the server is running.

### Session Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/schedule/{year}` | List Grand Prix event names for a season (feeds the Home page dropdown) |
| `GET` | `/api/sessions` | List loaded sessions with year/grand_prix/session_type/human-readable label |
| `POST` | `/api/sessions/load` | Validate and register a session (year/GP/session_type) — the actual FastF1 data load is deferred to first use, so this responds almost immediately |
| `GET` | `/api/sessions/{id}` | Get session metadata (year, grand_prix, session_type, label) |
| `GET` | `/api/sessions/{id}/drivers` | List driver codes in a session (triggers the deferred full session load on first call) |
| `GET` | `/api/sessions/{id}/drivers/{code}/telemetry` | Get fastest-lap telemetry for a driver |
| `GET` | `/api/sessions/{id}/drivers/{code}/sectors` | Get sector times (S1, S2, S3) for a driver — an individual sector can be `null` if that timing wasn't recorded |

### Analysis Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/sessions/{id}/analyze` | Run full analysis pipeline on selected drivers (3 minimum; up to a full grid). Responds once styles/predictions/report are ready; plots render in the background afterward |
| `GET` | `/api/analysis/{id}` | Get structured analysis data — session context, styles, predictions, features, sector times, per-plot insight captions, and a `plots_ready` flag |
| `GET` | `/api/analysis/{id}/report` | Get the text report for an analysis |
| `GET` | `/api/analysis/{id}/plots` | List available plot names |
| `GET` | `/api/analysis/{id}/plots/{name}.png` | Get a specific plot image — returns `202` with a small JSON body while it's still being generated in the background; the frontend polls until it's ready |

A request outside the allowed driver-count range, or naming a driver with no valid fastest lap in that session (e.g. a DNF before completing a timed lap), returns a `4xx` with a clear `detail` message rather than a generic server error.

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

`predictions` may come back as `{}` if lap-time model training failed for this driver set (logged server-side, never fails the whole request). For sector times, per-plot insight captions, and session context, fetch `GET /api/analysis/{analysis_id}` afterward — this initial response only carries what's needed to render the driver cards immediately.

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
2. **Stage 2 (Python 3.12-slim)** — Copies built frontend + Python app, installs requirements, then drops root to run as a non-root `appuser`

The container runs as **non-root**, matching your host user by default (UID/GID `1000`, the typical first-user id on Linux). This matters because the container writes into the bind-mounted `./cache` and `./output` volumes — if it ran as root, those files would come out root-owned and you wouldn't be able to write/delete them from the host afterward (and this app's own `output/store.json` persistence would silently start failing). `docker-compose.yml` passes your actual UID/GID as build args automatically; override them directly if you're not on the default:
```bash
docker compose build --build-arg UID=$(id -u) --build-arg GID=$(id -g)
```

### Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FASTF1_CACHE_DIR` | `cache` | FastF1 cache directory (relative to the working directory, or an absolute path) |
| `ALLOWED_ORIGINS` | `*` | Comma-separated CORS allowlist — only needed when the frontend is hosted on a different origin than this API |

### Volumes

| Host path | Container path | Purpose |
|-----------|---------------|---------|
| `./cache` | `/app/cache` | Persistent FastF1 data cache |
| `./output` | `/app/output` | Generated plot images |

---

## Split Deployment (Vercel + a backend host)

Vercel's serverless functions don't fit this backend — it keeps state in memory (loaded sessions, analyses) with file-backed persistence, streams real-time data over a long-lived WebSocket, and depends on a large on-disk FastF1 cache for reasonable performance. None of that survives Vercel's stateless, ephemeral function model. Instead, deploy the **frontend on Vercel** as a static site and the **backend on a host that runs a persistent container**. `render.yaml` (free tier) and the existing `Dockerfile` (works unmodified on Railway, Fly.io, or any other Docker host) are both included.

### 1. Backend on Render (free tier)

1. New **Blueprint** → connect this repo. Render reads `render.yaml` automatically and provisions the Docker web service on the free plan.
2. When prompted for `ALLOWED_ORIGINS` during blueprint setup, enter your Vercel frontend's URL if you already have it (e.g. `https://your-app.vercel.app`), or just leave it — it defaults to `*` (any origin) in code, which works but is more permissive than necessary; you can set it after the fact in **Environment**.
3. Deploy, then copy the generated URL (e.g. `https://f1-telemetry-api.onrender.com`) — you need it for the frontend build below.

**Free-tier trade-off**: Render's free plan has no persistent disk, so `cache/` and `output/store.json` reset on every restart. The app handles this gracefully (it just re-fetches from the F1 API instead of hitting a local cache), but two things follow from it: a session load after any restart is slower than a warm cache would be, and the service **spins down after 15 minutes of no traffic** — the next request wakes it back up, which can take 30-60 seconds. The frontend surfaces a "waking up the backend" message during that wait rather than looking stuck.

If you outgrow the free tier's cold starts, the same `Dockerfile` deploys to **Railway** or **Fly.io** with a persistent volume mounted at `/app/cache` and `/app/output` instead — no code changes, just a different host and a volume.

### 2. Frontend on Vercel

1. Import this repo into Vercel. The root-level `vercel.json` already points Vercel at the `frontend/` subdirectory's build (`buildCommand`/`outputDirectory`) and adds the SPA fallback rewrite React Router needs — no dashboard configuration required.
2. Add a **Production** (and Preview, if you want previews to also hit the real backend) environment variable:
   - `VITE_API_BASE_URL` = your backend URL from step 1 (e.g. `https://f1-telemetry-api.onrender.com`, no trailing slash).
3. Deploy. The frontend calls `${VITE_API_BASE_URL}/api/...` for REST and connects directly to the same host over `wss://` for the live telemetry WebSocket — Vercel never proxies either; the browser talks straight to the backend host.

`VITE_API_BASE_URL` is a Vite build-time variable, so it's baked into the JS bundle at build time — changing it requires a redeploy, not just a restart. Leaving it unset (e.g. for local dev or the single-container Docker setup) falls back to same-origin relative paths (`/api/...`), which is unchanged from before.

### 3. Lock down CORS

Once you have the Vercel URL, go back to the backend host's environment variables and set `ALLOWED_ORIGINS` to it exactly (scheme + host, no trailing slash, comma-separate multiple origins). This narrows CORS from the permissive `*` default.

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
- **Hosted platforms** (Railway, Render, etc.): the container's `CMD` binds to `$PORT` if the platform injects one, falling back to `8000` otherwise — no changes needed there.

### Analysis

KMeans `n_clusters=3` is fixed, but which cluster gets which name is **not** a fixed index mapping — cluster indices from KMeans are arbitrary and can flip between runs. Instead, `clustering.label_style_clusters()` names each cluster from its own computed feature values, every time:

| Label | How it's chosen |
|-------|-------|
| Aggressive | The cluster with the highest mean aggression index |
| Late Braker | Of what's left, the cluster with the highest mean brake frequency |
| Smooth Cornering | Whatever cluster remains |

This means a label always reflects a driver's behavior *relative to the others selected in that analysis*, not an absolute, cross-session classification — the same driver can land in a different style bucket depending on who else was analyzed alongside them. `MIN_DRIVERS`/`MAX_DRIVERS` (3 / 30) live in `server/main.py`.

### Design System

The frontend uses a custom dark F1 theme defined in `frontend/tailwind.config.js`:

- **Colors**: near-black `#050505` bg, Ferrari red `#e8002d` accent, carbon-fiber `#121214` / `#1a1a1e` surfaces
- **Fonts**: self-hosted Formula1 (Regular/Bold for `font-sans`, Wide for `font-wide` headings), JetBrains Mono for telemetry/data values — see `frontend/public/fonts/` and the `@font-face` rules in `frontend/src/index.css`
- **Motion**: `ease-out-quart` easing, 150–500ms durations, stagger entrance, reduced-motion support
- **Components**: `f1-card`, `f1-card-accent` (top accent stripe), `f1-btn-primary`, `f1-btn-secondary`, `f1-input`, `f1-select`, `f1-badge`, `f1-chip`, `f1-kicker` (small eyebrow label), `f1-progress`, with full hover/focus/active/disabled states

---

## Data Source

Uses [FastF1](https://github.com/theOehrly/FastF1) (v3.8.3) to load official Formula 1 session data from the Ergast API.

- **Cache**: `cache/` directory (gitignored; path configurable via the `FASTF1_CACHE_DIR` env var)
- **Tested sessions**: 2023/2024 Bahrain and Australian GPs, plus live-validated against a 2026 Monaco GP including a driver DNF (no valid fastest lap) edge case
- **Required columns**: Speed, Throttle, Brake, RPM, nGear, DRS, SessionTime (paces the live WebSocket replay), Distance (via FastF1's `add_distance()` — not present in the raw telemetry by default)
- **Steering/ERS**: Not available in FastF1 v3.8.3 for these sessions — these features are skipped

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

### Analyze fails with "no valid fastest lap"

A selected driver retired (or otherwise never set a representative timed lap) in that session, so FastF1 has nothing to pick as their "fastest lap" — a real race outcome, not a bug. Deselect that driver and re-run, or check `session.laps.pick_drivers('<code>')` yourself to confirm.

### Plot shows "Couldn't load this plot"

Plots render in the background after analysis completes and the card polls for up to ~30 seconds. If it still fails after that, check the server logs around `_generate_plots_task` — the analysis itself succeeded (styles/report are unaffected), only image rendering failed. Click **Retry** on the card to try again.

### `PermissionError: [Errno 13]` writing `output/store.json`

Usually means `output/` has a file left over from a container that once ran as root (pre-non-root-user images). Delete `output/store.json` — the app recreates it automatically — or `chown` the `output/`/`cache/` directories back to your user.

### Split deployment: requests fail or CORS errors in the browser console

- Confirm `VITE_API_BASE_URL` (Vercel) has no trailing slash and matches your backend's URL exactly — this is a **build-time** variable, so changing it requires a redeploy, not just a restart.
- Confirm `ALLOWED_ORIGINS` (Render/Railway/etc.) includes your exact Vercel URL (scheme + host, no trailing slash).

### Render free tier: first request after a while is very slow or times out

Expected — the free instance spins down after 15 minutes idle and the next request wakes it back up (30-60s). The frontend shows a "waking up the backend" message past a few seconds of waiting rather than looking frozen. If it's consistently timing out rather than just slow, check the Render service's logs; a cold start also has to rebuild the FastF1 cache from scratch (no persistent disk on the free plan), so the very first analysis after a wake can take longer than usual too.

---

## License

This project is for educational and research purposes. Formula 1 data is provided by [FastF1](https://github.com/theOehrly/FastF1) and originates from the official F1 timing feeds. The F1 logo and related trademarks are owned by Formula One World Championship Limited.
