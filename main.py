from fastapi import (
    FastAPI,
    Request
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.auth.endpoints import auth_router
from src.ai.endpoints import ai_router
from src.dashboard.endpoints import dashboard_router
from src.leads.endpoints import lead_router
from src.notes.endpoints import notes_router

from src.core.db import init_db
from src.core.config import templates


app = FastAPI(
    title="Leadstack"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

app.include_router(auth_router)
app.include_router(ai_router)
app.include_router(dashboard_router)
app.include_router(lead_router)
app.include_router(notes_router)