from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Finding
from . import ids


async def list_for_session(s: AsyncSession, sid: str, *, severity: str | None = None,
                           status: str | None = None, q: str | None = None,
                           limit: int | None = None, offset: int = 0) -> list[Finding]:
    from ._query import paginate, search
    stmt = select(Finding).where(Finding.session_id == sid)
    if severity:
        stmt = stmt.where(Finding.severity == severity)
    if status:
        stmt = stmt.where(Finding.status == status)
    stmt = search(stmt, q, [Finding.title, Finding.location, Finding.cwe])
    stmt = paginate(stmt.order_by(Finding.created_at.desc()), limit, offset)
    return list((await s.scalars(stmt)).all())


async def get(s: AsyncSession, fid: str) -> Finding | None:
    return await s.get(Finding, fid)


async def create(s: AsyncSession, data: dict) -> Finding:
    row = Finding(id=data.get("id") or ids.new_id("RC"), created_at=data.get("created_at") or ids.now_iso(),
                  **{k: v for k, v in data.items() if k not in ("id", "created_at")})
    s.add(row)
    await s.flush()
    return row


async def exists(s: AsyncSession, session_id: str, title: str, location: str) -> bool:
    q = select(Finding.id).where(
        Finding.session_id == session_id, Finding.title == title, Finding.location == location
    ).limit(1)
    return (await s.scalar(q)) is not None


async def verify(s: AsyncSession, fid: str) -> Finding | None:
    row = await s.get(Finding, fid)
    if row:
        row.status = "verified"
        await s.flush()
    return row
