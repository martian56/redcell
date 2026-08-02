from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Provider
from . import ids


async def list_all(s: AsyncSession) -> list[Provider]:
    return list((await s.scalars(select(Provider).order_by(Provider.label))).all())


async def upsert_many(s: AsyncSession, entries: list[dict]) -> None:
    for e in entries:
        row = await s.get(Provider, e["id"])
        if row is None:
            row = Provider(id=e["id"], created_at=ids.now_iso())
            s.add(row)
        row.label = e["label"]
        row.models = e.get("models", [])
        row.needs_key = e.get("needs_key", True)
    await s.flush()
