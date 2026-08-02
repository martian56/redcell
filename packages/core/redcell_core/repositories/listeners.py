from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Listener
from . import ids


async def list_for_session(s: AsyncSession, sid: str, *, status: str | None = None,
                           q: str | None = None, limit: int | None = None, offset: int = 0) -> list[Listener]:
    from ._query import paginate, search
    stmt = select(Listener).where(Listener.session_id == sid)
    if status:
        stmt = stmt.where(Listener.status == status)
    stmt = search(stmt, q, [Listener.bind, Listener.kind])
    stmt = paginate(stmt, limit, offset)
    return list((await s.scalars(stmt)).all())


async def get(s: AsyncSession, lid: str) -> Listener | None:
    return await s.get(Listener, lid)


async def create(s: AsyncSession, data: dict) -> Listener:
    row = Listener(id=data.get("id") or ids.new_id("ls"), created_at=ids.now_iso(),
                   **{k: v for k, v in data.items() if k != "id"})
    s.add(row)
    await s.flush()
    return row


async def set_status(s: AsyncSession, lid: str, status: str) -> None:
    row = await s.get(Listener, lid)
    if row:
        row.status = status
        await s.flush()
