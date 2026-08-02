import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useProxyById, useRemoveProxy, useTestProxy, useUpdateProxy } from '@/features/hooks';
import { Button, Empty, Spinner, StatusDot } from '@/components/ui/primitives';
import { Field, Segmented, TextInput } from '@/components/ui/fields';
import { Icon } from '@/components/ui/Icon';
import { toast } from '@/components/ui/toast';
import { PageShell } from './PageShell';
import { proxyTone } from './parts';
import type { Proxy, ProxyTestResult } from '@redcell/api-client';

function Fact({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="font-mono text-[9.5px] uppercase tracking-wider text-faint">{label}</span>
      <span className="font-mono text-[12px] text-text">{value}</span>
    </div>
  );
}

export function ProxyDetailPage() {
  const { id = '' } = useParams();
  const nav = useNavigate();
  const { data: proxy, isLoading } = useProxyById(id);
  const test = useTestProxy();
  const update = useUpdateProxy();
  const remove = useRemoveProxy();
  const [result, setResult] = useState<ProxyTestResult | null>(null);
  const [edit, setEdit] = useState(false);
  const [form, setForm] = useState({
    label: '',
    url: '',
    kind: 'http' as Proxy['kind'],
    auth: 'open' as 'open' | 'credentials',
    username: '',
    password: '',
  });

  if (isLoading) return <div className="grid h-full place-items-center"><Spinner /></div>;
  if (!proxy) return <Empty>Proxy not found.</Empty>;

  const runTest = async () => {
    const r = await test.mutateAsync(proxy.id);
    setResult(r);
    toast(r.ok ? `Healthy (${r.latencyMs ?? '?'} ms)` : `Proxy dead: ${r.error ?? 'unknown'}`, r.ok ? 'success' : 'error');
  };

  const startEdit = () => {
    setForm({
      label: proxy.label,
      url: proxy.url,
      kind: proxy.kind,
      auth: proxy.auth ?? 'open',
      username: proxy.username ?? '',
      password: '',
    });
    setEdit(true);
  };

  const saveEdit = async () => {
    await update.mutateAsync({
      id: proxy.id,
      input: {
        label: form.label.trim(),
        url: form.url.trim(),
        kind: form.kind,
        auth: form.auth,
        username: form.auth === 'credentials' ? form.username.trim() : undefined,
        ...(form.auth === 'credentials' && form.password ? { password: form.password } : {}),
      },
    });
    setEdit(false);
    setResult(null);
    toast('Proxy updated', 'success');
  };

  const del = async () => {
    await remove.mutateAsync(proxy.id);
    toast('Proxy removed', 'success');
    nav('/proxies');
  };

  return (
    <PageShell
      title={proxy.label}
      subtitle={`${proxy.kind} · ${proxy.url}`}
      actions={
        <>
          <button
            onClick={() => nav('/proxies')}
            className="flex items-center gap-1.5 rounded-[var(--radius)] px-2 py-1.5 text-xs font-semibold text-muted hover:bg-panel hover:text-text"
          >
            <Icon name="chevronLeft" size={15} />
            Proxies
          </button>
          <Button variant="primary" disabled={test.isPending} onClick={() => void runTest()}>
            {test.isPending ? 'Testing...' : 'Test proxy'}
          </Button>
          <Button onClick={() => void del()}>Delete</Button>
        </>
      }
    >
      <div className="grid max-w-[860px] gap-4 p-5">
        <div className="rounded-[var(--radius)] border border-border bg-bg2 p-4">
          <div className="mb-3 flex items-center justify-between">
            <div className="font-mono text-[10px] uppercase tracking-[0.14em] text-faint">Health</div>
            <span className="inline-flex items-center gap-2 font-mono text-[11px]">
              <StatusDot color={proxyTone(proxy.status)} glow={proxy.status === 'healthy'} />
              {proxy.status}
            </span>
          </div>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <Fact label="Latency" value={proxy.latencyMs != null ? `${proxy.latencyMs} ms` : '—'} />
            <Fact label="Egress IP" value={proxy.egressIp || '—'} />
            <Fact label="Last check" value={proxy.lastCheck ? new Date(proxy.lastCheck).toLocaleString() : 'never'} />
            <Fact label="Auth" value={proxy.auth === 'credentials' ? 'credentials (encrypted)' : 'open'} />
          </div>
          {proxy.status === 'dead' && proxy.lastError ? (
            <div className="mt-3 rounded-[var(--radius)] border border-crit bg-panel2 px-3 py-2 font-mono text-[11px] text-crit">
              {proxy.lastError}
            </div>
          ) : null}
          {result?.output ? (
            <pre className="mt-3 max-h-40 overflow-auto rounded-[var(--radius)] border border-border2 bg-black p-3 font-mono text-[11px] leading-relaxed text-muted">
{result.output}
            </pre>
          ) : (
            <div className="mt-3 text-[11px] text-faint">
              Run "Test proxy" to fetch your egress IP through it and confirm it forwards traffic.
            </div>
          )}
        </div>

        <div className="rounded-[var(--radius)] border border-border bg-bg2 p-4">
          <div className="mb-3 flex items-center justify-between">
            <div className="font-mono text-[10px] uppercase tracking-[0.14em] text-faint">Configuration</div>
            {!edit ? (
              <button onClick={startEdit} className="text-[11px] font-semibold text-muted hover:text-text">
                Edit
              </button>
            ) : null}
          </div>
          {!edit ? (
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
              <Fact label="Label" value={proxy.label} />
              <Fact label="Kind" value={proxy.kind} />
              <Fact label="URL" value={proxy.url} />
              <Fact label="Username" value={proxy.username || '—'} />
            </div>
          ) : (
            <div className="grid gap-3.5">
              <Field label="Label">
                <TextInput value={form.label} onChange={(e) => setForm((f) => ({ ...f, label: e.target.value }))} />
              </Field>
              <Field label="URL" hint="http://host:8080 or socks5://host:1080">
                <TextInput value={form.url} onChange={(e) => setForm((f) => ({ ...f, url: e.target.value }))} />
              </Field>
              <Field label="Kind">
                <Segmented
                  value={form.kind}
                  options={[
                    { value: 'http', label: 'HTTP' },
                    { value: 'https', label: 'HTTPS' },
                    { value: 'socks5', label: 'SOCKS5' },
                  ]}
                  onChange={(v) => setForm((f) => ({ ...f, kind: v }))}
                />
              </Field>
              <Field label="Auth">
                <Segmented
                  value={form.auth}
                  options={[
                    { value: 'open', label: 'Open' },
                    { value: 'credentials', label: 'Credentials' },
                  ]}
                  onChange={(v) => setForm((f) => ({ ...f, auth: v }))}
                />
              </Field>
              {form.auth === 'credentials' ? (
                <div className="grid grid-cols-2 gap-3.5">
                  <Field label="Username">
                    <TextInput value={form.username} onChange={(e) => setForm((f) => ({ ...f, username: e.target.value }))} />
                  </Field>
                  <Field label="Password" hint="Blank keeps the existing one.">
                    <TextInput type="password" value={form.password} onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))} />
                  </Field>
                </div>
              ) : null}
              <div className="flex items-center gap-2">
                <Button variant="primary" disabled={update.isPending} onClick={() => void saveEdit()}>
                  Save
                </Button>
                <Button onClick={() => setEdit(false)}>Cancel</Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </PageShell>
  );
}
