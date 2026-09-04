import { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAvailableModels, useCreateSession, useProxies, useServers } from '@/features/hooks';
import { useApi } from '@/lib/api';
import { Markdown } from '@/components/ui/Markdown';
import { Thinking } from '@/components/ui/Thinking';
import { toast } from '@/components/ui/toast';
import type { SessionKind } from '@redcell/api-client';

type Msg = { id: string; role: 'operator' | 'assistant'; text: string };
type Draft = {
  kind: SessionKind;
  name: string;
  client: string;
  targets: string;
  scope: string;
  roe: string;
  brief: string;
  source: string;
  serverId: string;
  proxyId: string;
  provider: string;
  model: string;
};

const apiBase = (import.meta.env.VITE_API_BASE_URL ?? '/api/v1') as string;
const lines = (s: string) => [...new Set(s.split('\n').map((x) => x.trim()).filter(Boolean))];
let seq = 0;
const mkMsg = (role: Msg['role'], text: string): Msg => ({ id: `m${++seq}`, role, text });

export function NewSessionPage() {
  const nav = useNavigate();
  const api = useApi();
  const create = useCreateSession();
  const { data: servers } = useServers();
  const { data: proxies } = useProxies();
  const { data: models } = useAvailableModels();

  const [draft, setDraft] = useState<Draft>({
    kind: 'network',
    name: '',
    client: '',
    targets: '',
    scope: '',
    roe: '',
    brief: '',
    source: '',
    serverId: '',
    proxyId: '',
    provider: '',
    model: '',
  });
  const [files, setFiles] = useState<File[]>([]);
  const [messages, setMessages] = useState<Msg[]>([
    mkMsg(
      'assistant',
      "Tell me what you want to test and I'll help scope it: a URL, a domain, a wildcard like *.example.com, or an IP range. Switch to Code scan to review a repo. I'll draft the session on the right as we go.",
    ),
  ]);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const scroller = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = scroller.current;
    if (el) el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' });
  }, [messages.length, busy]);

  const modelOptions = useMemo(
    () => [
      { id: '', label: 'Default (from Settings)' },
      ...(models ?? []).map((m) => ({ id: `${m.provider}::${m.model}`, label: `${m.model} · ${m.providerLabel}` })),
    ],
    [models],
  );

  const patch = (p: Partial<Draft>) => setDraft((d) => ({ ...d, ...p }));
  const isCode = draft.kind === 'code';
  const canCreate =
    draft.name.trim().length > 0 &&
    (isCode ? draft.source.trim().length > 0 : lines(draft.targets).length > 0 || lines(draft.scope).length > 0);

  const send = async () => {
    const text = input.trim();
    if (!text || busy) return;
    setInput('');
    const history = [...messages, mkMsg('operator', text)];
    setMessages(history);
    setBusy(true);
    try {
      const res = await api.ai.draftChat({
        messages: history.map((m) => ({ role: m.role === 'operator' ? 'user' : 'assistant', content: m.text })),
      });
      setMessages((m) => [...m, mkMsg('assistant', res.reply)]);
      const p = res.proposal;
      if (p) {
        setDraft((d) => ({
          ...d,
          name: p.name ?? d.name,
          client: p.client ?? d.client,
          scope: p.scope && p.scope.length ? p.scope.join('\n') : d.scope,
          targets: p.targets && p.targets.length ? p.targets.join('\n') : d.targets,
          brief: p.brief ?? d.brief,
        }));
      }
    } catch {
      setMessages((m) => [
        ...m,
        mkMsg('assistant', 'Something went wrong reaching the model. Check the provider key in Settings and try again.'),
      ]);
    } finally {
      setBusy(false);
    }
  };

  const onCreate = async () => {
    if (!canCreate) return;
    const created = await create.mutateAsync({
      name: draft.name.trim(),
      client: draft.client.trim() || 'Unknown',
      kind: draft.kind,
      source: isCode ? draft.source.trim() : undefined,
      targets: isCode ? [] : lines(draft.targets),
      scope: isCode ? [] : lines(draft.scope),
      roe: draft.roe.trim() || undefined,
      brief: draft.brief.trim() || undefined,
      serverId: draft.serverId || undefined,
      proxyId: draft.proxyId || undefined,
      provider: draft.provider || undefined,
      model: draft.model || undefined,
    });
    for (const f of files) {
      const fd = new FormData();
      fd.append('file', f);
      fd.append('kind', 'assessment');
      try {
        const res = await fetch(`${apiBase}/sessions/${created.id}/files`, { method: 'POST', body: fd, credentials: 'include' });
        if (!res.ok) throw new Error(String(res.status));
      } catch {
        toast(`Could not upload ${f.name}`, 'error');
      }
    }
    toast('Session created', 'success');
    nav(`/sessions/${created.id}`);
  };

  return (
    <div className="wrap">
      <div className="split">
        <div className="card chatcard">
          <div className="card-h" style={{ padding: '13px 16px 12px', borderBottom: '1px solid var(--line-soft)' }}>
            <h3>Plan the engagement</h3>
            <span className="cs">· AI planner</span>
          </div>
          <div className="cscroll" ref={scroller}>
            {messages.map((m) => (
              <div key={m.id} className={`msg ${m.role === 'operator' ? 'op' : 'as'} msg-in`}>
                <div className="who">{m.role === 'operator' ? 'you' : 'planner'}</div>
                <div className="bub">{m.role === 'operator' ? m.text : <Markdown>{m.text}</Markdown>}</div>
              </div>
            ))}
            {busy ? <Thinking /> : null}
          </div>
          <div className="composer">
            <input
              className="input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && void send()}
              placeholder="Describe the target…"
            />
            <button className="csend" onClick={send} disabled={!input.trim() || busy}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path d="M4 12l16-7-7 16-2-7-7-2z" />
              </svg>
            </button>
          </div>
        </div>

        <div className="card">
          <div className="card-b">
            <label className="field">
              <span className="label">Name</span>
              <input className="input" value={draft.name} placeholder="ACME External Q3" onChange={(e) => patch({ name: e.target.value })} />
            </label>
            <div className="grid2">
              <label className="field">
                <span className="label">Client</span>
                <input className="input" value={draft.client} placeholder="ACME Corp" onChange={(e) => patch({ client: e.target.value })} />
              </label>
              <div className="field">
                <span className="label">Type</span>
                <div className="seg">
                  <button className={draft.kind === 'network' ? 'on' : ''} onClick={() => patch({ kind: 'network' })}>
                    Network
                  </button>
                  <button className={draft.kind === 'code' ? 'on' : ''} onClick={() => patch({ kind: 'code' })}>
                    Code
                  </button>
                </div>
              </div>
            </div>

            {isCode ? (
              <label className="field">
                <span className="label">
                  Source <span className="opt">(git URL or local folder)</span>
                </span>
                <input className="input mono" value={draft.source} placeholder="https://github.com/org/repo" onChange={(e) => patch({ source: e.target.value })} />
              </label>
            ) : (
              <>
                <label className="field">
                  <span className="label">
                    Scope <span className="opt">(domains, wildcards, CIDRs)</span>
                  </span>
                  <textarea className="textarea mono" value={draft.scope} placeholder={'*.example.com\n10.0.0.0/24'} onChange={(e) => patch({ scope: e.target.value })} />
                </label>
                <label className="field">
                  <span className="label">
                    Targets <span className="opt">(concrete URLs / IPs)</span>
                  </span>
                  <textarea className="textarea mono" value={draft.targets} placeholder={'https://app.example.com'} onChange={(e) => patch({ targets: e.target.value })} />
                </label>
              </>
            )}

            <div className="grid2">
              <label className="field">
                <span className="label">Execution server</span>
                <select className="selectn" value={draft.serverId} onChange={(e) => patch({ serverId: e.target.value })}>
                  <option value="">Local (this host)</option>
                  {(servers ?? []).map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name}
                    </option>
                  ))}
                </select>
              </label>
              <label className="field">
                <span className="label">
                  Egress proxy <span className="opt">(optional)</span>
                </span>
                <select className="selectn" value={draft.proxyId} onChange={(e) => patch({ proxyId: e.target.value })}>
                  <option value="">Direct (no proxy)</option>
                  {(proxies ?? []).map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.label}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <label className="field">
              <span className="label">Model</span>
              <select
                className="selectn"
                value={draft.model ? `${draft.provider}::${draft.model}` : ''}
                onChange={(e) => {
                  const id = e.target.value;
                  if (!id) return patch({ provider: '', model: '' });
                  const [provider, model] = id.split('::');
                  patch({ provider: provider ?? '', model: model ?? '' });
                }}
              >
                {modelOptions.map((o) => (
                  <option key={o.id} value={o.id}>
                    {o.label}
                  </option>
                ))}
              </select>
            </label>

            <label className="field">
              <span className="label">Rules of engagement</span>
              <textarea className="textarea" value={draft.roe} rows={2} placeholder="Testing window, no-DoS, exclusions…" onChange={(e) => patch({ roe: e.target.value })} />
            </label>
            <label className="field">
              <span className="label">
                Engagement brief <span className="opt">(handed to the agents)</span>
              </span>
              <textarea className="textarea" value={draft.brief} rows={4} placeholder="What to focus on, what to skip, the objective…" onChange={(e) => patch({ brief: e.target.value })} />
            </label>

            <div className="field">
              <span className="label">
                Assessment files <span className="opt">(staged at /root/assessment)</span>
              </span>
              <div style={{ display: 'grid', gap: 6 }}>
                {files.map((f, i) => (
                  <div key={`${f.name}-${i}`} className="formrow" style={{ padding: '8px 0' }}>
                    <span className="mono meta">{f.name}</span>
                    <button className="btn sm ghost" onClick={() => setFiles((xs) => xs.filter((_, j) => j !== i))}>
                      Remove
                    </button>
                  </div>
                ))}
                <label className="btn ghost" style={{ borderStyle: 'dashed', borderColor: 'var(--line)', justifyContent: 'center', cursor: 'pointer' }}>
                  <svg viewBox="0 0 24 24">
                    <path d="M12 5v14M5 12h14" />
                  </svg>
                  Add files
                  <input
                    type="file"
                    multiple
                    style={{ display: 'none' }}
                    onChange={(e) => {
                      const picked = Array.from(e.target.files ?? []);
                      if (picked.length) setFiles((xs) => [...xs, ...picked]);
                      e.target.value = '';
                    }}
                  />
                </label>
              </div>
            </div>

            <div style={{ display: 'flex', gap: 8, marginTop: 4 }}>
              <button className="btn pri" style={{ flex: 1, justifyContent: 'center' }} disabled={!canCreate || create.isPending} onClick={onCreate}>
                Create session
              </button>
              <button className="btn" onClick={() => nav('/sessions')}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
