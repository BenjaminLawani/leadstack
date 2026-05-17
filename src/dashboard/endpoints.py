from fastapi import (
    APIRouter,
    Request,
    status,
    HTTPException,
)

from src.core.config import templates

dashboard_router = APIRouter(
    tags=["DASHBOARD"]
)

@dashboard_router.get("/")
def get_dashboard(
    request: Request
):
    return templates.TemplateResponse("dashboard.html", {"request": request})