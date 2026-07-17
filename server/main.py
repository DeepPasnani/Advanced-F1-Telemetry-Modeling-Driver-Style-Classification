"""F1 Telemetry API — FastAPI application."""

import uuid
import asyncio
import os
import json
from pathlib import Path
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

import data_loader as dl
import feature_engineering as fe
import clustering as cl
import prediction as pr
import report as rp
import visualization as vis

OUTPUT_DIR = "output"

app = FastAPI(title="F1 Telemetry API", version="1.0.0")

# In-memory storage: session_id -> session, analysis_id -> results
# ponytail: in-memory dict, add Redis/DB when persistence needed
sessions: dict = {}
analyses: dict = {}


# ── Pydantic models ──────────────────────────────────────────

class LoadSessionRequest(BaseModel):
    year: int
    grand_prix: str
    session_type: str = "R"


class AnalyzeRequest(BaseModel):
    driver_codes: list[str]


# ── Helper ──────────────────────────────────────────────────

def _get_session(session_id: str):
    session = sessions.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
    return session


# ── Session endpoints ───────────────────────────────────────

@app.get("/api/sessions")
def list_sessions():
    return {"status": "ok", "data": list(sessions.keys())}


@app.post("/api/sessions/load")
def load_session(req: LoadSessionRequest):
    try:
        session = dl.load_session(req.year, req.grand_prix, req.session_type)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    session_id = str(uuid.uuid4())
    sessions[session_id] = session
    return {
        "status": "ok",
        "data": {"session_id": session_id, "year": req.year, "grand_prix": req.grand_prix},
    }


@app.get("/api/sessions/{session_id}")
def get_session_info(session_id: str):
    session = _get_session(session_id)
    return {"status": "ok", "data": {"session_id": session_id}}


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
    return {"status": "ok", "data": telemetry.to_dict(orient="records")}


@app.get("/api/sessions/{session_id}/drivers/{driver_code}/sectors")
def get_driver_sectors(session_id: str, driver_code: str):
    session = _get_session(session_id)
    try:
        s1, s2, s3 = dl.get_sector_times(session, driver_code.upper())
    except dl.DriverNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"status": "ok", "data": {"sector_1": s1, "sector_2": s2, "sector_3": s3}}


# ── Analysis endpoints ──────────────────────────────────────

@app.post("/api/sessions/{session_id}/analyze")
def run_analysis(session_id: str, req: AnalyzeRequest):
    session = _get_session(session_id)

    telemetry_dict = {}
    sector_dict = {}
    for code in req.driver_codes:
        code = code.upper()
        try:
            telemetry_dict[code] = dl.get_driver_telemetry(session, code, laps="all")
            sector_dict[code] = dl.get_sector_times(session, code)
        except dl.DriverNotFound:
            raise HTTPException(status_code=404, detail=f"Driver '{code}' not found")

    weather_dict = dl.get_weather(session)
    feature_df = fe.extract_features(telemetry_dict, laps="all", weather_dict=weather_dict)
    style_labels, _ = cl.perform_clustering(feature_df, n_clusters=3)

    label_map = {0: "Aggressive", 1: "Smooth Cornering", 2: "Late Braker"}
    style_names = [label_map.get(l, "Unknown") for l in style_labels]

    # Lap time prediction
    predictions = {}
    try:
        target_times = {}
        for code in req.driver_codes:
            code = code.upper()
            fastest = session.laps.pick_drivers(code).pick_fastest()
            target_times[code] = fastest["LapTime"].total_seconds()
        target_series = feature_df.index.to_series().map(target_times)
        model_pack = pr.train_lap_time_predictor(feature_df, target_series)
        predictions = {
            code: pr.predict_lap_time(model_pack, feature_df.loc[code].tolist())
            for code in req.driver_codes
        }
    except Exception:
        predictions = {}

    report_text = rp.generate_report(feature_df, style_names, sector_dict, weather_dict=weather_dict)

    vis.generate_all_visualizations(telemetry_dict, sector_dict, feature_df, style_names)

    analysis_id = str(uuid.uuid4())
    analyses[analysis_id] = {
        "report": report_text,
        "session_id": session_id,
        "driver_codes": req.driver_codes,
        "plot_names": ["speed_trace", "throttle_brake", "sector_comparison", "radar_chart", "cluster_scatter"],
    }

    return {
        "status": "ok",
        "data": {
            "analysis_id": analysis_id,
            "styles": dict(zip(req.driver_codes, style_names)),
            "predictions": predictions,
            "features": feature_df.to_dict(orient="index"),
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
    path = os.path.join(OUTPUT_DIR, f"{name}.png")
    if not os.path.exists(path):
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
        prev_time = rows[0].get("SessionTime", 0) if "SessionTime" in rows[0] else 0

        for i, row in enumerate(rows):
            curr_time = row.get("SessionTime", prev_time)
            delay = max(0, curr_time - prev_time)
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
