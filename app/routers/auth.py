"""
routers/auth.py — Authentication routes: login and logout.
"""

from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import verify_password, set_session, clear_session
from app.models import User

router = APIRouter(tags=["auth"])
templates = Jinja2Templates(directory="templates")


# ---------------------------------------------------------------------------
# GET /login
# ---------------------------------------------------------------------------
@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, next: str = "/"):
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "next": next, "error": None},
    )


# ---------------------------------------------------------------------------
# POST /login
# ---------------------------------------------------------------------------
@router.post("/login")
def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    next: str = Form("/"),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(
        User.email == email,
        User.is_active == True,
    ).first()

    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "next": next,
                "error": "Invalid email or password. Please try again.",
            },
            status_code=401,
        )

    # Build role-based redirect destination
    role_home = {
        "employee": "/employee/dashboard",
        "manager":  "/manager/dashboard",
        "admin":    "/admin/dashboard",
    }
    destination = role_home.get(user.role, "/login")

    response = RedirectResponse(url=destination, status_code=302)
    set_session(response, user.id)
    return response


# ---------------------------------------------------------------------------
# GET /logout
# ---------------------------------------------------------------------------
@router.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=302)
    clear_session(response)
    return response
