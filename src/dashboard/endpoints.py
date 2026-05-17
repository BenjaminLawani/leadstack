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
    return templates.TemplateResponse(request=request, name="dashboard.html")

@dashboard_router.get("/steve")
def get_steve(
    request: Request,
):
    return templates.TemplateResponse(request=request, name="steve.html")