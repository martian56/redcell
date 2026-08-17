import asyncio

import pytest
from redcell_core.bus import Bus, control_channel
from redcell_core.config import settings
from redcell_core.engine.execution import ExecResult
from redcell_core.engine.runner import LiveRunner


class SleepBackend:
    def __init__(self) -> None:
        self.cancelled = False

    async def run(self, command, on_output=None) -> ExecResult:
        try:
            await asyncio.sleep(30)
            return ExecResult(exit_code=0, output="done")
        except asyncio.CancelledError:
            self.cancelled = True
            raise


@pytest.mark.asyncio
async def test_exec_returns_interrupted_when_current_command_cancelled():
    r = LiveRunner(bus=None, run_id="run-x")
    r.backend = SleepBackend()
    call = asyncio.create_task(r._exec("sleep 30"))
    for _ in range(50):
        if r._current_cmd_task is not None:
            break
        await asyncio.sleep(0.01)
    assert r._current_cmd_task is not None
    r._current_cmd_task.cancel()
    res = await asyncio.wait_for(call, timeout=5)
    assert res.exit_code == 130
    assert "interrupted" in res.output
    assert r._interrupted is True
    assert r.backend.cancelled is True


@pytest.mark.asyncio
async def test_control_interrupt_cancels_the_running_command():
    bus = Bus(settings.redis_url)
    await bus.connect()
    r = LiveRunner(bus=bus, run_id="run-ctl")
    r.backend = SleepBackend()
    watcher = asyncio.create_task(r._watch_control())
    call = asyncio.create_task(r._exec("sleep 30"))
    await asyncio.sleep(0.3)
    await bus.publish_json(control_channel("run-ctl"), {"action": "interrupt"})
    try:
        res = await asyncio.wait_for(call, timeout=5)
        assert res.exit_code == 130
        assert r.backend.cancelled is True
    finally:
        watcher.cancel()
        await bus.close()
