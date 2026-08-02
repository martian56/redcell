from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Event
from . import ids
from ._query import paginate, search


async def record(s: AsyncSession, run_id: str, source: str, type: str, text: str) -> Event:
    row = Event(id=ids.new_id("ev"), run_id=run_id, source=source, type=type,
                text=text, ts=ids.now_iso())
    s.add(row)
    await s.flush()
    return row


async def list_for_run(s: AsyncSession, run_id: str, *, source: str | None = None,
                       type: str | None = None, q: str | None = None,
                       limit: int | None = None, offset: int = 0) -> list[Event]:
    stmt = select(Event).where(Event.run_id == run_id)
    if source:
        stmt = stmt.where(Event.source == source)
    if type:
        stmt = stmt.where(Event.type == type)
    stmt = search(stmt, q, [Event.text, Event.source])
    stmt = paginate(stmt.order_by(Event.ts.desc()), limit, offset)
    return list((await s.scalars(stmt)).all())
