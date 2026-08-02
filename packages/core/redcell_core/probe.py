"""SSH connection test for a saved Server: connect, gather basic facts (hostname,
OS, CPU, RAM, first IP), and return a structured result."""

from __future__ import annotations

import asyncio
from time import perf_counter

# One command that prints prefixed, easy-to-parse lines. Sent verbatim to the
# remote shell (the $(...) / $2 are evaluated remotely, not by Python).
_PROBE = "; ".join([
    'echo "H:$(hostname 2>/dev/null)"',
    'echo "U:$(uname -sr 2>/dev/null)"',
    'echo "C:$(nproc 2>/dev/null)"',
    "echo \"M:$(awk '/MemTotal/{print int($2/1024)}' /proc/meminfo 2>/dev/null)\"",
    'echo "I:$(hostname -I 2>/dev/null)"',
])


async def probe_server(host: str, username: str | None, secret: str | None, timeout: float = 12.0) -> dict:
    from .engine.execution import SSHBackend, _looks_like_private_key

    pk = secret if _looks_like_private_key(secret) else None
    pw = None if pk else (secret or None)
    backend = SSHBackend(host, username or "root", password=pw, private_key=pk)
    t0 = perf_counter()
    try:
        await asyncio.wait_for(backend.start(), timeout=timeout)
        res = await asyncio.wait_for(backend.run(_PROBE), timeout=timeout)
        latency = int((perf_counter() - t0) * 1000)
    except asyncio.TimeoutError:
        return {"ok": False, "error": "connection timed out"}
    except Exception as exc:
        return {"ok": False, "error": (str(exc) or type(exc).__name__)[:220]}
    finally:
        try:
            await backend.close()
        except Exception:
            pass
    facts = _parse(res.output)
    facts.update({"ok": True, "latency_ms": latency, "output": (res.output or "").strip()[:2000]})
    return facts


async def probe_proxy(url: str, timeout: float = 12.0) -> dict:
    """Health-check a proxy by fetching the egress IP through it. Supports
    http/https/socks5 (socks needs socksio)."""
    import httpx

    t0 = perf_counter()
    try:
        async with httpx.AsyncClient(proxy=url, timeout=timeout) as client:
            r = await client.get("https://api.ipify.org?format=json")
        latency = int((perf_counter() - t0) * 1000)
        if r.status_code >= 400:
            return {"ok": False, "error": f"proxy returned HTTP {r.status_code}"}
        try:
            egress = r.json().get("ip")
        except Exception:
            egress = (r.text or "").strip()[:64]
        return {"ok": True, "latency_ms": latency, "egress_ip": egress,
                "output": f"egress IP via proxy: {egress}"}
    except Exception as exc:
        return {"ok": False, "error": (str(exc) or type(exc).__name__)[:220]}


def _parse(output: str) -> dict:
    out: dict = {}
    for raw in (output or "").splitlines():
        line = raw.strip()
        if line.startswith("H:"):
            out["hostname"] = line[2:].strip() or None
        elif line.startswith("U:"):
            out["os"] = line[2:].strip() or None
        elif line.startswith("C:"):
            try:
                out["cpu"] = int(line[2:].strip())
            except ValueError:
                pass
        elif line.startswith("M:"):
            try:
                mb = int(line[2:].strip())
                out["ram_gb"] = max(1, round(mb / 1024))
            except ValueError:
                pass
        elif line.startswith("I:"):
            ips = line[2:].strip().split()
            out["ip"] = ips[0] if ips else None
    return out
