from datetime import datetime
from typing import Any, Dict

import httpx

from app.services.providers.base import DataProvider


# OWM condition codes → simple icon names used by the template
_ICON_MAP = {
    "Clear": "sunny",
    "Clouds": "cloudy",
    "Rain": "rainy",
    "Drizzle": "rainy",
    "Thunderstorm": "rainy",
    "Snow": "snowy",
    "Mist": "cloudy",
    "Fog": "cloudy",
    "Haze": "cloudy",
}


class WeatherProvider(DataProvider):
    """Fetches current weather + forecast from OpenWeatherMap free-tier APIs."""

    BASE = "https://api.openweathermap.org/data/2.5"

    def __init__(self, api_key: str, location: str = "London"):
        self.api_key = api_key
        self.location = location
        self._client = httpx.AsyncClient(timeout=10.0)

    @property
    def name(self) -> str:
        return "weather"

    def _params(self, **extra) -> dict:
        return {"q": self.location, "appid": self.api_key, "units": "metric", **extra}

    @staticmethod
    def _ms_to_mph(ms: float) -> int:
        return round(ms * 2.237)

    @staticmethod
    def _ts_to_hhmm(ts: int) -> str:
        return datetime.fromtimestamp(ts).strftime("%H:%M")

    async def get_data(self) -> Dict[str, Any]:
        # Current weather
        cur_resp = await self._client.get(f"{self.BASE}/weather", params=self._params())
        cur_resp.raise_for_status()
        cur = cur_resp.json()

        # 5-day / 3-hour forecast (first 8 entries = next 24h)
        fc_resp = await self._client.get(f"{self.BASE}/forecast", params=self._params(cnt=8))
        fc_resp.raise_for_status()
        fc = fc_resp.json()

        # Extract high/low from today's forecast entries
        today_str = datetime.now().strftime("%Y-%m-%d")
        today_temps = [
            e["main"]["temp"]
            for e in fc.get("list", [])
            if e["dt_txt"].startswith(today_str)
        ]
        # Fall back to all returned entries if none match today
        if not today_temps:
            today_temps = [e["main"]["temp"] for e in fc.get("list", [])]

        temp_high = round(max(today_temps)) if today_temps else round(cur["main"]["temp_max"])
        temp_low = round(min(today_temps)) if today_temps else round(cur["main"]["temp_min"])

        # Rain chance: max pop (probability of precipitation) from forecast
        rain_pops = [e.get("pop", 0) for e in fc.get("list", [])]
        rain_chance = round(max(rain_pops) * 100) if rain_pops else 0

        main_weather = cur["weather"][0]["main"]
        condition = cur["weather"][0]["description"].title()

        return {
            "weather": {
                "temp": round(cur["main"]["temp"]),
                "temp_high": temp_high,
                "temp_low": temp_low,
                "feels_like": round(cur["main"]["feels_like"]),
                "icon": _ICON_MAP.get(main_weather, "cloudy"),
                "condition": condition,
                "location": self.location,
                "wind_mph": self._ms_to_mph(cur["wind"]["speed"]),
                "humidity": cur["main"]["humidity"],
                "rain_chance": rain_chance,
                "sunrise": self._ts_to_hhmm(cur["sys"]["sunrise"]),
                "sunset": self._ts_to_hhmm(cur["sys"]["sunset"]),
            },
        }

    async def health_check(self) -> bool:
        try:
            resp = await self._client.get(f"{self.BASE}/weather", params=self._params())
            return resp.status_code == 200
        except Exception:
            return False
