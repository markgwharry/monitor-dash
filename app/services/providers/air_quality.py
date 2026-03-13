import httpx
from typing import Any, Dict

from app.services.providers.base import DataProvider


class AirQualityProvider(DataProvider):
    """Fetches air quality and indoor environment data from the local sensor."""

    def __init__(self, endpoint: str = "http://192.168.1.65"):
        self.endpoint = endpoint
        self._client = httpx.AsyncClient(timeout=5.0)

    @property
    def name(self) -> str:
        return "air_quality"

    @staticmethod
    def _pm25_label(pm25: float) -> str:
        """WHO-aligned PM2.5 assessment."""
        if pm25 <= 12:
            return "Good"
        if pm25 <= 35:
            return "Fair"
        if pm25 <= 55:
            return "Poor"
        return "Bad"

    @staticmethod
    def _voc_label(voc_index: int, sensor_quality: str = "") -> str:
        """Map VOC index to a label."""
        if voc_index == 0:
            # Index 0 means clean air once calibrated; fall back to sensor's own reading
            return sensor_quality.lower() if sensor_quality else "good"
        if voc_index <= 100:
            return "good"
        if voc_index <= 200:
            return "fair"
        return "poor"

    async def get_data(self) -> Dict[str, Any]:
        resp = await self._client.get(self.endpoint)
        resp.raise_for_status()
        raw = resp.json()

        pm25 = raw.get("pm2_5", 0)

        voc_index = raw.get("voc_index", 0)

        return {
            "systems": {
                "air_quality": {
                    "pm25": round(pm25, 1),
                    "pm25_label": self._pm25_label(pm25),
                    "pm10": round(raw.get("pm10", 0), 1),
                    "pm1": round(raw.get("pm1_0", 0), 1),
                    "voc_index": voc_index,
                    "voc_label": self._voc_label(voc_index, raw.get("air_quality", "")),
                    "air_quality_overall": raw.get("air_quality", "Unknown"),
                },
                "indoor": {
                    "temp": round(raw.get("temperature", 0), 1),
                    "humidity": round(raw.get("humidity", 0), 1),
                },
            },
        }

    async def health_check(self) -> bool:
        try:
            resp = await self._client.get(self.endpoint)
            return resp.status_code == 200
        except Exception:
            return False
