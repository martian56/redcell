from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

PLAIN_TEXT = (
    "Write any prose in plain text. Do not use em-dashes; use commas, periods, or "
    "parentheses instead."
)


@dataclass(frozen=True)
class OrchestratorContext:
    goal: str
    scope: list[str]
    targets: list[str]
    roe: str | None = None
    brief: str | None = None
    instruction: str | None = None
    files: list[str] | None = None
    source: str | None = None


@dataclass(frozen=True)
class Kind:
    id: str
    label: str
    orchestrator_system: Callable[[OrchestratorContext], str]
    executor_system: Callable[[str, str], str]
    available: bool = True
    uses_browser: bool = True
    seeds_hosts: bool = True
    mounts_source: bool = False
    exploits: bool = True
