from __future__ import annotations

from .base import Kind
from .code import code_executor, code_orchestrator
from .network import network_executor, network_orchestrator

DEFAULT_KIND = "network"

KINDS: dict[str, Kind] = {
    "network": Kind(
        id="network",
        label="Network",
        orchestrator_system=network_orchestrator,
        executor_system=network_executor,
    ),
    "code": Kind(
        id="code",
        label="Code review",
        orchestrator_system=code_orchestrator,
        executor_system=code_executor,
        uses_browser=False,
        seeds_hosts=False,
        mounts_source=True,
        exploits=False,
    ),
}


def get_kind(kind_id: str | None) -> Kind:
    return KINDS.get((kind_id or "").strip().lower(), KINDS[DEFAULT_KIND])
