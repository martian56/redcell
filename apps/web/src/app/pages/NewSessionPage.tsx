import { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { cn } from '@/lib/cn';
import { useAvailableModels, useCreateSession, useProxies, useServers } from '@/features/hooks';
import { useApi } from '@/lib/api';
import { Button } from '@/components/ui/primitives';
import { Field, Segmented, SelectTrigger, TextInput } from '@/components/ui/fields';
import { Combobox } from '@/components/ui/Combobox';
import { Markdown } from '@/components/ui/Markdown';
import { Icon } from '@/components/ui/Icon';
import { Thinking } from '@/components/ui/Thinking';
import { toast } from '@/components/ui/toast';
import type { SessionKind } from '@redcell/api-client';

type Msg = { id: string; role: 'operator' | 'assistant'; text: string };
type Opt = { id: string; label: string; sub?: string };
type Draft = {
  kind: SessionKind;
  name: string;
  client: string;
  targets: string[];
  scope: string[];
  roe: string;
  brief: string;
  source: string;
  serverId: string;
  proxyId: string;
  provider: string;
  model: string;
};

const apiBase = (import.meta.env.VITE_API_BASE_URL ?? '/api/v1') as string;

function dedupe(a: string[]): string[] {
  return [...new Set(a)];
}

function Chip({ text, onRemove }: { text: string; onRemove: () => void }) {
  return (
    <span className="flex items-center gap-1 rounded-[4px] bg-elev px-2 py-0.5 font-mono text-[11px] text-text">
      {text}
      <button onClick={onRemove} className="text-faint hover:text-crit">
        <Icon name="close" size={11} />
      </button>
    </span>
  );
}

function ChipInput({
  label,
  hint,
  items,
  onAdd,
  onRemove,
  placeholder,
}: {
  label: string;
  hint?: string;
  items: string[];
  onAdd: (v: string) => void;
  onRemove: (v: string) => void;
  placeholder: string;
}) {
  const [v, setV] = useState('');
  return (
    <Field label={label} hint={hint}>
      <div className="flex flex-wrap gap-1.5 rounded-[var(--radius)] border border-border2 bg-black p-2">
        {items.map((it) => (
          <Chip key={it} text={it} onRemove={() => onRemove(it)} />
        ))}
        <input
          value={v}
          onChange={(e) => setV(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && v.trim()) {
              onAdd(v.trim());
              setV('');
              e.preventDefault();
            }
          }}
          placeholder={items.length ? 'add...' : placeholder}
          className="min-w-[120px] flex-1 bg-transparent px-1 font-mono text-[12px] text-text outline-none placeholder:text-faint"
        />
      </div>
    </Field>
  );
}

/** Labelled Combobox rendering the current option in a select-style box. */
function PickerField({
  label,
  hint,
  options,
  value,
  onChange,
  placeholder,
}: {
  label: string;
  hint?: string;
  options: Opt[];
  value: string;
  onChange: (id: string) => void;
  placeholder: string;
}) {
  const current = options.find((o) => o.id === value) ?? options[0];
  return (
    <Field label={label} hint={hint}>
      <Combobox<Opt>
        block
        items={options}
        current={current}
        getKey={(o) => o.id}
        getLabel={(o) => o.label}
        getSublabel={(o) => o.sub ?? ''}
        onSelect={(o) => onChange(o.id)}
        placeholder={placeholder}
        trigger={<SelectTrigger>{current ? current.label : placeholder}</SelectTrigger>}
      />
    </Field>
  );
}

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
    targets: [],
    scope: [],
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
      "Tell me what you want to test and I'll help scope it: a URL, a domain, a wildcard like *.example.com, or an IP range. For a code review, switch the type to Code scan and point me at a public repo or a local folder. I'll draft the session on the right as we go.",
    ),
  ]);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const scroller = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = scroller.current;
    if (el) el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' });
  }, [messages.length, busy]);

  const serverOptions = useMemo<Opt[]>(
    () => [
      { id: '', label: 'Local (this host)', sub: 'runs in the local Kali container' },
      ...(servers ?? []).map((s) => ({ id: s.id, label: s.name, sub: `${s.username ?? 'root'}@${s.host}` })),
    ],
    [servers],
  );
  const proxyOptions = useMemo<Opt[]>(
    () => [
      { id: '', label: 'Direct (no proxy)', sub: 'traffic egresses locally' },
      ...(proxies ?? []).map((p) => ({ id: p.id, label: p.label, sub: `${p.kind} · ${p.url}` })),
    ],
    [proxies],
  );
  const modelOptions = useMemo<Opt[]>(
    () => [
      { id: '', label: 'Default (from Settings)', sub: 'use the configured model' },
      ...(models ?? []).map((m) => ({ id: `${m.provider}::${m.model}`, label: m.model, sub: m.providerLabel })),
    ],
    [models],
  );

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
          scope: p.scope && p.scope.length ? dedupe(p.scope) : d.scope,
          targets: p.targets && p.targets.length ? dedupe(p.targets) : d.targets,
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

  const isCode = draft.kind === 'code';
  const canCreate =
    draft.name.trim().length > 0 &&
    (isCode ? draft.source.trim().length > 0 : draft.targets.length > 0 || draft.scope.length > 0);

  const onCreate = async () => {
    if (!canCreate) return;
    const [provider, model] = draft.model ? [draft.provider, draft.model] : ['', ''];
    const created = await create.mutateAsync({
      name: draft.name.trim(),
      client: draft.client.trim() || 'Unknown',
      kind: draft.kind,
      source: isCode ? draft.source.trim() : undefined,
      targets: isCode ? [] : draft.targets,
      scope: isCode ? [] : draft.scope,
      roe: draft.roe.trim() || undefined,
      brief: draft.brief.trim() || undefined,
      serverId: draft.serverId || undefined,
      proxyId: draft.proxyId || undefined,
      provider: provider || undefined,
      model: model || undefined,
    });
    for (const f of files) {
      const fd = new FormData();
      fd.append('file', f);
      fd.append('kind', 'assessment');
      try {
        await fetch(`${apiBase}/sessions/${created.id}/files`, {
          method: 'POST',
          body: fd,
          credentials: 'include',
        });
      } catch {
        toast(`Could not upload ${f.name}`, 'error');
      }
    }
    toast('Session created', 'success');
    nav(`/sessions/${created.id}`);
  };

  const patch = (p: Partial<Draft>) => setDraft((d) => ({ ...d, ...p }));

  return (
    <div className="flex h-full flex-col">
      <header className="flex h-[52px] flex-none items-center gap-3 border-b border-border bg-bg2 px-5">
        <button
          onClick={() => nav('/sessions')}
          className="flex items-center gap-1.5 rounded-[var(--radius)] px-2 py-1.5 text-xs font-semibold text-muted hover:bg-panel hover:text-text"
        >
          <Icon name="chevronLeft" size={15} />
          Sessions
        </button>
        <div className="flex flex-col leading-tight">
          <span className="text-[13px] font-bold">New session</span>
          <span className="text-[11px] text-faint">Talk to the setup agent, then create</span>
        </div>
        <div className="flex-1" />
        <Button variant="primary" disabled={!canCreate || create.isPending} onClick={onCreate}>
          Create session
        </Button>
      </header>

      <div className="grid min-h-0 flex-1 grid-cols-[1fr_400px]">
        <div className="flex min-h-0 flex-col border-r border-border">
          <div ref={scroller} className="flex min-h-0 flex-1 flex-col gap-2.5 overflow-auto p-4">
            {messages.map((m) => (
              <div
                key={m.id}
                className={cn(
                  'msg-in max-w-[80%] whitespace-pre-wrap rounded-[var(--radius)] px-3 py-2 text-xs leading-relaxed',
                  m.role === 'operator'
                    ? 'self-end bg-accent-dim text-accent-ink'
                    : 'self-start border border-border bg-panel2 text-text',
                )}
              >
                {m.role === 'operator' ? m.text : <Markdown>{m.text}</Markdown>}
              </div>
            ))}
            {busy ? <Thinking /> : null}
          </div>
          <div className="flex flex-none items-center gap-2 border-t border-border bg-bg2 p-2">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') void send();
              }}
              placeholder="Describe the target, scope, objectives..."
              className="h-9 flex-1 rounded-[var(--radius)] border border-border2 bg-black px-3 text-[13px] text-text outline-none placeholder:text-faint focus:border-accent"
            />
            <Button variant="primary" onClick={send} disabled={!input.trim() || busy}>
              Send
            </Button>
          </div>
        </div>

        <div className="min-h-0 overflow-auto bg-bg2 p-4">
          <div className="mb-3 font-mono text-[10px] uppercase tracking-[0.14em] text-faint">Session draft</div>
          <div className="grid gap-3.5">
            <Field label="Type">
              <Segmented<SessionKind>
                value={draft.kind}
                onChange={(kind) => patch({ kind })}
                options={[
                  { value: 'network', label: 'Network / Web' },
                  { value: 'code', label: 'Code scan' },
                ]}
              />
            </Field>
            <Field label="Name">
              <TextInput value={draft.name} placeholder="ACME External Q3" onChange={(e) => patch({ name: e.target.value })} />
            </Field>
            <Field label="Client">
              <TextInput value={draft.client} placeholder="ACME Corp" onChange={(e) => patch({ client: e.target.value })} />
            </Field>

            {isCode ? (
              <Field label="Source" hint="A public git repo URL (https://github.com/org/repo) or a local folder path.">
                <TextInput
                  value={draft.source}
                  placeholder="https://github.com/org/repo"
                  onChange={(e) => patch({ source: e.target.value })}
                />
              </Field>
            ) : (
              <>
                <ChipInput
                  label="Targets"
                  hint="Specific URLs, hosts, or IP ranges to test."
                  items={draft.targets}
                  placeholder="https://app.example.com"
                  onAdd={(v) => patch({ targets: dedupe([...draft.targets, v]) })}
                  onRemove={(v) => patch({ targets: draft.targets.filter((x) => x !== v) })}
                />
                <ChipInput
                  label="Scope"
                  hint="Allowed boundary. Wildcards allowed. Empty means unrestricted."
                  items={draft.scope}
                  placeholder="*.example.com"
                  onAdd={(v) => patch({ scope: dedupe([...draft.scope, v]) })}
                  onRemove={(v) => patch({ scope: draft.scope.filter((x) => x !== v) })}
                />
              </>
            )}

            <PickerField
              label="Model"
              hint="Which model runs this session. Defaults to your Settings model."
              options={modelOptions}
              value={draft.model ? `${draft.provider}::${draft.model}` : ''}
              onChange={(id) => {
                if (!id) return patch({ provider: '', model: '' });
                const [provider, model] = id.split('::');
                patch({ provider, model });
              }}
              placeholder="Search models..."
            />
            <PickerField
              label="Execution server"
              hint="Where commands run. Local uses the on-host Kali container; a saved server runs over SSH."
              options={serverOptions}
              value={draft.serverId}
              onChange={(serverId) => patch({ serverId })}
              placeholder="Search servers..."
            />
            <PickerField
              label="Proxy"
              hint="Route tool traffic through a saved proxy, or go direct."
              options={proxyOptions}
              value={draft.proxyId}
              onChange={(proxyId) => patch({ proxyId })}
              placeholder="Search proxies..."
            />

            <Field label="Rules of engagement">
              <textarea
                value={draft.roe}
                onChange={(e) => patch({ roe: e.target.value })}
                rows={3}
                placeholder="Testing window, no-DoS, exclusions..."
                className="w-full rounded-[var(--radius)] border border-border2 bg-black px-3 py-2 text-[13px] text-text outline-none placeholder:text-faint focus:border-accent"
              />
            </Field>

            <Field label="Engagement brief" hint="Objectives and constraints handed to the agents. Drafted from the chat; edit freely.">
              <textarea
                value={draft.brief}
                onChange={(e) => patch({ brief: e.target.value })}
                rows={4}
                placeholder="What to focus on, what to skip, the objective..."
                className="w-full rounded-[var(--radius)] border border-border2 bg-black px-3 py-2 text-[13px] text-text outline-none placeholder:text-faint focus:border-accent"
              />
            </Field>

            <Field label="Assessment files" hint="Files the agents work on (a binary, a pcap). Staged in the container at /root/assessment.">
              <div className="grid gap-1.5">
                {files.map((f, i) => (
                  <div
                    key={`${f.name}-${i}`}
                    className="flex items-center justify-between rounded-[var(--radius)] border border-border2 bg-black px-2.5 py-1.5 font-mono text-[11px] text-text"
                  >
                    <span className="truncate">{f.name}</span>
                    <button
                      onClick={() => setFiles((xs) => xs.filter((_, j) => j !== i))}
                      className="flex-none text-faint hover:text-crit"
                    >
                      <Icon name="close" size={12} />
                    </button>
                  </div>
                ))}
                <label className="flex cursor-pointer items-center justify-center gap-1.5 rounded-[var(--radius)] border border-dashed border-border2 px-2.5 py-2 text-[12px] text-muted hover:border-accent hover:text-text">
                  <Icon name="plus" size={13} />
                  Add files
                  <input
                    type="file"
                    multiple
                    className="hidden"
                    onChange={(e) => {
                      const picked = Array.from(e.target.files ?? []);
                      if (picked.length) setFiles((xs) => [...xs, ...picked]);
                      e.target.value = '';
                    }}
                  />
                </label>
              </div>
            </Field>
          </div>
        </div>
      </div>
    </div>
  );
}
