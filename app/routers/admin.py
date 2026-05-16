"""
routers/admin.py — All admin / HR-facing routes.

Endpoints (to be implemented module by module):
    GET  /admin/dashboard
    GET  /admin/cycles
    POST /admin/cycles
    PUT  /admin/cycles/{cycle_id}
    GET  /admin/shared-goals
    POST /admin/shared-goals
    GET  /admin/unlock
    POST /admin/unlock/{sheet_id}
    GET  /admin/reports
    GET  /admin/reports/achievement
    GET  /admin/reports/achievement/export    — CSV download
    GET  /admin/reports/completion
    GET  /admin/audit
"""

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin
from app.models import User

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="templates")


# ---------------------------------------------------------------------------
# Admin Dashboard
# ---------------------------------------------------------------------------
@router.get("/dashboard", response_class=HTMLResponse)
def admin_dashboard(
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return templates.TemplateResponse(
        "admin/dashboard.html",
        {"request": request, "user": current_user},
    )


# ---------------------------------------------------------------------------
# Cycle Management
# ---------------------------------------------------------------------------
@router.get("/cycles", response_class=HTMLResponse)
def cycle_management(
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return templates.TemplateResponse(
        "admin/cycle_management.html",
        {"request": request, "user": current_user},
    )


# ---------------------------------------------------------------------------
# Shared Goals
# ---------------------------------------------------------------------------
@router.get("/shared-goals", response_class=HTMLResponse)
def shared_goals(
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return templates.TemplateResponse(
        "admin/shared_goals.html",
        {"request": request, "user": current_user},
    )


# ---------------------------------------------------------------------------
# Unlock Goals
# ---------------------------------------------------------------------------
@router.get("/unlock", response_class=HTMLResponse)
def unlock_goals(
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return templates.TemplateResponse(
        "admin/unlock_goals.html",
        {"request": request, "user": current_user},
    )


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------
@router.get("/reports", response_class=HTMLResponse)
def reports(
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return templates.TemplateResponse(
        "admin/reports.html",
        {"request": request, "user": current_user},
    )


# ---------------------------------------------------------------------------
# Audit Logs
# ---------------------------------------------------------------------------
@router.get("/audit", response_class=HTMLResponse)
def audit_logs(
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return templates.TemplateResponse(
        "admin/audit_logs.html",
        {"request": request, "user": current_user},
    )
