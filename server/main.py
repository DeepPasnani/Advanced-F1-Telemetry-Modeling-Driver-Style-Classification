"""F1 Telemetry API — FastAPI application."""

import uuid
import asyncio
import os
import json
import logging
import threading
from pathlib import Path
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from pydantic import BaseModel

import data_loader as dl
import feature_engineering as fe
import clustering as cl
import prediction as pr
import report as rp
import visualization as vis
import insights as ins

logger = logging.getLogger("f1_telemetry")

OUTPUT_DIR = "output"
STORE_PATH = os.path.join(OUTPUT_DIR, "store.json")

# KMeans needs at least this many samples to form 3 style clusters. The
# upper bound just guards against a malformed request (e.g. duplicated
# codes) rather than the field itself — a full ~20-driver grid analyzes
# and plots in a few seconds, so it's set well above any real F1 grid size.
MIN_DRIVERS = 3
MAX_DRIVERS = 30

SESSION_TYPE_LABELS = {
    "R": "Race", "Q": "Qualifying", "S": "Sprint", "SQ": "Sprint Qualifying",
    "FP1": "Practice 1", "FP2": "Practice 2", "FP3": "Practice 3",
}

app = FastAPI(title="F1 Telemetry API", version="1.0.0")

# Needed when the frontend is hosted separately from this API (e.g. the
# frontend on Vercel, this backend on Railway/Render/Fly). Same-origin
# deployments (Docker serving both from one process) don't need this, but
# CORS on an unrelated origin is harmless either way.
ALLOWED_ORIGINS = [o.strip() for o in os.environ.get("ALLOWED_ORIGINS", "*").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,  # no cookies/auth in use; "*" + credentials is invalid anyway
    allow_methods=["*"],
    allow_headers=["*"],
)

# session_id -> loaded FastF1 Session object (heavy, kept in memory only —
# reloaded on demand from sessions_meta via FastF1's own on-disk cache, so
# a server restart doesn't turn old session links into dead ends).
sessions: dict = {}

# sessions_meta and analyses are plain JSON-serializable dicts persisted to
# STORE_PATH (inside the already-mounted output/ volume) so a restart keeps
# session links resolvable and past analyses/plots browsable.
sessions_meta: dict = {}
analyses: dict = {}


def _load_store():
    if os.path.exists(STORE_PATH):
        try:
            with open(STORE_PATH, "r") as f:
                data = json.load(f)
            sessions_meta.update(data.get("sessions_meta", {}))
            analyses.update(data.get("analyses", {}))
        except Exception:
            logger.exception("Failed to load persisted store from %s", STORE_PATH)


def _save_store():
    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        with open(STORE_PATH, "w") as f:
            json.dump({"sessions_meta": sessions_meta, "analyses": analyses}, f)
    except Exception:
        logger.exception("Failed to persist store to %s", STORE_PATH)


_load_store()


# ── Pydantic models ──────────────────────────────────────────

class LoadSessionRequest(BaseModel):
    year: int
    grand_prix: str
    session_type: str = "R"


class AnalyzeRequest(BaseModel):
    driver_codes: list[str]


# ── Helper ──────────────────────────────────────────────────

# Loading a session (even fully cached) is a couple of seconds of CPU-bound
# work, so /api/sessions/load only validates and defers the actual load to
# here, on first real use. The Session Detail page fires getDrivers and
# getSessionInfo in parallel, so without this lock both requests would race
# to load the same session concurrently, doubling the work for no reason.
_session_load_lock = threading.Lock()


def _get_session(session_id: str):
    session = sessions.get(session_id)
    if session is not None:
        return session

    with _session_load_lock:
        session = sessions.get(session_id)  # re-check: another thread may have just finished
        if session is not None:
            return session

        meta = sessions_meta.get(session_id)
        if meta is None:
            raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")

        try:
            session = dl.load_session(meta["year"], meta["grand_prix"], meta["session_type"])
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Failed to reload session: {e}")
        sessions[session_id] = session
        return session


# ── Session endpoints ───────────────────────────────────────

def _session_label(meta: dict) -> str:
    type_label = SESSION_TYPE_LABELS.get(meta["session_type"], meta["session_type"])
    return f"{meta['year']} {meta['grand_prix']} — {type_label}"


@app.get("/api/sessions")
def list_sessions():
    # sessions_meta is the persisted superset of sessions (which only holds
    # Session objects reloaded so far in this process), so list from there.
    return {
        "status": "ok",
        "data": [
            {
                "id": session_id,
                "year": meta["year"],
                "grand_prix": meta["grand_prix"],
                "session_type": meta["session_type"],
                "label": _session_label(meta),
            }
            for session_id, meta in sessions_meta.items()
        ],
    }


_schedule_cache: dict = {}  # year -> list of event names; a season's calendar is effectively static


@app.get("/api/schedule/{year}")
def get_schedule(year: int):
    if year in _schedule_cache:
        return {"status": "ok", "data": _schedule_cache[year]}
    try:
        events = dl.get_event_schedule(year)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    _schedule_cache[year] = events
    return {"status": "ok", "data": events}


@app.post("/api/sessions/load")
def load_session(req: LoadSessionRequest):
    # Only resolve (validate) the session here — the full data load is a
    # couple of seconds of work even fully cached, and this endpoint is
    # what the "Load" button waits on. Defer the actual load to first real
    # use (_get_session, triggered by the Session Detail page loading the
    # driver list), which already shows its own loading state.
    try:
        dl.resolve_session(req.year, req.grand_prix, req.session_type)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    session_id = str(uuid.uuid4())
    sessions_meta[session_id] = {
        "year": req.year,
        "grand_prix": req.grand_prix,
        "session_type": req.session_type,
    }
    _save_store()
    return {
        "status": "ok",
        "data": {"session_id": session_id, "year": req.year, "grand_prix": req.grand_prix},
    }


@app.get("/api/sessions/{session_id}")
def get_session_info(session_id: str):
    _get_session(session_id)  # validates the session exists / can be reloaded
    meta = sessions_meta.get(session_id, {})
    return {
        "status": "ok",
        "data": {
            "session_id": session_id,
            "year": meta.get("year"),
            "grand_prix": meta.get("grand_prix"),
            "session_type": meta.get("session_type"),
            "label": _session_label(meta) if meta else session_id,
        },
    }


@app.get("/api/sessions/{session_id}/drivers")
def get_drivers(session_id: str):
    session = _get_session(session_id)
    drivers = dl.get_drivers(session)
    return {"status": "ok", "data": drivers}


@app.get("/api/sessions/{session_id}/drivers/{driver_code}/telemetry")
def get_driver_telemetry(session_id: str, driver_code: str):
    session = _get_session(session_id)
    try:
        telemetry = dl.get_driver_telemetry(session, driver_code.upper())
    except dl.DriverNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except dl.NoValidLapError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return {"status": "ok", "data": telemetry.to_dict(orient="records")}


@app.get("/api/sessions/{session_id}/drivers/{driver_code}/sectors")
def get_driver_sectors(session_id: str, driver_code: str):
    session = _get_session(session_id)
    try:
        s1, s2, s3 = dl.get_sector_times(session, driver_code.upper())
    except dl.DriverNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except dl.NoValidLapError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return {"status": "ok", "data": {"sector_1": s1, "sector_2": s2, "sector_3": s3}}


# ── Analysis endpoints ──────────────────────────────────────

def _generate_plots_task(analysis_id, fastest_telemetry_dict, sector_dict, feature_df, style_names, plot_dir):
    """Runs after the /analyze response is already sent. Plot rendering
    (matplotlib + savefig for 5 charts) is the slowest part of an analysis;
    decoupling it means the report/styles/predictions come back almost
    immediately and the UI can show them while plots fill in."""
    try:
        vis.generate_all_visualizations(fastest_telemetry_dict, sector_dict, feature_df, style_names, output_dir=plot_dir)
    except Exception:
        logger.exception("Plot generation failed for analysis %s", analysis_id)
    finally:
        if analysis_id in analyses:
            analyses[analysis_id]["plots_ready"] = True
            _save_store()


@app.post("/api/sessions/{session_id}/analyze")
def run_analysis(session_id: str, req: AnalyzeRequest, background_tasks: BackgroundTasks):
    session = _get_session(session_id)

    # KMeans below is fixed at 3 clusters, so fewer drivers than that
    # crashes with an unhandled ValueError. Dedupe (preserving order) so a
    # repeated code can't be used to pad past MAX_DRIVERS for free.
    driver_codes = list(dict.fromkeys(c.upper() for c in req.driver_codes))
    if len(driver_codes) < MIN_DRIVERS:
        raise HTTPException(
            status_code=400,
            detail=f"Select at least {MIN_DRIVERS} drivers to run style classification",
        )
    if len(driver_codes) > MAX_DRIVERS:
        raise HTTPException(
            status_code=400,
            detail=f"Select at most {MAX_DRIVERS} drivers per analysis",
        )

    telemetry_dict = {}
    fastest_telemetry_dict = {}
    sector_dict = {}
    for code in driver_codes:
        try:
            # "all" laps is needed for feature aggregation (mean/std per
            # driver); the plots only ever show a single fastest lap, so
            # feeding them the full multi-lap telemetry (tens of thousands
            # of rows, with Distance resetting every lap) was both wrong
            # (a jagged, meaningless trace) and the main reason analysis
            # felt slow — fetch the much smaller fastest-lap set for those.
            telemetry_dict[code] = dl.get_driver_telemetry(session, code, laps="all")
            fastest_telemetry_dict[code] = dl.get_driver_telemetry(session, code, laps="fastest")
            sector_dict[code] = dl.get_sector_times(session, code)
        except dl.DriverNotFound:
            raise HTTPException(status_code=404, detail=f"Driver '{code}' not found")
        except dl.NoValidLapError as e:
            # A legitimate race outcome (e.g. a DNF before any timed lap),
            # not a bug — surface it clearly so the user can deselect this
            # driver, rather than a raw 500.
            raise HTTPException(status_code=422, detail=str(e))

    weather_dict = dl.get_weather(session)
    feature_df = fe.extract_features(telemetry_dict, laps="all", weather_dict=weather_dict)
    style_labels, _ = cl.perform_clustering(feature_df, n_clusters=3)

    # Cluster indices are arbitrary; name each cluster from its own feature
    # values so labels reflect actual relative driving behavior.
    style_names = cl.label_style_clusters(feature_df, style_labels)

    # Lap time prediction. Note: with only a handful of samples (one per
    # selected driver) this model is fit and evaluated on the same tiny
    # set, so it's better read as "how this driver's style compares to the
    # others' lap times" than a true out-of-sample forecast.
    predictions = {}
    try:
        target_times = {
            code: session.laps.pick_drivers(code).pick_fastest()["LapTime"].total_seconds()
            for code in driver_codes
        }
        target_series = feature_df.index.to_series().map(target_times)
        model_pack = pr.train_lap_time_predictor(feature_df, target_series)
        predictions = {
            code: pr.predict_lap_time(model_pack, feature_df.loc[code].tolist())
            for code in driver_codes
        }
    except Exception:
        logger.exception("Lap time prediction failed for session %s, drivers %s", session_id, driver_codes)
        predictions = {}

    report_text = rp.generate_report(feature_df, style_names, sector_dict, weather_dict=weather_dict)
    plot_insights = ins.generate_plot_insights(feature_df, style_names, sector_dict)

    analysis_id = str(uuid.uuid4())
    styles = dict(zip(driver_codes, style_names))
    features = feature_df.to_dict(orient="index")
    sector_times = {code: list(times) for code, times in sector_dict.items()}

    analyses[analysis_id] = {
        "report": report_text,
        "session_id": session_id,
        "driver_codes": driver_codes,
        "styles": styles,
        "predictions": predictions,
        "features": features,
        "sector_times": sector_times,
        "plot_insights": plot_insights,
        "plot_names": ["speed_trace", "throttle_brake", "sector_comparison", "radar_chart", "cluster_scatter"],
        "plots_ready": False,
    }
    _save_store()

    # Namespace plots per analysis so concurrent/successive analyses don't
    # overwrite each other's images; render them after responding so the
    # user isn't stuck waiting on matplotlib before seeing anything.
    plot_dir = os.path.join(OUTPUT_DIR, analysis_id)
    background_tasks.add_task(
        _generate_plots_task, analysis_id, fastest_telemetry_dict, sector_dict, feature_df, style_names, plot_dir
    )

    return {
        "status": "ok",
        "data": {
            "analysis_id": analysis_id,
            "styles": styles,
            "predictions": predictions,
            "features": features,
        },
    }


@app.get("/api/analysis/{analysis_id}")
def get_analysis(analysis_id: str):
    result = analyses.get(analysis_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Analysis '{analysis_id}' not found")
    session_meta = sessions_meta.get(result["session_id"], {})
    return {
        "status": "ok",
        "data": {
            "session_id": result["session_id"],
            "session": {
                "year": session_meta.get("year"),
                "grand_prix": session_meta.get("grand_prix"),
                "session_type": session_meta.get("session_type"),
                "label": _session_label(session_meta) if session_meta else None,
            },
            "driver_codes": result["driver_codes"],
            "styles": result["styles"],
            "predictions": result["predictions"],
            "features": result["features"],
            "sector_times": result["sector_times"],
            "plot_insights": result.get("plot_insights", {}),
            "plots_ready": result.get("plots_ready", True),
        },
    }


@app.get("/api/analysis/{analysis_id}/report")
def get_report(analysis_id: str):
    result = analyses.get(analysis_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Analysis '{analysis_id}' not found")
    return {"status": "ok", "data": {"report": result["report"]}}


@app.get("/api/analysis/{analysis_id}/plots")
def list_plots(analysis_id: str):
    result = analyses.get(analysis_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Analysis '{analysis_id}' not found")
    return {"status": "ok", "data": result["plot_names"]}


@app.get("/api/analysis/{analysis_id}/plots/{plot_name}")
def get_plot(analysis_id: str, plot_name: str):
    result = analyses.get(analysis_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Analysis '{analysis_id}' not found")
    allowed = result["plot_names"]
    if plot_name not in allowed and plot_name not in [p + ".png" for p in allowed]:
        raise HTTPException(status_code=404, detail=f"Plot '{plot_name}' not found. Available: {allowed}")
    name = plot_name.replace(".png", "")
    path = os.path.join(OUTPUT_DIR, analysis_id, f"{name}.png")
    if not os.path.exists(path):
        if not result.get("plots_ready", True):
            # Distinguishable from a real 404 so the frontend knows to
            # retry rather than show an error.
            return JSONResponse(status_code=202, content={"status": "pending", "detail": "Plot is still generating"})
        raise HTTPException(status_code=404, detail=f"Plot file not found on disk")
    return FileResponse(path, media_type="image/png")


# ── WebSocket telemetry stream ────────────────────────────


@app.websocket("/ws/telemetry/{session_id}/{driver_code}")
async def telemetry_stream(websocket: WebSocket, session_id: str, driver_code: str):
    """Stream driver telemetry in real time by replaying fastest-lap data."""
    await websocket.accept()
    try:
        session = _get_session(session_id)
        telemetry = dl.get_driver_telemetry(session, driver_code.upper())
        if telemetry.empty:
            await websocket.send_json({"error": "No telemetry data"})
            return

        rows = telemetry.to_dict(orient="records")
        total = len(rows)

        def _seconds(row):
            # SessionTime is a pandas Timedelta; to_dict() leaves it as-is
            # rather than converting it to a plain number.
            value = row.get("SessionTime")
            return value.total_seconds() if hasattr(value, "total_seconds") else 0.0

        prev_time = _seconds(rows[0]) if rows else 0.0

        for i, row in enumerate(rows):
            curr_time = _seconds(row)
            # Clamp to guard against any anomalous gap in the source data
            # stalling the whole replay.
            delay = min(max(0.0, curr_time - prev_time), 2.0)
            if delay > 0:
                await asyncio.sleep(delay)
            prev_time = curr_time

            data = {
                "speed": row.get("Speed", 0),
                "throttle": row.get("Throttle", 0),
                "brake": row.get("Brake", 0),
                "drs": row.get("DRS", 0),
                "rpm": row.get("RPM", 0),
                "gear": row.get("nGear", 0),
                "lap_progress": (i + 1) / total,
            }

            await websocket.send_json(data)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"error": str(e)})
        except Exception:
            pass


# ── Static file serving (production) ───────────────────────


FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"


@app.get("/assets/{file_path:path}")
async def serve_asset(file_path: str):
    path = FRONTEND_DIST / "assets" / file_path
    if path.is_file():
        return FileResponse(str(path))
    raise HTTPException(status_code=404)


@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    """Serve frontend static files with SPA fallback to index.html."""
    if not FRONTEND_DIST.is_dir():
        raise HTTPException(status_code=404, detail="Frontend not built")
    if not full_path or full_path == "":
        full_path = "index.html"
    path = FRONTEND_DIST / full_path
    if path.is_file():
        return FileResponse(str(path))
    # SPA fallback
    index = FRONTEND_DIST / "index.html"
    if index.is_file():
        return FileResponse(str(index))
    raise HTTPException(status_code=404)
