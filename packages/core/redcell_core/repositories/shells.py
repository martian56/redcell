from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Shell
from . import ids


async def list_for_session(s: AsyncSession, sid: str, *, kind: str | None = None,
                           status: str | None = None, q: str | None = None,
                           limit: int | None = None, offset: int = 0) -> list[Shell]:
    from ._query import paginate, search
    stmt = select(Shell).where(Shell.session_id == sid)
    if kind:
        stmt = stmt.where(Shell.kind == kind)
    if status:
        stmt = stmt.where(Shell.status == status)
    stmt = search(stmt, q, [Shell.label, Shell.host])
    stmt = paginate(stmt, limit, offset)
    return list((await s.scalars(stmt)).all())


async def get(s: AsyncSession, shell_id: str) -> Shell | None:
    return await s.get(Shell, shell_id)


async def create(s: AsyncSession, data: dict) -> Shell:
    row = Shell(id=data.get("id") or ids.new_id("sh"), created_at=ids.now_iso(),
                **{k: v for k, v in data.items() if k != "id"})
    s.add(row)
    await s.flush()
    return row


async def delete(s: AsyncSession, shell_id: str) -> bool:
    row = await s.get(Shell, shell_id)
    if not row:
        return False
    await s.delete(row)
    await s.flush()
    return True


async def list_running(s: AsyncSession) -> list[Shell]:
    return list((await s.scalars(select(Shell).where(Shell.status == "running"))).all())


async def set_status(s: AsyncSession, shell_id: str, status: str) -> None:
    row = await s.get(Shell, shell_id)
    if row:
        row.status = status
        await s.flush()
