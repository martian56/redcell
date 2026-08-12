"""Unit tests for the report generators: the prose humanizer, the SARIF
exporter, and a smoke test of the PDF builder. All pure, no DB or infra."""

from types import SimpleNamespace

from redcell_core.engine.reporting.pdf import build_pdf
from redcell_core.engine.reporting.sarif import build_sarif
from redcell_core.engine.reporting.text import humanize

# ---- humanize: the style safety net (no em-dashes, smart quotes, ellipses) ----

def test_humanize_replaces_em_dash_with_comma():
    assert humanize("foo — bar") == "foo, bar"


def test_humanize_strips_every_typographic_tell():
    out = humanize("He said “hi” and ‘bye’… then left–fast•now")
    for ch in ("—", "–", "‘", "’", "“", "”", "…", "•"):
        assert ch not in out
    assert '"hi"' in out
    assert "'bye'" in out
    assert "..." in out


def test_humanize_handles_none_and_empty():
    assert humanize(None) == ""
    assert humanize("") == ""


def test_humanize_collapses_runs_of_spaces():
    assert humanize("a    b") == "a b"


# ---- SARIF export ----

def _finding(**kw):
    base = dict(id="finding-1", title="SQL Injection", severity="critical", cvss=9.8,
                location="/api/search", cwe="CWE-89", status="verified")
    base.update(kw)
    return SimpleNamespace(**base)


def test_sarif_top_level_shape():
    doc = build_sarif([_finding()])
    assert doc["version"] == "2.1.0"
    assert doc["$schema"].endswith("sarif-2.1.0.json")
    driver = doc["runs"][0]["tool"]["driver"]
    assert driver["name"] == "REDCELL"
    assert len(doc["runs"][0]["results"]) == 1


def test_sarif_maps_severity_to_level():
    findings = [
        _finding(id="f-c", cwe=None, title="c", severity="critical"),
        _finding(id="f-h", cwe=None, title="h", severity="high"),
        _finding(id="f-m", cwe=None, title="m", severity="medium"),
        _finding(id="f-l", cwe=None, title="l", severity="low"),
        _finding(id="f-i", cwe=None, title="i", severity="info"),
        _finding(id="f-x", cwe=None, title="x", severity="bogus"),
    ]
    levels = {r["properties"]["severity"]: r["level"] for r in build_sarif(findings)["runs"][0]["results"]}
    assert levels["critical"] == "error"
    assert levels["high"] == "error"
    assert levels["medium"] == "warning"
    assert levels["low"] == "note"
    assert levels["info"] == "note"
    assert levels["bogus"] == "warning"  # unknown severity falls back to warning


def test_sarif_dedupes_rules_by_cwe():
    findings = [_finding(id="a", cwe="CWE-89"), _finding(id="b", cwe="CWE-89"),
                _finding(id="c", cwe="CWE-79")]
    doc = build_sarif(findings)
    assert len(doc["runs"][0]["tool"]["driver"]["rules"]) == 2  # CWE-89 collapses to one rule
    assert len(doc["runs"][0]["results"]) == 3


def test_sarif_falls_back_to_title_and_unspecified_location():
    doc = build_sarif([_finding(cwe=None, title="Open Redirect", location="")])
    result = doc["runs"][0]["results"][0]
    assert result["ruleId"] == "Open Redirect"
    uri = result["locations"][0]["physicalLocation"]["artifactLocation"]["uri"]
    assert uri == "unspecified"
    rule = doc["runs"][0]["tool"]["driver"]["rules"][0]
    assert rule["properties"]["security-severity"] == "9.8"


# ---- PDF builder (smoke) ----

def _session():
    return SimpleNamespace(client="Acme", name="Acme Q3 Pentest",
                           targets=["https://acme.test"], scope=["*.acme.test"], roe="no DoS")


def _narrative(with_findings=True):
    n = {
        "executive_summary": "One high-severity issue was found.",
        "posture": "Overall posture is fair.",
        "overview": "We tested the public application.",
        "methodology": "OWASP-aligned black-box testing.",
        "recommendations": ["Fix the SQL injection first."],
    }
    if with_findings:
        n["findings"] = {"finding-1": {"impact": "Full database read.", "remediation": "Parameterize queries."}}
    return n


def _base_ctx(findings, narrative, **extra):
    ctx = {
        "title": "Acme Penetration Test",
        "company": "REDCELL",
        "classification": "CONFIDENTIAL",
        "report_id": "RPT-001",
        "generated_at": "2026-08-12T10:00:00Z",
        "contact": "ops@redcell.local",
        "session": _session(),
        "findings": findings,
        "narrative": narrative,
    }
    ctx.update(extra)
    return ctx


def test_build_pdf_produces_a_valid_pdf():
    finding = SimpleNamespace(
        id="finding-1", title="SQL Injection", severity="high", cvss=8.2,
        location="/api/search?q=", cwe="CWE-89", status="verified",
        evidence_request="GET /api/search?q=1", evidence_response="error: SQL syntax near '1'",
        remediation="Use parameterized queries.")
    ctx = _base_ctx(
        [finding], _narrative(),
        hosts=[SimpleNamespace(host="acme.test", ip="203.0.113.5", tech=["nginx"], source="target")],
        loot=[SimpleNamespace(kind="credential", label="admin", value="s3cret", source="dump")])
    data = build_pdf(ctx)
    assert isinstance(data, bytes)
    assert data[:5] == b"%PDF-"
    assert len(data) > 1000


def test_build_pdf_with_no_findings_still_renders():
    data = build_pdf(_base_ctx([], _narrative(with_findings=False)))
    assert data[:5] == b"%PDF-"
    assert len(data) > 1000
