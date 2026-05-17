from fastapi import (
    APIRouter,
    Request,
    status,
    HTTPException,
)

from src.core.config import templates

dashboard_router = APIRouter(
    tags=["DASHBOARD"],
    prefix="/dashboard",
)

@dashboard_router.get("/")
def get_dashboard(
    request: Request
):
    return templates.TemplateResponse("dashboard.html", context={"request": request})

@dashboard_router.get("/steve")
def get_steve(
    request: Request,
):
    return templates.TemplateResponse("steve.html", context={"request": request})