from __future__ import annotations

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Run
from . import ids


async def list_for_session(s: AsyncSession, sid: str, *, status: str | None = None,
                           q: str | None = None, limit: int | None = None, offset: int = 0) -> list[Run]:
    from ._query import paginate, search
    stmt = select(Run).where(Run.session_id == sid)
    if status:
        stmt = stmt.where(Run.status == status)
    stmt = search(stmt, q, [Run.name, Run.model])
    stmt = paginate(stmt.order_by(Run.started_at.desc()), limit, offset)
    return list((await s.scalars(stmt)).all())


async def get(s: AsyncSession, rid: str) -> Run | None:
    return await s.get(Run, rid)


async def create(s: AsyncSession, data: dict) -> Run:
    row = Run(id=data.get("id") or ids.new_id("run"),
              started_at=data.get("started_at") or ids.now_iso(),
              **{k: v for k, v in data.items() if k not in ("id", "started_at")})
    s.add(row)
    await s.flush()
    return row


async def start_if_not_running(s: AsyncSession, rid: str) -> bool:
    result = await s.execute(
        update(Run).where(Run.id == rid, Run.status != "running").values(status="running"))
    await s.flush()
    return (result.rowcount or 0) > 0


async def set_status(s: AsyncSession, rid: str, status: str) -> Run | None:
    row = await s.get(Run, rid)
    if row:
        row.status = status
        await s.flush()
    return row


async def set_meters(s: AsyncSession, rid: str, tokens_delta: int, cost_delta: float, elapsed_delta: int) -> None:
    row = await s.get(Run, rid)
    if row:
        row.tokens = (row.tokens or 0) + tokens_delta
        row.cost_usd = round((row.cost_usd or 0.0) + cost_delta, 4)
        row.elapsed_sec = (row.elapsed_sec or 0) + elapsed_delta
        await s.flush()


async def list_by_status(s: AsyncSession, status: str) -> list[Run]:
    return list((await s.scalars(select(Run).where(Run.status == status))).all())
