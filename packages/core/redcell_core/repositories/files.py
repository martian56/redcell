from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import File
from . import ids


async def create(s: AsyncSession, data: dict) -> File:
    row = File(id=data.get("id") or ids.new_id("file"), created_at=ids.now_iso(),
               **{k: v for k, v in data.items() if k != "id"})
    s.add(row)
    await s.flush()
    return row


async def get(s: AsyncSession, fid: str) -> File | None:
    return await s.get(File, fid)


async def list_for_session(s: AsyncSession, sid: str) -> list[File]:
    return list((await s.scalars(
        select(File).where(File.session_id == sid).order_by(File.created_at.desc()))).all())


async def delete(s: AsyncSession, fid: str) -> bool:
    row = await s.get(File, fid)
    if not row:
        return False
    await s.delete(row)
    await s.flush()
    return True
