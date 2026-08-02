from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Host
from . import ids


async def list_for_session(s: AsyncSession, sid: str, *, q: str | None = None,
                           source: str | None = None, limit: int | None = None,
                           offset: int = 0) -> list[Host]:
    from ._query import paginate, search
    stmt = select(Host).where(Host.session_id == sid)
    if source:
        stmt = stmt.where(Host.source == source)
    stmt = search(stmt, q, [Host.host, Host.ip])
    stmt = paginate(stmt, limit, offset)
    return list((await s.scalars(stmt)).all())


async def exists(s: AsyncSession, session_id: str, host: str) -> bool:
    q = select(Host.id).where(Host.session_id == session_id, Host.host == host).limit(1)
    return (await s.scalar(q)) is not None


async def create(s: AsyncSession, data: dict) -> Host:
    row = Host(id=data.get("id") or ids.new_id("h"), **{k: v for k, v in data.items() if k != "id"})
    s.add(row)
    await s.flush()
    return row
