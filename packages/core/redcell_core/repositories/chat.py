from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import ChatMessage
from . import ids


async def list_for_run(s: AsyncSession, run_id: str, *, role: str | None = None,
                       q: str | None = None, limit: int | None = None, offset: int = 0) -> list[ChatMessage]:
    from ._query import paginate, search
    stmt = select(ChatMessage).where(ChatMessage.run_id == run_id)
    if role:
        stmt = stmt.where(ChatMessage.role == role)
    stmt = search(stmt, q, [ChatMessage.text])
    stmt = paginate(stmt.order_by(ChatMessage.ts), limit, offset)
    return list((await s.scalars(stmt)).all())


async def create(s: AsyncSession, run_id: str, role: str, text: str,
                 options: list[str] | None = None) -> ChatMessage:
    row = ChatMessage(id=ids.new_id("msg"), run_id=run_id, role=role, text=text,
                      options=options, ts=ids.now_iso())
    s.add(row)
    await s.flush()
    return row
