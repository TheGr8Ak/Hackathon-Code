"""
Nearest hospital utilities using Haversine distance.
"""
import json
import math
from pathlib import Path
from typing import Dict, List

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "hospitals_delhi.json"

with DATA_PATH.open("r", encoding="utf-8") as fp:
    HOSPITALS: List[Dict] = json.load(fp)


def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371000  # meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)

    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def find_nearest_hospital(lat: float, lng: float) -> Dict:
    emergency_hospitals = [h for h in HOSPITALS if h.get("emergency", True)]
    nearest = min(
        emergency_hospitals,
        key=lambda h: haversine_distance(lat, lng, h["lat"], h["lng"]),
    )
    return nearest


def get_all_hospitals(lat: float, lng: float, radius_km: float = 5) -> List[Dict]:
    radius_m = radius_km * 1000
    results = []
    for hospital in HOSPITALS:
        dist = haversine_distance(lat, lng, hospital["lat"], hospital["lng"])
        if dist <= radius_m:
            entry = hospital.copy()
            entry["distance_m"] = dist
            results.append(entry)
    return sorted(results, key=lambda x: x["distance_m"])

