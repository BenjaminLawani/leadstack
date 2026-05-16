from fastapi import (
    FastAPI,
    Request
)

from src.auth.endpoints import auth_router

from src.core.db import init_db
from src.core.config import templates



app = FastAPI(
    title="Leadstack"
)

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

app.include_router(auth_router)