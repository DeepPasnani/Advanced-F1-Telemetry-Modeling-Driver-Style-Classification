"""
Pydantic request/response models for the F1 Telemetry API.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Optional, Any
from enum import Enum


class SessionType(str, Enum):
    R = "R"
    Q = "Q"
    FP1 = "FP1"
    FP2 = "FP2"
    FP3 = "FP3"


class AnalyzeRequest(BaseModel):
    year: int = Field(..., ge=2018, le=2024, description="Year of the F1 season")
    gp: str = Field(..., min_length=1, description="Grand Prix name")
    session: SessionType = Field(..., description="Session type")
    drivers: List[str] = Field(..., min_length=2, max_length=6, description="List of driver codes")

    @field_validator("drivers")
    @classmethod
    def validate_drivers(cls, v: List[str]) -> List[str]:
        if not all(len(d) == 3 and d.isalpha() for d in v):
            raise ValueError("Each driver code must be a 3-letter string")
        return [d.upper() for d in v]


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"


class JobResponse(BaseModel):
    job_id: str
    status: JobStatus


class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    progress: int = Field(..., ge=0, le=100)
    step: str


class DriverFeatures(BaseModel):
    mean_speed: float
    max_speed: float
    mean_throttle: float
    brake_frequency: float
    mean_rpm: float
    mean_gear: float
    aggression_index: float


class ClustersResponse(BaseModel):
    kmeans: Dict[str, str]
    hierarchical: Dict[str, str]


class SectorTimes(BaseModel):
    s1: float
    s2: float
    s3: float


class SectorTimesResponse(BaseModel):
    sector_times: Dict[str, SectorTimes]


class LapTimePrediction(BaseModel):
    r2: float
    mae: float
    predictions: Dict[str, float]


class SessionInfo(BaseModel):
    year: int
    gp: str
    session: str


class AnalyzeResult(BaseModel):
    session_info: SessionInfo
    drivers: List[str]
    features: Dict[str, DriverFeatures]
    clusters: ClustersResponse
    sector_times: Dict[str, SectorTimes]
    lap_time_prediction: LapTimePrediction
    plots: Dict[str, str]
    report_text: str


class GPListResponse(BaseModel):
    gps: List[str]


class HealthResponse(BaseModel):
    status: str
    timestamp: str