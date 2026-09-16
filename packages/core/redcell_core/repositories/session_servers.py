from __future__ import annotations

from sqlalchemy import delete as sql_delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import SessionServer
from . import ids

SINGULAR_ROLES = frozenset({"execution", "mobile"})
VALID_ROLES = frozenset({"execution", "mobile", "pivot"})


async def list_for_session(s: AsyncSession, session_id: str) -> list[SessionServer]:
    stmt = select(SessionServer).where(SessionServer.session_id == session_id).order_by(
        SessionServer.role, SessionServer.created_at
    )
    return list((await s.scalars(stmt)).all())


async def get_by_role(s: AsyncSession, session_id: str, role: str) -> SessionServer | None:
    stmt = select(SessionServer).where(
        SessionServer.session_id == session_id, SessionServer.role == role
    ).order_by(SessionServer.created_at)
    return (await s.scalars(stmt)).first()


async def attach(s: AsyncSession, session_id: str, server_id: str, role: str) -> SessionServer:
    if role not in VALID_ROLES:
        raise ValueError(f"invalid server role: {role}")
    if role in SINGULAR_ROLES:
        await s.execute(sql_delete(SessionServer).where(
            SessionServer.session_id == session_id, SessionServer.role == role
        ))
    else:
        existing = (await s.scalars(select(SessionServer).where(
            SessionServer.session_id == session_id,
            SessionServer.server_id == server_id,
            SessionServer.role == role,
        ))).first()
        if existing is not None:
            return existing
    row = SessionServer(id=ids.new_id("ssv"), session_id=session_id, server_id=server_id,
                        role=role, created_at=ids.now_iso())
    s.add(row)
    await s.flush()
    return row


async def detach(s: AsyncSession, session_id: str, server_id: str, role: str) -> bool:
    result = await s.execute(sql_delete(SessionServer).where(
        SessionServer.session_id == session_id,
        SessionServer.server_id == server_id,
        SessionServer.role == role,
    ))
    await s.flush()
    return result.rowcount > 0
