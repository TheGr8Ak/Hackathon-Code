"""
Simple in-memory models for emergencies and vehicles.
"""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List
from uuid import uuid4


class Emergency:
    def __init__(self, lat: float, lng: float, condition: str = "CRITICAL"):
        self.id = str(uuid4())
        self.lat = lat
        self.lng = lng
        self.condition = condition
        self.created_at = datetime.utcnow()
        self.status = "ACTIVE"

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "lat": self.lat,
            "lng": self.lng,
            "condition": self.condition,
            "created_at": self.created_at.isoformat(),
            "status": self.status,
        }


class Vehicle:
    def __init__(self, vehicle_id: str, lat: float, lng: float):
        self.id = vehicle_id
        self.lat = lat
        self.lng = lng
        self.cleared = False

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "lat": self.lat,
            "lng": self.lng,
            "cleared": self.cleared,
        }


EMERGENCIES: Dict[str, Emergency] = {}


def add_emergency(emergency: Emergency) -> Emergency:
    EMERGENCIES[emergency.id] = emergency
    return emergency


def list_emergencies() -> List[Dict]:
    return [e.to_dict() for e in EMERGENCIES.values()]

