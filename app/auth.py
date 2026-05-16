"""
auth.py — Password hashing and session cookie helpers.

Uses:
  - passlib[bcrypt] for secure password hashing
  - itsdangerous (TimestampSigner) for signed, tamper-proof session cookies
"""

import os
from typing import Optional
from passlib.context import CryptContext
from itsdangerous import TimestampSigner, BadSignature, SignatureExpired
from fastapi import Request, Response

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ---------------------------------------------------------------------------
# Session cookie
# ---------------------------------------------------------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "goalflow-dev-secret-change-in-prod")
COOKIE_NAME = "goalflow_session"
SESSION_MAX_AGE = 60 * 60 * 8  # 8 hours in seconds

signer = TimestampSigner(SECRET_KEY)


def set_session(response: Response, user_id: int) -> None:
    """Sign user_id and write it into a secure HttpOnly cookie."""
    token = signer.sign(str(user_id)).decode()
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        max_age=SESSION_MAX_AGE,
        samesite="lax",
    )


def get_session_user_id(request: Request) -> Optional[int]:
    """
    Read and verify the session cookie.
    Returns the user_id (int) on success, None if missing/invalid/expired.
    """
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    try:
        raw = signer.unsign(token, max_age=SESSION_MAX_AGE)
        return int(raw.decode())
    except (BadSignature, SignatureExpired, ValueError):
        return None


def clear_session(response: Response) -> None:
    """Delete the session cookie."""
    response.delete_cookie(key=COOKIE_NAME)
