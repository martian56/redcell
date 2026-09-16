import pytest
from redcell_core.bus import Bus
from redcell_core.config import settings
from redcell_core.engine.runner import LiveRunner
from redcell_core.engine.tools import EXECUTOR_TOOLS, ORCHESTRATOR_TOOLS


def _names(ts):
    return {t["function"]["name"] for t in ts}


def test_shell_exec_tool_exposed_to_both_tiers():
    assert "shell_exec" in _names(ORCHESTRATOR_TOOLS)
    assert "shell_exec" in _names(EXECUTOR_TOOLS)


@pytest.mark.asyncio
async def test_shell_exec_requires_shell_and_command():
    r = LiveRunner(bus=Bus(settings.redis_url), run_id="run-se")
    r.session_id = "ses-se"
    assert "error" in await r._shell_exec({})
    assert "error" in await r._shell_exec({"shellId": "sh1"})


@pytest.mark.asyncio
async def test_shell_exec_blocks_destructive():
    r = LiveRunner(bus=Bus(settings.redis_url), run_id="run-se")
    r.session_id = "ses-se"
    res = await r._shell_exec({"shellId": "sh1", "command": "rm -rf /"})
    assert "error" in res and "destructive" in res["error"]
