// Domain model shared by the mock and HTTP clients.

export type ID = string;
export type ISODate = string;

export type Severity = 'critical' | 'high' | 'medium' | 'low' | 'info';
export type RunStatus = 'queued' | 'running' | 'paused' | 'completed' | 'failed' | 'stopped';
export type AgentStatus = 'running' | 'waiting' | 'done' | 'idle' | 'failed';
export type FindingStatus = 'candidate' | 'verified' | 'dismissed' | 'inconclusive';
export type ShellKind = 'tool' | 'interactive' | 'reverse';
export type ShellStatus = 'running' | 'idle' | 'closed';

export interface User {
  id: ID;
  username: string;
  role: 'admin' | 'operator';
}

export type SessionKind = 'network' | 'code';

/** A red-team project. */
export interface Session {
  id: ID;
  name: string;
  client: string;
  /** 'network' = web/host pentest, 'code' = source-code security scan. */
  kind: SessionKind;
  /** For a code scan: a public git repo URL or a local folder path. */
  source?: string;
  scope: string[];
  targets: string[];
  status: 'active' | 'archived';
  /** Rules of engagement. */
  roe?: string;
  brief?: string;
  createdAt: ISODate;
  activeRunId?: ID;
  /** Saved server where runs execute (undefined = local). */
  serverId?: ID;
  /** Saved proxy runs egress through (undefined = direct). */
  proxyId?: ID;
  /** Default LLM provider/model for runs in this session. */
  provider?: string;
  model?: string;
  findingsCount: number;
  severityCounts: Record<Severity, number>;
}

/** One execution against a session's targets. */
export interface Run {
  id: ID;
  sessionId: ID;
  name: string;
  instruction?: string;
  status: RunStatus;
  phase: string;
  startedAt: ISODate;
  elapsedSec: number;
  tokens: number;
  costUsd: number;
  model: string;
  budgetTokens?: number;
}

export interface Agent {
  id: ID;
  runId: ID;
  name: string;
  role: string;
  status: AgentStatus;
  parentId?: ID;
  action: string;
  calls: number;
}

export interface AgentEdge {
  from: ID;
  to: ID;
}

export interface AgentGraph {
  nodes: Agent[];
  edges: AgentEdge[];
}

export interface Finding {
  id: ID;
  sessionId: ID;
  runId?: ID;
  title: string;
  severity: Severity;
  cvss: number;
  cwe?: string;
  location: string;
  status: FindingStatus;
  evidenceRequest?: string;
  evidenceResponse?: string;
  remediation?: string;
  verificationMethod?: string;
  createdAt: ISODate;
}

/** A terminal: agent tool output, an interactive shell, or a caught reverse shell. */
export interface Shell {
  id: ID;
  sessionId: ID;
  kind: ShellKind;
  label: string;
  status: ShellStatus;
  host?: string;
  remoteAddr?: string;
  pty: boolean;
  buffer: string;
}

export interface Listener {
  id: ID;
  sessionId: ID;
  kind: 'tcp' | 'tls' | 'http';
  bind: string;
  status: 'listening' | 'stopped';
  sessions: number;
}

/** A row in a session's HTTP intercept history. */
export interface ProxyEntry {
  id: ID;
  method: string;
  url: string;
  status: number;
  length: string;
  ts: ISODate;
}

export type EventType = 'tool' | 'finding' | 'net' | 'steer' | 'error';

export interface EventMsg {
  id: ID;
  ts: ISODate;
  runId: ID;
  source: string;
  type: EventType;
  text: string;
}

/** Search, pagination, and filter controls accepted by list endpoints. */
export interface ListQuery {
  q?: string;
  limit?: number;
  offset?: number;
  [key: string]: string | number | boolean | undefined;
}

export interface ChatMessage {
  id: ID;
  runId: ID;
  role: 'operator' | 'assistant';
  text: string;
  /** On an assistant message, marks a question with quick replies. */
  options?: string[];
  ts: ISODate;
}

export interface HostPort {
  port: number;
  service: string;
  version?: string;
}

export interface Host {
  id: ID;
  sessionId: ID;
  host: string;
  ip?: string;
  ports: HostPort[];
  tech: string[];
  source: string;
}

export type LootKind = 'credential' | 'token' | 'file' | 'hash';

export interface LootItem {
  id: ID;
  sessionId: ID;
  kind: LootKind;
  label: string;
  value: string;
  source: string;
  ts: ISODate;
}

export interface ProviderCatalogEntry {
  id: string;
  label: string;
  models: string[];
  needsKey: boolean;
}

/** Whether a provider has an API key stored. */
export interface ProviderKeyStatus {
  providerId: string;
  hasKey: boolean;
  apiBase?: string | null;
}

export interface SetProviderKeyInput {
  providerId: string;
  apiKey: string;
  apiBase?: string | null;
}

/** A model available from a keyed or keyless provider. */
export interface AvailableModel {
  provider: string;
  providerLabel: string;
  model: string;
}

/** New-session chat with the model to scope an engagement. */
export interface DraftMessage {
  role: string;
  content: string;
}

export interface SessionProposal {
  name?: string;
  client?: string;
  kind?: SessionKind;
  source?: string;
  scope: string[];
  targets: string[];
  roe?: string;
  brief?: string;
}

export interface DraftChatInput {
  messages: DraftMessage[];
  provider?: string;
  model?: string;
}

export interface DraftChatOutput {
  reply: string;
  proposal?: SessionProposal | null;
}

export type ExecutionBackendKind = 'local-docker' | 'ssh-vps';
export type ReasoningEffort = 'low' | 'medium' | 'high' | 'xhigh';

export interface Settings {
  llm: {
    provider: string;
    model: string;
    apiKey: string;
    apiBase?: string;
    reasoningEffort: ReasoningEffort;
  };
  execution: {
    backend: ExecutionBackendKind;
    dockerImage: string;
    sshHost?: string;
    sshUser?: string;
  };
  scope: {
    allowPrivateTargets: boolean;
    requestsPerSecond: number;
  };
  proxy: {
    enabled: boolean;
    url?: string;
    rotation: 'off' | 'roundrobin' | 'random';
  };
  report: {
    companyName: string;
    classification: string;
    contact?: string;
    logoDataUrl?: string;
  };
}

export type ReportFormat = 'pdf' | 'json' | 'sarif';
export type ReportStatus = 'draft' | 'generating' | 'ready' | 'failed';

export interface Report {
  id: ID;
  sessionId: ID;
  title: string;
  status: ReportStatus;
  format: string;
  fileId?: ID;
  formats: ReportFormat[];
  artifacts: Partial<Record<ReportFormat, ID>>;
  summary?: string;
  error?: string;
  createdAt: ISODate;
}

export interface CreateReportInput {
  title: string;
  formats?: ReportFormat[];
}

/** A remote execution host (VPS or remote Docker). */
export type ServerStatus = 'connected' | 'offline' | 'provisioning' | 'unchecked' | 'error';

export interface Server {
  id: ID;
  name: string;
  host: string;
  username?: string;
  ip?: string;
  region?: string;
  status: ServerStatus;
  cpu?: number;
  ramGb?: number;
  runningSessions: number;
  os?: string;
  latencyMs?: number;
  lastCheck?: ISODate;
  lastError?: string;
  createdAt: ISODate;
}

export interface UpdateServerInput {
  name?: string;
  host?: string;
  region?: string;
  username?: string;
  authMethod?: 'key' | 'password';
  password?: string;
  privateKey?: string;
}

export interface ServerTestResult {
  ok: boolean;
  status: ServerStatus;
  latencyMs?: number;
  hostname?: string;
  os?: string;
  cpu?: number;
  ramGb?: number;
  ip?: string;
  output: string;
  error?: string;
}

/** An upstream proxy in the rotation pool. */
export type ProxyKind = 'http' | 'https' | 'socks5';
export type ProxyHealth = 'healthy' | 'dead' | 'unchecked';

export interface Proxy {
  id: ID;
  label: string;
  url: string;
  kind: ProxyKind;
  status: ProxyHealth;
  auth?: 'open' | 'credentials';
  username?: string;
  latencyMs?: number;
  lastCheck?: ISODate;
  lastError?: string;
  egressIp?: string;
}

export interface UpdateProxyInput {
  label?: string;
  url?: string;
  kind?: ProxyKind;
  auth?: 'open' | 'credentials';
  username?: string;
  password?: string;
}

export interface ProxyTestResult {
  ok: boolean;
  status: ProxyHealth;
  latencyMs?: number;
  egressIp?: string;
  output: string;
  error?: string;
}

export interface SystemVersion {
  current: string;
  latest?: string | null;
  updateAvailable: boolean;
}

export interface UpdateStarted {
  started: boolean;
  detail: string;
}
