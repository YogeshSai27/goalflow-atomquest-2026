"""
routers/employee.py — Employee-facing routes.

Module 2 implements:
    GET  /employee/dashboard
    GET  /employee/goals              — My Goals (read-only view)
    GET  /employee/goals/wizard       — 3-step Goal Creation Wizard
    POST /employee/goals              — Create a new goal (wizard step 1)
    POST /employee/goals/{id}/edit    — Edit an existing goal (draft only)
    POST /employee/goals/{id}/delete  — Delete a goal (draft only)
    POST /employee/goals/submit       — Submit sheet for manager approval
    GET  /employee/updates            — Quarterly updates (stub)
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_employee
from app.models import Cycle, Goal, GoalSheet, User

router = APIRouter(prefix="/employee", tags=["employee"])
templates = Jinja2Templates(directory="templates")

# ── Constants ────────────────────────────────────────────────────────────────
MAX_GOALS      = 8
MIN_WEIGHTAGE  = 10.0
TOTAL_REQUIRED = 100.0

UOM_LABELS = {
    "min":      "Higher is Better (Min)",
    "max":      "Lower is Better (Max)",
    "timeline": "Timeline (Date-based)",
    "zero":     "Zero = Success",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _active_goal_setting_cycle(db: Session) -> Optional[Cycle]:
    return db.query(Cycle).filter(
        Cycle.type == "goal_setting",
        Cycle.is_active == True,
    ).first()


def _get_or_create_draft_sheet(db: Session, user: User, cycle: Cycle) -> GoalSheet:
    """Return the employee's draft sheet for this cycle, creating it if needed."""
    sheet = db.query(GoalSheet).filter(
        GoalSheet.employee_id == user.id,
        GoalSheet.cycle_id    == cycle.id,
    ).first()
    if not sheet:
        sheet = GoalSheet(
            employee_id=user.id,
            cycle_id=cycle.id,
            status="draft",
        )
        db.add(sheet)
        db.commit()
        db.refresh(sheet)
    return sheet


def _sheet_for_user(db: Session, user: User) -> Optional[GoalSheet]:
    """Return the most-recent goal sheet for the user (any cycle)."""
    return (
        db.query(GoalSheet)
        .filter(GoalSheet.employee_id == user.id)
        .order_by(GoalSheet.created_at.desc())
        .first()
    )


def _validate_goals(goals: list) -> list:
    """Return a list of validation error strings (empty = valid)."""
    errors = []
    if len(goals) == 0:
        errors.append("Add at least one goal before submitting.")
        return errors
    if len(goals) > MAX_GOALS:
        errors.append(f"Maximum {MAX_GOALS} goals allowed (you have {len(goals)}).")
    for g in goals:
        if g.weightage < MIN_WEIGHTAGE:
            errors.append(
                f'Goal "{g.title}" has {g.weightage}% weightage — minimum is {int(MIN_WEIGHTAGE)}%.'
            )
    total = sum(g.weightage for g in goals)
    if abs(total - TOTAL_REQUIRED) > 0.01:
        errors.append(
            f"Total weightage is {total:.1f}% — must be exactly {int(TOTAL_REQUIRED)}%."
        )
    return errors


def _redirect(path: str, *, success: str = None, error: str = None) -> RedirectResponse:
    from urllib.parse import urlencode, quote
    params = {}
    if success:
        params["flash_success"] = success
    if error:
        params["flash_error"] = error
    qs = ("?" + urlencode(params, quote_via=quote)) if params else ""
    return RedirectResponse(url=f"{path}{qs}", status_code=302)


# ── Dashboard ─────────────────────────────────────────────────────────────────

@router.get("/dashboard", response_class=HTMLResponse)
def employee_dashboard(
    request: Request,
    flash_success: str = None,
    flash_error: str = None,
    current_user: User = Depends(require_employee),
    db: Session = Depends(get_db),
):
    cycle  = _active_goal_setting_cycle(db)
    sheet  = _sheet_for_user(db, current_user)
    goals  = sheet.goals if sheet else []
    total_w = sum(g.weightage for g in goals)

    return templates.TemplateResponse("employee/dashboard.html", {
        "request":       request,
        "user":          current_user,
        "cycle":         cycle,
        "sheet":         sheet,
        "goal_count":    len(goals),
        "total_weight":  total_w,
        "flash_success": flash_success,
        "flash_error":   flash_error,
    })


# ── My Goals (read-only view) ─────────────────────────────────────────────────

@router.get("/goals", response_class=HTMLResponse)
def my_goals(
    request: Request,
    flash_success: str = None,
    flash_error: str   = None,
    current_user: User = Depends(require_employee),
    db: Session = Depends(get_db),
):
    cycle = _active_goal_setting_cycle(db)
    sheet = _sheet_for_user(db, current_user)
    goals = sheet.goals if sheet else []

    return templates.TemplateResponse("employee/my_goals.html", {
        "request":       request,
        "user":          current_user,
        "cycle":         cycle,
        "sheet":         sheet,
        "goals":         goals,
        "uom_labels":    UOM_LABELS,
        "flash_success": flash_success,
        "flash_error":   flash_error,
    })


# ── Goal Creation Wizard ──────────────────────────────────────────────────────

@router.get("/goals/wizard", response_class=HTMLResponse)
def goal_wizard(
    request: Request,
    flash_success: str = None,
    flash_error: str   = None,
    current_user: User = Depends(require_employee),
    db: Session = Depends(get_db),
):
    cycle = _active_goal_setting_cycle(db)

    # Guard: no active goal-setting cycle
    if not cycle:
        return _redirect(
            "/employee/goals",
            error="No active goal-setting cycle. Contact your HR Admin.",
        )

    sheet  = _get_or_create_draft_sheet(db, current_user, cycle)

    # Guard: sheet already submitted / approved
    if sheet.status not in ("draft", "returned"):
        return _redirect(
            "/employee/goals",
            error=f"Your goal sheet is '{sheet.status}' and cannot be edited.",
        )

    goals      = sheet.goals
    total_w    = sum(g.weightage for g in goals)
    val_errors = _validate_goals(goals)

    return templates.TemplateResponse("employee/goal_wizard.html", {
        "request":       request,
        "user":          current_user,
        "cycle":         cycle,
        "sheet":         sheet,
        "goals":         goals,
        "total_weight":  total_w,
        "max_goals":     MAX_GOALS,
        "min_weight":    int(MIN_WEIGHTAGE),
        "uom_labels":    UOM_LABELS,
        "val_errors":    val_errors,
        "can_submit":    len(val_errors) == 0,
        "flash_success": flash_success,
        "flash_error":   flash_error,
    })


# ── Create Goal ───────────────────────────────────────────────────────────────

@router.post("/goals")
def create_goal(
    request: Request,
    thrust_area:  str   = Form(...),
    title:        str   = Form(...),
    description:  str   = Form(""),
    uom_type:     str   = Form(...),
    target_value: float = Form(...),
    weightage:    float = Form(...),
    current_user: User  = Depends(require_employee),
    db: Session = Depends(get_db),
):
    cycle = _active_goal_setting_cycle(db)
    if not cycle:
        return _redirect("/employee/goals", error="No active goal-setting cycle.")

    sheet = _get_or_create_draft_sheet(db, current_user, cycle)

    if sheet.status not in ("draft", "returned"):
        return _redirect("/employee/goals/wizard",
                         error="Goal sheet is locked and cannot be edited.")

    # Validation
    if len(sheet.goals) >= MAX_GOALS:
        return _redirect("/employee/goals/wizard",
                         error=f"Maximum {MAX_GOALS} goals already reached.")
    if weightage < MIN_WEIGHTAGE:
        return _redirect("/employee/goals/wizard",
                         error=f"Weightage must be at least {int(MIN_WEIGHTAGE)}%.")
    if weightage > TOTAL_REQUIRED:
        return _redirect("/employee/goals/wizard",
                         error="Weightage cannot exceed 100%.")
    if uom_type not in UOM_LABELS:
        return _redirect("/employee/goals/wizard", error="Invalid UoM type.")

    goal = Goal(
        goal_sheet_id=sheet.id,
        thrust_area=thrust_area.strip(),
        title=title.strip(),
        description=description.strip(),
        uom_type=uom_type,
        target_value=target_value,
        weightage=weightage,
    )
    db.add(goal)
    db.commit()

    return _redirect("/employee/goals/wizard",
                     success=f'Goal "{goal.title}" added.')


# ── Edit Goal ─────────────────────────────────────────────────────────────────

@router.post("/goals/{goal_id}/edit")
def edit_goal(
    goal_id: int,
    thrust_area:  str   = Form(...),
    title:        str   = Form(...),
    description:  str   = Form(""),
    uom_type:     str   = Form(...),
    target_value: float = Form(...),
    weightage:    float = Form(...),
    current_user: User  = Depends(require_employee),
    db: Session = Depends(get_db),
):
    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not goal:
        return _redirect("/employee/goals/wizard", error="Goal not found.")

    sheet = goal.goal_sheet
    if sheet.employee_id != current_user.id:
        return _redirect("/employee/goals/wizard", error="Access denied.")
    if sheet.status not in ("draft", "returned"):
        return _redirect("/employee/goals/wizard",
                         error="Goal sheet is locked and cannot be edited.")

    if weightage < MIN_WEIGHTAGE:
        return _redirect("/employee/goals/wizard",
                         error=f"Weightage must be at least {int(MIN_WEIGHTAGE)}%.")
    if uom_type not in UOM_LABELS:
        return _redirect("/employee/goals/wizard", error="Invalid UoM type.")

    goal.thrust_area  = thrust_area.strip()
    goal.title        = title.strip()
    goal.description  = description.strip()
    goal.uom_type     = uom_type
    goal.target_value = target_value
    goal.weightage    = weightage
    db.commit()

    return _redirect("/employee/goals/wizard",
                     success=f'Goal "{goal.title}" updated.')


# ── Delete Goal ───────────────────────────────────────────────────────────────

@router.post("/goals/{goal_id}/delete")
def delete_goal(
    goal_id: int,
    current_user: User = Depends(require_employee),
    db: Session = Depends(get_db),
):
    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not goal:
        return _redirect("/employee/goals/wizard", error="Goal not found.")

    sheet = goal.goal_sheet
    if sheet.employee_id != current_user.id:
        return _redirect("/employee/goals/wizard", error="Access denied.")
    if sheet.status not in ("draft", "returned"):
        return _redirect("/employee/goals/wizard",
                         error="Goal sheet is locked and cannot be deleted.")

    title = goal.title
    db.delete(goal)
    db.commit()

    return _redirect("/employee/goals/wizard",
                     success=f'Goal "{title}" removed.')


# ── Submit Goal Sheet ─────────────────────────────────────────────────────────

@router.post("/goals/submit")
def submit_goals(
    current_user: User = Depends(require_employee),
    db: Session = Depends(get_db),
):
    cycle = _active_goal_setting_cycle(db)
    if not cycle:
        return _redirect("/employee/goals/wizard",
                         error="No active goal-setting cycle.")

    sheet = _get_or_create_draft_sheet(db, current_user, cycle)
    if sheet.status not in ("draft", "returned"):
        return _redirect("/employee/goals",
                         error=f"Sheet is already '{sheet.status}'.")

    goals = sheet.goals
    errors = _validate_goals(goals)
    if errors:
        return _redirect("/employee/goals/wizard",
                         error=" | ".join(errors))

    sheet.status       = "submitted"
    sheet.submitted_at = datetime.utcnow()
    db.commit()

    return _redirect("/employee/goals",
                     success="Goal sheet submitted for manager approval!")


# ── Quarterly Updates (stub — implemented in Module 4) ───────────────────────

@router.get("/updates", response_class=HTMLResponse)
def quarterly_updates(
    request: Request,
    current_user: User = Depends(require_employee),
    db: Session = Depends(get_db),
):
    return templates.TemplateResponse("employee/quarterly_update.html", {
        "request": request,
        "user":    current_user,
    })
