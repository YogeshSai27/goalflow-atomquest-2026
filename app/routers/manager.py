"""
routers/manager.py — Manager-facing routes (Module 3).

Endpoints implemented:
    GET  /manager/dashboard                          — Attention dashboard
    GET  /manager/approvals                          — All team sheets (filterable)
    GET  /manager/approvals/{sheet_id}               — Goal sheet review page
    POST /manager/approvals/{sheet_id}/goals/{id}/edit — Inline edit goal
    POST /manager/approvals/{sheet_id}/approve       — Approve + lock sheet
    POST /manager/approvals/{sheet_id}/return        — Return for rework
    GET  /manager/checkin/{sheet_id}                 — Stub (Module 5)
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_manager
from app.models import Goal, GoalSheet, User
from app.services import audit

router = APIRouter(prefix="/manager", tags=["manager"])
templates = Jinja2Templates(directory="templates")

# ── Constants ────────────────────────────────────────────────────────────────
MIN_WEIGHTAGE  = 10.0
TOTAL_REQUIRED = 100.0

UOM_LABELS = {
    "min":      "Higher is Better (Min)",
    "max":      "Lower is Better (Max)",
    "timeline": "Timeline (Date-based)",
    "zero":     "Zero = Success",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _redirect(path: str, *, success: str = None, error: str = None) -> RedirectResponse:
    from urllib.parse import urlencode, quote
    params = {}
    if success:
        params["flash_success"] = success
    if error:
        params["flash_error"] = error
    qs = ("?" + urlencode(params, quote_via=quote)) if params else ""
    return RedirectResponse(url=f"{path}{qs}", status_code=302)


def _team_sheets(db: Session, manager: User) -> list:
    """Return all GoalSheets belonging to direct reports of this manager."""
    report_ids = [u.id for u in db.query(User).filter_by(
        manager_id=manager.id, is_active=True
    ).all()]
    if not report_ids:
        return []
    return (
        db.query(GoalSheet)
        .filter(GoalSheet.employee_id.in_(report_ids))
        .order_by(GoalSheet.submitted_at.desc().nullslast())
        .all()
    )


def _get_sheet_for_manager(db: Session, sheet_id: int, manager: User) -> Optional[GoalSheet]:
    """Return sheet only if it belongs to a direct report of this manager."""
    sheet = db.query(GoalSheet).filter_by(id=sheet_id).first()
    if not sheet:
        return None
    report_ids = [u.id for u in manager.direct_reports if u.is_active]
    if sheet.employee_id not in report_ids:
        return None
    return sheet


def _validate_goals(goals: list) -> list[str]:
    errors = []
    if not goals:
        errors.append("Goal sheet has no goals.")
        return errors
    for g in goals:
        if g.weightage < MIN_WEIGHTAGE:
            errors.append(
                f'Goal "{g.title}" has {g.weightage:.0f}% — minimum is {int(MIN_WEIGHTAGE)}%.'
            )
    total = sum(g.weightage for g in goals)
    if abs(total - TOTAL_REQUIRED) > 0.01:
        errors.append(
            f"Total weightage is {total:.1f}% — must be exactly {int(TOTAL_REQUIRED)}%."
        )
    return errors


def _sheet_stats(sheet: GoalSheet) -> dict:
    goals = sheet.goals
    return {
        "goal_count":   len(goals),
        "total_weight": sum(g.weightage for g in goals),
    }


# ── Dashboard ─────────────────────────────────────────────────────────────────

@router.get("/dashboard", response_class=HTMLResponse)
def manager_dashboard(
    request: Request,
    flash_success: str = None,
    flash_error: str   = None,
    current_user: User = Depends(require_manager),
    db: Session = Depends(get_db),
):
    sheets = _team_sheets(db, current_user)

    # Attention card counts
    pending_count  = sum(1 for s in sheets if s.status == "submitted")
    returned_count = sum(1 for s in sheets if s.status == "returned")
    approved_count = sum(1 for s in sheets if s.status == "approved")
    draft_count    = sum(1 for s in sheets if s.status == "draft")

    # Recent activity — last 5 submitted sheets needing action
    action_needed = [s for s in sheets if s.status == "submitted"][:5]

    return templates.TemplateResponse("manager/dashboard.html", {
        "request":        request,
        "user":           current_user,
        "pending_count":  pending_count,
        "returned_count": returned_count,
        "approved_count": approved_count,
        "draft_count":    draft_count,
        "action_needed":  action_needed,
        "total_reports":  len(current_user.direct_reports),
        "flash_success":  flash_success,
        "flash_error":    flash_error,
    })


# ── Approvals List ────────────────────────────────────────────────────────────

@router.get("/approvals", response_class=HTMLResponse)
def pending_approvals(
    request: Request,
    status_filter: str = "submitted",      # query param for tab switching
    flash_success: str = None,
    flash_error: str   = None,
    current_user: User = Depends(require_manager),
    db: Session = Depends(get_db),
):
    all_sheets = _team_sheets(db, current_user)

    # Tab counts
    counts = {
        "submitted": sum(1 for s in all_sheets if s.status == "submitted"),
        "returned":  sum(1 for s in all_sheets if s.status == "returned"),
        "approved":  sum(1 for s in all_sheets if s.status == "approved"),
        "all":       len(all_sheets),
    }

    # Apply filter
    if status_filter == "all":
        filtered = all_sheets
    else:
        filtered = [s for s in all_sheets if s.status == status_filter]

    # Enrich with stats
    enriched = []
    for s in filtered:
        stats = _sheet_stats(s)
        enriched.append({
            "sheet":        s,
            "employee":     s.employee,
            "goal_count":   stats["goal_count"],
            "total_weight": stats["total_weight"],
        })

    return templates.TemplateResponse("manager/pending_approvals.html", {
        "request":       request,
        "user":          current_user,
        "sheets":        enriched,
        "counts":        counts,
        "active_tab":    status_filter,
        "flash_success": flash_success,
        "flash_error":   flash_error,
    })


# ── Approval Detail ───────────────────────────────────────────────────────────

@router.get("/approvals/{sheet_id}", response_class=HTMLResponse)
def approval_detail(
    sheet_id: int,
    request: Request,
    flash_success: str = None,
    flash_error: str   = None,
    current_user: User = Depends(require_manager),
    db: Session = Depends(get_db),
):
    sheet = _get_sheet_for_manager(db, sheet_id, current_user)
    if not sheet:
        return _redirect("/manager/approvals", error="Goal sheet not found or access denied.")

    goals      = sheet.goals
    total_w    = sum(g.weightage for g in goals)
    val_errors = _validate_goals(goals) if sheet.status == "submitted" else []
    can_approve = sheet.status == "submitted" and len(val_errors) == 0

    return templates.TemplateResponse("manager/approval_detail.html", {
        "request":       request,
        "user":          current_user,
        "sheet":         sheet,
        "employee":      sheet.employee,
        "goals":         goals,
        "total_weight":  total_w,
        "val_errors":    val_errors,
        "can_approve":   can_approve,
        "uom_labels":    UOM_LABELS,
        "flash_success": flash_success,
        "flash_error":   flash_error,
    })


# ── Inline Edit Goal (manager edits target/weightage on submitted sheet) ──────

@router.post("/approvals/{sheet_id}/goals/{goal_id}/edit")
def manager_edit_goal(
    sheet_id: int,
    goal_id:  int,
    target_value: float = Form(...),
    weightage:    float = Form(...),
    current_user: User  = Depends(require_manager),
    db: Session = Depends(get_db),
):
    sheet = _get_sheet_for_manager(db, sheet_id, current_user)
    if not sheet:
        return _redirect("/manager/approvals", error="Access denied.")
    if sheet.status not in ("submitted", "returned"):
        return _redirect(f"/manager/approvals/{sheet_id}",
                         error="Sheet is not in a reviewable state.")

    goal = db.query(Goal).filter_by(id=goal_id, goal_sheet_id=sheet_id).first()
    if not goal:
        return _redirect(f"/manager/approvals/{sheet_id}", error="Goal not found.")

    if weightage < MIN_WEIGHTAGE:
        return _redirect(f"/manager/approvals/{sheet_id}",
                         error=f'Weightage must be at least {int(MIN_WEIGHTAGE)}%.')
    if target_value < 0:
        return _redirect(f"/manager/approvals/{sheet_id}",
                         error="Target value cannot be negative.")

    # Audit: record what changed
    changes = {}
    if abs(goal.target_value - target_value) > 0.001:
        changes["target_value"] = (goal.target_value, target_value)
    if abs(goal.weightage - weightage) > 0.001:
        changes["weightage"] = (goal.weightage, weightage)

    goal.target_value = target_value
    goal.weightage    = weightage
    db.commit()

    if changes:
        audit.log_goal_edit(db, goal.id, current_user.id, changes,
                            notes=f"Manager edit during approval review (sheet {sheet_id})")

    return _redirect(f"/manager/approvals/{sheet_id}",
                     success=f'Goal "{goal.title}" updated.')


# ── Approve ───────────────────────────────────────────────────────────────────

@router.post("/approvals/{sheet_id}/approve")
def approve_sheet(
    sheet_id:         int,
    manager_comments: str  = Form(""),
    current_user:     User = Depends(require_manager),
    db: Session = Depends(get_db),
):
    sheet = _get_sheet_for_manager(db, sheet_id, current_user)
    if not sheet:
        return _redirect("/manager/approvals", error="Access denied.")
    if sheet.status != "submitted":
        return _redirect(f"/manager/approvals/{sheet_id}",
                         error=f'Sheet status is "{sheet.status}" — only submitted sheets can be approved.')

    errors = _validate_goals(sheet.goals)
    if errors:
        return _redirect(f"/manager/approvals/{sheet_id}",
                         error="Fix validation errors before approving: " + " | ".join(errors))

    sheet.status           = "approved"
    sheet.approved_at      = datetime.utcnow()
    sheet.approved_by      = current_user.id
    sheet.locked_at        = datetime.utcnow()
    sheet.manager_comments = manager_comments.strip() or None
    db.commit()

    audit.log_sheet_action(db, sheet.id, "approve", current_user.id,
                           notes=manager_comments.strip() or None)

    emp_name = sheet.employee.name
    return _redirect("/manager/approvals",
                     success=f"{emp_name}'s goal sheet approved and locked.")


# ── Return for Rework ─────────────────────────────────────────────────────────

@router.post("/approvals/{sheet_id}/return")
def return_sheet(
    sheet_id:      int,
    return_reason: str  = Form(...),
    current_user:  User = Depends(require_manager),
    db: Session = Depends(get_db),
):
    sheet = _get_sheet_for_manager(db, sheet_id, current_user)
    if not sheet:
        return _redirect("/manager/approvals", error="Access denied.")
    if sheet.status != "submitted":
        return _redirect(f"/manager/approvals/{sheet_id}",
                         error=f'Sheet status is "{sheet.status}" — only submitted sheets can be returned.')

    if not return_reason.strip():
        return _redirect(f"/manager/approvals/{sheet_id}",
                         error="A return reason is required.")

    sheet.status        = "returned"
    sheet.return_reason = return_reason.strip()
    db.commit()

    audit.log_sheet_action(db, sheet.id, "return", current_user.id,
                           notes=return_reason.strip())

    emp_name = sheet.employee.name
    return _redirect("/manager/approvals",
                     success=f"{emp_name}'s goal sheet returned for revision.")


# ── Check-In (Module 5 stub) ──────────────────────────────────────────────────

@router.get("/checkin/{sheet_id}", response_class=HTMLResponse)
def checkin_page(
    sheet_id: int,
    request: Request,
    current_user: User = Depends(require_manager),
    db: Session = Depends(get_db),
):
    return templates.TemplateResponse("manager/checkin.html", {
        "request":  request,
        "user":     current_user,
        "sheet_id": sheet_id,
    })
