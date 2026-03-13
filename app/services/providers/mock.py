from datetime import datetime
from typing import Any, Dict, List

from app.services.providers.base import DataProvider


class MockDataProvider(DataProvider):
    """Mock data provider for Phase 1 development.

    Returns rich, semi-dynamic mock data. Time and day progress
    are computed from the system clock. Calendar events use fixed
    times but compute passed/active/next status dynamically.
    """

    @property
    def name(self) -> str:
        return "mock"

    def _build_events_today(self, now: datetime) -> List[Dict[str, Any]]:
        """Build today's events with dynamic status based on current time."""
        base_events = [
            {"title": "Standup", "time": "09:30", "end_time": "10:00", "location": "Teams", "duration": "30m"},
            {"title": "Design Review", "time": "10:30", "end_time": "11:30", "location": "Room 4", "duration": "1h"},
            {"title": "Lunch w/ Sarah", "time": "12:30", "end_time": "13:30", "location": "Dishoom", "duration": "1h"},
            {"title": "Sprint Review", "time": "15:00", "end_time": "16:00", "location": "Teams", "duration": "1h"},
            {"title": "1:1 with Alex", "time": "16:30", "end_time": "17:00", "location": "Teams", "duration": "30m"},
            {"title": "Wrap-up Notes", "time": "17:30", "end_time": "17:45", "location": "", "duration": "15m"},
        ]

        current_mins = now.hour * 60 + now.minute
        next_found = False

        for event in base_events:
            eh, em = map(int, event["time"].split(":"))
            eeh, eem = map(int, event["end_time"].split(":"))
            start_mins = eh * 60 + em
            end_mins = eeh * 60 + eem

            if current_mins >= end_mins:
                event["passed"] = True
                event["active"] = False
                event["is_next"] = False
            elif current_mins >= start_mins:
                event["passed"] = False
                event["active"] = True
                event["is_next"] = False
                event["minutes_remaining"] = end_mins - current_mins
            else:
                event["passed"] = False
                event["active"] = False
                if not next_found:
                    event["is_next"] = True
                    event["minutes_until"] = start_mins - current_mins
                    next_found = True
                else:
                    event["is_next"] = False

        return base_events

    @staticmethod
    def _parse_duration_mins(duration: str) -> int:
        """Parse duration string like '30m', '1h', '1h 30m' to minutes."""
        mins = 0
        if "h" in duration:
            parts = duration.split("h")
            mins += int(parts[0].strip()) * 60
            rest = parts[1].strip()
            if rest:
                mins += int(rest.replace("m", "").strip())
        elif "m" in duration:
            mins += int(duration.replace("m", "").strip())
        return mins

    @staticmethod
    def _fmt_mins(m: int) -> str:
        if m >= 60:
            h, remainder = divmod(m, 60)
            return f"{h}h {remainder}m" if remainder else f"{h}h"
        return f"{m}m"

    def _compute_day_summary(self, events: List[Dict[str, Any]], now: datetime) -> Dict[str, Any]:
        """Derive day-at-a-glance stats from today's events."""
        current_mins = now.hour * 60 + now.minute
        work_end = 18 * 60

        total = len(events)
        upcoming = [e for e in events if not e.get("passed")]
        remaining = len(upcoming)

        # Total meeting time for the whole day
        total_meeting_mins = sum(self._parse_duration_mins(e["duration"]) for e in events)

        # Free time = remaining work hours minus remaining meeting time
        remaining_meeting_mins = sum(self._parse_duration_mins(e["duration"]) for e in upcoming)
        work_remaining = max(0, work_end - current_mins)
        free_mins = max(0, work_remaining - remaining_meeting_mins)

        # Next break logic
        in_meeting = any(e.get("active") for e in events)
        next_break = None
        next_break_dur = None

        if not upcoming:
            next_break = "Done"
            next_break_dur = ""
        elif not in_meeting:
            # Currently free — show how long until next meeting
            first = upcoming[0]
            fh, fm = map(int, first["time"].split(":"))
            gap = (fh * 60 + fm) - current_mins
            if gap > 0:
                next_break = "Now"
                next_break_dur = self._fmt_mins(gap)

        # If still not set, find next gap between upcoming meetings
        if next_break is None:
            for i, e in enumerate(upcoming):
                eeh, eem = map(int, e["end_time"].split(":"))
                end = eeh * 60 + eem
                if i + 1 < len(upcoming):
                    nsh, nsm = map(int, upcoming[i + 1]["time"].split(":"))
                    gap = (nsh * 60 + nsm) - end
                    if gap > 0:
                        next_break = e["end_time"]
                        next_break_dur = self._fmt_mins(gap)
                        break
                else:
                    next_break = e["end_time"]
                    next_break_dur = "Done"

        # When does the last meeting end?
        done_at = upcoming[-1]["end_time"] if upcoming else "Done"

        return {
            "meetings_remaining": remaining,
            "meetings_total": total,
            "total_meeting_time": self._fmt_mins(total_meeting_mins),
            "free_remaining": self._fmt_mins(free_mins),
            "next_break": next_break,
            "next_break_duration": next_break_dur,
            "done_at": done_at,
        }

    def _get_next_meeting(self, events: List[Dict[str, Any]]) -> Dict[str, Any] | None:
        """Extract the next or currently active meeting."""
        for event in events:
            if event.get("active"):
                return {
                    "title": event["title"],
                    "time": event["time"],
                    "location": event["location"],
                    "active": True,
                    "minutes_remaining": event.get("minutes_remaining", 0),
                }
            if event.get("is_next"):
                return {
                    "title": event["title"],
                    "time": event["time"],
                    "location": event["location"],
                    "active": False,
                    "minutes_until": event.get("minutes_until", 0),
                }
        return None

    async def get_data(self) -> Dict[str, Any]:
        """Return expanded mock dashboard data."""
        now = datetime.now()

        # Day progress (9:00-18:00 work day)
        work_start = 9 * 60
        work_end = 18 * 60
        current_mins = now.hour * 60 + now.minute
        if current_mins <= work_start:
            day_progress = 0
        elif current_mins >= work_end:
            day_progress = 100
        else:
            day_progress = round((current_mins - work_start) / (work_end - work_start) * 100)

        events_today = self._build_events_today(now)
        next_meeting = self._get_next_meeting(events_today)
        day_summary = self._compute_day_summary(events_today, now)

        return {
            "time": {
                "current": now.strftime("%H:%M"),
                "seconds": now.strftime("%S"),
                "date": now.strftime("%A %-d %B"),
                "date_short": now.strftime("%a %-d %b").upper(),
                "week": f"W{now.isocalendar()[1]:02d}",
                "year": now.year,
                "day_progress_pct": day_progress,
            },
            "weather": {
                "temp": 8,
                "temp_high": 11,
                "temp_low": 4,
                "feels_like": 5,
                "icon": "cloudy",
                "condition": "Cloudy",
                "location": "London",
                "wind_mph": 12,
                "humidity": 78,
                "rain_chance": 40,
                "sunrise": "07:32",
                "sunset": "16:58",
            },
            "calendar": {
                "events_today": events_today,
                "events_tomorrow": [
                    {"title": "Standup", "time": "09:30"},
                    {"title": "Retrospective", "time": "14:00"},
                    {"title": "Sprint Planning", "time": "15:30"},
                ],
                "total_today": len(events_today),
                "next_meeting": next_meeting,
                "day_summary": day_summary,
                "travel_status": "At home",
            },
            "systems": {
                "docker": {
                    "running": 12,
                    "total": 14,
                    "status": "healthy",
                    "containers": [
                        {"name": "nginx", "status": "running"},
                        {"name": "postgres", "status": "running"},
                        {"name": "redis", "status": "running"},
                        {"name": "grafana", "status": "running"},
                        {"name": "pihole", "status": "running"},
                        {"name": "homebridge", "status": "stopped"},
                        {"name": "zigbee2mqtt", "status": "running"},
                        {"name": "mosquitto", "status": "running"},
                        {"name": "portainer", "status": "running"},
                        {"name": "unifi", "status": "running"},
                        {"name": "jellyfin", "status": "running"},
                        {"name": "vaultwarden", "status": "running"},
                        {"name": "watchtower", "status": "stopped"},
                        {"name": "caddy", "status": "running"},
                    ],
                },
                "network": {
                    "status": "up",
                    "external_ip": "86.24.x.x",
                    "local_ip": "192.168.1.100",
                    "download_mbps": 120,
                    "upload_mbps": 45,
                    "latency_ms": 12,
                },
                "pi": {
                    "cpu_pct": 42,
                    "memory_pct": 61,
                    "temp": 48,
                    "disk_pct": 34,
                    "uptime": "14d 7h",
                },
                "air_quality": {
                    "pm25": 8,
                    "pm25_label": "Good",
                    "voc": "good",
                    "co2": 620,
                    "co2_label": "Good",
                },
                "indoor": {
                    "temp": 21.5,
                    "humidity": 45,
                },
                "printer": {
                    "status": "idle",
                    "toners": {"black": 50, "cyan": 30, "magenta": 40, "yellow": 35},
                    "lowest_pct": 30,
                    "overall_status": "ok",
                    "page_count": 0,
                    "queue_active": 0,
                    "last_print": None,
                },
                "heating": {
                    "current_temp": 20.5,
                    "target_temp": 21.0,
                    "status": "idle",
                    "status_label": "Idle",
                    "mode": "auto",
                    "boost": False,
                    "water_on": False,
                    "water_boost": False,
                },
            },
            "camera": {
                "snapshot_url": "/api/camera",
            },
        }
