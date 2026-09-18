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


def test_hosts_in_command_bare_hostname_and_ipv6():
    # bare hostnames (the natural form) are now extracted, not just URLs/IPv4
    assert scope.hosts_in_command("nmap -sV evil.com") == ["evil.com"]
    assert scope.hosts_in_command("sqlmap -u https://t.acme.io/s --batch") == ["t.acme.io"]
    assert "fe80::1" in scope.hosts_in_command("ping fe80::1")
    assert "2001:db8::1" in scope.hosts_in_command("curl http://[2001:db8::1]:8080/")


def test_hosts_in_command_ignores_filenames_and_times():
    assert scope.hosts_in_command("python app.py --config config.json") == []
    assert scope.hosts_in_command("cat /etc/passwd && ls src/main.py") == []
    assert scope.hosts_in_command("grep 12:30:45 app.log") == []
    assert scope.hosts_in_command("echo hi > out.txt") == []


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
