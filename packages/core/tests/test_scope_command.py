import pytest
from redcell_core.bus import Bus
from redcell_core.config import settings
from redcell_core.engine import scope
from redcell_core.engine.kinds import get_kind
from redcell_core.engine.runner import LiveRunner


def test_hosts_in_command():
    assert scope.hosts_in_command("curl https://app.example.com/x") == ["app.example.com"]
    assert "10.0.0.5" in scope.hosts_in_command("nmap 10.0.0.5 -p80")
    assert scope.hosts_in_command("id; ls -la") == []
    assert scope.hosts_in_command("curl http://user@t.example.com:8080/") == ["t.example.com"]


@pytest.mark.asyncio
async def test_command_scope_block_offensive_kind():
    r = LiveRunner(bus=Bus(settings.redis_url), run_id="x")

    async def _noop(*a, **k):
        return None

    r._event = _noop
    r.scope = ["*.example.com"]
    r._kindspec = get_kind("network")
    assert await r._command_scope_block("id") is None
    assert await r._command_scope_block("curl https://app.example.com") is None
    assert await r._command_scope_block("curl https://raw.githubusercontent.com/o/r/x.sh") is None
    blk = await r._command_scope_block("sqlmap -u https://evil.com --batch")
    assert blk and "out-of-scope" in blk["error"]


@pytest.mark.asyncio
async def test_command_scope_block_passive_and_empty_scope():
    r = LiveRunner(bus=Bus(settings.redis_url), run_id="x")

    async def _noop(*a, **k):
        return None

    r._event = _noop
    r.scope = ["*.example.com"]
    r._kindspec = get_kind("osint")
    assert await r._command_scope_block("curl https://evil.com") is None
    r._kindspec = get_kind("network")
    r.scope = []
    assert await r._command_scope_block("curl https://evil.com") is None
