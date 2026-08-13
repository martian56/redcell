"""Unit tests for the structured tool integrations (issue #5): nmap/nuclei/ffuf/
gobuster parsers, command builders, and the runner dispatch that records hosts
and findings. No real tools or container."""

from redcell_core.engine.msf import build_msf_run, parse_msf_search, valid_module
from redcell_core.engine.nmap import build_nmap_command, parse_nmap_xml
from redcell_core.engine.runner import LiveRunner
from redcell_core.engine.webscan import (
    parse_ffuf_json,
    parse_gobuster_text,
    parse_nuclei_jsonl,
)

NMAP_XML = """<?xml version="1.0"?>
<nmaprun>
  <host>
    <status state="up"/>
    <address addr="10.0.0.5" addrtype="ipv4"/>
    <hostnames><hostname name="web.local"/></hostnames>
    <ports>
      <port protocol="tcp" portid="80"><state state="open"/><service name="http" product="nginx" version="1.18.0"/></port>
      <port protocol="tcp" portid="443"><state state="open"/><service name="https" product="nginx"/></port>
      <port protocol="tcp" portid="22"><state state="closed"/><service name="ssh"/></port>
    </ports>
  </host>
  <host>
    <status state="down"/>
    <address addr="10.0.0.6" addrtype="ipv4"/>
  </host>
</nmaprun>"""

NUCLEI_JSONL = (
    '{"template-id":"tech-detect","info":{"name":"nginx","severity":"info"},"host":"https://x","matched-at":"https://x"}\n'
    '{"template-id":"cve-x","info":{"name":"SQL Injection","severity":"high",'
    '"classification":{"cwe-id":["CWE-89"],"cvss-score":8.2}},"matched-at":"https://x/search"}\n'
)

FFUF_JSON = '{"results":[{"url":"https://x/admin","status":301,"length":178},{"url":"https://x/login","status":200,"length":540}]}'

GOBUSTER = "/admin (Status: 301) [Size: 178]\n/login (Status: 200) [Size: 540]\n"

MSF_SEARCH = """Matching Modules
================
   #  Name                                              Rank
   -  ----                                              ----
   0  exploit/multi/http/struts2_content_type_ognl      excellent
   1  auxiliary/scanner/http/apache_normalize_path_rce  normal
"""


class _Res:
    def __init__(self, output: str) -> None:
        self.output = output


class FakeBackend:
    def __init__(self, output: str = "") -> None:
        self.commands: list[str] = []
        self.output = output

    async def run(self, cmd: str, **kw):
        self.commands.append(cmd)
        return _Res(self.output)


# ---- parsers ----

def test_parse_nmap_xml():
    hosts = parse_nmap_xml(NMAP_XML)
    assert len(hosts) == 1  # the down host is excluded
    h = hosts[0]
    assert h["ip"] == "10.0.0.5"
    assert {p["port"] for p in h["ports"]} == {80, 443}  # closed port excluded
    assert any(p["version"] == "nginx 1.18.0" for p in h["ports"])


def test_parse_nmap_xml_tolerates_garbage():
    assert parse_nmap_xml("not xml") == []


def test_build_nmap_command_quotes_and_flags():
    cmd = build_nmap_command("10.0.0.5; rm -rf /", ports="80,443", service_detection=True, scripts=True)
    assert "-oX" in cmd and "-sV" in cmd and "-sC" in cmd and "-p" in cmd
    assert "'10.0.0.5; rm -rf /'" in cmd  # target quoted, injection neutralized


def test_parse_nuclei_jsonl():
    fs = parse_nuclei_jsonl(NUCLEI_JSONL)
    assert len(fs) == 2
    hi = next(f for f in fs if f["severity"] == "high")
    assert hi["cvss"] == 8.2 and hi["cwe"] == "CWE-89" and hi["location"] == "https://x/search"


def test_parse_ffuf_json():
    rs = parse_ffuf_json(FFUF_JSON)
    assert len(rs) == 2 and rs[0]["status"] == 301 and rs[0]["url"].endswith("/admin")


def test_parse_gobuster_text():
    rs = parse_gobuster_text(GOBUSTER)
    assert len(rs) == 2 and rs[0]["path"] == "/admin" and rs[0]["status"] == 301


def test_parse_msf_search():
    assert parse_msf_search(MSF_SEARCH) == [
        "exploit/multi/http/struts2_content_type_ognl",
        "auxiliary/scanner/http/apache_normalize_path_rce",
    ]


def test_valid_module():
    assert valid_module("auxiliary/scanner/http/http_version")
    assert not valid_module("../../etc/passwd")
    assert not valid_module("; ls")


def test_build_msf_run_quotes_script():
    cmd = build_msf_run("auxiliary/scanner/http/http_version", {"RHOSTS": "10.0.0.5"})
    assert "http_version" in cmd and "RHOSTS" in cmd and cmd.startswith("msfconsole -q -x ")


# ---- runner dispatch ----

def _runner(output=""):
    r = LiveRunner(bus=None, run_id="run-1")
    r.backend = FakeBackend(output)
    return r


async def test_run_nmap_records_hosts(monkeypatch):
    r = _runner(NMAP_XML)
    recorded: list[dict] = []

    async def fake_host(a):
        recorded.append(a)

    monkeypatch.setattr(r, "_record_host", fake_host)
    out = await r._run_nmap({"target": "10.0.0.5", "service_detection": True})
    assert out["ok"] and out["hosts_up"] == 1 and out["open_ports"] == 2
    assert recorded and recorded[0]["ip"] == "10.0.0.5" and recorded[0]["source"] == "nmap"
    assert any("-sV" in c for c in r.backend.commands)


async def test_run_nuclei_records_findings(monkeypatch):
    r = _runner(NUCLEI_JSONL)
    recorded: list[dict] = []

    async def fake_finding(a):
        recorded.append(a)

    monkeypatch.setattr(r, "_record_finding", fake_finding)
    out = await r._run_nuclei({"target": "https://x"})
    assert out["findings"] == 2
    assert any(f.get("cvss") == 8.2 for f in recorded)


async def test_run_web_discover_returns_paths():
    r = _runner(FFUF_JSON)
    out = await r._run_web_discover({"url": "https://x"})
    assert out["found"] == 2 and any(res["status"] == 301 for res in out["results"])


async def test_run_msf_search_parses_modules():
    r = _runner(MSF_SEARCH)
    out = await r._run_msf_search({"query": "struts"})
    assert out["count"] == 2
    assert "exploit/multi/http/struts2_content_type_ognl" in out["modules"]


async def test_run_msf_run_rejects_bad_module():
    r = _runner("done")
    assert "error" in await r._run_msf_run({"module": "; rm -rf /"})
    ok = await r._run_msf_run({"module": "auxiliary/scanner/http/http_version",
                               "options": {"RHOSTS": "10.0.0.5"}})
    assert ok["ok"] and any("RHOSTS" in c for c in r.backend.commands)


async def test_dispatch_toolset_unknown():
    r = _runner()
    assert "error" in await r._dispatch_toolset("nope", {})
