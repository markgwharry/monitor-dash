from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from app.services.mode_manager import ModeManager
from app.services.data_aggregator import DataAggregator
from app.services.providers.mock import MockDataProvider
from app.routers import api, mode

# Singleton instances
mode_manager = ModeManager()
data_aggregator = DataAggregator(providers=[MockDataProvider()])


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
