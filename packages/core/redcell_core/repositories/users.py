from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import User
from . import ids


async def get_by_username(s: AsyncSession, username: str) -> User | None:
    return await s.scalar(select(User).where(User.username == username))


async def get_any(s: AsyncSession) -> User | None:
    return await s.scalar(select(User).limit(1))


async def create(s: AsyncSession, username: str, password_hash: str, role: str = "admin") -> User:
    row = User(id=ids.new_id("u"), username=username, password_hash=password_hash,
               role=role, created_at=ids.now_iso())
    s.add(row)
    await s.flush()
    return row
