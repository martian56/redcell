"""Write the report prose with the engagement's LLM. Returns a structured dict;
all output is humanized (see text.py)."""

from __future__ import annotations

import json
from typing import Any

from .text import humanize

_SYSTEM = (
    "You are a senior penetration tester writing the narrative for a professional, client-facing "
    "engagement report. Write in clear, direct, humanized professional English.\n\n"
    "HARD STYLE RULES (a human editor will reject the report otherwise):\n"
    "- Never use em-dashes or en-dashes. Use commas, periods, or parentheses.\n"
    "- Never use smart/curly quotes; use straight quotes.\n"
    "- Do not use AI-tell phrases: no 'delve', 'it is important to note', 'in today's ever-evolving', "
    "'furthermore', 'moreover', 'leverage' as filler, 'robust', 'seamless', 'navigate the complexities', "
    "'testament to', 'unlock', 'realm', 'landscape'.\n"
    "- Active voice, concrete, concise. No marketing fluff. Reference findings by their real titles and "
    "affected locations. Write the way an experienced consultant writes for a technical client.\n\n"
    "Return ONLY valid JSON, no markdown fences, matching exactly this schema:\n"
    "{\n"
    '  "executive_summary": "2-4 short paragraphs for a non-technical executive: what was tested, the '
    'headline risk, and the overall security posture.",\n'
    '  "overview": "1-2 paragraphs on the engagement approach and what the team did.",\n'
    '  "methodology": "1 paragraph describing the methodology (recon, mapping, exploitation, '
    'post-exploitation) referencing PTES and OWASP WSTG where relevant.",\n'
    '  "posture": "1 short paragraph summarizing overall risk posture.",\n'
    '  "recommendations": ["prioritized strategic recommendation", "..."],\n'
    '  "findings": {"<finding_id>": {"impact": "business/technical impact in 1-3 sentences", '
    '"remediation": "concrete remediation steps in 1-4 sentences"}}\n'
    "}\n"
    "Provide a findings entry for every finding id given. Keep each field tight."
)


def _finding_brief(f) -> dict:
    tail = ((f.evidence_response or f.evidence_request or "") or "")[:400]
    return {
        "id": f.id, "title": f.title, "severity": f.severity, "cvss": f.cvss,
        "cwe": f.cwe, "location": f.location, "status": f.status,
        "existing_remediation": (f.remediation or "")[:400], "evidence": tail,
    }


def _fallback(session, findings) -> dict:
    """Deterministic prose when no LLM key is configured."""
    n = len(findings)
    crit = sum(1 for f in findings if f.severity == "critical")
    high = sum(1 for f in findings if f.severity == "high")
    return {
        "executive_summary": humanize(
            f"This report covers the security assessment of {session.name} for {session.client}. "
            f"The engagement identified {n} findings, including {crit} critical and {high} high severity "
            f"issues. Remediation of the high and critical items should be prioritized."),
        "overview": humanize(
            "The team enumerated the in-scope targets, mapped the attack surface, and validated "
            "exploitable conditions. Findings below are recorded with evidence and remediation guidance."),
        "methodology": humanize(
            "Testing followed a standard methodology covering reconnaissance, surface mapping, "
            "exploitation, and post-exploitation, aligned with PTES and the OWASP Web Security Testing "
            "Guide."),
        "posture": humanize(
            "Overall posture reflects the severity distribution of the findings recorded in this report."),
        "recommendations": [humanize("Prioritize remediation of critical and high severity findings."),
                            humanize("Re-test after fixes to confirm closure.")],
        "findings": {f.id: {"impact": humanize(f"See finding: {f.title}."),
                            "remediation": humanize(f.remediation or "Apply standard remediation for this issue class.")}
                     for f in findings},
    }


async def write_narrative(llm, session, findings, hosts, loot, max_findings: int = 60) -> dict:
    if llm is None:
        return _fallback(session, findings)
    subset = findings[:max_findings]
    payload = {
        "session": {"name": session.name, "client": session.client,
                    "scope": session.scope or [], "targets": session.targets or [],
                    "roe": session.roe or "", "kind": session.kind},
        "counts": {sev: sum(1 for f in findings if f.severity == sev)
                   for sev in ("critical", "high", "medium", "low", "info")},
        "findings": [_finding_brief(f) for f in subset],
        "hosts": [{"host": h.host, "ip": h.ip, "tech": h.tech or []} for h in hosts[:40]],
        "loot": [{"kind": x.kind, "label": x.label, "source": x.source} for x in loot[:40]],
    }
    messages = [
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": "Engagement data:\n" + json.dumps(payload, default=str)},
    ]
    try:
        out = await llm.complete(messages)
        content = (out.get("content") or "").strip()
        if content.startswith("```"):
            content = content.strip("`")
            content = content[content.find("{"):content.rfind("}") + 1]
        data = json.loads(content)
    except Exception:
        return _fallback(session, findings)

    def h(v: Any) -> Any:
        if isinstance(v, str):
            return humanize(v)
        if isinstance(v, list):
            return [h(x) for x in v]
        if isinstance(v, dict):
            return {k: h(x) for k, x in v.items()}
        return v

    data = h(data)
    # Guarantee every finding has an entry.
    data.setdefault("findings", {})
    for f in findings:
        data["findings"].setdefault(f.id, {
            "impact": humanize(f"Impact relates to: {f.title}."),
            "remediation": humanize(f.remediation or "Apply standard remediation for this issue class."),
        })
    return data
