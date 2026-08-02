"""Offline test of the live engine: the real plan/act loop, executor, SimBackend,
repositories, and bus wired together, with a scripted fake LLM instead of litellm.
Covers delegation, command execution, finding recording, the operator ask/answer
round-trip, and that everything gets persisted and published."""

import asyncio
import json

import pytest

from redcell_core.bus import Bus, chat_channel, events_channel
from redcell_core.db import session_scope
from redcell_core.engine.execution import SimBackend
from redcell_core.engine.runner import LiveRunner
from redcell_core.repositories import agents as agents_repo
from redcell_core.repositories import findings as findings_repo
from redcell_core.repositories import runs as runs_repo
from redcell_core.repositories import sessions as sessions_repo


def _tc(name, args):
    return {"role": "assistant", "content": "", "tool_calls": [{"id": f"c_{name}", "name": name, "arguments": args}]}


class FakeLLM:
    def __init__(self):
        self.orch = 0
        self.exec = 0

    async def complete(self, messages, tools=None, tool_choice="auto"):
        system = messages[0]["content"]
        if "orchestrator" in system:
            self.orch += 1
            if self.orch == 1:
                return _tc("delegate", {"agent": "recon", "objective": "map the attack surface"})
            if self.orch == 2:
                return _tc("record_finding", {"title": "Exposed admin panel", "severity": "high",
                                              "location": "/admin", "status": "candidate"})
            if self.orch == 3:
                return _tc("ask_operator", {"question": "Proceed to exploit /admin?", "options": ["Yes", "No"]})
            return _tc("finish", {"summary": "surface mapped, one finding"})
        self.exec += 1
        if self.exec == 1:
            return _tc("run_command", {"command": "nmap -sV app.acme-corp.io"})
        return _tc("report", {"summary": "https + ssh open",
                              "finding": {"title": "SSH exposed", "severity": "low", "location": "22/tcp"}})


@pytest.mark.asyncio
async def test_engine_runs_and_persists():
    # disable the SQLite checkpointer: its aiosqlite connection doesn't mix with
    # pytest's per-test event loops. we're exercising engine logic, not durability.
    from redcell_core.config import settings as _s
    _s.checkpoint_db = ""

    bus = Bus("redis://127.0.0.1:1")  # memory backend
    await bus.connect()

    async with session_scope() as s:
        ses = await sessions_repo.create(s, {"name": "Engine T", "client": "C", "scope": ["*.t"], "targets": ["https://t"]})
        run = await runs_repo.create(s, {"session_id": ses.id, "name": "r", "status": "running",
                                         "phase": "Recon", "model": "kimi-k3"})
        sid, rid = ses.id, run.id

    events, chats = [], []

    async def collect(channel, sink):
        async for payload in bus.subscribe(channel):
            sink.append(json.loads(payload))

    ev_task = asyncio.create_task(collect(events_channel(rid), events))
    ch_task = asyncio.create_task(collect(chat_channel(rid), chats))
    await asyncio.sleep(0.05)

    runner = LiveRunner(bus, rid)
    runner.llm = FakeLLM()
    runner.backend = SimBackend()

    async def answer():
        # once the assistant question is persisted, the runner is subscribed;
        # publish the operator reply a few times to avoid any subscribe race.
        for _ in range(200):
            async with session_scope() as s:
                from redcell_core.repositories import chat as chat_repo
                msgs = await chat_repo.list_for_run(s, rid)
            if any(m.role == "assistant" and m.options for m in msgs):
                for _ in range(3):
                    await bus.publish_json(chat_channel(rid), {"id": "op", "runId": rid, "role": "operator",
                                                               "text": "Yes", "ts": "t"})
                    await asyncio.sleep(0.1)
                return
            await asyncio.sleep(0.02)

    ans = asyncio.create_task(answer())
    await asyncio.wait_for(runner.run(), timeout=30)
    await asyncio.sleep(0.1)
    for t in (ev_task, ch_task, ans):
        t.cancel()

    async with session_scope() as s:
        run = await runs_repo.get(s, rid)
        nodes, edges = await agents_repo.graph(s, rid)
        finds = await findings_repo.list_for_session(s, sid)

    names = {a.name for a in nodes}
    titles = {f.title for f in finds}
    assert run.status == "completed"
    assert "recon" in names
    assert len(edges) >= 1
    assert "Exposed admin panel" in titles
    assert "SSH exposed" in titles
    assert any(e["type"] == "finding" for e in events)
    assert any(e["type"] == "tool" and e["text"].startswith("$") for e in events)
    assert any(c.get("options") for c in chats)

    # clean up so the test session does not linger in the shared dev DB
    from sqlalchemy import delete
    from redcell_core.models import (Agent, AgentEdge, ChatMessage, Finding, Host, Run as _Run,
                                     Session as _Session, Shell)
    async with session_scope() as s:
        for m in (Agent, AgentEdge, ChatMessage):
            await s.execute(delete(m).where(m.run_id == rid))
        for m in (Finding, Shell, Host):
            await s.execute(delete(m).where(m.session_id == sid))
        await s.execute(delete(_Run).where(_Run.session_id == sid))
        await s.execute(delete(_Session).where(_Session.id == sid))
