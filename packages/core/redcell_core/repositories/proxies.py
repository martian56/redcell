from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..crypto import decrypt, encrypt
from ..models import Proxy
from . import ids


async def list_all(s: AsyncSession, *, kind: str | None = None, status: str | None = None,
                   q: str | None = None, limit: int | None = None, offset: int = 0) -> list[Proxy]:
    from ._query import paginate, search
    stmt = select(Proxy)
    if kind:
        stmt = stmt.where(Proxy.kind == kind)
    if status:
        stmt = stmt.where(Proxy.status == status)
    stmt = search(stmt, q, [Proxy.label, Proxy.url])
    stmt = paginate(stmt.order_by(Proxy.created_at.desc()), limit, offset)
    return list((await s.scalars(stmt)).all())


async def get(s: AsyncSession, pid: str) -> Proxy | None:
    return await s.get(Proxy, pid)


async def create(s: AsyncSession, data: dict, secret_plain: str | None = None) -> Proxy:
    row = Proxy(id=data.get("id") or ids.new_id("px"), created_at=ids.now_iso(),
                secret_ref=encrypt(secret_plain), **{k: v for k, v in data.items() if k != "id"})
    s.add(row)
    await s.flush()
    return row


async def update(s: AsyncSession, pid: str, data: dict, secret_plain: str | None = None) -> Proxy | None:
    row = await s.get(Proxy, pid)
    if not row:
        return None
    for k, v in data.items():
        setattr(row, k, v)
    if secret_plain:
        row.secret_ref = encrypt(secret_plain)
    await s.flush()
    return row


async def delete(s: AsyncSession, pid: str) -> bool:
    row = await s.get(Proxy, pid)
    if not row:
        return False
    await s.delete(row)
    await s.flush()
    return True


async def get_secret(s: AsyncSession, pid: str) -> str:
    row = await s.get(Proxy, pid)
    return decrypt(row.secret_ref) if row else ""
