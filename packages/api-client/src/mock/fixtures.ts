import type {
  Agent,
  AgentEdge,
  ChatMessage,
  Finding,
  Host,
  Listener,
  LootItem,
  Proxy,
  ProxyEntry,
  Report,
  Run,
  Server,
  Session,
  Shell,
} from '../types';

export interface Fixtures {
  sessions: Session[];
  runs: Run[];
  agents: Agent[];
  edges: AgentEdge[];
  findings: Finding[];
  shells: Shell[];
  listeners: Listener[];
  proxy: ProxyEntry[];
  hosts: Host[];
  loot: LootItem[];
  chat: ChatMessage[];
  servers: Server[];
  proxies: Proxy[];
  reports: Report[];
}

/** Builds a fresh dataset for the mock client. */
export function makeFixtures(): Fixtures {
  const s1 = 'ses-acme';
  const runId = 'run-acme-1';
  const minutesAgo = (m: number) => new Date(Date.now() - m * 60_000).toISOString();

  const sessions: Session[] = [
    {
      id: s1,
      name: 'ACME External Q3',
      client: 'ACME Corp',
      kind: 'network',
      scope: ['*.acme-corp.io'],
      targets: ['https://app.acme-corp.io'],
      status: 'active',
      roe: 'Production in scope, no DoS. Testing window 09:00-18:00 UTC.',
      createdAt: minutesAgo(180),
      activeRunId: runId,
      serverId: 'srv-1',
      findingsCount: 30,
      severityCounts: { critical: 2, high: 5, medium: 8, low: 3, info: 12 },
    },
    {
      id: 'ses-globex',
      name: 'Globex Internal Netpen',
      client: 'Globex',
      kind: 'network',
      scope: ['10.0.0.0/16'],
      targets: ['10.0.0.0/16'],
      status: 'active',
      createdAt: minutesAgo(4320),
      serverId: 'srv-2',
      findingsCount: 11,
      severityCounts: { critical: 1, high: 3, medium: 4, low: 2, info: 1 },
    },
    {
      id: 'ses-initech',
      name: 'Initech Bug Bounty',
      client: 'Initech',
      kind: 'network',
      scope: ['*.initech.com'],
      targets: ['https://portal.initech.com'],
      status: 'archived',
      createdAt: minutesAgo(20160),
      findingsCount: 6,
      severityCounts: { critical: 0, high: 1, medium: 2, low: 2, info: 1 },
    },
  ];

  const runs: Run[] = [
    {
      id: runId,
      sessionId: s1,
      name: 'Full web assessment',
      status: 'running',
      phase: 'Exploitation',
      startedAt: minutesAgo(73),
      elapsedSec: 73 * 60,
      tokens: 4_810_000,
      costUsd: 6.2,
      model: 'kimi-k3',
      budgetTokens: 20_000_000,
    },
    {
      id: 'run-globex-1',
      sessionId: 'ses-globex',
      name: 'Internal sweep',
      status: 'running',
      phase: 'Reconnaissance',
      startedAt: minutesAgo(22),
      elapsedSec: 22 * 60,
      tokens: 900_000,
      costUsd: 1.1,
      model: 'deepseek-v4-pro',
    },
  ];

  const agents: Agent[] = [
    { id: 'ag-orch', runId, name: 'orchestrator', role: 'root', status: 'running', action: 'delegating: verify SQLi then dump users', calls: 61 },
    { id: 'ag-recon', runId, name: 'recon', role: 'researcher', status: 'done', parentId: 'ag-orch', action: '18 subdomains, 240 endpoints mapped', calls: 34 },
    { id: 'ag-web', runId, name: 'web-exploit', role: 'executor', status: 'running', parentId: 'ag-orch', action: 'sqlmap --batch --dump /api/v2/search', calls: 27 },
    { id: 'ag-auth', runId, name: 'auth-tester', role: 'executor', status: 'running', parentId: 'ag-orch', action: 'JWT alg-confusion on /oauth/token', calls: 19 },
    { id: 'ag-idor', runId, name: 'idor-hunter', role: 'executor', status: 'waiting', parentId: 'ag-web', action: 'waiting: needs valid session cookie', calls: 8 },
  ];

  const edges: AgentEdge[] = [
    { from: 'ag-orch', to: 'ag-recon' },
    { from: 'ag-orch', to: 'ag-web' },
    { from: 'ag-orch', to: 'ag-auth' },
    { from: 'ag-web', to: 'ag-idor' },
  ];

  const findings: Finding[] = [
    { id: 'RC-001', sessionId: s1, runId, title: 'SQL injection (error-based to union)', severity: 'critical', cvss: 9.8, cwe: 'CWE-89', location: '/api/v2/search', status: 'verified', evidenceRequest: "GET /api/v2/search?q=1' AND (SELECT 1 FROM(SELECT COUNT(*),CONCAT(version(),0x3a,FLOOR(RAND()*2))x FROM information_schema.tables GROUP BY x)a)-- -", evidenceResponse: 'HTTP/1.1 500 Internal Server Error\nDuplicate entry \'8.0.36:1\' for key <version leaked>', remediation: 'Use parameterized queries for q. Apply least-privilege DB grants and a WAF rule.', verificationMethod: 'data_extracted', createdAt: minutesAgo(1) },
    { id: 'RC-002', sessionId: s1, runId, title: 'Auth bypass via JWT alg confusion', severity: 'critical', cvss: 9.1, cwe: 'CWE-347', location: '/oauth/token', status: 'verified', remediation: 'Pin allowed algorithms, reject alg=none, verify with server public keys only.', createdAt: minutesAgo(9) },
    { id: 'RC-006', sessionId: s1, runId, title: "IDOR: read other users' orders", severity: 'high', cvss: 8.2, cwe: 'CWE-639', location: '/api/v2/orders/{id}', status: 'verified', createdAt: minutesAgo(15) },
    { id: 'RC-011', sessionId: s1, runId, title: 'SSRF via webhook URL', severity: 'high', cvss: 7.5, cwe: 'CWE-918', location: '/api/v2/hooks', status: 'candidate', createdAt: minutesAgo(20) },
    { id: 'RC-014', sessionId: s1, runId, title: 'Reflected XSS in search echo', severity: 'medium', cvss: 5.4, cwe: 'CWE-79', location: '/search?q=', status: 'verified', createdAt: minutesAgo(25) },
    { id: 'RC-021', sessionId: s1, runId, title: 'Verbose error stack traces', severity: 'low', cvss: 3.1, location: '/api/*', status: 'candidate', createdAt: minutesAgo(30) },
  ];

  const shells: Shell[] = [
    { id: 'sh-nmap', sessionId: s1, kind: 'tool', label: 'nmap', status: 'idle', pty: false, buffer: '' },
    { id: 'sh-sqlmap', sessionId: s1, kind: 'tool', label: 'sqlmap', status: 'running', pty: false, buffer: '' },
    { id: 'sh-kali', sessionId: s1, kind: 'interactive', label: 'shell@kali', status: 'idle', pty: true, buffer: '' },
    { id: 'sh-rev3', sessionId: s1, kind: 'reverse', label: 'revsh 10.0.3.9:4444', status: 'running', host: 'web-01.internal.acme-corp.io', remoteAddr: '10.0.3.9:51422', pty: true, buffer: '' },
  ];

  const listeners: Listener[] = [
    { id: 'ls-1', sessionId: s1, kind: 'tls', bind: '0.0.0.0:4444', status: 'listening', sessions: 1 },
  ];

  const proxy: ProxyEntry[] = [
    { id: '1042', method: 'GET', url: "/api/v2/search?q=1'", status: 500, length: '1.2k', ts: minutesAgo(1) },
    { id: '1041', method: 'POST', url: '/oauth/token', status: 200, length: '842', ts: minutesAgo(2) },
    { id: '1039', method: 'GET', url: '/api/v2/orders/1007', status: 403, length: '96', ts: minutesAgo(3) },
    { id: '1036', method: 'GET', url: '/api/v2/orders/1008', status: 200, length: '1.9k', ts: minutesAgo(4) },
  ];

  const hosts: Host[] = [
    { id: 'h1', sessionId: s1, host: 'app.acme-corp.io', ip: '203.0.113.24', ports: [{ port: 443, service: 'https', version: 'nginx 1.25.3' }, { port: 8443, service: 'https-alt', version: 'Express' }], tech: ['nginx', 'Node.js', 'React'], source: 'nmap' },
    { id: 'h2', sessionId: s1, host: 'api.acme-corp.io', ip: '203.0.113.25', ports: [{ port: 443, service: 'https' }], tech: ['Kong', 'PostgreSQL'], source: 'subfinder' },
    { id: 'h3', sessionId: s1, host: 'admin.acme-corp.io', ip: '203.0.113.26', ports: [{ port: 443, service: 'https' }], tech: ['nginx'], source: 'subfinder' },
    { id: 'h4', sessionId: s1, host: 'web-01.internal.acme-corp.io', ip: '10.0.3.9', ports: [{ port: 22, service: 'ssh', version: 'OpenSSH 9.6' }, { port: 80, service: 'http' }], tech: ['Apache'], source: 'reverse-shell' },
  ];

  const loot: LootItem[] = [
    { id: 'l1', sessionId: s1, kind: 'credential', label: 'admin@acme-corp.io', value: 'Spr1ng2026!', source: 'users_dump.csv', ts: minutesAgo(5) },
    { id: 'l2', sessionId: s1, kind: 'hash', label: 'svc_deploy', value: '$2b$12$e9Xk...', source: 'acme_prod.users', ts: minutesAgo(8) },
    { id: 'l3', sessionId: s1, kind: 'token', label: 'forged JWT (admin)', value: 'eyJhbGciOiJub25lIn0...', source: '/oauth/token', ts: minutesAgo(12) },
    { id: 'l4', sessionId: s1, kind: 'file', label: 'users_dump.csv', value: '1284 rows', source: 'web-01', ts: minutesAgo(3) },
  ];

  const chat: ChatMessage[] = [
    { id: 'c1', runId, role: 'operator', text: 'Focus on the auth surface first.', ts: minutesAgo(40) },
    { id: 'c2', runId, role: 'assistant', text: 'Understood. auth-tester is probing /oauth/token for alg-confusion, and recon handed off 6 auth-gated endpoints.', ts: minutesAgo(39) },
  ];

  const servers: Server[] = [
    { id: 'srv-1', name: 'redcell-ops-1', host: 'ops1.redcell.sh', username: 'root', ip: '203.0.113.10', region: 'eu-central', status: 'connected', cpu: 8, ramGb: 16, runningSessions: 1, createdAt: minutesAgo(5000) },
    { id: 'srv-2', name: 'redcell-ops-2', host: 'ops2.redcell.sh', username: 'root', ip: '198.51.100.4', region: 'us-east', status: 'connected', cpu: 4, ramGb: 8, runningSessions: 1, createdAt: minutesAgo(4000) },
    { id: 'srv-3', name: 'burner-uk', host: '10.8.0.3', username: 'ubuntu', region: 'uk-south', status: 'offline', cpu: 2, ramGb: 4, runningSessions: 0, createdAt: minutesAgo(600) },
  ];

  const proxies: Proxy[] = [
    { id: 'px-1', label: 'residential-eu-1', url: 'http://eu1.proxy.pool:8080', kind: 'http', status: 'healthy', latencyMs: 84, lastCheck: minutesAgo(2) },
    { id: 'px-2', label: 'residential-us-1', url: 'socks5://us1.proxy.pool:1080', kind: 'socks5', status: 'healthy', latencyMs: 121, lastCheck: minutesAgo(2) },
    { id: 'px-3', label: 'burner-1', url: 'http://10.8.0.9:3128', kind: 'http', status: 'dead', lastCheck: minutesAgo(15) },
  ];

  return { sessions, runs, agents, edges, findings, shells, listeners, proxy, hosts, loot, chat, servers, proxies, reports: [] };
}

/** Terminal output lines for the mock shell stream, by shell kind. */
export function shellLines(kind: Shell['kind']): string[] {
  if (kind === 'reverse') {
    return [
      'root@web-01:/var/www/app# ls -la',
      'total 48  drwxr-xr-x 6 www-data www-data 4096 config/',
      'root@web-01:/var/www/app# cat /etc/passwd | grep -i sql',
      'mysql:x:114:120:MySQL Server,,,:/nonexistent:/bin/false',
      'root@web-01:/var/www/app# id',
      'uid=0(root) gid=0(root) groups=0(root)',
    ];
  }
  if (kind === 'tool') {
    return [
      '[INFO] testing connection to the target URL',
      "[INFO] parameter 'q' is 'MySQL error-based' injectable",
      '[INFO] fetching database names',
      'available databases [4]: acme_prod, information_schema, mysql, sys',
      '[INFO] fetching tables for database: acme_prod',
    ];
  }
  return [
    'operator@kali:~/sessions/acme$ ls loot/',
    'creds.txt  users_dump.csv  jwt_forged.txt  subdomains.txt',
    'operator@kali:~/sessions/acme$ wc -l loot/users_dump.csv',
    '1284 loot/users_dump.csv',
  ];
}
