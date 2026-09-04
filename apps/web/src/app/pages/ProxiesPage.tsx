import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import type { Proxy, ProxyHealth } from '@redcell/api-client';
import { useCreateProxy, useProxies, useTestProxy } from '@/features/hooks';
import { Button } from '@/components/ui/primitives';
import { Dialog } from '@/components/ui/Dialog';
import { Field, Segmented, TextInput } from '@/components/ui/fields';
import { toast } from '@/components/ui/toast';

function proxyBadge(status: ProxyHealth) {
  if (status === 'healthy')
    return (
      <span className="badge ok">
        <span className="hd ok" />
        Healthy
      </span>
    );
  return (
    <span className="badge off">
      <span className={`hd ${status === 'dead' ? 'bad' : 'un'}`} />
      {status === 'dead' ? 'Dead' : 'Unknown'}
    </span>
  );
}

export function ProxiesPage() {
  const nav = useNavigate();
  const { data: proxies } = useProxies();
  const create = useCreateProxy();
  const test = useTestProxy();
  const [open, setOpen] = useState(false);

  const runTest = async (id: string) => {
    try {
      const r = await test.mutateAsync(id);
      toast(
        r.ok ? `Healthy (${r.latencyMs ?? '?'} ms, egress ${r.egressIp ?? '?'})` : `Proxy dead: ${r.error ?? 'unknown'}`,
        r.ok ? 'success' : 'error',
      );
    } catch {
      toast('Could not test the proxy', 'error');
    }
  };
  const [form, setForm] = useState<{
    label: string;
    url: string;
    kind: Proxy['kind'];
    auth: 'open' | 'credentials';
    username: string;
    password: string;
  }>({ label: '', url: '', kind: 'http', auth: 'open', username: '', password: '' });

  const submit = async () => {
    if (!form.label.trim() || !form.url.trim()) return;
    await create.mutateAsync({
      label: form.label.trim(),
      url: form.url.trim(),
      kind: form.kind,
      auth: form.auth,
      username: form.auth === 'credentials' ? form.username : undefined,
      password: form.auth === 'credentials' ? form.password : undefined,
    });
    setOpen(false);
    setForm({ label: '', url: '', kind: 'http', auth: 'open', username: '', password: '' });
    toast('Proxy added', 'success');
  };

  const list = proxies ?? [];

  return (
    <div className="wrap">
      <div className="filters">
        <div className="grow" />
        <button className="btn pri sm" onClick={() => setOpen(true)}>
          <svg viewBox="0 0 24 24">
            <path d="M12 5v14M5 12h14" />
          </svg>
          Add proxy
        </button>
      </div>
      <div className="card">
        <div className="card-b" style={{ padding: '12px 2px 4px' }}>
          <table className="tbl">
            <thead>
              <tr>
                <th>Label</th>
                <th>Endpoint</th>
                <th>Kind</th>
                <th>Status</th>
                <th>Latency</th>
                <th className="tright" />
              </tr>
            </thead>
            <tbody>
              {list.length === 0 ? (
                <tr>
                  <td colSpan={6} className="meta" style={{ padding: '22px', textAlign: 'center' }}>
                    No proxies yet. Add one, then test that it forwards traffic.
                  </td>
                </tr>
              ) : (
                list.map((p) => (
                  <tr key={p.id} className="row" onClick={() => nav(`/proxies/${p.id}`)}>
                    <td>
                      <span className="nn" style={{ fontWeight: 510 }}>
                        {p.label}
                      </span>
                    </td>
                    <td className="mono meta">{p.url}</td>
                    <td>
                      <span className="kind" style={{ textTransform: 'uppercase' }}>
                        {p.kind}
                      </span>
                    </td>
                    <td>{proxyBadge(p.status)}</td>
                    <td className="mono meta">{p.latencyMs ? `${p.latencyMs} ms` : '—'}</td>
                    <td className="tright" onClick={(e) => e.stopPropagation()}>
                      <button className="btn sm ghost" disabled={test.isPending} onClick={() => void runTest(p.id)}>
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

      <Dialog
        open={open}
        onClose={() => setOpen(false)}
        title="Add proxy"
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
          <Field label="Label">
            <TextInput
              autoFocus
              value={form.label}
              placeholder="residential-eu-2"
              onChange={(e) => setForm((f) => ({ ...f, label: e.target.value }))}
            />
          </Field>
          <Field label="URL">
            <TextInput
              value={form.url}
              placeholder="http://host:8080 or socks5://host:1080"
              onChange={(e) => setForm((f) => ({ ...f, url: e.target.value }))}
            />
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
              <Field label="Password">
                <TextInput
                  type="password"
                  value={form.password}
                  onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
                />
              </Field>
            </div>
          ) : null}
        </div>
      </Dialog>
    </div>
  );
}
