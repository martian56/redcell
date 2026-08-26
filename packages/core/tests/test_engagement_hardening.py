"""Vhost/network engagement hardening: /etc/hosts auto-seeding and the phase
severity gate."""

import pytest
from redcell_core.bus import Bus
from redcell_core.db import session_scope
from redcell_core.engine.execution import ExecResult
from redcell_core.engine.runner import LiveRunner
from redcell_core.repositories import runs as runs_repo
from redcell_core.repositories import sessions as sessions_repo


class RecBackend:
    def __init__(self) -> None:
        self.commands: list[str] = []

    async def run(self, cmd: str, **kw) -> ExecResult:
        self.commands.append(cmd)
        return ExecResult(exit_code=0, output="")


def _runner() -> LiveRunner:
    r = LiveRunner(bus=Bus("redis://127.0.0.1:1"), run_id="run-seed")
    r.backend = RecBackend()
    return r


@pytest.mark.asyncio
async def test_seed_hosts_maps_named_hosts_to_the_single_ip():
    r = _runner()
    await r.bus.connect()
    r.scope = ["futurevera.thm", "*.futurevera.thm", "10.114.171.243"]
    r.targets = ["https://futurevera.thm"]
    await r._seed_hosts()
    assert len(r.backend.commands) == 1
    cmd = r.backend.commands[0]
    assert "10.114.171.243" in cmd and "futurevera.thm" in cmd
    assert ">> /etc/hosts" in cmd and "getent hosts" in cmd


@pytest.mark.asyncio
async def test_seed_hosts_skips_when_the_mapping_is_ambiguous():
    r = _runner()
    await r.bus.connect()
    r.scope = ["a.thm", "10.0.0.1", "10.0.0.2"]
    r.targets = ["https://a.thm"]
    await r._seed_hosts()
    assert r.backend.commands == []


@pytest.mark.asyncio
async def test_seed_hosts_skips_when_no_named_host():
    r = _runner()
    await r.bus.connect()
    r.scope = ["10.0.0.5"]
    r.targets = ["10.0.0.5"]
    await r._seed_hosts()
    assert r.backend.commands == []


@pytest.mark.asyncio
async def test_info_finding_does_not_advance_phase_but_a_real_one_does():
    bus = Bus("redis://127.0.0.1:1")
    await bus.connect()

    async with session_scope() as s:
        ses = await sessions_repo.create(s, {"name": "HardenT", "client": "C",
                                             "scope": ["*.t"], "targets": ["https://t"]})
        run = await runs_repo.create(s, {"session_id": ses.id, "name": "r", "status": "running",
                                         "phase": "Reconnaissance", "model": "kimi-k3"})
        sid, rid = ses.id, run.id

    r = LiveRunner(bus, rid)
    r.session_id = sid
    r.kind = "network"

    await r._record_finding({"title": "domain does not resolve", "severity": "info",
                             "location": "dns"})
    async with session_scope() as s:
        assert (await runs_repo.get(s, rid)).phase == "Reconnaissance"

    await r._record_finding({"title": "SQLi in login", "severity": "high", "location": "/login"})
    async with session_scope() as s:
        assert (await runs_repo.get(s, rid)).phase == "Exploitation"

    from redcell_core.models import Finding
    from redcell_core.models import Run as _Run
    from redcell_core.models import Session as _Session
    from sqlalchemy import delete
    async with session_scope() as s:
        await s.execute(delete(Finding).where(Finding.session_id == sid))
        await s.execute(delete(_Run).where(_Run.session_id == sid))
        await s.execute(delete(_Session).where(_Session.id == sid))
