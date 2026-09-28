"""
FastAPI application factory / entry point.

Wires together:
  - static files + Jinja2 templates (server-rendered pages)
  - the auth, planners, and history API routers
  - startup DB initialization
"""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .config import settings
from .db import init_db
from .routes import auth, history, planners

BASE_DIR = Path(__file__).resolve().parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# ---------------------------------------------------------------------------
# Server-rendered pages
# ---------------------------------------------------------------------------


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html")


@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse(request, "register.html")


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request):
    return templates.TemplateResponse(request, "dashboard.html")


@app.get("/home-planner", response_class=HTMLResponse)
def home_planner_page(request: Request):
    return templates.TemplateResponse(request, "home_planner.html")


@app.get("/party-planner", response_class=HTMLResponse)
def party_planner_page(request: Request):
    return templates.TemplateResponse(request, "party_planner.html")


@app.get("/jewelry-planner", response_class=HTMLResponse)
def jewelry_planner_page(request: Request):
    return templates.TemplateResponse(request, "jewelry_planner.html")


@app.get("/history-page", response_class=HTMLResponse)
def history_page(request: Request):
    return templates.TemplateResponse(request, "history.html")


# ---------------------------------------------------------------------------
# API routers
# ---------------------------------------------------------------------------

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(planners.router, prefix="/api", tags=["Planners"])
app.include_router(history.router, prefix="/api", tags=["History"])


@app.get("/health")
def health():
    return {"status": "ok", "app": settings.app_name}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
