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
    air_sensor_url: str = "http://192.168.1.65"

    # OpenWeatherMap API key
    weather_api_key: str = "af1aec30b0bf4c4d92e98d095c138e54"

    # Calendar ICS URLs
    calendar_ics_urls: List[str] = [
        "https://outlook.office365.com/owa/calendar/b0d1a352210a41e1be0bb0e9ae082f4e%40modini.co.uk/ee719592913f44d5b40d05426ca8f6233967296529659239179/S-1-8-1786912635-2249673433-3159881887-1305142510/reachcalendar.ics",
        "https://p141-caldav.icloud.com/published/2/MTAxOTEzNTEwMTEwMTkxM4DpN7w-5gAK5Nc8ErB5BeV9Eirsr7NoIbrADCDgXjL1rsWGcO6NvuL1SPl5g0_Y5VdidTblBHXOF60vvDtUQx3sGhjvM03CA6t_aMDkG3Z7GcYf-G3vftK0aXAkiXeXEA",
        "https://p141-caldav.icloud.com/published/2/MTAxOTEzNTEwMTEwMTkxM4DpN7w-5gAK5Nc8ErB5BeWhhFR11Cire6N_MFM3ryhwwjRWHC6tWeeU8hsrKahiuHYYjaXgfttN4OOQZNm3J-Y",
    ]

    # Home Assistant
    homeassistant_url: str = "http://192.168.1.125:8123"
    homeassistant_token: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJiMDQxMTlmMWI0OWU0MzAxYjllNmYzNzc5OWRkMDExYSIsImlhdCI6MTc2MDI3MjEzNCwiZXhwIjoyMDc1NjMyMTM0fQ.L5i63UBymGfleyqavckMrXAcIsI-SUiJjj7M7yUbjhE"
    camera_entity_id: str = "camera.driveway_live_view_2"

    # CUPS (on NAS)
    cups_url: str = "http://192.168.1.125:631"

    # Portainer API
    portainer_url: str = "http://192.168.1.125:9000"
    portainer_api_key: str = "ptr_014GyzLudK1KNzL/2VhkSziKYy56YpozbJyLiwL2sm8="
    portainer_endpoint_id: int = 3

    class Config:
        env_prefix = "DASHBOARD_"


settings = Settings()
