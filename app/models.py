"""
models.py — SQLAlchemy ORM models matching the approved database schema.

Tables:
    users, cycles, goal_sheets, goals,
    achievement_updates, check_ins, shared_goals, audit_logs
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, Text, Float, ForeignKey, DateTime, Boolean
)
from sqlalchemy.orm import relationship
from app.database import Base


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------
class User(Base):
    __tablename__ = "users"

    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(Text, nullable=False)
    email      = Column(Text, unique=True, nullable=False, index=True)
    password_hash = Column(Text, nullable=False)
    role       = Column(Text, nullable=False)        # employee | manager | admin
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    department = Column(Text, nullable=True)
    is_active  = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    manager        = relationship("User", remote_side=[id], backref="direct_reports")
    goal_sheets    = relationship("GoalSheet", back_populates="employee",
                                  foreign_keys="GoalSheet.employee_id")
    approved_sheets = relationship("GoalSheet", back_populates="approver",
                                   foreign_keys="GoalSheet.approved_by")
    audit_logs     = relationship("AuditLog", back_populates="changed_by_user",
                                  foreign_keys="AuditLog.changed_by")


# ---------------------------------------------------------------------------
# Cycles
# ---------------------------------------------------------------------------
class Cycle(Base):
    __tablename__ = "cycles"

    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(Text, nullable=False)
    # goal_setting | q1 | q2 | q3 | q4
    type       = Column(Text, nullable=False)
    start_date = Column(Text, nullable=False)   # ISO date string YYYY-MM-DD
    end_date   = Column(Text, nullable=False)
    is_active  = Column(Boolean, default=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    goal_sheets          = relationship("GoalSheet", back_populates="cycle")
    achievement_updates  = relationship("AchievementUpdate", back_populates="cycle")
    check_ins            = relationship("CheckIn", back_populates="cycle")


# ---------------------------------------------------------------------------
# Goal Sheets (one per employee per goal-setting cycle)
# ---------------------------------------------------------------------------
class GoalSheet(Base):
    __tablename__ = "goal_sheets"

    id          = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    cycle_id    = Column(Integer, ForeignKey("cycles.id"), nullable=False)
    # draft | submitted | approved | returned
    status      = Column(Text, nullable=False, default="draft")
    submitted_at = Column(DateTime, nullable=True)
    approved_at  = Column(DateTime, nullable=True)
    approved_by  = Column(Integer, ForeignKey("users.id"), nullable=True)
    locked_at    = Column(DateTime, nullable=True)
    is_unlocked  = Column(Boolean, default=False)
    unlock_reason = Column(Text, nullable=True)
    unlocked_by  = Column(Integer, ForeignKey("users.id"), nullable=True)
    unlocked_at  = Column(DateTime, nullable=True)
    manager_comments = Column(Text, nullable=True)   # overall approval comments
    return_reason    = Column(Text, nullable=True)   # reason when returned
    created_at   = Column(DateTime, default=datetime.utcnow)

    # Relationships
    employee  = relationship("User", back_populates="goal_sheets",
                             foreign_keys=[employee_id])
    approver  = relationship("User", back_populates="approved_sheets",
                             foreign_keys=[approved_by])
    unlocker  = relationship("User", foreign_keys=[unlocked_by])
    cycle     = relationship("Cycle", back_populates="goal_sheets")
    goals     = relationship("Goal", back_populates="goal_sheet",
                             cascade="all, delete-orphan")
    check_ins = relationship("CheckIn", back_populates="goal_sheet")


# ---------------------------------------------------------------------------
# Goals (up to 8 per GoalSheet)
# ---------------------------------------------------------------------------
class Goal(Base):
    __tablename__ = "goals"

    id            = Column(Integer, primary_key=True, index=True)
    goal_sheet_id = Column(Integer, ForeignKey("goal_sheets.id"), nullable=False)
    thrust_area   = Column(Text, nullable=False)
    title         = Column(Text, nullable=False)
    description   = Column(Text, nullable=True)
    # min | max | timeline | zero
    uom_type      = Column(Text, nullable=False)
    target_value  = Column(Float, nullable=False)
    weightage     = Column(Float, nullable=False)
    is_shared     = Column(Boolean, default=False)
    primary_owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at    = Column(DateTime, default=datetime.utcnow)

    goal_sheet    = relationship("GoalSheet", back_populates="goals")
    primary_owner = relationship("User", foreign_keys=[primary_owner_id])
    achievement_updates = relationship("AchievementUpdate", back_populates="goal",
                                       cascade="all, delete-orphan")
    # Shared goal links where this goal is the master
    shared_as_master = relationship("SharedGoal",
                                    foreign_keys="SharedGoal.master_goal_id",
                                    back_populates="master_goal")
    # Shared goal links where this goal is the linked copy
    shared_as_linked = relationship("SharedGoal",
                                    foreign_keys="SharedGoal.linked_goal_id",
                                    back_populates="linked_goal")


# ---------------------------------------------------------------------------
# Achievement Updates (one per goal per quarter)
# ---------------------------------------------------------------------------
class AchievementUpdate(Base):
    __tablename__ = "achievement_updates"

    id              = Column(Integer, primary_key=True, index=True)
    goal_id         = Column(Integer, ForeignKey("goals.id"), nullable=False)
    cycle_id        = Column(Integer, ForeignKey("cycles.id"), nullable=False)
    actual_value    = Column(Float, nullable=True)
    completion_date = Column(Text, nullable=True)  # ISO date, for timeline UoM
    # not_started | on_track | completed
    status          = Column(Text, nullable=True, default="not_started")
    progress_percent = Column(Float, nullable=True)
    # healthy | watch | at_risk
    health_status   = Column(Text, nullable=True)
    updated_at      = Column(DateTime, default=datetime.utcnow,
                             onupdate=datetime.utcnow)

    goal  = relationship("Goal", back_populates="achievement_updates")
    cycle = relationship("Cycle", back_populates="achievement_updates")


# ---------------------------------------------------------------------------
# Check-Ins (one per goal-sheet per quarter, conducted by manager)
# ---------------------------------------------------------------------------
class CheckIn(Base):
    __tablename__ = "check_ins"

    id            = Column(Integer, primary_key=True, index=True)
    goal_sheet_id = Column(Integer, ForeignKey("goal_sheets.id"), nullable=False)
    cycle_id      = Column(Integer, ForeignKey("cycles.id"), nullable=False)
    manager_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    wins          = Column(Text, nullable=True)
    risks         = Column(Text, nullable=True)
    support_needed = Column(Text, nullable=True)
    next_steps    = Column(Text, nullable=True)
    conducted_at  = Column(DateTime, default=datetime.utcnow)

    goal_sheet = relationship("GoalSheet", back_populates="check_ins")
    cycle      = relationship("Cycle", back_populates="check_ins")
    manager    = relationship("User", foreign_keys=[manager_id])


# ---------------------------------------------------------------------------
# Shared Goals (links a master goal to a recipient's goal copy)
# ---------------------------------------------------------------------------
class SharedGoal(Base):
    __tablename__ = "shared_goals"

    id             = Column(Integer, primary_key=True, index=True)
    master_goal_id = Column(Integer, ForeignKey("goals.id"), nullable=False)
    linked_goal_id = Column(Integer, ForeignKey("goals.id"), nullable=False)
    created_by     = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at     = Column(DateTime, default=datetime.utcnow)

    master_goal = relationship("Goal", foreign_keys=[master_goal_id],
                               back_populates="shared_as_master")
    linked_goal = relationship("Goal", foreign_keys=[linked_goal_id],
                               back_populates="shared_as_linked")
    creator     = relationship("User", foreign_keys=[created_by])


# ---------------------------------------------------------------------------
# Audit Logs (immutable record of all post-lock mutations)
# ---------------------------------------------------------------------------
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id          = Column(Integer, primary_key=True, index=True)
    entity_type = Column(Text, nullable=False)   # goal | goal_sheet | cycle
    entity_id   = Column(Integer, nullable=False)
    field_name  = Column(Text, nullable=True)    # which column changed
    old_value   = Column(Text, nullable=True)
    new_value   = Column(Text, nullable=True)
    # edit | approve | return | unlock | lock | shared_push
    action      = Column(Text, nullable=False)
    changed_by  = Column(Integer, ForeignKey("users.id"), nullable=False)
    changed_at  = Column(DateTime, default=datetime.utcnow)
    notes       = Column(Text, nullable=True)

    changed_by_user = relationship("User", back_populates="audit_logs",
                                   foreign_keys=[changed_by])
