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
    assert scope.hosts_in_command("curl http://[2001:db8::1]:8080/") == ["2001:db8::1"]


def test_encoded_ipv4_is_scoped():
    # integer-encoded IPv4 (2130706433 == 127.0.0.1) is extracted and canonicalised
    assert scope.hosts_in_command("curl http://2130706433/") == ["2130706433"]
    assert scope.in_scope("2130706433", ["*.example.com"]) is False
    assert scope.in_scope("2130706433", ["127.0.0.0/8"]) is True
    assert scope.in_scope("0x7f000001", ["127.0.0.0/8"]) is True


def test_hosts_in_command_ignores_filenames_and_times():
    assert scope.hosts_in_command("python app.py --config config.json") == []
    assert scope.hosts_in_command("cat /etc/passwd && ls src/main.py") == []
    assert scope.hosts_in_command("grep 12:30:45 app.log") == []
    assert scope.hosts_in_command("echo hi > out.txt") == []


def test_hosts_in_command_ignores_dotted_code_tokens():
    assert scope.hosts_in_command('python3 -c "page.evaluate(1)"') == []
    assert scope.hosts_in_command('python3 -c "json.load(f)"') == []
    assert scope.hosts_in_command("import os; os.path") == []
    assert scope.hosts_in_command("subprocess.run(['id'])") == []
    assert scope.hosts_in_command("requests.get('http://t.co/')") == ["t.co"]
    assert scope.hosts_in_command("socket.connect(('evil.com', 80))") == ["evil.com"]
    assert scope.hosts_in_command("driver.get('http://target.io')") == ["target.io"]
    assert scope.hosts_in_command("response.text; curl evil.com") == ["evil.com"]


def _make_runner(scope_list, kind="network", llm_verdict="BLOCK"):
    r = LiveRunner(bus=Bus(settings.redis_url), run_id="x")

    async def _noop(*a, **k):
        return None

    r._event = _noop
    r.scope = scope_list
    r._kindspec = get_kind(kind)

    class _FakeLlm:
        async def complete(self, messages, **kw):
            return {"content": llm_verdict, "usage_tokens": 0, "cost": 0}

    r.llm = _FakeLlm()
    return r


@pytest.mark.asyncio
async def test_command_scope_block_offensive_kind():
    r = _make_runner(["*.example.com"], llm_verdict="BLOCK")
    assert await r._command_scope_block("id") is None
    assert await r._command_scope_block("curl https://app.example.com") is None
    assert await r._command_scope_block("curl https://raw.githubusercontent.com/o/r/x.sh") is None
    blk = await r._command_scope_block("sqlmap -u https://evil.com --batch")
    assert blk and "out-of-scope" in blk["error"]


@pytest.mark.asyncio
async def test_command_scope_block_llm_allows_recon_tools():
    r = _make_runner(["*.example.com"], llm_verdict="ALLOW")
    assert await r._command_scope_block("curl 'https://crt.sh/?q=%25.example.com&output=json'") is None
    assert await r._command_scope_block("curl https://api.shodan.io/shodan/host/1.2.3.4") is None
    assert await r._command_scope_block("curl https://urlscan.io/api/v1/search/?q=example.com") is None


@pytest.mark.asyncio
async def test_command_scope_block_llm_blocks_real_attack():
    r = _make_runner(["*.example.com"], llm_verdict="BLOCK")
    blk = await r._command_scope_block("nmap -sV evil.com")
    assert blk and "out-of-scope" in blk["error"]


@pytest.mark.asyncio
async def test_command_scope_block_passive_and_empty_scope():
    r = _make_runner(["*.example.com"], kind="osint")
    assert await r._command_scope_block("curl https://evil.com") is None
    r._kindspec = get_kind("network")
    r.scope = []
    assert await r._command_scope_block("curl https://evil.com") is None
