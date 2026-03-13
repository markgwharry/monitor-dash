from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from app.config import settings
from app.services.mode_manager import ModeManager
from app.services.data_aggregator import DataAggregator
from app.services.providers.mock import MockDataProvider
from app.services.providers.pi_health import PiHealthProvider
from app.services.providers.air_quality import AirQualityProvider
from app.services.providers.docker import DockerProvider
from app.services.providers.weather import WeatherProvider
from app.services.providers.calendar import CalendarProvider
from app.services.providers.camera import CameraProvider
from app.services.providers.heating import HeatingProvider
from app.services.providers.printer import PrinterProvider
from app.routers import api, mode

# Singleton instances
mode_manager = ModeManager()
data_aggregator = DataAggregator(providers=[
    MockDataProvider(),          # fallback base layer
    PiHealthProvider(),
    AirQualityProvider(endpoint=settings.air_sensor_url),
    DockerProvider(
        portainer_url=settings.portainer_url,
        api_key=settings.portainer_api_key,
        endpoint_id=settings.portainer_endpoint_id,
    ),
    WeatherProvider(api_key=settings.weather_api_key, location=settings.location),
    CalendarProvider(ics_urls=settings.calendar_ics_urls),
    CameraProvider(
        ha_url=settings.homeassistant_url,
        token=settings.homeassistant_token,
        entity_id=settings.camera_entity_id,
    ),
    HeatingProvider(
        ha_url=settings.homeassistant_url,
        token=settings.homeassistant_token,
    ),
    PrinterProvider(
        ha_url=settings.homeassistant_url,
        token=settings.homeassistant_token,
        cups_url=settings.cups_url,
    ),
])


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    print("Dashboard starting up...")

    # Inject dependencies into routers
    api.set_data_aggregator(data_aggregator)
    mode.set_mode_manager(mode_manager)

    yield

    print("Dashboard shutting down...")


app = FastAPI(
    title="Pi Dashboard",
    description="Always-on dashboard with operational and ambient modes",
    version="1.0.0",
    lifespan=lifespan,
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Mount Aine's letter game (static HTML/CSS/JS)
app.mount(
    "/games/letters-app",
    StaticFiles(directory="/home/pi/apps/aine-letters/repo", html=True),
    name="letters-game",
)

# Templates
templates = Jinja2Templates(directory="app/templates")

# Include routers
app.include_router(api.router)
app.include_router(mode.router)


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Main dashboard entry point - renders based on current mode."""
    current_mode, mode_reason = mode_manager.get_effective_mode()
    data = await data_aggregator.get_dashboard_data()

    template = (
        "operational.html"
        if current_mode.value == "operational"
        else "ambient.html"
    )

    return templates.TemplateResponse(
        template,
        {
            "request": request,
            "data": data,
            "mode": current_mode,
            "mode_reason": mode_reason,
        },
    )


@app.get("/operational", response_class=HTMLResponse)
async def operational_preview(request: Request):
    """Preview operational mode regardless of time."""
    data = await data_aggregator.get_dashboard_data()
    from app.services.mode_manager import DashboardMode

    return templates.TemplateResponse(
        "operational.html",
        {
            "request": request,
            "data": data,
            "mode": DashboardMode.OPERATIONAL,
            "mode_reason": "preview",
        },
    )


@app.get("/ambient", response_class=HTMLResponse)
async def ambient_preview(request: Request):
    """Preview ambient mode regardless of time."""
    data = await data_aggregator.get_dashboard_data()
    from app.services.mode_manager import DashboardMode

    return templates.TemplateResponse(
        "ambient.html",
        {
            "request": request,
            "data": data,
            "mode": DashboardMode.AMBIENT,
            "mode_reason": "preview",
        },
    )


@app.get("/games/letters", response_class=HTMLResponse)
async def letters_game(request: Request):
    """Aine's Letter Stars game wrapper."""
    return templates.TemplateResponse("games/letters.html", {"request": request})
