from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Finding, Session
from . import ids


async def list_all(s: AsyncSession, *, status: str | None = None, kind: str | None = None,
                   q: str | None = None, limit: int | None = None, offset: int = 0) -> list[Session]:
    from ._query import paginate, search
    stmt = select(Session)
    if status:
        stmt = stmt.where(Session.status == status)
    if kind:
        stmt = stmt.where(Session.kind == kind)
    stmt = search(stmt, q, [Session.name, Session.client])
    stmt = paginate(stmt.order_by(Session.created_at.desc()), limit, offset)
    return list((await s.scalars(stmt)).all())


async def get(s: AsyncSession, sid: str) -> Session | None:
    return await s.get(Session, sid)


async def create(s: AsyncSession, data: dict) -> Session:
    row = Session(id=data.get("id") or ids.new_id("ses"), created_at=ids.now_iso(),
                  **{k: v for k, v in data.items() if k != "id"})
    s.add(row)
    await s.flush()
    return row


async def set_active_run(s: AsyncSession, sid: str, run_id: str) -> None:
    row = await s.get(Session, sid)
    if row:
        row.active_run_id = run_id
        await s.flush()


async def severity_counts(s: AsyncSession, sid: str) -> dict[str, int]:
    base = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    rows = await s.execute(
        select(Finding.severity, func.count()).where(Finding.session_id == sid).group_by(Finding.severity))
    for sev, n in rows.all():
        if sev in base:
            base[sev] = int(n)
    return base


async def findings_count(s: AsyncSession, sid: str) -> int:
    return int(await s.scalar(
        select(func.count()).select_from(Finding).where(Finding.session_id == sid)) or 0)
