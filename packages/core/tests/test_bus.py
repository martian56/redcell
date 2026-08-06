import asyncio

import pytest
from redcell_core.bus import Bus, control_channel


@pytest.mark.asyncio
async def test_memory_pubsub_roundtrip():
    bus = Bus("redis://127.0.0.1:1")  # unreachable -> memory backend
    await bus.connect()
    assert bus.transport == "memory"
    got = []

    async def sub():
        async for m in bus.subscribe("t"):
            got.append(m)
            return

    task = asyncio.create_task(sub())
    await asyncio.sleep(0.05)
    await bus.publish("t", "hello")
    await asyncio.wait_for(task, timeout=2)
    assert got == ["hello"]


def test_control_channel():
    assert control_channel("run-1") == "control:run-1"
