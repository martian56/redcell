"""Per-session and per-run resources."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, HTTPException, Query
from redcell_core import queue, steer
from redcell_core.bus import (
    browser_channel,
    bus,
    chat_channel,
    control_channel,
    shell_channel,
    shell_input_channel,
)
from redcell_core.db import session_scope
from redcell_core.repositories import agents as agents_repo
from redcell_core.repositories import chat as chat_repo
from redcell_core.repositories import events as events_repo
from redcell_core.repositories import findings as findings_repo
from redcell_core.repositories import hosts as hosts_repo
from redcell_core.repositories import listeners as listeners_repo
from redcell_core.repositories import loot as loot_repo
from redcell_core.repositories import proxy_entries as proxy_repo
from redcell_core.repositories import runs as runs_repo
from redcell_core.repositories import sessions as sessions_repo
from redcell_core.repositories import shells as shells_repo
from redcell_core.schemas import (
    Agent,
    AgentEdge,
    AgentGraph,
    BrowserControlInput,
    ChatMessage,
    ChatSendInput,
    CreateRunInput,
    CreateSessionInput,
    EventMsg,
    Finding,
    Host,
    Listener,
    LootItem,
    OpenShellInput,
    ProxyEntry,
    Run,
    Session,
    Shell,
    ShellWriteInput,
    StartListenerInput,
)
from redcell_core.security import current_user
from sqlalchemy.ext.asyncio import AsyncSession

from ..deps import ListParams, db, list_params

router = APIRouter(tags=["resources"], dependencies=[Depends(current_user)])


# ---- mappers ----
async def _session_schema(s: AsyncSession, row) -> Session:
    sch = Session.model_validate(row)
    sch.findings_count = await sessions_repo.findings_count(s, row.id)
    sch.severity_counts = await sessions_repo.severity_counts(s, row.id)
    return sch


def _listener_schema(row) -> Listener:
    return Listener(id=row.id, session_id=row.session_id, kind=row.kind, bind=row.bind,
                    status=row.status, sessions=row.sessions_count)


async def _get_session(s: AsyncSession, sid: str):
    row = await sessions_repo.get(s, sid)
    if row is None:
        raise HTTPException(404, "session not found")
    return row


async def _get_run(s: AsyncSession, rid: str):
    row = await runs_repo.get(s, rid)
    if row is None:
        raise HTTPException(404, "run not found")
    return row


# ---- sessions ----
@router.get("/sessions", response_model=list[Session])
async def list_sessions(s: AsyncSession = Depends(db), p: ListParams = Depends(list_params),
                        status: str | None = Query(None), kind: str | None = Query(None)) -> list[Session]:
    rows = await sessions_repo.list_all(s, status=status, kind=kind, q=p.q, limit=p.limit, offset=p.offset)
    return [await _session_schema(s, r) for r in rows]


@router.get("/sessions/{sid}", response_model=Session)
async def get_session(sid: str, s: AsyncSession = Depends(db)) -> Session:
    return await _session_schema(s, await _get_session(s, sid))


@router.post("/sessions", response_model=Session)
async def create_session(body: CreateSessionInput, s: AsyncSession = Depends(db)) -> Session:
    row = await sessions_repo.create(s, {
        "name": body.name, "client": body.client, "kind": body.kind, "source": body.source,
        "scope": body.scope, "targets": body.targets, "roe": body.roe, "status": "active",
        "server_id": body.server_id, "proxy_id": body.proxy_id,
        "provider": body.provider, "model": body.model,
    })
    return await _session_schema(s, row)


# ---- runs ----
@router.get("/sessions/{sid}/runs", response_model=list[Run])
async def list_runs(sid: str, s: AsyncSession = Depends(db), p: ListParams = Depends(list_params),
                    status: str | None = Query(None)) -> list[Run]:
    await _get_session(s, sid)
    rows = await runs_repo.list_for_session(s, sid, status=status, q=p.q, limit=p.limit, offset=p.offset)
    return [Run.model_validate(r) for r in rows]


@router.get("/runs/{rid}", response_model=Run)
async def get_run(rid: str, s: AsyncSession = Depends(db)) -> Run:
    return Run.model_validate(await _get_run(s, rid))


@router.post("/sessions/{sid}/runs", response_model=Run)
async def create_run(sid: str, body: CreateRunInput, s: AsyncSession = Depends(db)) -> Run:
    await _get_session(s, sid)
    run = await runs_repo.create(s, {"session_id": sid, "name": body.name, "status": "queued",
                                     "phase": "Reconnaissance", "model": body.model,
                                     "provider": body.provider})
    await sessions_repo.set_active_run(s, sid, run.id)
    await agents_repo.add(s, {"run_id": run.id, "name": "orchestrator", "role": "root",
                             "status": "running", "action": body.instruction or "planning the engagement",
                             "calls": 0})
    schema = Run.model_validate(run)
    await s.commit()  # commit before enqueue; worker reads the run
    await queue.enqueue("run_engagement", run.id)
    return schema


@router.post("/runs/{rid}/pause", response_model=Run)
async def pause_run(rid: str, s: AsyncSession = Depends(db)) -> Run:
    run = await _get_run(s, rid)
    await runs_repo.set_status(s, rid, "paused")
    schema = Run.model_validate(run)
    await s.commit()
    await bus.publish_json(control_channel(rid), {"action": "pause"})
    return schema


@router.post("/runs/{rid}/resume", response_model=Run)
async def resume_run(rid: str, s: AsyncSession = Depends(db)) -> Run:
    run = await _get_run(s, rid)
    await runs_repo.set_status(s, rid, "running")
    schema = Run.model_validate(run)
    await s.commit()
    await bus.publish_json(control_channel(rid), {"action": "resume"})
    await queue.enqueue("run_engagement", rid)
    return schema


@router.post("/runs/{rid}/stop", response_model=Run)
async def stop_run(rid: str, s: AsyncSession = Depends(db)) -> Run:
    run = await _get_run(s, rid)
    await runs_repo.set_status(s, rid, "stopped")
    schema = Run.model_validate(run)
    await s.commit()
    await bus.publish_json(control_channel(rid), {"action": "stop"})
    return schema


@router.post("/sessions/{sid}/browser/control")
async def browser_control(sid: str, body: BrowserControlInput, s: AsyncSession = Depends(db)) -> dict[str, str]:
    await _get_session(s, sid)
    owner = "operator" if body.owner == "operator" else "agent"
    await bus.publish_json(browser_channel(sid), {"owner": owner})
    return {"owner": owner}


# ---- agents ----
@router.get("/runs/{rid}/agents", response_model=AgentGraph)
async def agent_graph(rid: str, s: AsyncSession = Depends(db)) -> AgentGraph:
    await _get_run(s, rid)
    nodes, edges = await agents_repo.graph(s, rid)
    return AgentGraph(
        nodes=[Agent.model_validate(n) for n in nodes],
        edges=[AgentEdge(**{"from": e.from_id, "to": e.to_id}) for e in edges],
    )


@router.get("/agents/{aid}", response_model=Agent)
async def get_agent(aid: str, s: AsyncSession = Depends(db)) -> Agent:
    row = await agents_repo.get(s, aid)
    if row is None:
        raise HTTPException(404, "agent not found")
    return Agent.model_validate(row)


# ---- findings ----
@router.get("/sessions/{sid}/findings", response_model=list[Finding])
async def list_findings(sid: str, s: AsyncSession = Depends(db), p: ListParams = Depends(list_params),
                        severity: str | None = Query(None), status: str | None = Query(None)) -> list[Finding]:
    await _get_session(s, sid)
    rows = await findings_repo.list_for_session(s, sid, severity=severity, status=status,
                                                q=p.q, limit=p.limit, offset=p.offset)
    return [Finding.model_validate(f) for f in rows]


@router.get("/findings/{fid}", response_model=Finding)
async def get_finding(fid: str, s: AsyncSession = Depends(db)) -> Finding:
    row = await findings_repo.get(s, fid)
    if row is None:
        raise HTTPException(404, "finding not found")
    return Finding.model_validate(row)


@router.post("/findings/{fid}/verify", response_model=Finding)
async def verify_finding(fid: str, s: AsyncSession = Depends(db)) -> Finding:
    row = await findings_repo.verify(s, fid)
    if row is None:
        raise HTTPException(404, "finding not found")
    return Finding.model_validate(row)


# ---- shells ----
@router.get("/sessions/{sid}/shells", response_model=list[Shell])
async def list_shells(sid: str, s: AsyncSession = Depends(db), p: ListParams = Depends(list_params),
                      kind: str | None = Query(None), status: str | None = Query(None)) -> list[Shell]:
    await _get_session(s, sid)
    rows = await shells_repo.list_for_session(s, sid, kind=kind, status=status,
                                              q=p.q, limit=p.limit, offset=p.offset)
    return [Shell.model_validate(sh) for sh in rows]


@router.post("/sessions/{sid}/shells", response_model=Shell)
async def open_shell(sid: str, body: OpenShellInput, s: AsyncSession = Depends(db)) -> Shell:
    await _get_session(s, sid)
    row = await shells_repo.create(s, {"session_id": sid, "kind": body.kind, "label": body.label or body.kind,
                                       "status": "running" if body.kind in ("tool", "reverse", "interactive") else "idle",
                                       "pty": body.kind in ("interactive", "reverse")})
    schema = Shell.model_validate(row)
    if body.kind == "interactive":
        # operator terminal driven by the worker
        await s.commit()
        await queue.enqueue("operate_shell", row.id)
    return schema


@router.post("/shells/{shell_id}/write")
async def write_shell(shell_id: str, body: ShellWriteInput, s: AsyncSession = Depends(db)) -> dict[str, bool]:
    sh = await shells_repo.get(s, shell_id)
    if sh is None:
        raise HTTPException(404, "shell not found")
    await bus.publish(shell_input_channel(shell_id), body.data)
    if sh.kind != "reverse":
        # Line-mode echo for non-PTY shells (reverse shells echo remotely).
        # DEL translated to backspace-space-backspace to erase.
        await bus.publish(shell_channel(shell_id), body.data.replace("\x7f", "\b \b"))
    return {"ok": True}


@router.delete("/shells/{shell_id}", status_code=204)
async def close_shell(shell_id: str, s: AsyncSession = Depends(db)) -> None:
    if not await shells_repo.delete(s, shell_id):
        raise HTTPException(404, "shell not found")


# ---- listeners ----
@router.get("/sessions/{sid}/listeners", response_model=list[Listener])
async def list_listeners(sid: str, s: AsyncSession = Depends(db), p: ListParams = Depends(list_params),
                         status: str | None = Query(None)) -> list[Listener]:
    await _get_session(s, sid)
    rows = await listeners_repo.list_for_session(s, sid, status=status, q=p.q, limit=p.limit, offset=p.offset)
    return [_listener_schema(row) for row in rows]


@router.post("/sessions/{sid}/listeners", response_model=Listener)
async def start_listener(sid: str, body: StartListenerInput, s: AsyncSession = Depends(db)) -> Listener:
    await _get_session(s, sid)
    row = await listeners_repo.create(s, {"session_id": sid, "kind": body.kind, "bind": body.bind,
                                          "status": "listening", "sessions_count": 0})
    return _listener_schema(row)


# ---- proxy history / hosts / loot ----
@router.get("/sessions/{sid}/proxy", response_model=list[ProxyEntry])
async def proxy_history(sid: str, s: AsyncSession = Depends(db), p: ListParams = Depends(list_params),
                        method: str | None = Query(None)) -> list[ProxyEntry]:
    await _get_session(s, sid)
    rows = await proxy_repo.list_for_session(s, sid, method=method, q=p.q, limit=p.limit, offset=p.offset)
    return [ProxyEntry.model_validate(p_) for p_ in rows]


@router.get("/sessions/{sid}/hosts", response_model=list[Host])
async def hosts(sid: str, s: AsyncSession = Depends(db), p: ListParams = Depends(list_params),
                source: str | None = Query(None)) -> list[Host]:
    await _get_session(s, sid)
    rows = await hosts_repo.list_for_session(s, sid, source=source, q=p.q, limit=p.limit, offset=p.offset)
    return [Host.model_validate(h) for h in rows]


@router.get("/sessions/{sid}/loot", response_model=list[LootItem])
async def loot(sid: str, s: AsyncSession = Depends(db), p: ListParams = Depends(list_params),
               kind: str | None = Query(None)) -> list[LootItem]:
    await _get_session(s, sid)
    rows = await loot_repo.list_for_session(s, sid, kind=kind, q=p.q, limit=p.limit, offset=p.offset)
    return [LootItem.model_validate(x) for x in rows]


# ---- chat + events ----
@router.get("/runs/{rid}/chat", response_model=list[ChatMessage])
async def chat_history(rid: str, s: AsyncSession = Depends(db), p: ListParams = Depends(list_params),
                       role: str | None = Query(None)) -> list[ChatMessage]:
    await _get_run(s, rid)
    rows = await chat_repo.list_for_run(s, rid, role=role, q=p.q, limit=p.limit, offset=p.offset)
    return [ChatMessage.model_validate(c) for c in rows]


@router.get("/runs/{rid}/events", response_model=list[EventMsg])
async def run_events(rid: str, s: AsyncSession = Depends(db), p: ListParams = Depends(list_params),
                     source: str | None = Query(None), type: str | None = Query(None)) -> list[EventMsg]:
    await _get_run(s, rid)
    rows = await events_repo.list_for_run(s, rid, source=source, type=type,
                                          q=p.q, limit=p.limit, offset=p.offset)
    return [EventMsg.model_validate(e) for e in rows]


@router.post("/runs/{rid}/chat", response_model=ChatMessage)
async def chat_send(rid: str, body: ChatSendInput, s: AsyncSession = Depends(db)) -> ChatMessage:
    run = await _get_run(s, rid)
    msg = await chat_repo.create(s, rid, "operator", body.text)
    schema = ChatMessage.model_validate(msg)
    await s.commit()
    # publish on the chat channel; consumed as the answer if a question is pending
    await bus.publish_json(chat_channel(rid), {"id": msg.id, "runId": rid, "role": "operator",
                                               "text": body.text, "options": None, "ts": msg.ts})

    if await steer.is_awaiting(rid):
        # orchestrator asked a question; this message is the answer
        return schema
    if run.status == "running":
        # steer the live run; picked up at the next step
        await steer.push_steer(rid, body.text)
        ack = await chat_repo.create(s, rid, "assistant", "Got it. Steering the run now.")
        await s.commit()
        await bus.publish_json(chat_channel(rid), {"id": ack.id, "runId": rid, "role": "assistant",
                                                   "text": ack.text, "options": None, "ts": ack.ts})
        return schema
    # run inactive; read-only assistant answers
    asyncio.create_task(_answer_chat(rid, body.text))
    return schema


async def _answer_chat(rid: str, text: str) -> None:
    from redcell_core.engine.assistant import answer_run
    try:
        result = await answer_run(rid, text)
        reply = result.get("text") or "(no response)"
        async with session_scope() as s:
            m = await chat_repo.create(s, rid, "assistant", reply)
            payload = {"id": m.id, "runId": rid, "role": "assistant", "text": reply,
                       "options": None, "ts": m.ts}
        await bus.publish_json(chat_channel(rid), payload)
        # operator asked for action; hand off to the orchestrator and reopen the run
        if result.get("kind") == "continue":
            await steer.push_steer(rid, result.get("instruction") or text)
            async with session_scope() as s:
                await runs_repo.set_status(s, rid, "running")
            await queue.enqueue("run_engagement", rid)
    except Exception:
        pass
