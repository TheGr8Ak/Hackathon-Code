"""
Traffic simulation for 30 random vehicles.
"""
from __future__ import annotations

import asyncio
import random
from typing import Dict, List


class TrafficSimulator:
    def __init__(self, sio):
        self.sio = sio
        self.vehicles: List[Dict] = []
        self.running = False

    async def start(self, center_lat: float, center_lng: float, num_cars: int = 30):
        self.vehicles = []
        for i in range(num_cars):
            self.vehicles.append(
                {
                    "id": f"car_{i}",
                    "lat": center_lat + random.uniform(-0.02, 0.02),
                    "lng": center_lng + random.uniform(-0.02, 0.02),
                    "speed_kmh": random.randint(20, 60),
                    "cleared": False,
                }
            )

        self.running = True
        asyncio.create_task(self._move_loop())

    async def _move_loop(self):
        while self.running:
            for vehicle in self.vehicles:
                if not vehicle.get("cleared"):
                    vehicle["lat"] += random.uniform(-0.0001, 0.0001)
                    vehicle["lng"] += random.uniform(-0.0001, 0.0001)
            await self.sio.emit("vehicles_update", {"vehicles": self.vehicles})
            await asyncio.sleep(1)

    def stop(self):
        self.running = False


