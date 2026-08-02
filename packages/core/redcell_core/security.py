"""Auth: bcrypt password check, JWT in an httpOnly cookie, current-user dependency."""

from __future__ import annotations

import datetime as dt

import bcrypt
import jwt
from fastapi import Cookie, HTTPException, Response

from .config import settings
from .schemas import User

COOKIE_NAME = "rc_session"
_ALGO = "HS256"


def hash_password(password: str) -> str:
    # bcrypt truncates at 72 bytes; do it explicitly so long inputs never error.
    return bcrypt.hashpw(password.encode()[:72], bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode()[:72], password_hash.encode())
    except Exception:
        return False


def issue_cookie(response: Response, username: str, role: str = "admin") -> None:
    now = dt.datetime.now(dt.timezone.utc)
    payload = {
        "sub": username,
        "role": role,
        "iat": now,
        "exp": now + dt.timedelta(hours=settings.jwt_ttl_hours),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=_ALGO)
    response.set_cookie(
        COOKIE_NAME, token, httponly=True, samesite="lax", secure=False,
        max_age=settings.jwt_ttl_hours * 3600, path="/",
    )


def clear_cookie(response: Response) -> None:
    response.delete_cookie(COOKIE_NAME, path="/")


def current_user(rc_session: str | None = Cookie(default=None)) -> User:
    if not rc_session:
        raise HTTPException(status_code=401, detail="not authenticated")
    try:
        payload = jwt.decode(rc_session, settings.jwt_secret, algorithms=[_ALGO])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="invalid session")
    return User(id="u-1", username=payload.get("sub", "admin"), role=payload.get("role", "admin"))
