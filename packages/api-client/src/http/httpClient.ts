// HTTP/WS implementation of ApiClient.

import type { ApiClient, Unsubscribe } from '../client';

function resolveWsUrl(url: string): string {
  if (/^wss?:\/\//i.test(url)) return url;
  if (typeof window === 'undefined') return url;
  const scheme = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const path = url.startsWith('/') ? url : `/${url}`;
  return `${scheme}//${window.location.host}${path}`;
}

export function createHttpClient(baseUrl: string, rawWsUrl: string): ApiClient {
  const wsUrl = resolveWsUrl(rawWsUrl);
  const req = async <T>(path: string, init?: RequestInit): Promise<T> => {
    const res = await fetch(`${baseUrl}${path}`, {
      headers: { 'content-type': 'application/json' },
      credentials: 'include',
      ...init,
    });
    if (!res.ok) throw new Error(`${res.status} ${res.statusText} on ${path}`);
    if (res.status === 204) return undefined as T;
    return (await res.json()) as T;
  };

  const subscribe = (channel: string, id: string, cb: (msg: unknown) => void): Unsubscribe => {
    const ws = new WebSocket(`${wsUrl}/${channel}/${encodeURIComponent(id)}`);
    ws.onmessage = (ev) => {
      try {
        cb(JSON.parse(ev.data as string));
      } catch {
        cb(ev.data);
      }
    };
    return () => ws.close();
  };

  const json = (body: unknown): RequestInit => ({ method: 'POST', body: JSON.stringify(body) });

  const qs = (params?: Record<string, string | number | boolean | undefined>): string => {
    if (!params) return '';
    const sp = new URLSearchParams();
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined && v !== null && v !== '') sp.set(k, String(v));
    }
    const s = sp.toString();
    return s ? `?${s}` : '';
  };

  return {
    auth: {
      firstRun: () => req('/auth/first-run'),
      login: (username, password) => req('/auth/login', json({ username, password })),
      me: () => req('/auth/me'),
      logout: () => req('/auth/logout', { method: 'POST' }),
    },
    sessions: {
      list: (params) => req(`/sessions${qs(params)}`),
      get: (id) => req(`/sessions/${id}`),
      create: (input) => req('/sessions', json(input)),
    },
    runs: {
      list: (sessionId, params) => req(`/sessions/${sessionId}/runs${qs(params)}`),
      get: (id) => req(`/runs/${id}`),
      create: (sessionId, input) => req(`/sessions/${sessionId}/runs`, json(input)),
      pause: (id) => req(`/runs/${id}/pause`, { method: 'POST' }),
      resume: (id) => req(`/runs/${id}/resume`, { method: 'POST' }),
      stop: (id) => req(`/runs/${id}/stop`, { method: 'POST' }),
    },
    agents: {
      graph: (runId) => req(`/runs/${runId}/agents`),
      get: (id) => req(`/agents/${id}`),
    },
    findings: {
      list: (sessionId, params) => req(`/sessions/${sessionId}/findings${qs(params)}`),
      get: (id) => req(`/findings/${id}`),
      verify: (id) => req(`/findings/${id}/verify`, { method: 'POST' }),
      setStatus: (id, status) => req(`/findings/${id}/status`, json({ status })),
      merge: (primaryId, duplicateIds) => req(`/findings/${primaryId}/merge`, json({ duplicateIds })),
    },
    shells: {
      list: (sessionId, params) => req(`/sessions/${sessionId}/shells${qs(params)}`),
      open: (sessionId, input) => req(`/sessions/${sessionId}/shells`, json(input)),
      write: (id, data) => req(`/shells/${id}/write`, json({ data })),
      close: (id) => req(`/shells/${id}`, { method: 'DELETE' }),
    },
    listeners: {
      list: (sessionId, params) => req(`/sessions/${sessionId}/listeners${qs(params)}`),
      start: (sessionId, input) => req(`/sessions/${sessionId}/listeners`, json(input)),
    },
    proxy: {
      history: (sessionId, params) => req(`/sessions/${sessionId}/proxy${qs(params)}`),
    },
    attackSurface: {
      hosts: (sessionId, params) => req(`/sessions/${sessionId}/hosts${qs(params)}`),
    },
    loot: {
      list: (sessionId, params) => req(`/sessions/${sessionId}/loot${qs(params)}`),
    },
    reports: {
      list: (sessionId, params) => req(`/sessions/${sessionId}/reports${qs(params)}`),
      get: (id) => req(`/reports/${id}`),
      create: (sessionId, input) => req(`/sessions/${sessionId}/reports`, json(input)),
      remove: (id) => req(`/reports/${id}`, { method: 'DELETE' }),
    },
    settings: {
      get: () => req('/settings'),
      save: (next) => req('/settings', json(next)),
      providers: () => req('/providers'),
      providerKeys: () => req('/provider-keys'),
      setProviderKey: (input) => req('/provider-keys', json(input)),
      removeProviderKey: (providerId) =>
        req(`/provider-keys/${encodeURIComponent(providerId)}`, { method: 'DELETE' }),
      availableModels: () => req('/models/available'),
    },
    ai: {
      draftChat: (input) => req('/sessions/draft/chat', json(input)),
    },
    servers: {
      list: (params) => req(`/servers${qs(params)}`),
      get: (id) => req(`/servers/${id}`),
      create: (input) => req('/servers', json(input)),
      update: (id, input) => req(`/servers/${id}`, { method: 'PATCH', body: JSON.stringify(input) }),
      test: (id) => req(`/servers/${id}/test`, { method: 'POST' }),
      remove: (id) => req(`/servers/${id}`, { method: 'DELETE' }),
    },
    proxies: {
      list: (params) => req(`/proxies${qs(params)}`),
      get: (id) => req(`/proxies/${id}`),
      create: (input) => req('/proxies', json(input)),
      update: (id, input) => req(`/proxies/${id}`, { method: 'PATCH', body: JSON.stringify(input) }),
      test: (id) => req(`/proxies/${id}/test`, { method: 'POST' }),
      remove: (id) => req(`/proxies/${id}`, { method: 'DELETE' }),
    },
    chat: {
      history: (runId, params) => req(`/runs/${runId}/chat${qs(params)}`),
      send: (runId, text) => req(`/runs/${runId}/chat`, json({ text })),
      subscribe: (runId, cb) => subscribe('chat', runId, (m) => cb(m as never)),
    },
    events: {
      history: (runId, params) => req(`/runs/${runId}/events${qs(params)}`),
      subscribe: (runId, cb) => subscribe('events', runId, (m) => cb(m as never)),
    },
    shellIO: {
      subscribe: (shellId, cb) =>
        subscribe('shell', shellId, (m) => cb(typeof m === 'string' ? m : String(m))),
    },
    browser: {
      start: (sessionId) => req(`/sessions/${sessionId}/browser/start`, { method: 'POST' }),
      control: (sessionId, owner) => req(`/sessions/${sessionId}/browser/control`, json({ owner })),
      vncUrl: (sessionId) => `${wsUrl}/browser/${encodeURIComponent(sessionId)}`,
    },
    system: {
      version: () => req('/system/version'),
      update: () => req('/system/update', { method: 'POST' }),
    },
    notifications: {
      list: () => req('/notifications'),
      markRead: (id) => req(`/notifications/${id}/read`, { method: 'POST' }),
      markAllRead: () => req('/notifications/read-all', { method: 'POST' }),
    },
  };
}
