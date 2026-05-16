"""
services/progress.py — Progress calculation engine.

Implements the four UoM formulas from the BRD:

    min  (Higher is Better)  →  actual / target
    max  (Lower is Better)   →  target / actual
    timeline                 →  based on completion_date vs target_date
    zero (Zero = Success)    →  100% if actual == 0, else 0%

Also derives health_status:
    ≥ 90%  → healthy  (green)
    60–89% → watch    (yellow)
    < 60%  → at_risk  (red)
"""

from datetime import date, datetime
from typing import Optional, List


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
def calculate_progress(
    uom_type: str,
    target_value: float,
    actual_value: Optional[float],
    completion_date: Optional[str] = None,   # ISO string "YYYY-MM-DD"
    target_date: Optional[str] = None,       # ISO string — used for timeline
) -> dict:
    """
    Returns a dict:
        {
            "progress_percent": float (0–100+),
            "health_status":    "healthy" | "watch" | "at_risk" | "not_started"
        }
    """
    if actual_value is None:
        return {"progress_percent": 0.0, "health_status": "not_started"}

    pct = _compute_percent(uom_type, target_value, actual_value,
                           completion_date, target_date)
    pct = max(0.0, min(pct, 200.0))   # Cap at 200% to avoid display chaos

    health = _derive_health(pct)
    return {"progress_percent": round(pct, 2), "health_status": health}


# ---------------------------------------------------------------------------
# UoM formulas
# ---------------------------------------------------------------------------
def _compute_percent(
    uom_type: str,
    target: float,
    actual: float,
    completion_date: Optional[str],
    target_date: Optional[str],
) -> float:

    uom = uom_type.lower().strip()

    if uom == "min":
        # Higher actual is better — e.g. Revenue, Units Sold
        if target == 0:
            return 100.0 if actual >= 0 else 0.0
        return (actual / target) * 100.0

    if uom == "max":
        # Lower actual is better — e.g. TAT, Cost, Defects
        if actual == 0:
            return 100.0   # Perfect — zero cost / zero defects
        if target == 0:
            return 0.0
        return (target / actual) * 100.0

    if uom == "timeline":
        # Completion date vs deadline
        return _timeline_percent(completion_date, target_date)

    if uom == "zero":
        # Zero actual = 100% success (e.g. safety incidents)
        return 100.0 if actual == 0 else 0.0

    # Unknown UoM — default to min formula
    if target == 0:
        return 0.0
    return (actual / target) * 100.0


def _timeline_percent(
    completion_date: Optional[str],
    target_date: Optional[str],
) -> float:
    """
    100%  → completed on or before deadline
    Partial → proportional based on how late
    0%    → not completed and past deadline
    """
    if not completion_date:
        # Not yet completed — check if past deadline
        if not target_date:
            return 0.0
        today = date.today()
        deadline = _parse_date(target_date)
        if deadline is None:
            return 0.0
        return 100.0 if today <= deadline else 0.0

    completed = _parse_date(completion_date)
    if completed is None:
        return 0.0

    if not target_date:
        return 100.0   # No deadline set — assume on time

    deadline = _parse_date(target_date)
    if deadline is None:
        return 100.0

    if completed <= deadline:
        return 100.0

    # Completed late — penalise proportionally (days overdue vs a 30-day grace)
    days_late = (completed - deadline).days
    penalty = min(days_late / 30.0, 1.0)   # max 100% penalty over 30 days
    return max(0.0, (1.0 - penalty) * 100.0)


def _parse_date(date_str: str) -> Optional[date]:
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None


# ---------------------------------------------------------------------------
# Health status derivation
# ---------------------------------------------------------------------------
def _derive_health(pct: float) -> str:
    if pct >= 90.0:
        return "healthy"
    if pct >= 60.0:
        return "watch"
    return "at_risk"


# ---------------------------------------------------------------------------
# Weighted overall score helper (used in dashboards)
# ---------------------------------------------------------------------------
def compute_overall_score(goals_with_updates: List[dict]) -> float:
    """
    Accepts a list of dicts:
        {"weightage": float, "progress_percent": float}
    Returns the weighted average score (0–100).
    """
    total_weight = sum(g["weightage"] for g in goals_with_updates)
    if total_weight == 0:
        return 0.0
    weighted_sum = sum(
        g["weightage"] * (g["progress_percent"] or 0.0)
        for g in goals_with_updates
    )
    return round(weighted_sum / total_weight, 2)
