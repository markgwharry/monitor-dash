import httpx
from typing import Any, Dict, List

from app.services.providers.base import DataProvider


class DockerProvider(DataProvider):
    """Reads container status via Portainer API.

    Uses the Portainer REST API to list containers from a given endpoint.
    """

    def __init__(self, portainer_url: str, api_key: str, endpoint_id: int = 3):
        self.portainer_url = portainer_url.rstrip("/")
        self.endpoint_id = endpoint_id
        self._client = httpx.AsyncClient(
            base_url=self.portainer_url,
            headers={"X-API-Key": api_key},
            timeout=10.0,
        )

    @property
    def name(self) -> str:
        return "docker"

    @staticmethod
    def _map_status(state: str) -> str:
        """Normalise Docker container state to running/stopped/error."""
        state = state.lower()
        if state == "running":
            return "running"
        if state in ("exited", "created", "dead"):
            return "stopped"
        return "error"

    async def get_data(self) -> Dict[str, Any]:
        resp = await self._client.get(
            f"/api/endpoints/{self.endpoint_id}/docker/containers/json",
            params={"all": "true"},
        )
        resp.raise_for_status()
        raw: List[dict] = resp.json()

        containers = []
        for c in raw:
            name = c.get("Names", [""])[0].lstrip("/")
            status = self._map_status(c.get("State", "unknown"))
            containers.append({"name": name, "status": status})

        containers.sort(key=lambda c: (c["status"] != "running", c["name"]))

        running = sum(1 for c in containers if c["status"] == "running")
        total = len(containers)
        health = "healthy" if running == total else "degraded" if running > 0 else "down"

        return {
            "systems": {
                "docker": {
                    "running": running,
                    "total": total,
                    "status": health,
                    "containers": containers,
                },
            },
        }

    async def health_check(self) -> bool:
        try:
            resp = await self._client.get("/api/status")
            return resp.status_code == 200
        except Exception:
            return False
