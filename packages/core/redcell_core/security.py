"""Auth: bcrypt password check, JWT in an httpOnly cookie, current-user dependency."""

from __future__ import annotations

import datetime as dt

import bcrypt
import jwt
from fastapi import Cookie, HTTPException, Response

from .config import settings
from .db import session_scope
from .repositories import users as users_repo
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
    now = dt.datetime.now(dt.UTC)
    payload = {
        "sub": username,
        "role": role,
        "iat": now,
        "exp": now + dt.timedelta(hours=settings.jwt_ttl_hours),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=_ALGO)
    response.set_cookie(
        COOKIE_NAME, token, httponly=True, samesite="lax", secure=settings.secure_cookies,
        max_age=settings.jwt_ttl_hours * 3600, path="/",
    )


def clear_cookie(response: Response) -> None:
    response.delete_cookie(COOKIE_NAME, path="/")


async def current_user(rc_session: str | None = Cookie(default=None)) -> User:
    if not rc_session:
        raise HTTPException(status_code=401, detail="not authenticated")
    try:
        payload = jwt.decode(rc_session, settings.jwt_secret, algorithms=[_ALGO])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="invalid session") from None
    sub = payload.get("sub")
    async with session_scope() as s:
        user = await users_repo.get_by_username(s, sub) if sub else None
    if user is None:
        raise HTTPException(status_code=401, detail="invalid session")
    return User(id=user.id, username=user.username, role=user.role)
