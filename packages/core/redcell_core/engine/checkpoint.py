"""Durable checkpointing for the LangGraph orchestrator loop, keyed by
thread_id = run_id. Uses a SQLite store (aiosqlite): works on the Windows
ProactorEventLoop the worker needs for `docker exec`. Business data stays in
Postgres; this only holds transient agent-loop state. One connection shared across runs."""

from __future__ import annotations

from ..config import settings

_saver = None


async def get_checkpointer():
    """Return a process-wide AsyncSqliteSaver (lazily created + migrated), or None
    if checkpointing is disabled (empty checkpoint_db, e.g. in unit tests)."""
    global _saver
    if not settings.checkpoint_db:
        return None
    if _saver is not None:
        return _saver
    import aiosqlite
    from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

    conn = await aiosqlite.connect(settings.checkpoint_db)
    saver = AsyncSqliteSaver(conn)
    await saver.setup()  # idempotent: creates the checkpoint tables if missing
    _saver = saver
    return _saver
