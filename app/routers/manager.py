"""
routers/manager.py — All manager-facing routes.

Endpoints (to be implemented module by module):
    GET  /manager/dashboard
    GET  /manager/approvals
    GET  /manager/approvals/{sheet_id}
    POST /manager/approvals/{sheet_id}/approve
    POST /manager/approvals/{sheet_id}/return
    PUT  /manager/approvals/{sheet_id}/goals/{goal_id}
    GET  /manager/checkin/{sheet_id}
    POST /manager/checkin/{sheet_id}
"""

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_manager
from app.models import User

router = APIRouter(prefix="/manager", tags=["manager"])
templates = Jinja2Templates(directory="templates")


# ---------------------------------------------------------------------------
# Attention Dashboard
# ---------------------------------------------------------------------------
@router.get("/dashboard", response_class=HTMLResponse)
def manager_dashboard(
    request: Request,
    current_user: User = Depends(require_manager),
    db: Session = Depends(get_db),
):
    return templates.TemplateResponse(
        "manager/dashboard.html",
        {"request": request, "user": current_user},
    )


# ---------------------------------------------------------------------------
# Pending Approvals List
# ---------------------------------------------------------------------------
@router.get("/approvals", response_class=HTMLResponse)
def pending_approvals(
    request: Request,
    current_user: User = Depends(require_manager),
    db: Session = Depends(get_db),
):
    return templates.TemplateResponse(
        "manager/pending_approvals.html",
        {"request": request, "user": current_user},
    )


# ---------------------------------------------------------------------------
# Approval Detail (inline edit + compare + approve/return)
# ---------------------------------------------------------------------------
@router.get("/approvals/{sheet_id}", response_class=HTMLResponse)
def approval_detail(
    sheet_id: int,
    request: Request,
    current_user: User = Depends(require_manager),
    db: Session = Depends(get_db),
):
    return templates.TemplateResponse(
        "manager/approval_detail.html",
        {"request": request, "user": current_user, "sheet_id": sheet_id},
    )


# ---------------------------------------------------------------------------
# Check-In Page
# ---------------------------------------------------------------------------
@router.get("/checkin/{sheet_id}", response_class=HTMLResponse)
def checkin_page(
    sheet_id: int,
    request: Request,
    current_user: User = Depends(require_manager),
    db: Session = Depends(get_db),
):
    return templates.TemplateResponse(
        "manager/checkin.html",
        {"request": request, "user": current_user, "sheet_id": sheet_id},
    )
