"""
main.py — GoalFlow FastAPI application entry point.

Auth: Custom itsdangerous signed cookie (see app/auth.py).
      No SessionMiddleware — it conflicts with our cookie system.
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.database import init_db
from app.seed import seed
from app.routers import auth, employee, manager, admin


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed()      # no-op if already seeded
    yield


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="GoalFlow — Goal Setting & Tracking Portal",
    description="AtomQuest Hackathon 2026 submission",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Static files
# ---------------------------------------------------------------------------
app.mount("/static", StaticFiles(directory="static"), name="static")

# ---------------------------------------------------------------------------
# Templates (error pages only)
# ---------------------------------------------------------------------------
templates = Jinja2Templates(directory="templates")

# ---------------------------------------------------------------------------
# Root
# ---------------------------------------------------------------------------
@app.get("/")
def root():
    return RedirectResponse(url="/login", status_code=302)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(auth.router)
app.include_router(employee.router)
app.include_router(manager.router)
app.include_router(admin.router)

# ---------------------------------------------------------------------------
# Exception handler — converts 303 guards to redirects, renders 404
# ---------------------------------------------------------------------------
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 303 and "Location" in (exc.headers or {}):
        return RedirectResponse(url=exc.headers["Location"], status_code=302)
    if exc.status_code == 404:
        return templates.TemplateResponse(
            "errors/404.html", {"request": request}, status_code=404
        )
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


# ---------------------------------------------------------------------------
# Dev runner
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
