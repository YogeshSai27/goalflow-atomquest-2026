"""
services/audit.py — Centralised audit log writer.

Call log_action() from any route that mutates a locked or sensitive entity.
The audit trail is the governance backbone of the portal.
"""

from datetime import datetime
from sqlalchemy.orm import Session
from app.models import AuditLog


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def log_action(
    db: Session,
    *,
    entity_type: str,        # "goal" | "goal_sheet" | "cycle"
    entity_id: int,
    action: str,             # "edit" | "approve" | "return" | "unlock" | "lock" | "shared_push"
    changed_by: int,         # user.id
    field_name: str = None,  # which field changed (for edit actions)
    old_value: str = None,
    new_value: str = None,
    notes: str = None,
) -> AuditLog:
    """
    Creates and commits an AuditLog entry.

    Example usage:
        audit.log_action(
            db,
            entity_type="goal",
            entity_id=goal.id,
            action="edit",
            changed_by=manager.id,
            field_name="target_value",
            old_value="100",
            new_value="120",
        )
    """
    entry = AuditLog(
        entity_type=entity_type,
        entity_id=entity_id,
        field_name=field_name,
        old_value=str(old_value) if old_value is not None else None,
        new_value=str(new_value) if new_value is not None else None,
        action=action,
        changed_by=changed_by,
        changed_at=datetime.utcnow(),
        notes=notes,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def log_goal_edit(
    db: Session,
    goal_id: int,
    changed_by: int,
    changes: dict,      # {"field_name": (old_value, new_value), ...}
    notes: str = None,
) -> None:
    """
    Convenience wrapper for logging multiple field edits on a goal.
    Writes one audit row per changed field.
    """
    for field, (old, new) in changes.items():
        if str(old) != str(new):   # Only log actual changes
            log_action(
                db,
                entity_type="goal",
                entity_id=goal_id,
                action="edit",
                changed_by=changed_by,
                field_name=field,
                old_value=old,
                new_value=new,
                notes=notes,
            )


def log_sheet_action(
    db: Session,
    sheet_id: int,
    action: str,
    changed_by: int,
    notes: str = None,
) -> AuditLog:
    """Shortcut for goal_sheet-level actions (approve, return, lock, unlock)."""
    return log_action(
        db,
        entity_type="goal_sheet",
        entity_id=sheet_id,
        action=action,
        changed_by=changed_by,
        notes=notes,
    )
