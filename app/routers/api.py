from fastapi import APIRouter
from typing import Any, Dict

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


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}
