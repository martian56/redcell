from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..crypto import decrypt, encrypt
from ..models import Server
from . import ids


async def list_all(s: AsyncSession, *, status: str | None = None, q: str | None = None,
                   limit: int | None = None, offset: int = 0) -> list[Server]:
    from ._query import paginate, search
    stmt = select(Server)
    if status:
        stmt = stmt.where(Server.status == status)
    stmt = search(stmt, q, [Server.name, Server.host, Server.region])
    stmt = paginate(stmt.order_by(Server.created_at.desc()), limit, offset)
    return list((await s.scalars(stmt)).all())


async def get(s: AsyncSession, sid: str) -> Server | None:
    return await s.get(Server, sid)


async def create(s: AsyncSession, data: dict, secret_plain: str | None = None) -> Server:
    row = Server(id=data.get("id") or ids.new_id("srv"), created_at=ids.now_iso(),
                 secret_ref=encrypt(secret_plain), **{k: v for k, v in data.items() if k != "id"})
    s.add(row)
    await s.flush()
    return row


async def update(s: AsyncSession, sid: str, data: dict, secret_plain: str | None = None) -> Server | None:
    row = await s.get(Server, sid)
    if not row:
        return None
    for k, v in data.items():
        setattr(row, k, v)
    if secret_plain:
        row.secret_ref = encrypt(secret_plain)
    await s.flush()
    return row


async def delete(s: AsyncSession, sid: str) -> bool:
    row = await s.get(Server, sid)
    if not row:
        return False
    await s.delete(row)
    await s.flush()
    return True


async def get_secret(s: AsyncSession, sid: str) -> str:
    row = await s.get(Server, sid)
    return decrypt(row.secret_ref) if row else ""
