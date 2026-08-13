"""Orchestrate report generation: gather the whole session, write the humanized
narrative with the engagement's model, render PDF/JSON/SARIF, store each artifact,
and flip the report to ready (or failed)."""

from __future__ import annotations

import asyncio
import json
import re

from ...config import settings
from ...db import session_scope
from ...repositories import files as files_repo
from ...repositories import findings as findings_repo
from ...repositories import hosts as hosts_repo
from ...repositories import ids
from ...repositories import loot as loot_repo
from ...repositories import provider_credentials as creds_repo
from ...repositories import reports as reports_repo
from ...repositories import sessions as sessions_repo
from ...repositories import settings as settings_repo
from ...schemas import LlmSettings, ReportSettings
from ...storage import storage
from .narrative import write_narrative
from .pdf import build_pdf
from .sarif import build_sarif

_CT = {"pdf": "application/pdf", "json": "application/json", "sarif": "application/sarif+json"}
_EXT = {"pdf": "pdf", "json": "json", "sarif": "sarif.json"}


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (text or "report").lower()).strip("-")[:50] or "report"


def select_report_findings(findings) -> list:
    """Findings that belong in a client report: dismissed ones (false positives
    and merged duplicates) are excluded; everything else is kept."""
    return [f for f in findings if f.status != "dismissed"]


def _findings_json(findings) -> list:
    return [{
        "id": f.id, "title": f.title, "severity": f.severity, "cvss": f.cvss, "cwe": f.cwe,
        "location": f.location, "status": f.status, "remediation": f.remediation,
        "evidenceRequest": f.evidence_request, "evidenceResponse": f.evidence_response,
    } for f in findings]


async def generate_report(report_id: str) -> None:
    try:
        async with session_scope() as s:
            report = await reports_repo.get(s, report_id)
            if report is None:
                return
            session = await sessions_repo.get(s, report.session_id)
            findings = select_report_findings(await findings_repo.list_for_session(s, report.session_id))
            hosts = await hosts_repo.list_for_session(s, report.session_id)
            loot = await loot_repo.list_for_session(s, report.session_id)
            cfg = await settings_repo.get(s)
            base = LlmSettings(**cfg.llm) if cfg.llm else LlmSettings()
            brand = ReportSettings(**cfg.report) if cfg.report else ReportSettings()
            provider = session.provider or base.provider
            model = session.model or base.model
            api_key, api_base = await creds_repo.get_secret(s, provider)
            if not api_key and provider == base.provider:
                api_key, api_base = base.api_key, base.api_base
            formats = report.formats or ["pdf", "json", "sarif"]
            title = report.title
            sid = report.session_id

        llm = None
        if api_key:
            from ..llm import LlmClient
            llm = LlmClient(LlmSettings(provider=provider, model=model, api_key=api_key,
                                        api_base=api_base or base.api_base,
                                        reasoning_effort=base.reasoning_effort))

        narrative = await write_narrative(llm, session, findings, hosts, loot)
        generated_at = ids.now_iso()
        report_ref = "RC-" + report_id.replace("rep-", "")[:8].upper()

        artifacts: dict[str, str] = {}
        for fmt in formats:
            if fmt == "pdf":
                ctx = {
                    "title": title, "company": brand.company_name, "classification": brand.classification,
                    "contact": brand.contact, "logo_data_url": brand.logo_data_url,
                    "report_id": report_ref, "generated_at": generated_at, "session": session,
                    "findings": findings, "hosts": hosts, "loot": loot, "narrative": narrative,
                }
                data = await asyncio.to_thread(build_pdf, ctx)
            elif fmt == "json":
                data = json.dumps({
                    "reportId": report_ref, "title": title, "generatedAt": generated_at,
                    "client": session.client, "engagement": session.name,
                    "scope": session.scope or [], "targets": session.targets or [],
                    "narrative": narrative, "findings": _findings_json(findings),
                    "hosts": [{"host": h.host, "ip": h.ip, "tech": h.tech or []} for h in hosts],
                    "loot": [{"kind": x.kind, "label": x.label, "source": x.source} for x in loot],
                }, indent=2).encode()
            elif fmt == "sarif":
                data = json.dumps(build_sarif(findings), indent=2).encode()
            else:
                continue
            key = f"{sid}/{ids.new_id('f')}/{_slug(title)}.{_EXT[fmt]}"
            await storage.put(settings.bucket_reports, key, data, _CT[fmt])
            async with session_scope() as s:
                row = await files_repo.create(s, {
                    "session_id": sid, "bucket": settings.bucket_reports, "object_key": key,
                    "filename": f"{_slug(title)}.{_EXT[fmt]}", "kind": "report",
                    "content_type": _CT[fmt], "size": len(data), "visibility": "private",
                    "source": "report-generator",
                })
                artifacts[fmt] = row.id

        async with session_scope() as s:
            await reports_repo.update(s, report_id, {
                "status": "ready", "artifacts": artifacts,
                "file_id": artifacts.get("pdf"), "summary": narrative.get("executive_summary"),
                "error": None,
            })
    except Exception as exc:
        async with session_scope() as s:
            await reports_repo.update(s, report_id, {"status": "failed", "error": str(exc)[:500]})
        raise
