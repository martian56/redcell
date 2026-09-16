from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

PLAIN_TEXT = (
    "Write any prose in plain text. Do not use em-dashes; use commas, periods, or "
    "parentheses instead."
)

TRADECRAFT = (
    "Operate like a real red teamer, not a scan pipeline. Automated tools are a starting "
    "point, not the work: form a hypothesis about where the objective is reachable, pick the "
    "tool or the manual technique that tests it, read the result closely, and adapt. When a "
    "scanner or template comes back empty, do NOT move on: probe by hand. Craft the requests "
    "yourself, tamper with parameters, cookies, JWTs, and hidden fields, compare responses, "
    "and reason about the auth, access-control, and business logic that tools do not "
    "understand (IDOR, privilege escalation, workflow and race conditions, SSRF, injection in "
    "unusual sinks). Verify a finding before you trust it. Then CHAIN: use what you learn to "
    "reach the next step (a leaked key opens an API, an SSRF reaches an internal host, a "
    "low-severity info leak enables a real exploit) and build an attack path toward the "
    "objective. Prefer depth on a promising lead over breadth of shallow scans."
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
    image_setting: str = "docker_image"
