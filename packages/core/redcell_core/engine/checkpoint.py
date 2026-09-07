"""Durable checkpointing for the LangGraph orchestrator loop, keyed by
thread_id = run_id, stored in the same Postgres database as everything else.
This only holds transient agent-loop state; business data lives in its own
tables. One connection pool is shared across runs."""

from __future__ import annotations

from ..config import settings

_saver = None


def _checkpoint_uri() -> str:
    return (
        settings.database_url.replace("+asyncpg", "").replace("postgresql+psycopg", "postgresql")
    )


async def get_checkpointer():
    """Return a process-wide AsyncPostgresSaver (lazily created and migrated), or
    None when checkpointing is disabled (for example in unit tests)."""
    global _saver
    if not settings.checkpoint_enabled:
        return None
    if _saver is not None:
        return _saver

    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
    from psycopg.rows import dict_row
    from psycopg_pool import AsyncConnectionPool

    pool = AsyncConnectionPool(
        conninfo=_checkpoint_uri(),
        max_size=5,
        open=False,
        kwargs={"autocommit": True, "row_factory": dict_row},
    )
    await pool.open()
    saver = AsyncPostgresSaver(pool)
    await saver.setup()
    _saver = saver
    return _saver
