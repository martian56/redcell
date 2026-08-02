import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useRemoveServer, useServer, useTestServer, useUpdateServer } from '@/features/hooks';
import { Button, Empty, Spinner, StatusDot } from '@/components/ui/primitives';
import { Field, Segmented, TextInput } from '@/components/ui/fields';
import { Icon } from '@/components/ui/Icon';
import { toast } from '@/components/ui/toast';
import { PageShell } from './PageShell';
import { serverTone } from './parts';
import type { ServerTestResult } from '@redcell/api-client';

function Fact({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="font-mono text-[9.5px] uppercase tracking-wider text-faint">{label}</span>
      <span className="font-mono text-[12px] text-text">{value}</span>
    </div>
  );
}

export function ServerDetailPage() {
  const { id = '' } = useParams();
  const nav = useNavigate();
  const { data: server, isLoading } = useServer(id);
  const test = useTestServer();
  const update = useUpdateServer();
  const remove = useRemoveServer();
  const [result, setResult] = useState<ServerTestResult | null>(null);

  const [edit, setEdit] = useState(false);
  const [form, setForm] = useState({ name: '', host: '', region: '', username: '', authMethod: 'key' as 'key' | 'password', password: '', privateKey: '' });

  if (isLoading) return <div className="grid h-full place-items-center"><Spinner /></div>;
  if (!server) return <Empty>Server not found.</Empty>;

  const runTest = async () => {
    const r = await test.mutateAsync(server.id);
    setResult(r);
    toast(r.ok ? `Connected (${r.latencyMs ?? '?'} ms)` : `Connection failed: ${r.error ?? 'unknown'}`, r.ok ? 'success' : 'error');
  };

  const startEdit = () => {
    setForm({
      name: server.name,
      host: server.host,
      region: server.region ?? '',
      username: server.username ?? 'root',
      authMethod: 'key',
      password: '',
      privateKey: '',
    });
    setEdit(true);
  };

  const saveEdit = async () => {
    await update.mutateAsync({
      id: server.id,
      input: {
        name: form.name.trim(),
        host: form.host.trim(),
        region: form.region.trim(),
        username: form.username.trim(),
        ...(form.authMethod === 'password' && form.password ? { authMethod: 'password', password: form.password } : {}),
        ...(form.authMethod === 'key' && form.privateKey ? { authMethod: 'key', privateKey: form.privateKey } : {}),
      },
    });
    setEdit(false);
    setResult(null);
    toast('Server updated', 'success');
  };

  const del = async () => {
    await remove.mutateAsync(server.id);
    toast('Server removed', 'success');
    nav('/servers');
  };

  return (
    <PageShell
      title={server.name}
      subtitle={`${server.username ?? 'root'}@${server.host}${server.region ? ` · ${server.region}` : ''}`}
      actions={
        <>
          <button
            onClick={() => nav('/servers')}
            className="flex items-center gap-1.5 rounded-[var(--radius)] px-2 py-1.5 text-xs font-semibold text-muted hover:bg-panel hover:text-text"
          >
            <Icon name="chevronLeft" size={15} />
            Servers
          </button>
          <Button variant="primary" disabled={test.isPending} onClick={() => void runTest()}>
            {test.isPending ? 'Testing...' : 'Test connection'}
          </Button>
          <Button onClick={() => void del()}>Delete</Button>
        </>
      }
    >
      <div className="grid max-w-[860px] gap-4 p-5">
        <div className="rounded-[var(--radius)] border border-border bg-bg2 p-4">
          <div className="mb-3 flex items-center justify-between">
            <div className="font-mono text-[10px] uppercase tracking-[0.14em] text-faint">Connection</div>
            <span className="inline-flex items-center gap-2 font-mono text-[11px]">
              <StatusDot color={serverTone(server.status)} glow={server.status === 'connected'} />
              {server.status}
            </span>
          </div>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <Fact label="Latency" value={server.latencyMs != null ? `${server.latencyMs} ms` : '—'} />
            <Fact label="Last check" value={server.lastCheck ? new Date(server.lastCheck).toLocaleString() : 'never'} />
            <Fact label="Running sessions" value={String(server.runningSessions)} />
            <Fact label="Auth" value="stored (encrypted)" />
          </div>
          {server.status === 'error' && server.lastError ? (
            <div className="mt-3 rounded-[var(--radius)] border border-crit bg-panel2 px-3 py-2 font-mono text-[11px] text-crit">
              {server.lastError}
            </div>
          ) : null}
          {result?.output ? (
            <pre className="mt-3 max-h-48 overflow-auto rounded-[var(--radius)] border border-border2 bg-black p-3 font-mono text-[11px] leading-relaxed text-muted">
{result.output}
            </pre>
          ) : (
            <div className="mt-3 text-[11px] text-faint">
              Run "Test connection" to SSH in and confirm reachability, then read back the host facts below.
            </div>
          )}
        </div>

        <div className="rounded-[var(--radius)] border border-border bg-bg2 p-4">
          <div className="mb-3 font-mono text-[10px] uppercase tracking-[0.14em] text-faint">Host</div>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <Fact label="Host" value={server.host} />
            <Fact label="Username" value={server.username ?? 'root'} />
            <Fact label="Region" value={server.region || '—'} />
            <Fact label="IP" value={server.ip || '—'} />
            <Fact label="OS" value={server.os || '—'} />
            <Fact label="CPU" value={server.cpu != null ? `${server.cpu} cores` : '—'} />
            <Fact label="RAM" value={server.ramGb != null ? `${server.ramGb} GB` : '—'} />
            <Fact label="Added" value={new Date(server.createdAt).toLocaleDateString()} />
          </div>
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
            <div className="text-[11px] text-faint">Edit to change host, credentials, or region. Saving marks the server unchecked until you test it again.</div>
          ) : (
            <div className="grid gap-3.5">
              <Field label="Name">
                <TextInput value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} />
              </Field>
              <Field label="Host">
                <TextInput value={form.host} onChange={(e) => setForm((f) => ({ ...f, host: e.target.value }))} />
              </Field>
              <Field label="Region">
                <TextInput value={form.region} onChange={(e) => setForm((f) => ({ ...f, region: e.target.value }))} />
              </Field>
              <Field label="SSH username">
                <TextInput value={form.username} onChange={(e) => setForm((f) => ({ ...f, username: e.target.value }))} />
              </Field>
              <Field label="Replace credential (optional)">
                <Segmented
                  value={form.authMethod}
                  options={[
                    { value: 'key', label: 'Private key' },
                    { value: 'password', label: 'Password' },
                  ]}
                  onChange={(v) => setForm((f) => ({ ...f, authMethod: v }))}
                />
              </Field>
              {form.authMethod === 'password' ? (
                <Field label="New password" hint="Leave blank to keep the existing credential.">
                  <TextInput type="password" value={form.password} onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))} />
                </Field>
              ) : (
                <Field label="New private key" hint="Leave blank to keep the existing credential.">
                  <textarea
                    value={form.privateKey}
                    onChange={(e) => setForm((f) => ({ ...f, privateKey: e.target.value }))}
                    rows={3}
                    placeholder="-----BEGIN OPENSSH PRIVATE KEY-----"
                    className="w-full rounded-[var(--radius)] border border-border2 bg-black px-3 py-2 font-mono text-[12px] text-text outline-none placeholder:text-faint focus:border-accent"
                  />
                </Field>
              )}
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
