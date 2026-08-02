from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Report
from . import ids


async def list_for_session(s: AsyncSession, sid: str) -> list[Report]:
    return list((await s.scalars(
        select(Report).where(Report.session_id == sid).order_by(Report.created_at.desc()))).all())


async def get(s: AsyncSession, rid: str) -> Report | None:
    return await s.get(Report, rid)


async def create(s: AsyncSession, sid: str, title: str, formats: list[str] | None = None) -> Report:
    formats = formats or ["pdf", "json", "sarif"]
    row = Report(id=ids.new_id("rep"), session_id=sid, title=title, status="generating",
                 format=formats[0], formats=formats, artifacts={}, created_at=ids.now_iso())
    s.add(row)
    await s.flush()
    return row


async def update(s: AsyncSession, rid: str, data: dict) -> Report | None:
    row = await s.get(Report, rid)
    if not row:
        return None
    for k, v in data.items():
        setattr(row, k, v)
    await s.flush()
    return row


async def delete(s: AsyncSession, rid: str) -> bool:
    row = await s.get(Report, rid)
    if not row:
        return False
    await s.delete(row)
    await s.flush()
    return True
