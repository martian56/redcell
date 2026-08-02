"""Map findings to SARIF 2.1.0 for CI and security tooling."""

from __future__ import annotations

_LEVEL = {"critical": "error", "high": "error", "medium": "warning", "low": "note", "info": "note"}


def build_sarif(findings) -> dict:
    rules: dict[str, dict] = {}
    results = []
    for f in findings:
        rule_id = f.cwe or f.title
        if rule_id not in rules:
            rules[rule_id] = {
                "id": rule_id,
                "name": (f.cwe or f.title)[:120],
                "shortDescription": {"text": f.title},
                "defaultConfiguration": {"level": _LEVEL.get(f.severity, "warning")},
                "properties": {"security-severity": str(f.cvss or 0.0), "cwe": f.cwe or ""},
            }
        results.append({
            "ruleId": rule_id,
            "level": _LEVEL.get(f.severity, "warning"),
            "message": {"text": f"{f.title} ({f.severity}, CVSS {f.cvss})"},
            "locations": [{
                "physicalLocation": {
                    "artifactLocation": {"uri": f.location or "unspecified"},
                }
            }],
            "properties": {"severity": f.severity, "cvss": f.cvss, "status": f.status,
                           "cwe": f.cwe or "", "findingId": f.id},
        })
    return {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [{
            "tool": {"driver": {
                "name": "REDCELL",
                "informationUri": "https://redcell.local",
                "rules": list(rules.values()),
            }},
            "results": results,
        }],
    }
