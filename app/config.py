from pydantic_settings import BaseSettings
from typing import Tuple


class Settings(BaseSettings):
    """Dashboard configuration settings."""

    # Work hours (24h format)
    work_start_hour: int = 9
    work_end_hour: int = 18

    # Work days (0=Monday, 6=Sunday)
    work_days: Tuple[int, ...] = (0, 1, 2, 3, 4)  # Mon-Fri

    # Mode override timeout (seconds) - how long manual override lasts
    mode_override_timeout: int = 3600  # 1 hour

    # Data refresh interval (seconds)
    data_refresh_interval: int = 60

    # Location for weather
    location: str = "London"

    class Config:
        env_prefix = "DASHBOARD_"


settings = Settings()
