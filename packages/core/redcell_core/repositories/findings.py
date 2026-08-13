from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Finding
from . import ids

# Triage states an operator can set. "candidate" is the default an agent records
# under; "verified" is confirmed; "dismissed" is a false positive or duplicate
# and is excluded from generated reports.
VALID_STATUSES = ("candidate", "verified", "dismissed", "inconclusive")


async def list_for_session(s: AsyncSession, sid: str, *, severity: str | None = None,
                           status: str | None = None, q: str | None = None,
                           limit: int | None = None, offset: int = 0) -> list[Finding]:
    from ._query import paginate, search
    stmt = select(Finding).where(Finding.session_id == sid)
    if severity:
        stmt = stmt.where(Finding.severity == severity)
    if status:
        stmt = stmt.where(Finding.status == status)
    stmt = search(stmt, q, [Finding.title, Finding.location, Finding.cwe])
    stmt = paginate(stmt.order_by(Finding.created_at.desc()), limit, offset)
    return list((await s.scalars(stmt)).all())


async def get(s: AsyncSession, fid: str) -> Finding | None:
    return await s.get(Finding, fid)


async def create(s: AsyncSession, data: dict) -> Finding:
    row = Finding(id=data.get("id") or ids.new_id("RC"), created_at=data.get("created_at") or ids.now_iso(),
                  **{k: v for k, v in data.items() if k not in ("id", "created_at")})
    s.add(row)
    await s.flush()
    return row


async def exists(s: AsyncSession, session_id: str, title: str, location: str) -> bool:
    q = select(Finding.id).where(
        Finding.session_id == session_id, Finding.title == title, Finding.location == location
    ).limit(1)
    return (await s.scalar(q)) is not None


async def set_status(s: AsyncSession, fid: str, status: str) -> Finding | None:
    """Set a finding's triage status. Returns None if the finding is missing.
    Raises ValueError on an unknown status."""
    if status not in VALID_STATUSES:
        raise ValueError(f"invalid status: {status}")
    row = await s.get(Finding, fid)
    if row:
        row.status = status
        await s.flush()
    return row


async def verify(s: AsyncSession, fid: str) -> Finding | None:
    return await set_status(s, fid, "verified")


async def merge(s: AsyncSession, primary_id: str, duplicate_ids: list[str]) -> Finding | None:
    """Fold duplicates into a primary finding by dismissing them. The primary is
    kept as the canonical record. Only duplicates in the primary's session are
    touched, and the primary itself is never dismissed. Returns the primary, or
    None if it is missing."""
    primary = await s.get(Finding, primary_id)
    if primary is None:
        return None
    for dup_id in duplicate_ids:
        if dup_id == primary_id:
            continue
        dup = await s.get(Finding, dup_id)
        if dup is not None and dup.session_id == primary.session_id:
            dup.status = "dismissed"
    await s.flush()
    return primary
