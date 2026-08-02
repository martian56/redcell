from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import ProxyEntry
from . import ids


async def list_for_session(s: AsyncSession, sid: str, *, method: str | None = None,
                           q: str | None = None, limit: int | None = None, offset: int = 0) -> list[ProxyEntry]:
    from ._query import paginate, search
    stmt = select(ProxyEntry).where(ProxyEntry.session_id == sid)
    if method:
        stmt = stmt.where(ProxyEntry.method == method)
    stmt = search(stmt, q, [ProxyEntry.url])
    stmt = paginate(stmt.order_by(ProxyEntry.ts.desc()), limit, offset)
    return list((await s.scalars(stmt)).all())


async def add_capped(s: AsyncSession, sid: str, data: dict, cap: int = 200) -> ProxyEntry:
    row = ProxyEntry(id=ids.new_id("px"), session_id=sid, ts=data.get("ts") or ids.now_iso(),
                     **{k: v for k, v in data.items() if k not in ("ts",)})
    s.add(row)
    await s.flush()
    keep = (await s.scalars(
        select(ProxyEntry.id).where(ProxyEntry.session_id == sid)
        .order_by(ProxyEntry.ts.desc()).limit(cap))).all()
    await s.execute(
        ProxyEntry.__table__.delete().where(
            ProxyEntry.session_id == sid, ProxyEntry.id.notin_(keep)))
    return row
