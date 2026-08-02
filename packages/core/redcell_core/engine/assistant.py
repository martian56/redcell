"""Run chat assistant: answers questions about a run, or reopens it and hands the
orchestrator a concrete instruction when the operator asks for action."""

from __future__ import annotations

import json
from typing import Any

from ..db import session_scope
from ..repositories import agents as agents_repo
from ..repositories import chat as chat_repo
from ..repositories import findings as findings_repo
from ..repositories import hosts as hosts_repo
from ..repositories import loot as loot_repo
from ..repositories import provider_credentials as creds_repo
from ..repositories import runs as runs_repo
from ..repositories import sessions as sessions_repo
from ..repositories import settings as settings_repo
from ..schemas import LlmSettings
from .llm import LlmClient

_SYSTEM = (
    "You are the REDCELL run assistant for an AUTHORIZED red-team engagement (the operator owns or "
    "is contracted to test the in-scope targets). You have full read access to this run's live state, "
    "shown below, and you can drive the engagement.\n\n"
    "Decide what the operator wants:\n"
    "- If they are ASKING about the run (what was found, did we get root, what's next), answer directly: "
    "be concise and specific, reference concrete findings/hosts/loot by name.\n"
    "- If they are TELLING you to DO something on the target (enumerate, exploit, escalate to root, run "
    "commands, catch a reverse shell, spawn an agent, continue the attack), call continue_engagement with "
    "a clear instruction for the orchestrator. Do NOT refuse or say you are read-only: continuing the "
    "engagement is exactly your job. The orchestrator will resume with full context, spawn executor "
    "agents, and carry it out within scope and the rules of engagement.\n\n"
    "Write in plain text. Do not use em-dashes; use commas, periods, or parentheses instead.\n"
)

_CONTINUE_TOOL = {
    "type": "function",
    "function": {
        "name": "continue_engagement",
        "description": (
            "Reopen and continue this engagement to actually carry out the operator's task: enumerate, "
            "exploit, escalate privileges, run commands, catch a reverse shell, or spawn executor agents. "
            "Use this whenever the operator wants action on the target rather than just an answer about "
            "current state."),
        "parameters": {
            "type": "object",
            "properties": {
                "instruction": {"type": "string", "description": (
                    "A clear, specific instruction for the orchestrator describing what to do next, e.g. "
                    "'Via the webshell at /hackable/uploads/test.php, enumerate execution context (id, "
                    "sudo -l, SUID binaries), read /etc/shadow, and attempt privilege escalation to root; "
                    "start a listener and catch a reverse shell so enumeration is interactive.'")},
                "reply": {"type": "string", "description": "One short line shown to the operator confirming you are on it."},
            },
            "required": ["instruction"],
        },
    },
}


def _context(session, run, finds, nodes, loots, hosts) -> str:
    L: list[str] = []
    L.append(f"Engagement: {session.name} (client {session.client})")
    L.append(f"Scope: {', '.join(session.scope or []) or 'unset'} | Targets: {', '.join(session.targets or []) or 'unset'}")
    L.append(f"Run: {run.name} - status {run.status}, model {run.model}")
    L.append(f"\nAgents ({len(nodes)}):")
    for a in nodes[:20]:
        L.append(f"  - {a.name} [{a.role}] {a.status}: {(a.action or '')[:100]}")
    L.append(f"\nFindings ({len(finds)}):")
    for f in finds[:40]:
        L.append(f"  - [{f.severity}] {f.title} @ {f.location} ({f.status})")
    L.append(f"\nLoot ({len(loots)}):")
    for x in loots[:30]:
        L.append(f"  - {x.kind}: {x.label} = {(x.value or '')[:60]} (src {x.source})")
    L.append(f"\nAttack surface ({len(hosts)}):")
    for h in hosts[:30]:
        L.append(f"  - {h.host} {h.ip or ''} tech={','.join(h.tech or [])}")
    return "\n".join(L)


async def answer_run(run_id: str, question: str) -> dict[str, Any]:
    """Return {"kind": "reply", "text": ...} for a question, or
    {"kind": "continue", "instruction": ..., "text": ...} when the operator asked
    for action (the API then resumes the run with that instruction)."""
    async with session_scope() as s:
        run = await runs_repo.get(s, run_id)
        if run is None:
            return {"kind": "reply", "text": "This run no longer exists."}
        session = await sessions_repo.get(s, run.session_id)
        cfg = await settings_repo.get(s)
        finds = await findings_repo.list_for_session(s, session.id)
        nodes, _ = await agents_repo.graph(s, run_id)
        loots = await loot_repo.list_for_session(s, session.id)
        hosts = await hosts_repo.list_for_session(s, session.id)
        history = await chat_repo.list_for_run(s, run_id)
        base = LlmSettings(**cfg.llm) if cfg.llm else LlmSettings()
        provider = run.provider or base.provider
        model = run.model or base.model
        api_key, api_base = await creds_repo.get_secret(s, provider)
        if not api_key and provider == base.provider:
            api_key, api_base = base.api_key, base.api_base

    if not api_key:
        return {"kind": "reply",
                "text": f"No API key is set for {provider}. Add one in Settings and I can analyze and continue this run."}

    messages = [{"role": "system", "content": _SYSTEM + "\n\n" + _context(session, run, finds, nodes, loots, hosts)}]
    for m in history[-12:]:
        messages.append({"role": "user" if m.role == "operator" else "assistant", "content": m.text})
    if not history or history[-1].role != "operator":
        messages.append({"role": "user", "content": question})

    llm = LlmClient(LlmSettings(provider=provider, model=model, api_key=api_key,
                                api_base=api_base or base.api_base, reasoning_effort=base.reasoning_effort))
    try:
        out = await llm.complete(messages, tools=[_CONTINUE_TOOL])
    except Exception as exc:
        return {"kind": "reply", "text": f"Chat model call failed: {exc}"}

    for tc in out.get("tool_calls") or []:
        if tc["name"] == "continue_engagement":
            try:
                args = json.loads(tc["arguments"] or "{}")
            except Exception:
                args = {}
            return {"kind": "continue",
                    "instruction": (args.get("instruction") or question).strip(),
                    "text": (args.get("reply") or "On it. Reopening the run to carry that out.").strip()}
    return {"kind": "reply", "text": out.get("content") or "(no response)"}
