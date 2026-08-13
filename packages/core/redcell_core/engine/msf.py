"""Build controlled Metasploit invocations (msfconsole batch mode) and parse the
module search table. Same execution posture as run_command (the agent can already
run msfconsole); this just gives it a structured search and run surface."""

from __future__ import annotations

import re
import shlex

_MODULE_RE = re.compile(r"\b((?:exploit|auxiliary|post|payload|encoder|nop|evasion)/[\w/\-.]+)")
_MODULE_OK = re.compile(r"^[\w/\-.]+$")


def build_msf_search(query: str) -> str:
    return f"msfconsole -q -x {shlex.quote(f'search {query}; exit')}"


def build_msf_run(module: str, options: dict[str, str] | None = None) -> str:
    """`use <module>; set K V; ...; run; exit`, shell-quoted as one script."""
    lines = [f"use {module}"]
    for k, v in (options or {}).items():
        lines.append(f"set {k} {v}")
    lines += ["run", "exit"]
    return f"msfconsole -q -x {shlex.quote('; '.join(lines))}"


def valid_module(module: str) -> bool:
    return bool(module) and bool(_MODULE_OK.match(module)) and ".." not in module


def parse_msf_search(output: str) -> list[str]:
    """Pull module paths out of a `search` result table, order-preserving, deduped."""
    seen: set[str] = set()
    out: list[str] = []
    for line in output.splitlines():
        m = _MODULE_RE.search(line)
        if m and m.group(1) not in seen:
            seen.add(m.group(1))
            out.append(m.group(1))
    return out
