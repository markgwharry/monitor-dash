from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

import httpx
from icalendar import Calendar

from app.services.providers.base import DataProvider


class CalendarProvider(DataProvider):
    """Fetches calendar events from ICS subscription URLs."""

    def __init__(self, ics_urls: List[str], timezone: str = "Europe/London"):
        self.ics_urls = ics_urls
        self.tz = ZoneInfo(timezone)
        self._client = httpx.AsyncClient(timeout=30.0)

    @property
    def name(self) -> str:
        return "calendar"

    def _parse_dt(self, dt_val) -> Optional[datetime]:
        """Convert icalendar dt to timezone-aware datetime."""
        if dt_val is None:
            return None
        dt = dt_val.dt if hasattr(dt_val, "dt") else dt_val
        if isinstance(dt, datetime):
            if dt.tzinfo is None:
                return dt.replace(tzinfo=self.tz)
            return dt.astimezone(self.tz)
        if isinstance(dt, date):
            # All-day event — treat as midnight
            return datetime.combine(dt, datetime.min.time(), tzinfo=self.tz)
        return None

    def _is_all_day(self, component) -> bool:
        """Check if event is all-day (DATE vs DATETIME)."""
        dtstart = component.get("DTSTART")
        if dtstart is None:
            return False
        return not isinstance(dtstart.dt, datetime)

    def _format_duration(self, start: datetime, end: datetime) -> str:
        """Format duration as '30m', '1h', '1h 30m'."""
        mins = int((end - start).total_seconds() // 60)
        if mins >= 60:
            h, m = divmod(mins, 60)
            return f"{h}h {m}m" if m else f"{h}h"
        return f"{mins}m"

    async def _fetch_events(self) -> List[dict]:
        """Fetch and parse events from all ICS URLs."""
        events = []

        for url in self.ics_urls:
            try:
                resp = await self._client.get(url)
                resp.raise_for_status()
                cal = Calendar.from_ical(resp.text)

                for component in cal.walk():
                    if component.name != "VEVENT":
                        continue

                    summary = str(component.get("SUMMARY", ""))
                    # Skip cancelled events
                    if summary.lower().startswith("canceled:"):
                        continue

                    dtstart = self._parse_dt(component.get("DTSTART"))
                    dtend = self._parse_dt(component.get("DTEND"))

                    if dtstart is None:
                        continue

                    # Default end to start + 1 hour if missing
                    if dtend is None:
                        dtend = dtstart + timedelta(hours=1)

                    location = str(component.get("LOCATION", "") or "")
                    # Clean up location
                    if location.lower() == "microsoft teams meeting":
                        location = "Teams"
                    elif location.lower() == "webex":
                        location = "Webex"
                    elif len(location) > 30:
                        location = location[:27] + "..."

                    # Clean up summary - remove EXTERNAL: prefix
                    if summary.upper().startswith("EXTERNAL:"):
                        summary = summary[9:].strip()
                    if summary.upper().startswith("FW:"):
                        summary = summary[3:].strip()

                    events.append({
                        "summary": summary,
                        "start": dtstart,
                        "end": dtend,
                        "location": location,
                        "all_day": self._is_all_day(component),
                    })
            except Exception as e:
                print(f"Error fetching calendar {url}: {e}")

        return events

    def _filter_day(self, events: List[dict], target: date) -> List[dict]:
        """Filter events for a specific day, excluding all-day events."""
        day_start = datetime.combine(target, datetime.min.time(), tzinfo=self.tz)
        day_end = day_start + timedelta(days=1)

        filtered = []
        for e in events:
            if e["all_day"]:
                continue
            # Event overlaps with target day
            if e["start"] < day_end and e["end"] > day_start:
                filtered.append(e)

        return sorted(filtered, key=lambda x: x["start"])

    def _build_event_list(self, events: List[dict], now: datetime) -> List[Dict[str, Any]]:
        """Build the event list with status flags."""
        current_mins = now.hour * 60 + now.minute
        result = []
        next_found = False

        for e in events:
            start_mins = e["start"].hour * 60 + e["start"].minute
            end_mins = e["end"].hour * 60 + e["end"].minute
            # Handle events crossing midnight
            if e["end"].date() > e["start"].date():
                end_mins = 24 * 60

            event_data = {
                "title": e["summary"],
                "time": e["start"].strftime("%H:%M"),
                "end_time": e["end"].strftime("%H:%M"),
                "location": e["location"],
                "duration": self._format_duration(e["start"], e["end"]),
                "passed": False,
                "active": False,
                "is_next": False,
            }

            if current_mins >= end_mins:
                event_data["passed"] = True
            elif current_mins >= start_mins:
                event_data["active"] = True
                event_data["minutes_remaining"] = end_mins - current_mins
            else:
                if not next_found:
                    event_data["is_next"] = True
                    event_data["minutes_until"] = start_mins - current_mins
                    next_found = True

            result.append(event_data)

        return result

    def _get_next_meeting(self, events: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
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

    @staticmethod
    def _fmt_mins(m: int) -> str:
        if m >= 60:
            h, remainder = divmod(m, 60)
            return f"{h}h {remainder}m" if remainder else f"{h}h"
        return f"{m}m"

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

    def _compute_day_summary(
        self, events: List[Dict[str, Any]], now: datetime
    ) -> Dict[str, Any]:
        """Derive day-at-a-glance stats from today's events."""
        current_mins = now.hour * 60 + now.minute
        work_end = 18 * 60

        total = len(events)
        upcoming = [e for e in events if not e.get("passed")]
        remaining = len(upcoming)

        total_meeting_mins = sum(
            self._parse_duration_mins(e["duration"]) for e in events
        )
        remaining_meeting_mins = sum(
            self._parse_duration_mins(e["duration"]) for e in upcoming
        )
        work_remaining = max(0, work_end - current_mins)
        free_mins = max(0, work_remaining - remaining_meeting_mins)

        in_meeting = any(e.get("active") for e in events)
        next_break = None
        next_break_dur = None

        if not upcoming:
            next_break = "Done"
            next_break_dur = ""
        elif not in_meeting:
            first = upcoming[0]
            fh, fm = map(int, first["time"].split(":"))
            gap = (fh * 60 + fm) - current_mins
            if gap > 0:
                next_break = "Now"
                next_break_dur = self._fmt_mins(gap)

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

    async def get_data(self) -> Dict[str, Any]:
        now = datetime.now(self.tz)
        today = now.date()
        tomorrow = today + timedelta(days=1)

        all_events = await self._fetch_events()

        events_today = self._filter_day(all_events, today)
        events_tomorrow = self._filter_day(all_events, tomorrow)

        today_list = self._build_event_list(events_today, now)
        tomorrow_list = [
            {"title": e["summary"], "time": e["start"].strftime("%H:%M")}
            for e in events_tomorrow
        ]

        next_meeting = self._get_next_meeting(today_list)
        day_summary = self._compute_day_summary(today_list, now)

        return {
            "calendar": {
                "events_today": today_list,
                "events_tomorrow": tomorrow_list,
                "total_today": len(today_list),
                "next_meeting": next_meeting,
                "day_summary": day_summary,
            },
        }

    async def health_check(self) -> bool:
        try:
            for url in self.ics_urls:
                resp = await self._client.head(url)
                if resp.status_code != 200:
                    return False
            return True
        except Exception:
            return False
