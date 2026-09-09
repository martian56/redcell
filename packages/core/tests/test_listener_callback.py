import pytest
from redcell_core.bus import Bus
from redcell_core.config import settings
from redcell_core.engine.runner import LiveRunner, _in_callback_range


def test_in_callback_range_bounds():
    lo, hi = settings.callback_port_min, settings.callback_port_max
    assert _in_callback_range(lo)
    assert _in_callback_range(hi)
    assert _in_callback_range((lo + hi) // 2)
    assert not _in_callback_range(lo - 1)
    assert not _in_callback_range(hi + 1)
    assert not _in_callback_range(22)


@pytest.mark.asyncio
async def test_start_listener_rejects_port_outside_range():
    r = LiveRunner(bus=Bus(settings.redis_url), run_id="run-listener")
    r.session_id = "ses-listener"
    result = await r._start_listener(settings.callback_port_max + 100)
    assert "error" in result
    assert "outside" in result["error"]
