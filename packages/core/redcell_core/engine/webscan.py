"""Web-tool command builders and output parsers: nuclei (-> findings with CVSS)
and ffuf/gobuster directory-vhost discovery (-> structured paths). Pure and
unit-testable; the runner runs the commands and records or returns the results."""

from __future__ import annotations

import json
import re
import shlex
from typing import Any

DEFAULT_WORDLIST = "/usr/share/wordlists/dirb/common.txt"
_MATCH_CODES = "200,204,301,302,307,401,403,405"


# ---- nuclei -> findings ----

def build_nuclei_command(target: str, severity: str | None = None) -> str:
    parts = ["nuclei", "-u", target, "-jsonl", "-silent", "-nc"]
    if severity:
        parts += ["-severity", severity]
    return " ".join(shlex.quote(p) for p in parts)


def parse_nuclei_jsonl(output: str, target: str = "") -> list[dict[str, Any]]:
    """One JSON object per line. Map each to a finding dict for _record_finding."""
    findings: list[dict[str, Any]] = []
    for line in output.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        info = obj.get("info") or {}
        classification = info.get("classification") or {}
        cwe_ids = classification.get("cwe-id") or []
        finding = {
            "title": info.get("name") or obj.get("template-id") or "nuclei finding",
            "severity": (info.get("severity") or "info").lower(),
            "location": obj.get("matched-at") or obj.get("host") or target,
            "cwe": (cwe_ids[0].upper() if cwe_ids else "").replace("CWE-CWE-", "CWE-"),
            "status": "candidate",
        }
        score = classification.get("cvss-score")
        if isinstance(score, (int, float)) and score > 0:
            finding["cvss"] = float(score)
        findings.append(finding)
    return findings


# ---- ffuf / gobuster -> discovered paths ----

def build_ffuf_command(url: str, wordlist: str | None = None, vhost: bool = False) -> str:
    """ffuf writing a JSON report to a temp file, then cat it, so parsing gets clean
    JSON without ffuf's progress noise on stdout."""
    wl = wordlist or DEFAULT_WORDLIST
    out = "/tmp/rc-ffuf.json"
    if vhost:
        base = url.rstrip("/")
        host = re.sub(r"^https?://", "", base)
        target = ["-u", base, "-H", f"Host: FUZZ.{host}"]
    else:
        target = ["-u", url.rstrip("/") + "/FUZZ"]
    parts = ["ffuf", *target, "-w", wl, "-mc", _MATCH_CODES, "-of", "json", "-o", out, "-s"]
    cmd = " ".join(shlex.quote(p) for p in parts)
    return f"{cmd} >/dev/null 2>&1; cat {out}"


def parse_ffuf_json(output: str) -> list[dict[str, Any]]:
    """ffuf JSON report: {results: [{url, status, length, ...}]}."""
    text = output.strip()
    start = text.find("{")
    if start < 0:
        return []
    try:
        doc = json.loads(text[start:])
    except json.JSONDecodeError:
        return []
    out: list[dict[str, Any]] = []
    for r in doc.get("results") or []:
        out.append({
            "url": r.get("url", ""),
            "status": r.get("status", 0),
            "length": r.get("length", 0),
        })
    return out


def parse_gobuster_text(output: str) -> list[dict[str, Any]]:
    """gobuster dir text lines like `/admin (Status: 301) [Size: 178]`."""
    out: list[dict[str, Any]] = []
    for line in output.splitlines():
        m = re.match(r"\s*(\S+)\s+\(Status:\s*(\d+)\)(?:\s*\[Size:\s*(\d+)\])?", line)
        if m:
            out.append({"path": m.group(1), "status": int(m.group(2)),
                        "length": int(m.group(3) or 0)})
    return out
