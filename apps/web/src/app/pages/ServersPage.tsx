import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import type { ServerStatus } from '@redcell/api-client';
import { useCreateServer, useServers, useTestServer } from '@/features/hooks';
import { Button } from '@/components/ui/primitives';
import { Dialog } from '@/components/ui/Dialog';
import { Field, Segmented, TextInput } from '@/components/ui/fields';
import { toast } from '@/components/ui/toast';

function statusBadge(status: ServerStatus) {
  if (status === 'connected')
    return (
      <span className="badge ok">
        <span className="hd ok" />
        Connected
      </span>
    );
  if (status === 'provisioning')
    return (
      <span className="badge off">
        <span className="hd un" />
        Provisioning
      </span>
    );
  return (
    <span className="badge off">
      <span className="hd bad" />
      {status === 'offline' ? 'Offline' : 'Error'}
    </span>
  );
}

export function ServersPage() {
  const nav = useNavigate();
  const { data: servers } = useServers();
  const create = useCreateServer();
  const test = useTestServer();

  const runTest = async (id: string) => {
    const r = await test.mutateAsync(id);
    toast(
      r.ok ? `Connected (${r.latencyMs ?? '?'} ms)` : `Connection failed: ${r.error ?? 'unknown'}`,
      r.ok ? 'success' : 'error',
    );
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
  }>({ name: '', host: '', region: '', username: 'root', authMethod: 'key', password: '', privateKey: '' });

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

  const list = servers ?? [];

  return (
    <div className="wrap">
      <div className="filters">
        <div className="grow" />
        <button className="btn pri sm" onClick={() => setOpen(true)}>
          <svg viewBox="0 0 24 24">
            <path d="M12 5v14M5 12h14" />
          </svg>
          Add server
        </button>
      </div>
      <div className="card">
        <div className="card-b" style={{ padding: '12px 2px 4px' }}>
          <table className="tbl">
            <thead>
              <tr>
                <th>Server</th>
                <th>Host</th>
                <th>Status</th>
                <th>Sessions</th>
                <th>Latency</th>
                <th className="tright" />
              </tr>
            </thead>
            <tbody>
              {list.length === 0 ? (
                <tr>
                  <td colSpan={6} className="meta" style={{ padding: '22px', textAlign: 'center' }}>
                    No servers yet. Add one, then test the connection.
                  </td>
                </tr>
              ) : (
                list.map((s) => (
                  <tr key={s.id} className="row" onClick={() => nav(`/servers/${s.id}`)}>
                    <td>
                      <div className="name">
                        <span className="nn">{s.name}</span>
                      </div>
                      <div className="meta" style={{ marginTop: 1 }}>
                        {s.region ?? '—'}
                      </div>
                    </td>
                    <td className="mono meta">{s.host}</td>
                    <td>{statusBadge(s.status)}</td>
                    <td className="meta tab">{s.runningSessions}</td>
                    <td className="mono meta">{s.latencyMs != null ? `${s.latencyMs} ms` : '—'}</td>
                    <td className="tright" onClick={(e) => e.stopPropagation()}>
                      <button className="btn sm ghost" disabled={test.isPending} onClick={() => void runTest(s.id)}>
                        Test
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
      <p className="hint" style={{ margin: '12px 2px' }}>
        Servers run the Kali execution container over SSH. Each is verified with a real connection test before a
        session can use it.
      </p>

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
            <TextInput
              autoFocus
              value={form.name}
              placeholder="redcell-ops-3"
              onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
            />
          </Field>
          <Field label="Host" hint="SSH host or Docker endpoint.">
            <TextInput
              value={form.host}
              placeholder="1.2.3.4 or ops3.redcell.sh"
              onChange={(e) => setForm((f) => ({ ...f, host: e.target.value }))}
            />
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
                className="textarea mono"
              />
            </Field>
          )}
        </div>
      </Dialog>
    </div>
  );
}
