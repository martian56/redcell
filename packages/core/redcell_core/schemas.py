"""API I/O models. Serialized camelCase to match the frontend ApiClient
contract (packages/api-client/src/types.ts). `from_attributes=True` lets these
validate straight from SQLAlchemy ORM rows."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class Camel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)


# ---- auth ----
class User(Camel):
    id: str
    username: str
    role: str = "admin"


class LoginInput(Camel):
    username: str
    password: str


class FirstRun(Camel):
    needs_setup: bool = False
    admin_password_hint: str | None = None


# ---- sessions / runs / agents ----
class Session(Camel):
    id: str
    name: str
    client: str
    kind: str = "network"
    source: str | None = None
    scope: list[str] = []
    targets: list[str] = []
    status: str = "active"
    roe: str | None = None
    created_at: str
    active_run_id: str | None = None
    server_id: str | None = None
    proxy_id: str | None = None
    provider: str | None = None
    model: str | None = None
    findings_count: int = 0
    severity_counts: dict[str, int] = {}


class CreateSessionInput(Camel):
    name: str
    client: str
    kind: str = "network"
    source: str | None = None
    scope: list[str] = []
    targets: list[str] = []
    roe: str | None = None
    server_id: str | None = None
    proxy_id: str | None = None
    provider: str | None = None
    model: str | None = None


class Run(Camel):
    id: str
    session_id: str
    name: str
    status: str
    phase: str
    started_at: str
    elapsed_sec: int = 0
    tokens: int = 0
    cost_usd: float = 0.0
    model: str
    provider: str | None = None
    budget_tokens: int | None = None


class CreateRunInput(Camel):
    name: str
    model: str
    provider: str | None = None
    instruction: str | None = None


class Agent(Camel):
    id: str
    run_id: str
    name: str
    role: str
    status: str
    parent_id: str | None = None
    action: str = ""
    calls: int = 0


class AgentEdge(Camel):
    from_: str = Field(alias="from")
    to: str


class AgentGraph(Camel):
    nodes: list[Agent] = []
    edges: list[AgentEdge] = []


# ---- findings ----
class Finding(Camel):
    id: str
    session_id: str
    run_id: str | None = None
    title: str
    severity: str
    cvss: float = 0.0
    cwe: str | None = None
    location: str = ""
    status: str = "candidate"
    evidence_request: str | None = None
    evidence_response: str | None = None
    remediation: str | None = None
    verification_method: str | None = None
    created_at: str


# ---- shells ----
class Shell(Camel):
    id: str
    session_id: str
    kind: str
    label: str
    status: str
    host: str | None = None
    remote_addr: str | None = None
    pty: bool = False
    buffer: str = ""


class OpenShellInput(Camel):
    kind: str
    label: str | None = None


class ShellWriteInput(Camel):
    data: str


# ---- listeners / proxy history / hosts / loot ----
class Listener(Camel):
    id: str
    session_id: str
    kind: str
    bind: str
    status: str
    sessions: int = 0


class StartListenerInput(Camel):
    kind: str
    bind: str


class ProxyEntry(Camel):
    id: str
    method: str
    url: str
    status: int
    length: str
    ts: str


class HostPort(Camel):
    port: int
    service: str
    version: str | None = None


class Host(Camel):
    id: str
    session_id: str
    host: str
    ip: str | None = None
    ports: list[HostPort] = []
    tech: list[str] = []
    source: str = ""


class LootItem(Camel):
    id: str
    session_id: str
    kind: str
    label: str
    value: str
    source: str = ""
    ts: str


# ---- events / chat ----
class EventMsg(Camel):
    id: str
    ts: str
    run_id: str
    source: str
    type: str
    text: str


class ChatMessage(Camel):
    id: str
    run_id: str
    role: str
    text: str
    options: list[str] | None = None
    ts: str


class ChatSendInput(Camel):
    text: str


class BrowserControlInput(Camel):
    owner: str  # "operator" to take control, "agent" to release


# ---- settings / providers ----
class LlmSettings(Camel):
    provider: str = "moonshot"
    model: str = "kimi-k3"
    api_key: str = ""
    api_base: str | None = ""
    reasoning_effort: str = "high"


class ExecutionSettings(Camel):
    backend: str = "local-docker"
    # prebuilt Kali image on Docker Hub. any host can pull it, so remote servers
    # pull instead of shipping the local build.
    docker_image: str = "martian56/kali:latest"
    ssh_host: str | None = ""
    ssh_user: str | None = "root"


class ScopeSettings(Camel):
    allow_private_targets: bool = False
    requests_per_second: int = 10


class ProxySettings(Camel):
    enabled: bool = False
    url: str | None = ""
    rotation: str = "off"


class ReportSettings(Camel):
    company_name: str = "REDCELL"
    classification: str = "CONFIDENTIAL"
    contact: str | None = ""
    # Optional logo as a data URL (data:image/png;base64,...) shown on the cover.
    logo_data_url: str | None = None


class Settings(Camel):
    llm: LlmSettings = LlmSettings()
    execution: ExecutionSettings = ExecutionSettings()
    scope: ScopeSettings = ScopeSettings()
    proxy: ProxySettings = ProxySettings()
    report: ReportSettings = ReportSettings()


class ProviderCatalogEntry(Camel):
    id: str
    label: str
    models: list[str] = []
    needs_key: bool = True


# ---- servers / proxies (dashboard entities) ----
class Server(Camel):
    id: str
    name: str
    host: str
    username: str | None = None
    ip: str | None = None
    region: str | None = None
    status: str = "unchecked"
    cpu: int | None = None
    ram_gb: int | None = None
    running_sessions: int = 0
    os: str | None = None
    latency_ms: int | None = None
    last_check: str | None = None
    last_error: str | None = None
    created_at: str


class CreateServerInput(Camel):
    name: str
    host: str
    region: str | None = None
    username: str | None = None
    auth_method: str | None = None
    password: str | None = None
    private_key: str | None = None


class UpdateServerInput(Camel):
    name: str | None = None
    host: str | None = None
    region: str | None = None
    username: str | None = None
    auth_method: str | None = None
    password: str | None = None
    private_key: str | None = None


class ServerTestResult(Camel):
    ok: bool
    status: str
    latency_ms: int | None = None
    hostname: str | None = None
    os: str | None = None
    cpu: int | None = None
    ram_gb: int | None = None
    ip: str | None = None
    output: str = ""
    error: str | None = None


class Proxy(Camel):
    id: str
    label: str
    url: str
    kind: str
    status: str = "unchecked"
    auth: str | None = None
    username: str | None = None
    latency_ms: int | None = None
    last_check: str | None = None
    last_error: str | None = None
    egress_ip: str | None = None


class CreateProxyInput(Camel):
    label: str
    url: str
    kind: str
    auth: str = "open"
    username: str | None = None
    password: str | None = None


class UpdateProxyInput(Camel):
    label: str | None = None
    url: str | None = None
    kind: str | None = None
    auth: str | None = None
    username: str | None = None
    password: str | None = None


class ProxyTestResult(Camel):
    ok: bool
    status: str
    latency_ms: int | None = None
    egress_ip: str | None = None
    output: str = ""
    error: str | None = None


# ---- files / reports ----
class FileMeta(Camel):
    id: str
    session_id: str | None = None
    filename: str
    kind: str = "upload"
    content_type: str = "application/octet-stream"
    size: int = 0
    visibility: str = "private"
    source: str = ""
    created_at: str


class Report(Camel):
    id: str
    session_id: str
    title: str
    status: str = "draft"
    format: str = "pdf"
    file_id: str | None = None
    formats: list[str] = []
    artifacts: dict[str, str] = {}
    summary: str | None = None
    error: str | None = None
    created_at: str


class CreateReportInput(Camel):
    title: str
    formats: list[str] = ["pdf", "json", "sarif"]


# ---- provider keys / available models ----
class ProviderKeyStatus(Camel):
    provider_id: str
    has_key: bool = False
    api_base: str | None = None


class ProviderKeyInput(Camel):
    provider_id: str
    api_key: str = ""
    api_base: str | None = None


class AvailableModel(Camel):
    provider: str
    provider_label: str
    model: str


# ---- draft (new-session) chat ----
class DraftMessage(Camel):
    role: str
    content: str


class SessionProposal(Camel):
    name: str | None = None
    client: str | None = None
    scope: list[str] = []
    targets: list[str] = []


class DraftChatInput(Camel):
    messages: list[DraftMessage] = []
    provider: str | None = None
    model: str | None = None


class DraftChatOutput(Camel):
    reply: str
    proposal: SessionProposal | None = None
