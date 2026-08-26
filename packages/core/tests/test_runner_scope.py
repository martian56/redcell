import pytest
from redcell_core.bus import Bus
from redcell_core.config import settings
from redcell_core.engine.runner import LiveRunner


@pytest.mark.asyncio
async def test_scope_block_gates_targets():
    bus = Bus(settings.redis_url)
    await bus.connect()
    r = LiveRunner(bus=bus, run_id="run-scope")
    r.scope = ["*.example.com", "10.0.0.0/16"]
    try:
        assert await r._scope_block("https://api.example.com") is None
        assert await r._scope_block("10.0.5.5") is None
        blocked = await r._scope_block("http://evil.com")
        assert blocked is not None and "out of scope" in blocked["error"]
    finally:
        await bus.close()


@pytest.mark.asyncio
async def test_scope_block_unrestricted_when_scope_empty():
    bus = Bus(settings.redis_url)
    await bus.connect()
    r = LiveRunner(bus=bus, run_id="run-scope2")
    r.scope = []
    try:
        assert await r._scope_block("http://anything.example.org") is None
    finally:
        await bus.close()
