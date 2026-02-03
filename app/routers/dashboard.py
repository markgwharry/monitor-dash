from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """
    Main dashboard page - redirects to appropriate mode template.
    This is handled by main.py directly.
    """
    # This route is overridden in main.py
    pass
