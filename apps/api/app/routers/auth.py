"""Auth endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response
from redcell_core.config import settings
from redcell_core.repositories import users as users_repo
from redcell_core.schemas import FirstRun, LoginInput, User
from redcell_core.security import clear_cookie, current_user, issue_cookie, verify_password
from sqlalchemy.ext.asyncio import AsyncSession

from ..deps import db

router = APIRouter(tags=["auth"])


@router.get("/auth/first-run", response_model=FirstRun)
async def first_run() -> FirstRun:
    hint = "admin / admin" if (settings.admin_username == "admin" and settings.admin_password == "admin") else None
    return FirstRun(needs_setup=False, admin_password_hint=hint)


@router.post("/auth/login", response_model=User)
async def login(body: LoginInput, response: Response, s: AsyncSession = Depends(db)) -> User:
    user = await users_repo.get_by_username(s, body.username)
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="invalid credentials")
    issue_cookie(response, user.username, user.role)
    return User(id=user.id, username=user.username, role=user.role)


@router.get("/auth/me", response_model=User)
async def me(user: User = Depends(current_user)) -> User:
    return user


@router.post("/auth/logout")
async def logout(response: Response) -> dict[str, bool]:
    clear_cookie(response)
    return {"ok": True}
