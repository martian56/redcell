from __future__ import annotations

from typing import Any

from ...config import settings

_CVSS_BY_SEVERITY = {"critical": 9.5, "high": 8.0, "medium": 5.5, "low": 3.1, "info": 0.0}

_REMOTE_LISTENER_PY = (
    "import socket,sys,os,threading\n"
    "p=int(sys.argv[1])\n"
    "s=socket.socket()\n"
    "s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)\n"
    "s.bind(('0.0.0.0',p))\n"
    "s.listen(1)\n"
    "sys.stderr.write('LISTENING %d\\n'%p);sys.stderr.flush()\n"
    "c,a=s.accept()\n"
    "sys.stderr.write('CONNECT %s:%d\\n'%(a[0],a[1]));sys.stderr.flush()\n"
    "def _pin():\n"
    "    while True:\n"
    "        d=os.read(0,4096)\n"
    "        if not d:break\n"
    "        try:c.sendall(d)\n"
    "        except Exception:break\n"
    "threading.Thread(target=_pin,daemon=True).start()\n"
    "while True:\n"
    "    d=c.recv(4096)\n"
    "    if not d:break\n"
    "    os.write(1,d)\n"
)


def summarize_progress(findings, hosts, loot) -> str | None:
    live = [f for f in findings if getattr(f, "status", "") != "dismissed"]
    if not (live or hosts or loot):
        return None
    lines: list[str] = []
    if live:
        lines.append("Findings already recorded:")
        for f in live[:40]:
            loc = f" @ {f.location}" if getattr(f, "location", "") else ""
            lines.append(f"- [{f.severity}] {f.title}{loc} (status: {f.status})")
    if hosts:
        lines.append("Attack surface already mapped:")
        for h in hosts[:40]:
            ip = f" ({h.ip})" if getattr(h, "ip", None) else ""
            ports = [p.get("port", p) if isinstance(p, dict) else p for p in (h.ports or [])][:12]
            pstr = f" ports {', '.join(str(p) for p in ports)}" if ports else ""
            tech = f" tech {', '.join(str(t) for t in (h.tech or [])[:8])}" if h.tech else ""
            lines.append(f"- {h.host}{ip}{pstr}{tech}")
    if loot:
        lines.append("Loot and credentials already collected:")
        for x in loot[:30]:
            lines.append(f"- {x.kind}: {x.label}")
    return "\n".join(lines)


def resolve_cvss(args: dict[str, Any]) -> float:
    raw = args.get("cvss")
    try:
        score = float(raw) if raw is not None else 0.0
    except (TypeError, ValueError):
        score = 0.0
    if score <= 0.0:
        score = _CVSS_BY_SEVERITY.get(str(args.get("severity", "info")).lower(), 0.0)
    return round(max(0.0, min(10.0, score)), 1)


def is_source_url(source: str) -> bool:
    s = source.strip().lower()
    return "://" in s or s.startswith("git@")


def safe_source(source: str) -> bool:
    return not any(c in source for c in ("'", '"', ";", "|", "&", "`", "$", "\n", "\\", "<", ">", "("))


def in_callback_range(port: int) -> bool:
    return settings.callback_port_min <= port <= settings.callback_port_max


def proxy_url_with_creds(proxy, secret: str | None) -> str:
    url = (proxy.url or "").strip()
    if "://" not in url:
        scheme = "socks5" if getattr(proxy, "kind", "") == "socks5" else "http"
        url = f"{scheme}://{url}"
    user = getattr(proxy, "username", None)
    if user and secret and "@" not in url.split("://", 1)[1]:
        scheme, rest = url.split("://", 1)
        return f"{scheme}://{user}:{secret}@{rest}"
    return url
