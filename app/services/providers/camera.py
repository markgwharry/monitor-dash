from typing import Any, Dict

from app.services.providers.base import DataProvider


class CameraProvider(DataProvider):
    """Provides Home Assistant camera snapshot URL."""

    def __init__(self, ha_url: str, token: str, entity_id: str):
        self.ha_url = ha_url.rstrip("/")
        self.token = token
        self.entity_id = entity_id

    @property
    def name(self) -> str:
        return "camera"

    async def get_data(self) -> Dict[str, Any]:
        # Proxy through our own backend (HA rejects token as query param)
        snapshot_url = "/api/camera"

        return {
            "camera": {
                "snapshot_url": snapshot_url,
                "entity_id": self.entity_id,
            },
        }
