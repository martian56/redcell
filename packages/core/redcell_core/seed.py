"""Seeding. `bootstrap` sets up the minimum a fresh install needs (buckets,
provider catalog, admin user, default settings). `demo` adds the ACME/Globex/
Initech demo data. `unseed` wipes Postgres app data and empties the buckets."""

from __future__ import annotations

import datetime as dt

from sqlalchemy import delete

from .config import settings
from .db import session_scope
from .models import (
    Agent, AgentEdge, AppSettings, ChatMessage, File, Finding, Host, Listener, Loot,
    Provider, ProviderCredential, Proxy, ProxyEntry, Report, Run, Server, Session, Shell, User,
)
from .repositories import ids
from .repositories import providers as providers_repo
from .repositories import settings as settings_repo
from .repositories import users as users_repo
from .schemas import Settings as SettingsSchema
from .security import hash_password
from .storage import storage

PROVIDERS = [
    {"id": "openai", "label": "OpenAI", "models": ["gpt-5.6", "gpt-5.5", "gpt-5.4-mini", "gpt-5.4", "o4-mini"], "needs_key": True},
    {"id": "anthropic", "label": "Anthropic", "models": ["claude-opus-5", "claude-sonnet-5", "claude-haiku-4-5"], "needs_key": True},
    {"id": "google", "label": "Google Gemini", "models": ["gemini-3.1-pro", "gemini-3.6-flash", "gemini-3.1-flash-lite"], "needs_key": True},
    {"id": "xai", "label": "xAI (Grok)", "models": ["grok-5", "grok-4-mini", "grok-code-2"], "needs_key": True},
    {"id": "deepseek", "label": "DeepSeek", "models": ["deepseek-v4-pro", "deepseek-v4-flash", "deepseek-r2"], "needs_key": True},
    {"id": "moonshot", "label": "Moonshot (Kimi)", "models": ["kimi-k3", "kimi-k2.7-code"], "needs_key": True},
    {"id": "zhipu", "label": "Zhipu (GLM)", "models": ["glm-5.2", "glm-4.6", "glm-4.5-air"], "needs_key": True},
    {"id": "qwen", "label": "Alibaba Qwen", "models": ["qwen3.8-max", "qwen3.5-flash", "qwen3-coder"], "needs_key": True},
    {"id": "mistral", "label": "Mistral", "models": ["mistral-large-3", "mistral-small-3", "codestral-2"], "needs_key": True},
    {"id": "groq", "label": "Groq (fast)", "models": ["llama-4.1-70b", "llama-4.1-8b", "mixtral-8x22b"], "needs_key": True},
    {"id": "together", "label": "Together AI", "models": ["meta-llama/Llama-4-70b", "Qwen/Qwen3-72b", "deepseek-ai/DeepSeek-V4"], "needs_key": True},
    {"id": "fireworks", "label": "Fireworks AI", "models": ["llama-v4-70b", "qwen3-72b", "deepseek-v4"], "needs_key": True},
    {"id": "cohere", "label": "Cohere", "models": ["command-r2", "command-r2-plus"], "needs_key": True},
    {"id": "perplexity", "label": "Perplexity", "models": ["sonar-pro", "sonar-reasoning"], "needs_key": True},
    {"id": "deepinfra", "label": "DeepInfra", "models": ["meta-llama/Llama-4-70b", "Qwen/Qwen3-72b"], "needs_key": True},
    {"id": "openrouter", "label": "OpenRouter", "models": [
        "anthropic/claude-opus-5", "anthropic/claude-sonnet-5", "anthropic/claude-haiku-4-5",
        "openai/gpt-5.6", "openai/gpt-5.5", "openai/o4-mini",
        "google/gemini-3.1-pro", "google/gemini-3.6-flash",
        "x-ai/grok-5", "x-ai/grok-code-2",
        "deepseek/deepseek-v4-pro", "deepseek/deepseek-r2",
        "moonshotai/kimi-k3", "moonshotai/kimi-k2.7-code",
        "z-ai/glm-5.2", "z-ai/glm-4.6",
        "qwen/qwen3.8-max", "qwen/qwen3-coder",
        "mistralai/mistral-large-3", "mistralai/codestral-2",
        "meta-llama/llama-4-70b", "meta-llama/llama-4-8b",
        "nvidia/nemotron-4-340b", "cohere/command-r2", "perplexity/sonar-pro",
        "microsoft/phi-5", "amazon/nova-pro",
    ], "needs_key": True},
    {"id": "ollama", "label": "Ollama (local)", "models": ["qwen3", "llama3.3", "deepseek-r1", "phi4", "glm-4"], "needs_key": False},
    {"id": "custom", "label": "Custom (OpenAI-compatible)", "models": [], "needs_key": True},
]


def _mins_ago(minutes: int) -> str:
    return (dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=minutes)).isoformat()


async def bootstrap() -> None:
    await storage.ensure_buckets()
    async with session_scope() as s:
        await providers_repo.upsert_many(s, PROVIDERS)
        if await users_repo.get_by_username(s, settings.admin_username) is None:
            await users_repo.create(s, settings.admin_username, hash_password(settings.admin_password), "admin")
        await settings_repo.get(s)  # materialize default app_settings row


async def demo() -> None:
    async with session_scope() as s:
        s.add(Session(id="ses-acme", name="ACME External Q3", client="ACME Corp",
                      scope=["*.acme-corp.io"], targets=["https://app.acme-corp.io"], status="active",
                      roe="Production in scope, no DoS. Testing window 09:00-18:00 UTC.",
                      created_at=_mins_ago(180), active_run_id="run-acme-1", server_id="srv-1"))
        s.add(Session(id="ses-globex", name="Globex Internal Netpen", client="Globex",
                      scope=["10.0.0.0/16"], targets=["10.0.0.0/16"], status="active",
                      created_at=_mins_ago(4320), active_run_id="run-globex-1", server_id="srv-2"))
        s.add(Session(id="ses-initech", name="Initech Bug Bounty", client="Initech",
                      scope=["*.initech.com"], targets=["https://portal.initech.com"], status="archived",
                      created_at=_mins_ago(20160)))

        s.add(Run(id="run-acme-1", session_id="ses-acme", name="Full web assessment", status="running",
                  phase="Exploitation", started_at=_mins_ago(73), elapsed_sec=73 * 60, tokens=4_810_000,
                  cost_usd=6.2, model="kimi-k3", budget_tokens=20_000_000))
        s.add(Run(id="run-globex-1", session_id="ses-globex", name="Internal sweep", status="running",
                  phase="Reconnaissance", started_at=_mins_ago(22), elapsed_sec=22 * 60, tokens=900_000,
                  cost_usd=1.1, model="deepseek-v4-pro"))

        for a in [
            Agent(id="ag-orch", run_id="run-acme-1", name="orchestrator", role="root", status="running",
                  action="delegating: verify SQLi then dump users", calls=61),
            Agent(id="ag-recon", run_id="run-acme-1", name="recon", role="researcher", status="done",
                  parent_id="ag-orch", action="18 subdomains, 240 endpoints mapped", calls=34),
            Agent(id="ag-web", run_id="run-acme-1", name="web-exploit", role="executor", status="running",
                  parent_id="ag-orch", action="sqlmap --batch --dump /api/v2/search", calls=27),
            Agent(id="ag-auth", run_id="run-acme-1", name="auth-tester", role="executor", status="running",
                  parent_id="ag-orch", action="JWT alg-confusion on /oauth/token", calls=19),
            Agent(id="ag-idor", run_id="run-acme-1", name="idor-hunter", role="executor", status="waiting",
                  parent_id="ag-web", action="waiting: needs valid session cookie", calls=8),
        ]:
            s.add(a)
        for e in [("ag-orch", "ag-recon"), ("ag-orch", "ag-web"), ("ag-orch", "ag-auth"), ("ag-web", "ag-idor")]:
            s.add(AgentEdge(id=ids.new_id("edge"), run_id="run-acme-1", from_id=e[0], to_id=e[1]))

        for f in [
            Finding(id="RC-001", session_id="ses-acme", run_id="run-acme-1", title="SQL injection (error-based to union)",
                    severity="critical", cvss=9.8, cwe="CWE-89", location="/api/v2/search", status="verified",
                    evidence_request="GET /api/v2/search?q=1' AND (SELECT 1 FROM(SELECT COUNT(*),CONCAT(version(),0x3a,FLOOR(RAND()*2))x FROM information_schema.tables GROUP BY x)a)-- -",
                    evidence_response="HTTP/1.1 500 Internal Server Error\nDuplicate entry '8.0.36:1' for key <version leaked>",
                    remediation="Use parameterized queries. Least-privilege DB grants and a WAF rule.",
                    verification_method="data_extracted", created_at=_mins_ago(1)),
            Finding(id="RC-002", session_id="ses-acme", run_id="run-acme-1", title="Auth bypass via JWT alg confusion",
                    severity="critical", cvss=9.1, cwe="CWE-347", location="/oauth/token", status="verified",
                    remediation="Pin allowed algorithms, reject alg=none.", created_at=_mins_ago(9)),
            Finding(id="RC-006", session_id="ses-acme", run_id="run-acme-1", title="IDOR: read other users' orders",
                    severity="high", cvss=8.2, cwe="CWE-639", location="/api/v2/orders/{id}", status="verified",
                    created_at=_mins_ago(15)),
            Finding(id="RC-011", session_id="ses-acme", run_id="run-acme-1", title="SSRF via webhook URL",
                    severity="high", cvss=7.5, cwe="CWE-918", location="/api/v2/hooks", status="candidate",
                    created_at=_mins_ago(20)),
            Finding(id="RC-014", session_id="ses-acme", run_id="run-acme-1", title="Reflected XSS in search echo",
                    severity="medium", cvss=5.4, cwe="CWE-79", location="/search?q=", status="verified",
                    created_at=_mins_ago(25)),
            Finding(id="RC-021", session_id="ses-acme", run_id="run-acme-1", title="Verbose error stack traces",
                    severity="low", cvss=3.1, location="/api/*", status="candidate", created_at=_mins_ago(30)),
            Finding(id="GX-001", session_id="ses-globex", run_id="run-globex-1", title="SMB signing not required",
                    severity="high", cvss=7.4, location="10.0.3.0/24", status="verified", created_at=_mins_ago(10)),
            Finding(id="IN-001", session_id="ses-initech", title="Missing rate limiting on login",
                    severity="medium", cvss=5.0, location="/login", status="candidate", created_at=_mins_ago(500)),
        ]:
            s.add(f)

        for h in [
            Host(id="h1", session_id="ses-acme", host="app.acme-corp.io", ip="203.0.113.24",
                 ports=[{"port": 443, "service": "https", "version": "nginx 1.25.3"},
                        {"port": 8443, "service": "https-alt", "version": "Express"}],
                 tech=["nginx", "Node.js", "React"], source="nmap"),
            Host(id="h2", session_id="ses-acme", host="api.acme-corp.io", ip="203.0.113.25",
                 ports=[{"port": 443, "service": "https"}], tech=["Kong", "PostgreSQL"], source="subfinder"),
            Host(id="h4", session_id="ses-acme", host="web-01.internal.acme-corp.io", ip="10.0.3.9",
                 ports=[{"port": 22, "service": "ssh", "version": "OpenSSH 9.6"}, {"port": 80, "service": "http"}],
                 tech=["Apache"], source="reverse-shell"),
        ]:
            s.add(h)

        for x in [
            Loot(id="l1", session_id="ses-acme", kind="credential", label="admin@acme-corp.io",
                 value="Spr1ng2026!", source="users_dump.csv", ts=_mins_ago(5)),
            Loot(id="l3", session_id="ses-acme", kind="token", label="forged JWT (admin)",
                 value="eyJhbGciOiJub25lIn0...", source="/oauth/token", ts=_mins_ago(12)),
            Loot(id="l4", session_id="ses-acme", kind="file", label="users_dump.csv", value="1284 rows",
                 source="web-01", ts=_mins_ago(3)),
        ]:
            s.add(x)

        s.add(ChatMessage(id="c1", run_id="run-acme-1", role="operator", text="Focus on the auth surface first.", ts=_mins_ago(40)))
        s.add(ChatMessage(id="c2", run_id="run-acme-1", role="assistant",
                          text="Understood. auth-tester is probing /oauth/token for alg-confusion.", ts=_mins_ago(39)))

        for sh in [
            Shell(id="sh-nmap", session_id="ses-acme", kind="tool", label="nmap", status="idle", pty=False, created_at=_mins_ago(60)),
            Shell(id="sh-sqlmap", session_id="ses-acme", kind="tool", label="sqlmap", status="running", pty=False, created_at=_mins_ago(30)),
            Shell(id="sh-kali", session_id="ses-acme", kind="interactive", label="shell@kali", status="idle", pty=True, created_at=_mins_ago(20)),
            Shell(id="sh-rev3", session_id="ses-acme", kind="reverse", label="revsh 10.0.3.9:4444", status="running",
                  host="web-01.internal.acme-corp.io", remote_addr="10.0.3.9:51422", pty=True, created_at=_mins_ago(15)),
        ]:
            s.add(sh)

        s.add(Listener(id="ls-1", session_id="ses-acme", kind="tls", bind="0.0.0.0:4444", status="listening", sessions_count=1, created_at=_mins_ago(50)))

        for i, pe in enumerate([
            ("GET", "/api/v2/search?q=1'", 500, "1.2k"),
            ("POST", "/oauth/token", 200, "842"),
            ("GET", "/api/v2/orders/1007", 403, "96"),
            ("GET", "/api/v2/orders/1008", 200, "1.9k"),
        ]):
            s.add(ProxyEntry(id=ids.new_id("pe"), session_id="ses-acme", method=pe[0], url=pe[1],
                             status=pe[2], length=pe[3], ts=_mins_ago(i + 1)))

        for srv in [
            Server(id="srv-1", name="redcell-ops-1", host="ops1.redcell.sh", username="root", ip="203.0.113.10",
                   region="eu-central", status="connected", cpu=8, ram_gb=16, running_sessions=1, created_at=_mins_ago(5000)),
            Server(id="srv-2", name="redcell-ops-2", host="ops2.redcell.sh", username="root", ip="198.51.100.4",
                   region="us-east", status="connected", cpu=4, ram_gb=8, running_sessions=1, created_at=_mins_ago(4000)),
            Server(id="srv-3", name="burner-uk", host="10.8.0.3", username="ubuntu", region="uk-south",
                   status="offline", cpu=2, ram_gb=4, running_sessions=0, created_at=_mins_ago(600)),
        ]:
            s.add(srv)

        for px in [
            Proxy(id="px-1", label="residential-eu-1", url="http://eu1.proxy.pool:8080", kind="http",
                  status="healthy", latency_ms=84, last_check=_mins_ago(2), created_at=_mins_ago(300)),
            Proxy(id="px-2", label="residential-us-1", url="socks5://us1.proxy.pool:1080", kind="socks5",
                  status="healthy", latency_ms=121, last_check=_mins_ago(2), created_at=_mins_ago(300)),
            Proxy(id="px-3", label="burner-1", url="http://10.8.0.9:3128", kind="http", status="dead",
                  last_check=_mins_ago(15), created_at=_mins_ago(200)),
        ]:
            s.add(px)


_ALL_MODELS = [ProxyEntry, AgentEdge, Agent, Finding, Host, Loot, ChatMessage, Shell, Listener,
               Report, File, Run, Session, Server, Proxy, Provider, ProviderCredential,
               AppSettings, User]


async def unseed(force: bool = False) -> None:
    if settings.env != "dev" and not force:
        raise RuntimeError("refusing to unseed outside dev without force=True")
    async with session_scope() as s:
        for model in _ALL_MODELS:
            await s.execute(delete(model))
    for bucket in storage.buckets:
        try:
            await storage.empty_bucket(bucket)
        except Exception:
            pass
