"""Branch coverage: the orchestrator can finish on the first plan step without
delegating any executor."""

import asyncio

import pytest
from redcell_core.bus import Bus
from redcell_core.db import session_scope
from redcell_core.engine.execution import SimBackend
from redcell_core.engine.runner import LiveRunner
from redcell_core.repositories import agents as agents_repo
from redcell_core.repositories import runs as runs_repo
from redcell_core.repositories import sessions as sessions_repo


class FinishFirstLLM:
    async def complete(self, messages, tools=None, tool_choice="auto"):
        return {"role": "assistant", "content": "",
                "tool_calls": [{"id": "c_finish", "name": "finish",
                                "arguments": '{"summary": "nothing to do"}'}]}


@pytest.mark.asyncio
async def test_orchestrator_finishes_without_delegating():
    from redcell_core.config import settings as _s
    _s.checkpoint_db = ""

    bus = Bus("redis://127.0.0.1:1")  # memory backend
    await bus.connect()

    async with session_scope() as s:
        ses = await sessions_repo.create(s, {"name": "FinishT", "client": "C",
                                             "scope": ["*.t"], "targets": ["https://t"]})
        run = await runs_repo.create(s, {"session_id": ses.id, "name": "r", "status": "running",
                                         "phase": "Recon", "model": "kimi-k3"})
        sid, rid = ses.id, run.id

    runner = LiveRunner(bus, rid)
    runner.llm = FinishFirstLLM()
    runner.backend = SimBackend()
    await asyncio.wait_for(runner.run(), timeout=30)

    async with session_scope() as s:
        run = await runs_repo.get(s, rid)
        nodes, edges = await agents_repo.graph(s, rid)

    assert run.status == "completed"
    assert "recon" not in {a.name for a in nodes}
    assert len(edges) == 0

    from redcell_core.models import Agent, AgentEdge
    from redcell_core.models import Run as _Run
    from redcell_core.models import Session as _Session
    from sqlalchemy import delete
    async with session_scope() as s:
        for m in (Agent, AgentEdge):
            await s.execute(delete(m).where(m.run_id == rid))
        await s.execute(delete(_Run).where(_Run.session_id == sid))
        await s.execute(delete(_Session).where(_Session.id == sid))
