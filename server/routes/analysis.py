"""
API routes for F1 Telemetry analysis.
"""

from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from typing import List
import fastf1

from server.models import (
    AnalyzeRequest, JobResponse, JobStatusResponse, AnalyzeResult,
    GPListResponse, HealthResponse
)
from server.cache import job_store
from server.services import pipeline


router = APIRouter()


@router.post("/api/analyze", response_model=JobResponse)
async def analyze(request: AnalyzeRequest):
    """Start an analysis job."""
    job_id = pipeline.start_analysis(
        year=request.year,
        gp=request.gp,
        session=request.session.value,
        drivers=request.drivers
    )
    return JobResponse(job_id=job_id, status="queued")


@router.get("/api/status/{job_id}", response_model=JobStatusResponse)
async def get_status(job_id: str):
    """Get job status."""
    job = job_store.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatusResponse(
        job_id=job_id,
        status=job["status"],
        progress=job["progress"],
        step=job["step"]
    )


@router.get("/api/result/{job_id}")
async def get_result(job_id: str):
    """Get job result."""
    job = job_store.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] == "error":
        raise HTTPException(status_code=500, detail=job.get("error", "Unknown error"))
    if job["status"] != "done":
        raise HTTPException(status_code=400, detail="Job not complete")
    return job["result"]


@router.get("/api/gp_list", response_model=GPListResponse)
async def get_gp_list(year: int = Query(..., ge=2018, le=2024)):
    """Get list of Grand Prix for a given year."""
    try:
        schedule = fastf1.get_session(year, "Bahrain", "R").event
        schedule.load()
        
        year_events = fastf1.get_session(year, "Bahrain", "R")
        year_events.load()
        
        events = []
        try:
            event_loop = fastf1.get_event_schedule(year)
            if not event_loop.empty:
                events = event_loop["EventName"].tolist()
        except:
            pass
        
        if not events:
            events = [
                "Bahrain", "Saudi Arabia", "Australia", "Japan", "China",
                "Miami", "Monaco", "Canada", "Spain", "Austria", "Great Britain",
                "Hungary", "Belgium", "Netherlands", "Italy", "Azerbaijan",
                "Singapore", "Mexico", "Brazil", "United States", "Abu Dhabi"
            ]
        
        return GPListResponse(gps=events)
    except Exception as e:
        default_gps = [
            "Bahrain", "Saudi Arabia", "Australia", "Japan", "China",
            "Miami", "Monaco", "Canada", "Spain", "Austria", "Great Britain",
            "Hungary", "Belgium", "Netherlands", "Italy", "Azerbaijan",
            "Singapore", "Mexico", "Brazil", "United States", "Abu Dhabi"
        ]
        return GPListResponse(gps=default_gps)


@router.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="ok",
        timestamp=datetime.now().isoformat()
    )