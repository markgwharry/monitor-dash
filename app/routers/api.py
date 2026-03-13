import httpx
from fastapi import APIRouter
from fastapi.responses import Response
from typing import Any, Dict

from app.config import settings

router = APIRouter(prefix="/api")

# These will be injected from main.py
_data_aggregator = None


def set_data_aggregator(aggregator):
    global _data_aggregator
    _data_aggregator = aggregator


@router.get("/data")
async def get_data() -> Dict[str, Any]:
    """Get current dashboard data."""
    if _data_aggregator is None:
        return {"error": "Data aggregator not initialized"}

    return await _data_aggregator.get_dashboard_data()


@router.get("/camera")
async def camera_proxy():
    """Proxy camera snapshot from Home Assistant with proper auth."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            f"{settings.homeassistant_url}/api/camera_proxy/{settings.camera_entity_id}",
            headers={"Authorization": f"Bearer {settings.homeassistant_token}"},
        )
        return Response(
            content=resp.content,
            media_type=resp.headers.get("content-type", "image/jpeg"),
            headers={"Cache-Control": "no-cache, max-age=0"},
        )


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}
