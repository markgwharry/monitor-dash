import re
import httpx
from typing import Any, Dict, List
from datetime import datetime

from app.services.providers.base import DataProvider


class PrinterProvider(DataProvider):
    """Fetches printer status, toner levels, and print queue from HA + CUPS."""

    def __init__(self, ha_url: str, token: str, cups_url: str = "http://192.168.1.125:631"):
        self.ha_url = ha_url.rstrip("/")
        self.token = token
        self.cups_url = cups_url.rstrip("/")
        self._ha_client = httpx.AsyncClient(
            timeout=10.0,
            headers={"Authorization": f"Bearer {token}"},
        )
        self._cups_client = httpx.AsyncClient(timeout=5.0)

    @property
    def name(self) -> str:
        return "printer"

    async def _get_state(self, entity_id: str) -> Dict[str, Any]:
        """Fetch state for a single entity."""
        resp = await self._ha_client.get(
            f"{self.ha_url}/api/states/{entity_id}"
        )
        resp.raise_for_status()
        return resp.json()

    async def _get_queue(self) -> Dict[str, Any]:
        """Fetch print queue info from CUPS."""
        try:
            # Active jobs
            resp = await self._cups_client.get(
                f"{self.cups_url}/jobs?which_jobs=not-completed"
            )
            resp.raise_for_status()
            active_rows = re.findall(r'<TR VALIGN', resp.text)
            active_count = len(active_rows)

            # Recent completed jobs (last few)
            resp = await self._cups_client.get(
                f"{self.cups_url}/jobs?which_jobs=all"
            )
            resp.raise_for_status()
            html = resp.text

            # Parse completed jobs to get the last one
            dates = re.findall(
                r'completed at<BR>\s*(.+?)&nbsp;', html
            )
            last_print = None
            if dates:
                raw = dates[-1].strip()
                # Parse "Wed 30 Dec 2025 06:01:05 PM GMT" format
                for fmt in (
                    "%a %d %b %Y %I:%M:%S %p %Z",
                    "%a %d %b %Y %I:%M:%S %p",
                ):
                    try:
                        dt = datetime.strptime(raw, fmt)
                        last_print = dt.strftime("%-d %b %Y")
                        break
                    except ValueError:
                        continue
                if not last_print:
                    last_print = raw

            return {
                "active_jobs": active_count,
                "last_print": last_print,
            }
        except Exception:
            return {
                "active_jobs": 0,
                "last_print": None,
            }

    async def get_data(self) -> Dict[str, Any]:
        # Fetch toner levels
        black = await self._get_state("sensor.mfc_l8690cdw_black_toner_remaining")
        cyan = await self._get_state("sensor.mfc_l8690cdw_cyan_toner_remaining")
        magenta = await self._get_state("sensor.mfc_l8690cdw_magenta_toner_remaining")
        yellow = await self._get_state("sensor.mfc_l8690cdw_yellow_toner_remaining")
        status = await self._get_state("sensor.mfc_l8690cdw_status")
        page_counter = await self._get_state("sensor.mfc_l8690cdw_page_counter")

        # Fetch queue from CUPS
        queue = await self._get_queue()

        def parse_pct(entity: Dict) -> int:
            try:
                return int(float(entity.get("state", 0)))
            except (ValueError, TypeError):
                return 0

        def toner_status(pct: int) -> str:
            if pct <= 10:
                return "critical"
            if pct <= 25:
                return "low"
            return "ok"

        toners = {
            "black": parse_pct(black),
            "cyan": parse_pct(cyan),
            "magenta": parse_pct(magenta),
            "yellow": parse_pct(yellow),
        }

        # Find lowest toner
        lowest = min(toners.values())
        overall_status = toner_status(lowest)

        return {
            "systems": {
                "printer": {
                    "status": status.get("state", "unknown"),
                    "toners": toners,
                    "lowest_pct": lowest,
                    "overall_status": overall_status,
                    "page_count": parse_pct(page_counter),
                    "queue_active": queue["active_jobs"],
                    "last_print": queue["last_print"],
                },
            },
        }

    async def health_check(self) -> bool:
        try:
            resp = await self._ha_client.get(f"{self.ha_url}/api/")
            return resp.status_code == 200
        except Exception:
            return False
