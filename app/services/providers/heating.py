import httpx
from typing import Any, Dict

from app.services.providers.base import DataProvider


class HeatingProvider(DataProvider):
    """Fetches heating and hot water status from Home Assistant."""

    def __init__(self, ha_url: str, token: str):
        self.ha_url = ha_url.rstrip("/")
        self.token = token
        self._client = httpx.AsyncClient(
            timeout=10.0,
            headers={"Authorization": f"Bearer {token}"},
        )

    @property
    def name(self) -> str:
        return "heating"

    async def _get_state(self, entity_id: str) -> Dict[str, Any]:
        """Fetch state for a single entity."""
        resp = await self._client.get(
            f"{self.ha_url}/api/states/{entity_id}"
        )
        resp.raise_for_status()
        return resp.json()

    async def get_data(self) -> Dict[str, Any]:
        # Fetch thermostat and related entities
        thermostat = await self._get_state("climate.thermostat_3")
        thermostat_boost = await self._get_state("binary_sensor.thermostat_3_boost")
        hotwater_boost = await self._get_state("binary_sensor.hotwater_boost")
        hotwater_state = await self._get_state("binary_sensor.hotwater_state")

        attrs = thermostat.get("attributes", {})
        current_temp = attrs.get("current_temperature")
        target_temp = attrs.get("temperature")
        hvac_action = attrs.get("hvac_action", "unknown")
        hvac_mode = thermostat.get("state", "unknown")

        # Determine heating status
        if hvac_action == "heating":
            status = "heating"
            status_label = "Heating"
        elif hvac_action == "idle":
            status = "idle"
            status_label = "Idle"
        elif hvac_mode == "off":
            status = "off"
            status_label = "Off"
        else:
            status = hvac_action
            status_label = hvac_action.title()

        # Check if boost is active
        heating_boost = thermostat_boost.get("state") == "on"
        water_boost = hotwater_boost.get("state") == "on"
        water_on = hotwater_state.get("state") == "on"

        return {
            "systems": {
                "heating": {
                    "current_temp": round(current_temp, 1) if current_temp else None,
                    "target_temp": round(target_temp, 1) if target_temp else None,
                    "status": status,
                    "status_label": status_label,
                    "mode": hvac_mode,
                    "boost": heating_boost,
                    "water_on": water_on,
                    "water_boost": water_boost,
                },
            },
        }

    async def health_check(self) -> bool:
        try:
            resp = await self._client.get(f"{self.ha_url}/api/")
            return resp.status_code == 200
        except Exception:
            return False
