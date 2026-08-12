import { beforeEach, describe, expect, it } from 'vitest';
import { createMockClient, type ApiClient } from '@redcell/api-client';

// The mock client backs the app with no server. Every test gets a fresh
// in-memory dataset so cases never see each other's writes.
let client: ApiClient;
beforeEach(() => {
  client = createMockClient();
});

describe('sessions', () => {
  it('lists the seeded sessions', async () => {
    const sessions = await client.sessions.list();
    expect(sessions.length).toBeGreaterThan(0);
  });

  it('creates a session and makes it retrievable', async () => {
    const created = await client.sessions.create({
      name: 'Acme test',
      client: 'Acme',
      scope: ['*.acme.test'],
      targets: ['https://acme.test'],
    });
    expect(created.id).toBeTruthy();
    expect(created.status).toBe('active');
    const fetched = await client.sessions.get(created.id);
    expect(fetched.name).toBe('Acme test');
  });

  it('throws for an unknown session id', async () => {
    await expect(client.sessions.get('ses-nope')).rejects.toThrow();
  });
});

describe('runs', () => {
  it('moves a run through pause, resume, and stop', async () => {
    const [session] = await client.sessions.list();
    expect(session).toBeTruthy();
    const run = await client.runs.create(session!.id, { name: 'r', model: 'kimi-k3' });
    expect(run.status).toBe('running');
    expect((await client.runs.pause(run.id)).status).toBe('paused');
    expect((await client.runs.resume(run.id)).status).toBe('running');
    expect((await client.runs.stop(run.id)).status).toBe('stopped');
  });
});

describe('findings', () => {
  it('marks a finding verified', async () => {
    const sessions = await client.sessions.list();
    let target;
    for (const s of sessions) {
      const findings = await client.findings.list(s.id);
      if (findings.length) {
        target = findings[0];
        break;
      }
    }
    expect(target, 'expected a fixture finding to verify').toBeTruthy();
    const verified = await client.findings.verify(target!.id);
    expect(verified.status).toBe('verified');
  });
});

describe('servers.test', () => {
  it('reports a reachable private host as connected', async () => {
    const server = await client.servers.create({ name: 'lab', host: '10.0.0.5', username: 'root' });
    const result = await client.servers.test(server.id);
    expect(result.ok).toBe(true);
    expect(result.status).toBe('connected');
  });

  it('reports an arbitrary public host as an error', async () => {
    const server = await client.servers.create({ name: 'wan', host: 'scanme.example.com', username: 'root' });
    const result = await client.servers.test(server.id);
    expect(result.ok).toBe(false);
    expect(result.status).toBe('error');
  });
});

describe('proxies.test', () => {
  it('marks a normal proxy healthy', async () => {
    const proxy = await client.proxies.create({ label: 'p', url: 'http://1.2.3.4:8080', kind: 'http', auth: 'open' });
    const result = await client.proxies.test(proxy.id);
    expect(result.ok).toBe(true);
    expect(result.status).toBe('healthy');
  });

  it('marks a proxy on the 10.8.x tunnel dead', async () => {
    const proxy = await client.proxies.create({ label: 'vpn', url: 'socks5://10.8.0.1:1080', kind: 'socks5', auth: 'open' });
    const result = await client.proxies.test(proxy.id);
    expect(result.ok).toBe(false);
    expect(result.status).toBe('dead');
  });
});

describe('settings', () => {
  it('round-trips a saved settings object', async () => {
    const current = await client.settings.get();
    const next = { ...current, report: { ...current.report, companyName: 'Test Co' } };
    const saved = await client.settings.save(next);
    expect(saved.report.companyName).toBe('Test Co');
    expect((await client.settings.get()).report.companyName).toBe('Test Co');
  });

  it('lists keyless providers in the available models regardless of stored keys', async () => {
    const models = await client.settings.availableModels();
    // Ollama needs no key, so at least one of its models is always available.
    expect(models.some((m) => m.provider === 'ollama')).toBe(true);
  });
});
