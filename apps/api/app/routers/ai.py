"""AI endpoints not tied to a run."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends
from redcell_core.engine.llm import LlmClient
from redcell_core.repositories import provider_credentials as creds_repo
from redcell_core.repositories import settings as settings_repo
from redcell_core.schemas import DraftChatInput, DraftChatOutput, LlmSettings, SessionProposal
from redcell_core.security import current_user
from sqlalchemy.ext.asyncio import AsyncSession

from ..deps import db
from ..ratelimit import rate_limit

router = APIRouter(tags=["ai"], dependencies=[Depends(current_user)])

_SYSTEM = (
    "You are a red-team engagement planner helping an operator scope a NEW authorized "
    "assessment. Ask focused questions about the target, the in-scope domains/IPs, and the "
    "rules of engagement. Keep replies short and practical. As soon as you have a reasonable "
    "picture, call propose_session with your best draft (the operator can edit it). Refine the "
    "proposal as the conversation continues. Include a short brief: a few sentences capturing the "
    "objectives, constraints, and any specifics the operator gave (target type, what to focus on, "
    "what to skip). The brief is handed to the agents that run the engagement. Only in-scope, "
    "authorized targets. Write in plain text; do not use em-dashes (use commas, periods, or "
    "parentheses instead)."
)

_PROPOSE_TOOL = [{
    "type": "function",
    "function": {
        "name": "propose_session",
        "description": "Propose (or update) the draft session fields for the operator to review.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Short engagement name."},
                "client": {"type": "string", "description": "Client / org name."},
                "scope": {"type": "array", "items": {"type": "string"}, "description": "In-scope domains, wildcards, or CIDRs."},
                "targets": {"type": "array", "items": {"type": "string"}, "description": "Concrete target URLs or IPs."},
                "brief": {"type": "string", "description": "A few sentences: objectives, constraints, and specifics for the agents running the engagement."},
            },
        },
    },
}]


@router.post("/sessions/draft/chat", response_model=DraftChatOutput,
             dependencies=[Depends(rate_limit("draft-chat", 20, 60))])
async def draft_chat(body: DraftChatInput, s: AsyncSession = Depends(db)) -> DraftChatOutput:
    cfg = await settings_repo.get(s)
    base = LlmSettings(**cfg.llm) if cfg.llm else LlmSettings()
    provider = body.provider or base.provider
    model = body.model or base.model
    api_key, api_base = await creds_repo.get_secret(s, provider)
    # Legacy single key belongs to the default provider only.
    if not api_key and provider == base.provider:
        api_key, api_base = base.api_key, base.api_base
    if not api_key:
        return DraftChatOutput(
            reply=f"No API key is set for {provider}. Add one in Settings, then we can plan the engagement here.",
            proposal=None,
        )

    llm = LlmClient(LlmSettings(provider=provider, model=model, api_key=api_key,
                                api_base=api_base or base.api_base, reasoning_effort=base.reasoning_effort))
    messages = [{"role": "system", "content": _SYSTEM}]
    messages += [{"role": m.role, "content": m.content} for m in body.messages]

    try:
        resp = await llm.complete(messages, tools=_PROPOSE_TOOL)
    except Exception as exc:
        return DraftChatOutput(reply=f"Model call failed: {exc}", proposal=None)

    reply = resp.get("content") or ""
    proposal = None
    for tc in resp.get("tool_calls") or []:
        if tc["name"] == "propose_session":
            args = tc["arguments"]
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except Exception:
                    args = {}
            proposal = SessionProposal(
                name=args.get("name"), client=args.get("client"),
                scope=args.get("scope") or [], targets=args.get("targets") or [],
                brief=args.get("brief"),
            )
    if proposal and not reply:
        reply = "I've drafted the session on the right. Review and adjust, or tell me what to change."
    return DraftChatOutput(reply=reply or "(no response)", proposal=proposal)
