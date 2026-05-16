"""
routers/employee.py — All employee-facing routes.

Endpoints (to be implemented module by module):
    GET  /employee/dashboard
    GET  /employee/goals
    GET  /employee/goals/wizard
    POST /employee/goals                  — create a goal
    PUT  /employee/goals/{goal_id}        — edit a goal (draft only)
    DELETE /employee/goals/{goal_id}      — delete a goal (draft only)
    POST /employee/goals/submit           — submit sheet for approval
    GET  /employee/updates                — quarterly update page
    POST /employee/updates/{goal_id}      — save achievement update
"""

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_employee
from app.models import User

router = APIRouter(prefix="/employee", tags=["employee"])
templates = Jinja2Templates(directory="templates")


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
@router.get("/dashboard", response_class=HTMLResponse)
def employee_dashboard(
    request: Request,
    current_user: User = Depends(require_employee),
    db: Session = Depends(get_db),
):
    return templates.TemplateResponse(
        "employee/dashboard.html",
        {"request": request, "user": current_user},
    )


# ---------------------------------------------------------------------------
# My Goals (view current goal sheet)
# ---------------------------------------------------------------------------
@router.get("/goals", response_class=HTMLResponse)
def my_goals(
    request: Request,
    current_user: User = Depends(require_employee),
    db: Session = Depends(get_db),
):
    return templates.TemplateResponse(
        "employee/my_goals.html",
        {"request": request, "user": current_user},
    )


# ---------------------------------------------------------------------------
# Goal Creation Wizard
# ---------------------------------------------------------------------------
@router.get("/goals/wizard", response_class=HTMLResponse)
def goal_wizard(
    request: Request,
    current_user: User = Depends(require_employee),
    db: Session = Depends(get_db),
):
    return templates.TemplateResponse(
        "employee/goal_wizard.html",
        {"request": request, "user": current_user},
    )


# ---------------------------------------------------------------------------
# Quarterly Updates
# ---------------------------------------------------------------------------
@router.get("/updates", response_class=HTMLResponse)
def quarterly_updates(
    request: Request,
    current_user: User = Depends(require_employee),
    db: Session = Depends(get_db),
):
    return templates.TemplateResponse(
        "employee/quarterly_update.html",
        {"request": request, "user": current_user},
    )
