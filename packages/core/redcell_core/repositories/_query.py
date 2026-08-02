"""Shared helpers so every list query supports search + pagination consistently."""

from __future__ import annotations

from sqlalchemy import or_


def search(stmt, q: str | None, cols):
    """Case-insensitive OR match of `q` across the given columns (no-op if empty)."""
    if q and cols:
        like = f"%{q}%"
        stmt = stmt.where(or_(*[c.ilike(like) for c in cols]))
    return stmt


def paginate(stmt, limit: int | None, offset: int | None):
    """Apply offset/limit. limit=None returns everything (backward compatible)."""
    if offset:
        stmt = stmt.offset(offset)
    if limit is not None:
        stmt = stmt.limit(limit)
    return stmt
