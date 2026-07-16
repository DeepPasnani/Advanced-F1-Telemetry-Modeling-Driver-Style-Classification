# F1 Telemetry Dashboard — Phase 2 Design

## Overview

Build a React + Vite + Tailwind frontend for the F1 Telemetry API. Multi-page dashboard for browsing sessions, selecting drivers, running analysis, and viewing results (cluster styles, predictions, plots, report).

## Architecture

```
Frontend (Vite + React + Tailwind) ──HTTP──► FastAPI (port 8000)
                                              │
                                              ▼
                                         Core Modules
```

- Vite dev server proxies `/api/*` to `http://localhost:8000/*`
- Client-side routing via React Router
- No backend changes needed — all data comes from existing API endpoints

## Page Routes

| Route | Page | Key Data |
|-------|------|----------|
| `/` | Home | `GET /sessions`, list cached + load form |
| `/session/:id` | Session Detail | `GET /sessions/:id/drivers` |
| `/analysis/:id` | Analysis Results | `POST /sessions/:id/analyze` results |
| `/analysis/:id/report` | Report | `GET /analysis/:id/report` + plot images |

## Components

- **Header** — nav bar with route links
- **Home** — `SessionList` (cards), `LoadSessionForm` (year/grand_prix/session_type), `EmptyState`
- **SessionDetail** — `DriverSelector` (checkboxes/toggle), `AnalyzeButton`
- **AnalysisResults** — `StyleBadges`, `PredictionTable`, `FeatureTable`, `PlotViewer`
- **Report** — `ReportText` (formatted text), `PlotGallery` (images from API)

## Data Flow

1. Home → `GET /sessions` → display cards
2. Load session → `POST /sessions/load` → redirect to `/session/:id`
3. Session page → `GET /sessions/:id/drivers` → show driver list
4. Run analysis → `POST /sessions/:id/analyze` → redirect to `/analysis/:id`
5. Analysis page → display styles, predictions, features + `GET /analysis/:id/report`, plot URLs
6. Report page → full text + plot images

Error states: 404 handling for unknown sessions/analyses, loading spinners, empty states.

## Out of Scope

- Authentication (add when deployed publicly)
- Real-time telemetry streaming
- Deep learning model improvements
