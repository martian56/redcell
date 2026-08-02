"""FastAPI dependencies: DB session, current-user guard, list-query params."""

from dataclasses import dataclass
from typing import AsyncIterator

from fastapi import Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from redcell_core.db import SessionLocal
from redcell_core.security import current_user  # noqa: F401  re-exported

__all__ = ["db", "current_user", "ListParams", "list_params"]


async def db() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@dataclass
class ListParams:
    """Common list controls; limit=None returns all rows."""
    q: str | None = None
    limit: int | None = None
    offset: int = 0


def list_params(
    q: str | None = Query(None, description="Case-insensitive search over the list's key fields."),
    limit: int | None = Query(None, ge=1, le=1000, description="Max rows to return (omit for all)."),
    offset: int = Query(0, ge=0, description="Rows to skip (for pagination)."),
) -> ListParams:
    return ListParams(q=q, limit=limit, offset=offset)


ListDep = Depends(list_params)
