"""
Pydantic schemas for API payloads/responses.
"""
from datetime import datetime
from typing import List, Dict, Optional
from pydantic import BaseModel


class SOSRequest(BaseModel):
    lat: float
    lng: float
    condition: str = "CRITICAL"


class EmergencyResponse(BaseModel):
    id: str
    message: str


class Hospital(BaseModel):
    name: str
    lat: float
    lng: float
    type: str
    emergency: bool = True
    distance_m: Optional[float] = None


class RoutePoint(BaseModel):
    lat: float
    lng: float


class AmbulancePosition(BaseModel):
    lat: float
    lng: float
    timestamp: datetime

