"""In-scope validation and a destructive-command denylist, enforced in code at the
tool boundary so a hallucinated or injected target can't be scanned/exploited and
an obviously destructive command can't run. Pure and unit-testable."""

from __future__ import annotations

import ipaddress
import re
from urllib.parse import urlparse


def _as_ip(value: str):
    try:
        return ipaddress.ip_address(value)
    except ValueError:
        return None


def _as_network(value: str):
    if "/" not in value:
        return None
    try:
        return ipaddress.ip_network(value, strict=False)
    except ValueError:
        return None


def target_host(target: str) -> str:
    """Reduce a URL / host:port / host / IP to a bare lowercase host or IP."""
    t = (target or "").strip()
    if not t:
        return ""
    if "://" in t:
        t = urlparse(t).hostname or ""
    else:
        t = t.split("/", 1)[0]
        if t.count(":") == 1 and _as_ip(t) is None:  # host:port, not bare IPv6
            t = t.split(":", 1)[0]
    return t.lower().rstrip(".")


def _scope_host(entry: str) -> str:
    e = (entry or "").strip().lower()
    if "://" in e:
        e = urlparse(e).hostname or ""
    return e.split("/", 1)[0].rstrip(".")


_URL_HOST_RE = re.compile(r"https?://([^/\s:\"'`)]+(?::\d+)?)", re.I)
_BARE_IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")


def hosts_in_command(command: str) -> list[str]:
    """Best-effort extraction of target hosts from a shell command: hostnames from
    http(s) URLs and bare IPv4 addresses, normalized to bare host/IP. Used to
    scope-gate free-form commands without false-positiving on flags/paths."""
    raw: list[str] = list(_URL_HOST_RE.findall(command or "")) + list(_BARE_IP_RE.findall(command or ""))
    seen: set[str] = set()
    out: list[str] = []
    for h in raw:
        host = target_host(h.split("@")[-1])
        if host and host not in seen:
            seen.add(host)
            out.append(host)
    return out


def in_scope(target: str, scope: list[str] | None) -> bool:
    """True if target falls within scope. An empty scope is unrestricted by design
    (the UI documents this); a non-empty scope is enforced."""
    entries = [s.strip() for s in (scope or []) if s and s.strip()]
    if not entries:
        return True
    host = target_host(target)
    if not host:
        return False
    ip = _as_ip(host)
    for entry in entries:
        net = _as_network(entry)
        if net is not None:
            if ip is not None and ip in net:
                return True
            continue
        eh = _scope_host(entry)
        if not eh:
            continue
        if eh.startswith("*."):
            base = eh[2:]
            if host == base or host.endswith("." + base):
                return True
        elif host == eh or host.endswith("." + eh):
            return True
    return False


_DESTRUCTIVE = [
    re.compile(r"\bmkfs(\.\w+)?\b", re.I),
    re.compile(r"\bdd\b[^\n]*\bof=/dev/(sd|nvme|vd|hd)", re.I),
    re.compile(r">\s*/dev/(sd|nvme|vd|hd)\w+", re.I),
    re.compile(r":\s*\(\s*\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:", re.I),
    re.compile(r"\b(shutdown|reboot|halt|poweroff|init\s+0|init\s+6)\b", re.I),
    re.compile(r"\bchmod\s+-R\s+0?00\s+/(?:\s|$)", re.I),
    re.compile(r"\b(wipefs|shred)\b[^\n]*\b/dev/", re.I),
]

_RM = re.compile(r"\brm\b((?:\s+-\S+)+)\s+(\S.*)?", re.I)
_WIPE_TARGETS = {"/", "/*", "~", "$HOME", "/etc", "/var", "/usr", "/bin", "/sbin",
                 "/boot", "/lib", "/lib64", "/root", "/home", "/opt", "/sys", "/proc",
                 "/dev", "/srv"}


def _dangerous_rm(command: str) -> bool:
    for m in _RM.finditer(command):
        flags = m.group(1).lower()
        if "r" not in flags or "f" not in flags:
            continue
        for tok in (m.group(2) or "").split():
            norm = tok.rstrip("/") or "/"
            if tok in _WIPE_TARGETS or norm in _WIPE_TARGETS:
                return True
    return False


def is_destructive(command: str) -> bool:
    c = command or ""
    return _dangerous_rm(c) or any(p.search(c) for p in _DESTRUCTIVE)
