// In-memory implementation of ApiClient with simulated latency and timer-driven event streams.

import type { ApiClient, Unsubscribe } from '../client';
import type {
  ChatMessage,
  EventMsg,
  Host,
  LootItem,
  Proxy,
  ProviderCatalogEntry,
  Run,
  Server,
  Session,
  Settings,
} from '../types';
import { makeFixtures, shellLines } from './fixtures';

const delay = (ms = 140) => new Promise<void>((r) => setTimeout(r, ms));

function assistantReply(text: string): string {
  return `Acknowledged. Reprioritizing the run toward: ${text.trim()}. I'll steer web-exploit and auth-tester accordingly and surface any new findings here.`;
}

const PROVIDERS: ProviderCatalogEntry[] = [
  { id: 'openai', label: 'OpenAI', models: ['gpt-5.6', 'gpt-5.5', 'gpt-5.4-mini'], needsKey: true },
  { id: 'anthropic', label: 'Anthropic', models: ['claude-opus-5', 'claude-sonnet-5', 'claude-haiku-4-5'], needsKey: true },
  { id: 'google', label: 'Google Gemini', models: ['gemini-3.1-pro', 'gemini-3.6-flash'], needsKey: true },
  { id: 'deepseek', label: 'DeepSeek', models: ['deepseek-v4-pro', 'deepseek-v4-flash'], needsKey: true },
  { id: 'moonshot', label: 'Moonshot (Kimi)', models: ['kimi-k3', 'kimi-k2.7-code'], needsKey: true },
  { id: 'qwen', label: 'Alibaba Qwen', models: ['qwen3.8-max', 'qwen3.5-flash'], needsKey: true },
  {
    id: 'openrouter',
    label: 'OpenRouter',
    models: ['anthropic/claude-opus-5', 'deepseek/deepseek-v4-pro', 'moonshotai/kimi-k3'],
    needsKey: true,
  },
  { id: 'ollama', label: 'Ollama (local)', models: ['qwen3', 'llama3.3'], needsKey: false },
  { id: 'custom', label: 'Custom (OpenAI-compatible)', models: [], needsKey: true },
];

const DEFAULT_SETTINGS: Settings = {
  llm: { provider: 'moonshot', model: 'kimi-k3', apiKey: '', apiBase: '', reasoningEffort: 'high' },
  execution: { backend: 'local-docker', dockerImage: 'redcell/kali:latest', sshHost: '', sshUser: 'root' },
  scope: { allowPrivateTargets: false, requestsPerSecond: 10 },
  proxy: { enabled: false, url: '', rotation: 'off' },
  report: { companyName: 'REDCELL', classification: 'CONFIDENTIAL', contact: '', logoDataUrl: undefined },
};

export function createMockClient(): ApiClient {
  const db = makeFixtures();
  let settings = structuredClone(DEFAULT_SETTINGS);
  let mockKeys: string[] = [settings.llm.provider];
  const chatSubs = new Map<string, Set<(m: ChatMessage) => void>>();
  const now = () => new Date().toISOString();
  let counter = 1000;
  const nid = (prefix: string) => `${prefix}-${++counter}`;

  const eventTemplates: Array<Pick<EventMsg, 'source' | 'type' | 'text'>> = [
    { source: 'web-exploit', type: 'tool', text: 'sqlmap -u ".../search?q=1" --batch --dump' },
    { source: 'recon', type: 'net', text: 'httpx: 12 new endpoints discovered' },
    { source: 'auth-tester', type: 'tool', text: 'jwt_tool: testing alg=none bypass' },
    { source: 'idor-hunter', type: 'net', text: 'enumerating /api/v2/orders/{id}' },
    { source: 'web-exploit', type: 'finding', text: 'candidate: reflected XSS in /search echo' },
    { source: 'orchestrator', type: 'steer', text: 'reprioritizing: focus on auth surface' },
    { source: 'listener', type: 'net', text: 'heartbeat from session #3 (10.0.3.9)' },
  ];

  const requireSession = (id: string): Session => {
    const found = db.sessions.find((e) => e.id === id);
    if (!found) throw new Error(`session ${id} not found`);
    return found;
  };

  let qi = 0;
  const QUESTIONS: Array<{ text: string; options: string[] }> = [
    {
      text: 'web-01 is SSH-reachable with creds recovered from loot. Pivot to the internal 10.0.0.0/16 network?',
      options: ['Yes, pivot', 'Stay external', 'Ask me later'],
    },
    {
      text: 'The SQLi on /api/v2/search can dump the full users table (1284 rows). Proceed with the dump?',
      options: ['Dump users', 'Prove it with 1 row', 'Skip'],
    },
    {
      text: 'Found an admin panel at /admin behind basic auth. Try the recovered credentials there?',
      options: ['Yes', 'No'],
    },
  ];
  const mkQuestion = (runId: string): ChatMessage => {
    const q = QUESTIONS[qi % QUESTIONS.length]!;
    qi += 1;
    return { id: nid('msg'), runId, role: 'assistant', text: q.text, options: q.options, ts: now() };
  };

  return {
    auth: {
      async firstRun() {
        await delay();
        return { needsSetup: false, adminPasswordHint: 'rc_7f3a.k9Qm.2Xv0' };
      },
      async login(username) {
        await delay(220);
        return { id: 'u-1', username, role: 'admin' };
      },
      async me() {
        await delay();
        return { id: 'u-1', username: 'admin', role: 'admin' };
      },
      async logout() {
        await delay();
      },
    },

    sessions: {
      async list() {
        await delay();
        return structuredClone(db.sessions);
      },
      async get(id) {
        await delay();
        return structuredClone(requireSession(id));
      },
      async create(input) {
        await delay(200);
        const session: Session = {
          id: nid('ses'),
          name: input.name,
          client: input.client,
          kind: input.kind ?? 'network',
          source: input.source,
          scope: input.scope,
          targets: input.targets,
          roe: input.roe,
          status: 'active',
          createdAt: now(),
          serverId: input.serverId,
          proxyId: input.proxyId,
          provider: input.provider,
          model: input.model,
          findingsCount: 0,
          severityCounts: { critical: 0, high: 0, medium: 0, low: 0, info: 0 },
        };
        db.sessions.unshift(session);
        return structuredClone(session);
      },
    },

    runs: {
      async list(sessionId) {
        await delay();
        return structuredClone(db.runs.filter((r) => r.sessionId === sessionId));
      },
      async get(id) {
        await delay();
        const run = db.runs.find((r) => r.id === id);
        if (!run) throw new Error(`run ${id} not found`);
        return structuredClone(run);
      },
      async create(sessionId, input) {
        await delay(200);
        const run: Run = {
          id: nid('run'),
          sessionId,
          name: input.name,
          status: 'running',
          phase: 'Reconnaissance',
          startedAt: now(),
          elapsedSec: 0,
          tokens: 0,
          costUsd: 0,
          model: input.model,
        };
        db.runs.unshift(run);
        return structuredClone(run);
      },
      async pause(id) {
        return setRunStatus(db, id, 'paused');
      },
      async resume(id) {
        return setRunStatus(db, id, 'running');
      },
      async stop(id) {
        return setRunStatus(db, id, 'stopped');
      },
    },

    agents: {
      async graph(runId) {
        await delay();
        return {
          nodes: structuredClone(db.agents.filter((a) => a.runId === runId)),
          edges: structuredClone(db.edges),
        };
      },
      async get(id) {
        await delay();
        const agent = db.agents.find((a) => a.id === id);
        if (!agent) throw new Error(`agent ${id} not found`);
        return structuredClone(agent);
      },
    },

    findings: {
      async list(sessionId) {
        await delay();
        return structuredClone(db.findings.filter((f) => f.sessionId === sessionId));
      },
      async get(id) {
        await delay();
        const finding = db.findings.find((f) => f.id === id);
        if (!finding) throw new Error(`finding ${id} not found`);
        return structuredClone(finding);
      },
      async verify(id) {
        await delay(300);
        const finding = db.findings.find((f) => f.id === id);
        if (!finding) throw new Error(`finding ${id} not found`);
        finding.status = 'verified';
        return structuredClone(finding);
      },
    },

    shells: {
      async list(sessionId) {
        await delay();
        return structuredClone(db.shells.filter((s) => s.sessionId === sessionId));
      },
      async open(sessionId, input) {
        await delay();
        const shell = {
          id: nid('sh'),
          sessionId,
          kind: input.kind,
          label: input.label ?? input.kind,
          status: 'running' as const,
          pty: input.kind !== 'tool',
          buffer: '',
        };
        db.shells.push(shell);
        return structuredClone(shell);
      },
      async write(id, data) {
        await delay(40);
        const shell = db.shells.find((s) => s.id === id);
        if (shell) shell.buffer += data;
      },
      async close(id) {
        await delay();
        const shell = db.shells.find((s) => s.id === id);
        if (shell) shell.status = 'closed';
      },
    },

    listeners: {
      async list(sessionId) {
        await delay();
        return structuredClone(db.listeners.filter((l) => l.sessionId === sessionId));
      },
      async start(sessionId, input) {
        await delay(160);
        const listener = {
          id: nid('ls'),
          sessionId,
          kind: input.kind,
          bind: input.bind,
          status: 'listening' as const,
          sessions: 0,
        };
        db.listeners.push(listener);
        return structuredClone(listener);
      },
    },

    proxy: {
      async history() {
        await delay();
        return structuredClone(db.proxy);
      },
    },

    attackSurface: {
      async hosts(sessionId) {
        await delay();
        return structuredClone(db.hosts.filter((h: Host) => h.sessionId === sessionId));
      },
    },

    loot: {
      async list(sessionId) {
        await delay();
        return structuredClone(db.loot.filter((l: LootItem) => l.sessionId === sessionId));
      },
    },

    reports: {
      async list(sessionId) {
        await delay();
        return structuredClone((db.reports ?? []).filter((r) => r.sessionId === sessionId));
      },
      async get(id) {
        await delay();
        const r = (db.reports ?? []).find((x) => x.id === id);
        if (!r) throw new Error('404 report not found');
        return structuredClone(r);
      },
      async create(sessionId, input) {
        await delay(200);
        const report = {
          id: nid('rep'),
          sessionId,
          title: input.title,
          status: 'ready' as const,
          format: 'pdf',
          formats: input.formats ?? (['pdf', 'json', 'sarif'] as const),
          artifacts: { pdf: nid('f'), json: nid('f'), sarif: nid('f') },
          summary: 'Mock report generated.',
          createdAt: now(),
        };
        (db.reports ??= []).push(report as never);
        return structuredClone(report) as never;
      },
      async remove(id) {
        await delay();
        db.reports = (db.reports ?? []).filter((r) => r.id !== id);
      },
    },

    settings: {
      async get() {
        await delay();
        return structuredClone(settings);
      },
      async save(next) {
        await delay(200);
        settings = structuredClone(next);
        return structuredClone(settings);
      },
      async providers() {
        await delay();
        return structuredClone(PROVIDERS);
      },
      async providerKeys() {
        await delay();
        return mockKeys.map((providerId) => ({ providerId, hasKey: true, apiBase: null }));
      },
      async setProviderKey(input) {
        await delay(150);
        if (!mockKeys.includes(input.providerId)) mockKeys.push(input.providerId);
        return { providerId: input.providerId, hasKey: true, apiBase: input.apiBase ?? null };
      },
      async removeProviderKey(providerId) {
        await delay(150);
        mockKeys = mockKeys.filter((p) => p !== providerId);
      },
      async availableModels() {
        await delay();
        return PROVIDERS.filter((p) => !p.needsKey || mockKeys.includes(p.id)).flatMap((p) =>
          p.models.map((model) => ({ provider: p.id, providerLabel: p.label, model })),
        );
      },
    },

    ai: {
      async draftChat(input) {
        await delay(400);
        const last = input.messages[input.messages.length - 1]?.content ?? '';
        return {
          reply: `(${settings.llm.model}) Understood: "${last}". Tell me the target domain and I'll draft the scope.`,
          proposal: null,
        };
      },
    },

    servers: {
      async list() {
        await delay();
        return structuredClone(db.servers);
      },
      async get(id) {
        await delay();
        const server = db.servers.find((s) => s.id === id);
        if (!server) throw new Error('404 server not found');
        return structuredClone(server);
      },
      async create(input) {
        await delay(200);
        const server: Server = {
          id: nid('srv'),
          name: input.name,
          host: input.host,
          username: input.username,
          region: input.region,
          status: 'unchecked',
          runningSessions: 0,
          createdAt: now(),
        };
        db.servers.push(server);
        return structuredClone(server);
      },
      async update(id, input) {
        await delay();
        const server = db.servers.find((s) => s.id === id);
        if (!server) throw new Error('404 server not found');
        Object.assign(server, {
          ...(input.name !== undefined && { name: input.name }),
          ...(input.host !== undefined && { host: input.host }),
          ...(input.username !== undefined && { username: input.username }),
          ...(input.region !== undefined && { region: input.region }),
          status: 'unchecked' as const,
        });
        return structuredClone(server);
      },
      async test(id) {
        await delay(700);
        const server = db.servers.find((s) => s.id === id);
        if (!server) throw new Error('404 server not found');
        const ok = /localhost|127\.0\.0\.1|10\.|192\.168\./.test(server.host);
        Object.assign(server, {
          status: ok ? ('connected' as const) : ('error' as const),
          latencyMs: ok ? 42 : undefined,
          os: ok ? 'Linux 6.1.0' : undefined,
          cpu: ok ? 4 : undefined,
          ramGb: ok ? 8 : undefined,
          lastCheck: now(),
          lastError: ok ? undefined : 'connection refused',
        });
        return {
          ok,
          status: server.status,
          latencyMs: server.latencyMs,
          hostname: ok ? server.name : undefined,
          os: server.os,
          cpu: server.cpu,
          ramGb: server.ramGb,
          ip: ok ? server.host : undefined,
          output: ok ? 'H:host\nU:Linux 6.1.0\nC:4\nM:8192' : '',
          error: ok ? undefined : 'connection refused',
        };
      },
      async remove(id) {
        await delay();
        const i = db.servers.findIndex((s) => s.id === id);
        if (i >= 0) db.servers.splice(i, 1);
      },
    },

    proxies: {
      async list() {
        await delay();
        return structuredClone(db.proxies);
      },
      async get(id) {
        await delay();
        const proxy = db.proxies.find((p) => p.id === id);
        if (!proxy) throw new Error('404 proxy not found');
        return structuredClone(proxy);
      },
      async create(input) {
        await delay(160);
        const proxy: Proxy = {
          id: nid('px'),
          label: input.label,
          url: input.url,
          kind: input.kind,
          auth: input.auth,
          username: input.username,
          status: 'unchecked',
        };
        db.proxies.push(proxy);
        return structuredClone(proxy);
      },
      async update(id, input) {
        await delay();
        const proxy = db.proxies.find((p) => p.id === id);
        if (!proxy) throw new Error('404 proxy not found');
        Object.assign(proxy, {
          ...(input.label !== undefined && { label: input.label }),
          ...(input.url !== undefined && { url: input.url }),
          ...(input.kind !== undefined && { kind: input.kind }),
          ...(input.auth !== undefined && { auth: input.auth }),
          ...(input.username !== undefined && { username: input.username }),
          status: 'unchecked' as const,
        });
        return structuredClone(proxy);
      },
      async test(id) {
        await delay(600);
        const proxy = db.proxies.find((p) => p.id === id);
        if (!proxy) throw new Error('404 proxy not found');
        const ok = !/dead|10\.8\./.test(`${proxy.status} ${proxy.url}`);
        Object.assign(proxy, {
          status: ok ? ('healthy' as const) : ('dead' as const),
          latencyMs: ok ? 96 : undefined,
          egressIp: ok ? '203.0.113.7' : undefined,
          lastCheck: now(),
          lastError: ok ? undefined : 'connection refused',
        });
        return {
          ok,
          status: proxy.status,
          latencyMs: proxy.latencyMs,
          egressIp: proxy.egressIp,
          output: ok ? 'egress IP via proxy: 203.0.113.7' : '',
          error: ok ? undefined : 'connection refused',
        };
      },
      async remove(id) {
        await delay();
        const i = db.proxies.findIndex((p) => p.id === id);
        if (i >= 0) db.proxies.splice(i, 1);
      },
    },

    chat: {
      async history(runId) {
        await delay();
        return structuredClone(db.chat.filter((m) => m.runId === runId));
      },
      async send(runId, text) {
        await delay(120);
        const msg: ChatMessage = { id: nid('msg'), runId, role: 'operator', text, ts: now() };
        db.chat.push(msg);
        setTimeout(() => {
          const reply: ChatMessage = {
            id: nid('msg'),
            runId,
            role: 'assistant',
            text: assistantReply(text),
            ts: now(),
          };
          db.chat.push(reply);
          chatSubs.get(runId)?.forEach((cb) => cb(structuredClone(reply)));
        }, 950);
        return structuredClone(msg);
      },
      subscribe(runId, cb): Unsubscribe {
        const set = chatSubs.get(runId) ?? new Set<(m: ChatMessage) => void>();
        set.add(cb);
        chatSubs.set(runId, set);
        const emitQuestion = () => {
          const q = mkQuestion(runId);
          db.chat.push(q);
          cb(structuredClone(q));
        };
        const first = setTimeout(emitQuestion, 6000);
        const timer = setInterval(emitQuestion, 30000);
        return () => {
          set.delete(cb);
          clearTimeout(first);
          clearInterval(timer);
        };
      },
    },

    events: {
      async history(runId) {
        await delay();
        return eventTemplates.slice(0, 8).map((tpl) => ({
          id: nid('ev'), ts: now(), runId, source: tpl.source, type: tpl.type, text: tpl.text,
        }));
      },
      subscribe(runId, cb): Unsubscribe {
        const timer = setInterval(() => {
          const tpl = eventTemplates[Math.floor(Math.random() * eventTemplates.length)]!;
          cb({ id: nid('ev'), ts: now(), runId, source: tpl.source, type: tpl.type, text: tpl.text });
        }, 2200);
        return () => clearInterval(timer);
      },
    },

    shellIO: {
      subscribe(shellId, cb): Unsubscribe {
        const shell = db.shells.find((s) => s.id === shellId);
        const lines = shellLines(shell?.kind ?? 'tool');
        let i = 0;
        const timer = setInterval(() => {
          const line = lines[i % lines.length]!;
          cb(line + '\n');
          i += 1;
        }, 1600);
        return () => clearInterval(timer);
      },
    },
    browser: {
      async start() {
        return { ok: true };
      },
      async control(_sessionId, owner) {
        return { owner };
      },
      vncUrl(sessionId) {
        return `ws://mock/api/v1/ws/browser/${sessionId}`;
      },
    },
  };
}

async function setRunStatus(
  db: ReturnType<typeof makeFixtures>,
  id: string,
  status: Run['status'],
): Promise<Run> {
  await delay(120);
  const run = db.runs.find((r) => r.id === id);
  if (!run) throw new Error(`run ${id} not found`);
  run.status = status;
  return structuredClone(run);
}
