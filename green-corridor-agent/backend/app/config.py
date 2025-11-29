"""
Configuration for Green Corridor Agent backend.
"""
from pydantic import BaseSettings
from typing import Tuple


class Settings(BaseSettings):
    map_center_lat: float = 28.6139  # Delhi default
    map_center_lng: float = 77.2090

    socket_namespace: str = "/"

    osrm_base_url: str = "http://router.project-osrm.org"

    class Config:
        env_prefix = "GCA_"
        env_file = ".env"


settings = Settings()


def get_map_center() -> Tuple[float, float]:
    return settings.map_center_lat, settings.map_center_lng

