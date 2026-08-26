"""The orchestrator delegates multiple executors concurrently; their reports come
back and both findings are recorded."""

import asyncio
import json
import re

import pytest
from redcell_core.bus import Bus
from redcell_core.db import session_scope
from redcell_core.engine.execution import SimBackend
from redcell_core.engine.runner import LiveRunner
from redcell_core.repositories import agents as agents_repo
from redcell_core.repositories import findings as findings_repo
from redcell_core.repositories import runs as runs_repo
from redcell_core.repositories import sessions as sessions_repo


def _tc(name, args):
    return {"role": "assistant", "content": "",
            "tool_calls": [{"id": f"c_{name}", "name": name, "arguments": args}]}


class ParallelLLM:
    def __init__(self):
        self.orch = 0
        self.exec_counts = {}

    async def complete(self, messages, tools=None, tool_choice="auto"):
        system = messages[0]["content"]
        if "orchestrator" in system:
            self.orch += 1
            if self.orch == 1:
                return _tc("delegate", '{"agent": "recon", "objective": "map"}')
            if self.orch == 2:
                return _tc("delegate", '{"agent": "web-exploit", "objective": "exploit"}')
            if self.orch == 3:
                return _tc("await_executors", "{}")
            return _tc("finish", '{"summary": "done"}')
        n = self.exec_counts.get(system, 0) + 1
        self.exec_counts[system] = n
        agent = (re.search(r"'([^']+)' executor", system) or [None, "exec"])[1]
        if n == 1:
            return _tc("run_command", '{"command": "echo hi"}')
        return _tc("report", json.dumps({"summary": "ok",
                                         "finding": {"title": f"{agent} finding", "severity": "low",
                                                     "location": "x"}}))


@pytest.mark.asyncio
async def test_two_executors_run_concurrently():
    from redcell_core.config import settings as _s
    _s.checkpoint_db = ""

    bus = Bus("redis://127.0.0.1:1")  # memory backend
    await bus.connect()

    async with session_scope() as s:
        ses = await sessions_repo.create(s, {"name": "ParT", "client": "C",
                                             "scope": ["*.t"], "targets": ["https://t"]})
        run = await runs_repo.create(s, {"session_id": ses.id, "name": "r", "status": "running",
                                         "phase": "Recon", "model": "kimi-k3"})
        sid, rid = ses.id, run.id

    runner = LiveRunner(bus, rid)
    runner.llm = ParallelLLM()
    runner.backend = SimBackend()
    await asyncio.wait_for(runner.run(), timeout=30)

    async with session_scope() as s:
        run = await runs_repo.get(s, rid)
        nodes, edges = await agents_repo.graph(s, rid)
        finds = await findings_repo.list_for_session(s, sid)

    names = {a.name for a in nodes}
    titles = {f.title for f in finds}
    assert run.status == "completed"
    assert "recon" in names and "web-exploit" in names
    assert len(edges) >= 2
    assert "recon finding" in titles and "web-exploit finding" in titles

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
