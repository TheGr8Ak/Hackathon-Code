"""
Route generation using OSRM with straight-line fallback.
"""
from __future__ import annotations

import logging
from typing import List, Dict, Tuple

import requests

from ..app.config import settings

logger = logging.getLogger(__name__)


def generate_route(start: Tuple[float, float], end: Tuple[float, float]) -> List[Dict[str, float]]:
    """
    Generate a route polyline between start and end coordinates.
    """
    start_lat, start_lng = start
    end_lat, end_lng = end

    url = f"{settings.osrm_base_url}/route/v1/driving/{start_lng},{start_lat};{end_lng},{end_lat}"
    params = {
        "overview": "full",
        "geometries": "geojson",
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()

        if data.get("code") != "Ok":
            raise ValueError(data.get("message", "OSRM error"))

        coordinates = data["routes"][0]["geometry"]["coordinates"]
        polyline = [{"lat": lat, "lng": lng} for lng, lat in coordinates]
        logger.info(f"Generated OSRM route with {len(polyline)} points")
        return polyline

    except Exception as exc:
        logger.warning(f"OSRM routing failed ({exc}). Falling back to straight line.")
        # simple two-point route
        return [
            {"lat": start_lat, "lng": start_lng},
            {"lat": end_lat, "lng": end_lng},
        ]

