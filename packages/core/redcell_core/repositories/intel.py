from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import IntelEntity, IntelRelation
from . import ids


async def list_for_session(s: AsyncSession, session_id: str) -> tuple[list[IntelEntity], list[IntelRelation]]:
    ents = list((await s.scalars(
        select(IntelEntity).where(IntelEntity.session_id == session_id)
        .order_by(IntelEntity.type, IntelEntity.created_at))).all())
    rels = list((await s.scalars(
        select(IntelRelation).where(IntelRelation.session_id == session_id)
        .order_by(IntelRelation.created_at))).all())
    return ents, rels


async def get_by_value(s: AsyncSession, session_id: str, type_: str, value: str) -> IntelEntity | None:
    stmt = select(IntelEntity).where(
        IntelEntity.session_id == session_id, IntelEntity.type == type_, IntelEntity.value == value)
    return (await s.scalars(stmt)).first()


async def find_value(s: AsyncSession, session_id: str, value: str) -> IntelEntity | None:
    stmt = select(IntelEntity).where(
        IntelEntity.session_id == session_id, IntelEntity.value == value).order_by(IntelEntity.created_at)
    return (await s.scalars(stmt)).first()


async def add_entity(s: AsyncSession, session_id: str, data: dict) -> IntelEntity:
    existing = await get_by_value(s, session_id, data["type"], data["value"])
    if existing is not None:
        for k in ("label", "source"):
            if data.get(k) and not getattr(existing, k):
                setattr(existing, k, data[k])
        if data.get("meta"):
            existing.meta = {**(existing.meta or {}), **data["meta"]}
        await s.flush()
        return existing
    row = IntelEntity(id=ids.new_id("ent"), session_id=session_id, created_at=ids.now_iso(),
                      type=data["type"], value=data["value"], label=data.get("label", ""),
                      source=data.get("source", ""), meta=data.get("meta") or {})
    s.add(row)
    await s.flush()
    return row


async def add_relation(s: AsyncSession, session_id: str, from_id: str, to_id: str,
                       label: str = "related") -> IntelRelation | None:
    if from_id == to_id:
        return None
    existing = (await s.scalars(select(IntelRelation).where(
        IntelRelation.from_id == from_id, IntelRelation.to_id == to_id, IntelRelation.label == label))).first()
    if existing is not None:
        return existing
    row = IntelRelation(id=ids.new_id("rel"), session_id=session_id, from_id=from_id, to_id=to_id,
                        label=label, created_at=ids.now_iso())
    s.add(row)
    await s.flush()
    return row
