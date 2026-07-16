"""F1 Telemetry API — FastAPI application."""

import uuid

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import data_loader as dl
import feature_engineering as fe
import clustering as cl
import prediction as pr
import report as rp
import visualization as vis

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

@app.get("/sessions")
def list_sessions():
    return {"status": "ok", "data": list(sessions.keys())}


@app.post("/sessions/load")
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


@app.get("/sessions/{session_id}")
def get_session_info(session_id: str):
    session = _get_session(session_id)
    return {"status": "ok", "data": {"session_id": session_id}}


@app.get("/sessions/{session_id}/drivers")
def get_drivers(session_id: str):
    session = _get_session(session_id)
    drivers = dl.get_drivers(session)
    return {"status": "ok", "data": drivers}


@app.get("/sessions/{session_id}/drivers/{driver_code}/telemetry")
def get_driver_telemetry(session_id: str, driver_code: str):
    session = _get_session(session_id)
    try:
        telemetry = dl.get_driver_telemetry(session, driver_code.upper())
    except dl.DriverNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"status": "ok", "data": telemetry.to_dict(orient="records")}


@app.get("/sessions/{session_id}/drivers/{driver_code}/sectors")
def get_driver_sectors(session_id: str, driver_code: str):
    session = _get_session(session_id)
    try:
        s1, s2, s3 = dl.get_sector_times(session, driver_code.upper())
    except dl.DriverNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"status": "ok", "data": {"sector_1": s1, "sector_2": s2, "sector_3": s3}}


# ── Analysis endpoints ──────────────────────────────────────

@app.post("/sessions/{session_id}/analyze")
def run_analysis(session_id: str, req: AnalyzeRequest):
    session = _get_session(session_id)

    telemetry_dict = {}
    sector_dict = {}
    for code in req.driver_codes:
        code = code.upper()
        try:
            telemetry_dict[code] = dl.get_driver_telemetry(session, code)
            sector_dict[code] = dl.get_sector_times(session, code)
        except dl.DriverNotFound:
            raise HTTPException(status_code=404, detail=f"Driver '{code}' not found")

    feature_df = fe.extract_features(telemetry_dict)
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

    report_text = rp.generate_report(feature_df, style_names, sector_dict)

    vis.generate_all_visualizations(telemetry_dict, sector_dict, feature_df, style_names)

    analysis_id = str(uuid.uuid4())
    analyses[analysis_id] = {
        "report": report_text,
        "session_id": session_id,
        "driver_codes": req.driver_codes,
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


@app.get("/analysis/{analysis_id}/report")
def get_report(analysis_id: str):
    result = analyses.get(analysis_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Analysis '{analysis_id}' not found")
    return {"status": "ok", "data": {"report": result["report"]}}
