from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Loot
from . import ids


async def list_for_session(s: AsyncSession, sid: str, *, kind: str | None = None,
                           q: str | None = None, limit: int | None = None, offset: int = 0) -> list[Loot]:
    from ._query import paginate, search
    stmt = select(Loot).where(Loot.session_id == sid)
    if kind:
        stmt = stmt.where(Loot.kind == kind)
    stmt = search(stmt, q, [Loot.label, Loot.value, Loot.source])
    stmt = paginate(stmt.order_by(Loot.ts.desc()), limit, offset)
    return list((await s.scalars(stmt)).all())


async def exists(s: AsyncSession, session_id: str, label: str, value: str) -> bool:
    q = select(Loot.id).where(
        Loot.session_id == session_id, Loot.label == label, Loot.value == value
    ).limit(1)
    return (await s.scalar(q)) is not None


async def create(s: AsyncSession, data: dict) -> Loot:
    row = Loot(id=data.get("id") or ids.new_id("l"), ts=data.get("ts") or ids.now_iso(),
               **{k: v for k, v in data.items() if k not in ("id", "ts")})
    s.add(row)
    await s.flush()
    return row
