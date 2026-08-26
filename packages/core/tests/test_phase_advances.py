"""The engagement phase advances as the run progresses and never moves backward."""

import asyncio

import pytest
from redcell_core.bus import Bus
from redcell_core.db import session_scope
from redcell_core.engine.execution import SimBackend
from redcell_core.engine.runner import LiveRunner
from redcell_core.repositories import runs as runs_repo
from redcell_core.repositories import sessions as sessions_repo


class PhaseLLM:
    """set_phase -> Exploitation, record a finding, then finish."""

    def __init__(self):
        self.n = 0

    async def complete(self, messages, tools=None, tool_choice="auto"):
        self.n += 1
        if self.n == 1:
            return _tc("set_phase", '{"phase": "Exploitation"}')
        if self.n == 2:
            return _tc("record_finding",
                       '{"title": "SQLi in login", "severity": "high", "location": "/login"}')
        return _tc("finish", '{"summary": "done"}')


def _tc(name, args):
    return {"role": "assistant", "content": "",
            "tool_calls": [{"id": f"c_{name}", "name": name, "arguments": args}]}


@pytest.mark.asyncio
async def test_phase_advances_to_reporting():
    from redcell_core.config import settings as _s
    _s.checkpoint_db = ""

    bus = Bus("redis://127.0.0.1:1")
    await bus.connect()

    async with session_scope() as s:
        ses = await sessions_repo.create(s, {"name": "PhaseT", "client": "C",
                                             "scope": ["*.t"], "targets": ["https://t"]})
        run = await runs_repo.create(s, {"session_id": ses.id, "name": "r", "status": "running",
                                         "phase": "Reconnaissance", "model": "kimi-k3"})
        sid, rid = ses.id, run.id

    runner = LiveRunner(bus, rid)
    runner.llm = PhaseLLM()
    runner.backend = SimBackend()
    await asyncio.wait_for(runner.run(), timeout=30)

    async with session_scope() as s:
        run = await runs_repo.get(s, rid)

    assert run.status == "completed"
    assert run.phase == "Reporting"

    from redcell_core.models import Agent, AgentEdge, Finding, Shell
    from redcell_core.models import Run as _Run
    from redcell_core.models import Session as _Session
    from sqlalchemy import delete
    async with session_scope() as s:
        for m in (Agent, AgentEdge):
            await s.execute(delete(m).where(m.run_id == rid))
        for m in (Finding, Shell):
            await s.execute(delete(m).where(m.session_id == sid))
        await s.execute(delete(_Run).where(_Run.session_id == sid))
        await s.execute(delete(_Session).where(_Session.id == sid))


@pytest.mark.asyncio
async def test_set_phase_is_forward_only():
    async with session_scope() as s:
        ses = await sessions_repo.create(s, {"name": "FwdT", "client": "C",
                                             "scope": ["*.t"], "targets": ["https://t"]})
        run = await runs_repo.create(s, {"session_id": ses.id, "name": "r", "status": "running",
                                         "phase": "Reconnaissance", "model": "kimi-k3"})
        rid, sid = run.id, ses.id

        assert await runs_repo.set_phase(s, rid, "Post-Exploitation") == "Post-Exploitation"
        assert await runs_repo.set_phase(s, rid, "Reconnaissance") == "Post-Exploitation"
        assert await runs_repo.set_phase(s, rid, "bogus") == "Post-Exploitation"
        assert await runs_repo.set_phase(s, rid, "Reporting") == "Reporting"

        from redcell_core.models import Run as _Run
        from redcell_core.models import Session as _Session
        from sqlalchemy import delete
        await s.execute(delete(_Run).where(_Run.session_id == sid))
        await s.execute(delete(_Session).where(_Session.id == sid))
