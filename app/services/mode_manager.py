from enum import Enum
from datetime import datetime, timedelta
from typing import Optional, Tuple

from app.config import settings


class DashboardMode(Enum):
    OPERATIONAL = "operational"
    AMBIENT = "ambient"


class ModeManager:
    """Manages dashboard mode switching logic."""

    def __init__(self):
        self._manual_override: Optional[DashboardMode] = None
        self._override_expires: Optional[datetime] = None

    def get_effective_mode(self) -> Tuple[DashboardMode, str]:
        """
        Returns the current mode and reason.

        Returns:
            Tuple of (mode, reason_string)
        """
        now = datetime.now()

        # Check manual override
        if self._manual_override and self._override_expires:
            if now < self._override_expires:
                return self._manual_override, "manual override"
            else:
                # Override expired
                self._manual_override = None
                self._override_expires = None

        # Check time-based rules
        if self._is_work_time(now):
            return DashboardMode.OPERATIONAL, "work hours"
        else:
            return DashboardMode.AMBIENT, "outside work hours"

    def _is_work_time(self, dt: datetime) -> bool:
        """Check if the given datetime is within work hours."""
        # Check if it's a work day
        if dt.weekday() not in settings.work_days:
            return False

        # Check if it's within work hours
        return settings.work_start_hour <= dt.hour < settings.work_end_hour

    def set_override(self, mode: DashboardMode, duration_seconds: Optional[int] = None) -> None:
        """
        Set a manual mode override.

        Args:
            mode: The mode to switch to
            duration_seconds: How long the override lasts (default from settings)
        """
        self._manual_override = mode
        duration = duration_seconds or settings.mode_override_timeout
        self._override_expires = datetime.now() + timedelta(seconds=duration)

    def clear_override(self) -> None:
        """Clear any manual override."""
        self._manual_override = None
        self._override_expires = None

    def toggle_mode(self) -> DashboardMode:
        """
        Toggle between operational and ambient modes.

        Returns:
            The new mode
        """
        current, _ = self.get_effective_mode()
        new_mode = (
            DashboardMode.AMBIENT
            if current == DashboardMode.OPERATIONAL
            else DashboardMode.OPERATIONAL
        )
        self.set_override(new_mode)
        return new_mode

    def get_override_remaining(self) -> Optional[int]:
        """Get seconds remaining on override, or None if no override."""
        if self._manual_override and self._override_expires:
            remaining = (self._override_expires - datetime.now()).total_seconds()
            return max(0, int(remaining))
        return None
