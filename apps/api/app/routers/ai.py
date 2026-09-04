"""AI endpoints not tied to a run."""

from __future__ import annotations

import json
import re
from urllib.parse import urlparse

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
    "assessment. Keep replies short and practical. On every turn, once the operator has named "
    "any target, call propose_session with your best draft and fill every field you can infer: "
    "a short name, the client if stated, kind (code for a git repo or local code review, "
    "otherwise network), scope (in-scope domains, wildcards, or CIDRs), targets (concrete URLs "
    "or IPs), rules of engagement if given, and a short brief. Prefer drafting over asking; the "
    "operator can edit anything. Never leave name, scope, or targets empty when the operator has "
    "given a domain, URL, or IP. Refine the proposal as the conversation continues. The brief is "
    "a few sentences of objectives, constraints, and specifics handed to the agents that run the "
    "engagement. Only in-scope, authorized targets. Write in plain text; do not use em-dashes "
    "(use commas, periods, or parentheses instead)."
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
                "kind": {"type": "string", "enum": ["network", "code"], "description": "network for external, infra, or web testing; code for a source code review."},
                "source": {"type": "string", "description": "For a code review: the git URL or local folder path."},
                "scope": {"type": "array", "items": {"type": "string"}, "description": "In-scope domains, wildcards, or CIDRs."},
                "targets": {"type": "array", "items": {"type": "string"}, "description": "Concrete target URLs or IPs."},
                "roe": {"type": "string", "description": "Rules of engagement: testing window, exclusions, no-DoS, and similar constraints."},
                "brief": {"type": "string", "description": "A few sentences: objectives, constraints, and specifics for the agents running the engagement."},
            },
        },
    },
}]

_URL_RE = re.compile(r"https?://[^\s<>()\"'`]+", re.I)
_GIT_RE = re.compile(r"(?:https?://)?(?:github\.com|gitlab\.com|bitbucket\.org)/[^\s<>()\"'`]+|[^\s<>()\"'`]+\.git", re.I)
_CIDR_RE = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}(?:/\d{1,2})?\b")
_DOMAIN_RE = re.compile(r"\b(?:\*\.)?(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}\b", re.I)
_CODE_HOSTS = {"github.com", "gitlab.com", "bitbucket.org"}


def _uniq(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for raw in items:
        it = raw.strip().rstrip(".,;)")
        if it and it not in seen:
            seen.add(it)
            out.append(it)
    return out


def _name_from(host: str) -> str | None:
    labels = [x for x in host.lstrip("*.").strip().lower().split(".") if x]
    if not labels:
        return None
    sld = labels[-2] if len(labels) >= 2 else labels[0]
    return f"{sld.capitalize()} assessment"


def enrich_proposal(proposal: SessionProposal | None, operator_text: str) -> SessionProposal | None:
    """Fill any fields the model left blank from targets found in the operator's text."""
    text = operator_text or ""
    urls = _uniq(_URL_RE.findall(text))
    cidrs = _uniq(_CIDR_RE.findall(text))
    git = _GIT_RE.search(text)
    domains = [d for d in _uniq(_DOMAIN_RE.findall(text)) if d.lower() not in _CODE_HOSTS]

    name = client = brief = source = roe = kind = None
    scope: list[str] = []
    targets: list[str] = []
    if proposal is not None:
        name, client, brief = proposal.name, proposal.client, proposal.brief
        source, roe, kind = proposal.source, proposal.roe, proposal.kind
        scope, targets = list(proposal.scope), list(proposal.targets)

    if kind not in ("code", "network"):
        kind = "code" if git else ("network" if (domains or cidrs or urls) else None)

    if kind == "code":
        if not source:
            source = git.group(0) if git else (urls[0] if urls else None)
    elif kind == "network":
        if not scope:
            scope = _uniq(domains + cidrs)
        if not targets:
            targets = urls or ([f"https://{domains[0]}"] if domains else [])

    if not name:
        host = domains[0] if domains else (urlparse(urls[0]).hostname if urls else None)
        if host:
            name = _name_from(host)

    if not any([name, client, brief, source, roe, scope, targets]) and kind is None:
        return None
    return SessionProposal(
        name=name, client=client, kind=kind, source=source,
        scope=scope, targets=targets, roe=roe, brief=brief,
    )


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
                kind=args.get("kind"), source=args.get("source"),
                scope=args.get("scope") or [], targets=args.get("targets") or [],
                roe=args.get("roe"), brief=args.get("brief"),
            )

    operator_text = "\n".join(m.content for m in body.messages if m.role == "user")
    proposal = enrich_proposal(proposal, operator_text)
    if proposal and not reply:
        reply = "I've drafted the session on the right. Review and adjust, or tell me what to change."
    return DraftChatOutput(reply=reply or "(no response)", proposal=proposal)
