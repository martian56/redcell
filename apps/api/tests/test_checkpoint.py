import asyncio

import redcell_core.engine.checkpoint as cp
from redcell_core.config import settings


def test_checkpoint_uri_strips_async_driver():
    prev = settings.database_url
    try:
        settings.database_url = "postgresql+asyncpg://u:p@host:5432/db"
        assert cp._checkpoint_uri() == "postgresql://u:p@host:5432/db"
    finally:
        settings.database_url = prev


def test_disabled_returns_none():
    async def run():
        prev = settings.checkpoint_enabled
        settings.checkpoint_enabled = False
        cp._saver = None
        try:
            assert await cp.get_checkpointer() is None
        finally:
            settings.checkpoint_enabled = prev
            cp._saver = None

    asyncio.run(run())


def test_postgres_checkpointer_initializes():
    async def run():
        prev = settings.checkpoint_enabled
        settings.checkpoint_enabled = True
        cp._saver = None
        saver = None
        try:
            saver = await cp.get_checkpointer()
            assert saver is not None
            assert await cp.get_checkpointer() is saver
        finally:
            settings.checkpoint_enabled = prev
            pool = getattr(saver, "conn", None)
            if pool is not None:
                try:
                    await pool.close()
                except Exception:
                    pass
            cp._saver = None

    asyncio.run(run())
