import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCreateServer, useServers, useTestServer } from '@/features/hooks';
import { Button, StatusDot } from '@/components/ui/primitives';
import { Dialog } from '@/components/ui/Dialog';
import { Field, Segmented, TextInput } from '@/components/ui/fields';
import { Icon } from '@/components/ui/Icon';
import { toast } from '@/components/ui/toast';
import { PageShell } from './PageShell';
import { serverTone, th } from './parts';

export function ServersPage() {
  const nav = useNavigate();
  const { data: servers } = useServers();
  const create = useCreateServer();
  const test = useTestServer();

  const runTest = async (id: string) => {
    const r = await test.mutateAsync(id);
    toast(r.ok ? `Connected (${r.latencyMs ?? '?'} ms)` : `Connection failed: ${r.error ?? 'unknown'}`, r.ok ? 'success' : 'error');
  };
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<{
    name: string;
    host: string;
    region: string;
    username: string;
    authMethod: 'password' | 'key';
    password: string;
    privateKey: string;
  }>({
    name: '',
    host: '',
    region: '',
    username: 'root',
    authMethod: 'key',
    password: '',
    privateKey: '',
  });

  const submit = async () => {
    if (!form.name.trim() || !form.host.trim()) return;
    await create.mutateAsync({
      name: form.name.trim(),
      host: form.host.trim(),
      region: form.region.trim(),
      username: form.username.trim(),
      authMethod: form.authMethod,
      password: form.authMethod === 'password' ? form.password : undefined,
      privateKey: form.authMethod === 'key' ? form.privateKey : undefined,
    });
    setOpen(false);
    setForm({ name: '', host: '', region: '', username: 'root', authMethod: 'key', password: '', privateKey: '' });
    toast('Server added', 'success');
  };

  return (
    <PageShell
      title="Servers"
      subtitle="Remote execution hosts (VPS / remote Docker)"
      actions={
        <Button variant="primary" onClick={() => setOpen(true)}>
          <Icon name="plus" size={14} />
          Add server
        </Button>
      }
    >
      <div className="p-5">
        <div className="overflow-hidden rounded-[var(--radius)] border border-border">
          <table className="w-full border-collapse text-xs">
            <thead>
              <tr>
                <th className={th}>Name</th>
                <th className={th}>Host</th>
                <th className={th}>Region</th>
                <th className={th}>Status</th>
                <th className={th}>Latency</th>
                <th className={th}>Sessions</th>
                <th className={th} />
              </tr>
            </thead>
            <tbody>
              {(servers ?? []).length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-3 py-8 text-center text-faint">
                    No servers yet. Add one, then test the connection.
                  </td>
                </tr>
              ) : null}
              {(servers ?? []).map((s) => (
                <tr
                  key={s.id}
                  onClick={() => nav(`/servers/${s.id}`)}
                  className="cursor-pointer border-b border-border hover:bg-panel2"
                >
                  <td className="px-3 py-2.5 font-mono text-text">{s.name}</td>
                  <td className="px-3 py-2.5 font-mono text-faint">{s.host}</td>
                  <td className="px-3 py-2.5 font-mono text-muted">{s.region ?? '—'}</td>
                  <td className="px-3 py-2.5">
                    <span className="inline-flex items-center gap-2 font-mono text-[11px]">
                      <StatusDot color={serverTone(s.status)} glow={s.status === 'connected'} />
                      {s.status}
                    </span>
                  </td>
                  <td className="px-3 py-2.5 font-mono tabular-nums text-muted">
                    {s.latencyMs != null ? `${s.latencyMs} ms` : '—'}
                  </td>
                  <td className="px-3 py-2.5 font-mono tabular-nums text-text">{s.runningSessions}</td>
                  <td className="px-3 py-2.5 text-right" onClick={(e) => e.stopPropagation()}>
                    <div className="flex items-center justify-end gap-1.5">
                      <button
                        onClick={() => void runTest(s.id)}
                        disabled={test.isPending}
                        className="rounded-[var(--radius)] border border-border2 px-2 py-1 text-[11px] font-semibold text-muted hover:bg-elev hover:text-text disabled:opacity-40"
                        title="Test SSH connection"
                      >
                        Test
                      </button>
                      <Icon name="chevronRight" size={14} className="text-faint" />
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <Dialog
        open={open}
        onClose={() => setOpen(false)}
        title="Add server"
        footer={
          <>
            <Button onClick={() => setOpen(false)}>Cancel</Button>
            <Button variant="primary" disabled={create.isPending} onClick={submit}>
              Add
            </Button>
          </>
        }
      >
        <div className="grid gap-3.5">
          <Field label="Name">
            <TextInput autoFocus value={form.name} placeholder="redcell-ops-3" onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} />
          </Field>
          <Field label="Host" hint="SSH host or Docker endpoint.">
            <TextInput value={form.host} placeholder="1.2.3.4 or ops3.redcell.sh" onChange={(e) => setForm((f) => ({ ...f, host: e.target.value }))} />
          </Field>
          <Field label="Region">
            <TextInput value={form.region} placeholder="eu-central" onChange={(e) => setForm((f) => ({ ...f, region: e.target.value }))} />
          </Field>
          <Field label="SSH username">
            <TextInput value={form.username} onChange={(e) => setForm((f) => ({ ...f, username: e.target.value }))} />
          </Field>
          <Field label="Auth method">
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
            <Field label="Password">
              <TextInput
                type="password"
                value={form.password}
                onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
              />
            </Field>
          ) : (
            <Field label="Private key">
              <textarea
                value={form.privateKey}
                onChange={(e) => setForm((f) => ({ ...f, privateKey: e.target.value }))}
                rows={3}
                placeholder="-----BEGIN OPENSSH PRIVATE KEY-----"
                className="w-full rounded-[var(--radius)] border border-border2 bg-black px-3 py-2 font-mono text-[12px] text-text outline-none placeholder:text-faint focus:border-accent"
              />
            </Field>
          )}
        </div>
      </Dialog>
    </PageShell>
  );
}
