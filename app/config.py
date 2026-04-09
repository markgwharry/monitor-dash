from pydantic_settings import BaseSettings
from typing import List, Tuple


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
    location: str = "Linlithgow"

    # Air quality sensor endpoint
    air_sensor_url: str = ""

    # OpenWeatherMap API key
    weather_api_key: str = ""

    # Calendar ICS URLs
    calendar_ics_urls: List[str] = []

    # Home Assistant
    homeassistant_url: str = ""
    homeassistant_token: str = ""
    camera_entity_id: str = ""

    # CUPS (on NAS)
    cups_url: str = ""

    # Portainer API
    portainer_url: str = ""
    portainer_api_key: str = ""
    portainer_endpoint_id: int = 0

    # Aine letters game path (relative or absolute)
    letters_game_path: str = "../aine-letters/repo"

    class Config:
        env_prefix = "DASHBOARD_"
        env_file = ".env"


settings = Settings()
