"""
dependencies.py — FastAPI dependency functions for authentication
and role-based access control.

On auth failure, raises HTTPException(303) with a Location header.
main.py's exception handler converts this to a proper RedirectResponse.
"""

from typing import Optional
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_session_user_id
from app.models import User


def _resolve_user(request: Request, db: Session) -> Optional[User]:
    user_id = get_session_user_id(request)
    if user_id is None:
        return None
    return db.query(User).filter(
        User.id == user_id,
        User.is_active == True,
    ).first()


def _role_home(role: str) -> str:
    return {
        "employee": "/employee/dashboard",
        "manager":  "/manager/dashboard",
        "admin":    "/admin/dashboard",
    }.get(role, "/login")


def _auth_redirect(location: str):
    raise HTTPException(
        status_code=status.HTTP_303_SEE_OTHER,
        headers={"Location": location},
        detail="Redirect",
    )


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    user = _resolve_user(request, db)
    if user is None:
        _auth_redirect("/login")
    return user


def require_employee(request: Request, db: Session = Depends(get_db)) -> User:
    user = _resolve_user(request, db)
    if user is None:
        _auth_redirect("/login")
    if user.role != "employee":
        _auth_redirect(_role_home(user.role))
    return user


def require_manager(request: Request, db: Session = Depends(get_db)) -> User:
    user = _resolve_user(request, db)
    if user is None:
        _auth_redirect("/login")
    if user.role != "manager":
        _auth_redirect(_role_home(user.role))
    return user


def require_admin(request: Request, db: Session = Depends(get_db)) -> User:
    user = _resolve_user(request, db)
    if user is None:
        _auth_redirect("/login")
    if user.role != "admin":
        _auth_redirect(_role_home(user.role))
    return user


def require_manager_or_admin(request: Request, db: Session = Depends(get_db)) -> User:
    user = _resolve_user(request, db)
    if user is None:
        _auth_redirect("/login")
    if user.role not in ("manager", "admin"):
        _auth_redirect(_role_home(user.role))
    return user
