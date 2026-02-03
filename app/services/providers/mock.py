from datetime import datetime
from typing import Any, Dict

from app.services.providers.base import DataProvider


class MockDataProvider(DataProvider):
    """Mock data provider for Phase 1 development."""

    @property
    def name(self) -> str:
        return "mock"

    async def get_data(self) -> Dict[str, Any]:
        """Return mock dashboard data."""
        now = datetime.now()

        return {
            "time": {
                "current": now.strftime("%H:%M"),
                "date": now.strftime("%A %-d %B"),
                "week": f"W{now.isocalendar()[1]:02d}",
                "year": now.year,
            },
            "weather": {
                "temp": 8,
                "icon": "cloudy",
                "condition": "Cloudy",
                "location": "London",
            },
            "calendar": {
                "next_meeting": {
                    "title": "Sprint Review",
                    "time": "15:00",
                    "location": "Teams",
                    "minutes_until": 45,
                },
                "tomorrow_first": {
                    "title": "Standup",
                    "time": "09:30",
                },
                "travel_status": "At home",
            },
            "focus": {
                "headline": "Q1 Planning",
                "subtitle": "Strategy review",
                "deadline": None,
                "deadline_label": None,
            },
            "systems": {
                "nas": {
                    "status": "online",
                    "name": "Synology",
                    "used_pct": 67,
                    "used_tb": 8.1,
                    "total_tb": 12.0,
                },
                "docker": {
                    "running": 12,
                    "total": 14,
                    "status": "healthy",
                },
                "network": {
                    "status": "up",
                    "external_ip": "Connected",
                },
                "air_quality": {
                    "pm25": 8,
                    "pm25_label": "Good",
                    "voc": "good",
                },
                "indoor": {
                    "temp": 21.5,
                    "humidity": 45,
                },
            },
        }
