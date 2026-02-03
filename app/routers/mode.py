from fastapi import APIRouter
from typing import Any, Dict, Optional
from pydantic import BaseModel

from app.services.mode_manager import DashboardMode

router = APIRouter(prefix="/api/mode")

# Will be injected from main.py
_mode_manager = None


def set_mode_manager(manager):
    global _mode_manager
    _mode_manager = manager


class ModeOverrideRequest(BaseModel):
    mode: str
    duration_seconds: Optional[int] = None


@router.get("")
async def get_mode() -> Dict[str, Any]:
    """Get current mode and reason."""
    if _mode_manager is None:
        return {"error": "Mode manager not initialized"}

    mode, reason = _mode_manager.get_effective_mode()
    override_remaining = _mode_manager.get_override_remaining()

    return {
        "mode": mode.value,
        "reason": reason,
        "override_remaining": override_remaining,
    }


@router.post("/operational")
async def set_operational(duration_seconds: Optional[int] = None) -> Dict[str, Any]:
    """Switch to operational mode."""
    if _mode_manager is None:
        return {"error": "Mode manager not initialized"}

    _mode_manager.set_override(DashboardMode.OPERATIONAL, duration_seconds)
    mode, reason = _mode_manager.get_effective_mode()

    return {
        "mode": mode.value,
        "reason": reason,
        "message": "Switched to operational mode",
    }


@router.post("/ambient")
async def set_ambient(duration_seconds: Optional[int] = None) -> Dict[str, Any]:
    """Switch to ambient mode."""
    if _mode_manager is None:
        return {"error": "Mode manager not initialized"}

    _mode_manager.set_override(DashboardMode.AMBIENT, duration_seconds)
    mode, reason = _mode_manager.get_effective_mode()

    return {
        "mode": mode.value,
        "reason": reason,
        "message": "Switched to ambient mode",
    }


@router.post("/toggle")
async def toggle_mode() -> Dict[str, Any]:
    """Toggle between operational and ambient modes."""
    if _mode_manager is None:
        return {"error": "Mode manager not initialized"}

    new_mode = _mode_manager.toggle_mode()

    return {
        "mode": new_mode.value,
        "message": f"Toggled to {new_mode.value} mode",
    }


@router.post("/clear")
async def clear_override() -> Dict[str, Any]:
    """Clear any manual override and return to automatic mode."""
    if _mode_manager is None:
        return {"error": "Mode manager not initialized"}

    _mode_manager.clear_override()
    mode, reason = _mode_manager.get_effective_mode()

    return {
        "mode": mode.value,
        "reason": reason,
        "message": "Override cleared, returning to automatic mode",
    }
