import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCreateProxy, useProxies, useTestProxy } from '@/features/hooks';
import { Button, StatusDot } from '@/components/ui/primitives';
import { Dialog } from '@/components/ui/Dialog';
import { Field, Segmented, TextInput } from '@/components/ui/fields';
import { Icon } from '@/components/ui/Icon';
import { toast } from '@/components/ui/toast';
import { PageShell } from './PageShell';
import { proxyTone, th } from './parts';
import type { Proxy } from '@redcell/api-client';

export function ProxiesPage() {
  const nav = useNavigate();
  const { data: proxies } = useProxies();
  const create = useCreateProxy();
  const test = useTestProxy();
  const [open, setOpen] = useState(false);

  const runTest = async (id: string) => {
    const r = await test.mutateAsync(id);
    toast(r.ok ? `Healthy (${r.latencyMs ?? '?'} ms, egress ${r.egressIp ?? '?'})` : `Proxy dead: ${r.error ?? 'unknown'}`, r.ok ? 'success' : 'error');
  };
  const [form, setForm] = useState<{
    label: string;
    url: string;
    kind: Proxy['kind'];
    auth: 'open' | 'credentials';
    username: string;
    password: string;
  }>({
    label: '',
    url: '',
    kind: 'http',
    auth: 'open',
    username: '',
    password: '',
  });

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

  return (
    <PageShell
      title="Proxies"
      subtitle="Upstream proxy pool for tool traffic"
      actions={
        <Button variant="primary" onClick={() => setOpen(true)}>
          <Icon name="plus" size={14} />
          Add proxy
        </Button>
      }
    >
      <div className="p-5">
        <div className="overflow-hidden rounded-[var(--radius)] border border-border">
          <table className="w-full border-collapse text-xs">
            <thead>
              <tr>
                <th className={th}>Label</th>
                <th className={th}>URL</th>
                <th className={th}>Kind</th>
                <th className={th}>Status</th>
                <th className={th}>Latency</th>
                <th className={th} />
              </tr>
            </thead>
            <tbody>
              {(proxies ?? []).length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-3 py-8 text-center text-faint">
                    No proxies yet. Add one, then test that it forwards traffic.
                  </td>
                </tr>
              ) : null}
              {(proxies ?? []).map((p) => (
                <tr
                  key={p.id}
                  onClick={() => nav(`/proxies/${p.id}`)}
                  className="cursor-pointer border-b border-border hover:bg-panel2"
                >
                  <td className="px-3 py-2.5 font-mono text-text">{p.label}</td>
                  <td className="px-3 py-2.5 font-mono text-faint">{p.url}</td>
                  <td className="px-3 py-2.5 font-mono uppercase text-muted">{p.kind}</td>
                  <td className="px-3 py-2.5">
                    <span className="inline-flex items-center gap-2 font-mono text-[11px]">
                      <StatusDot color={proxyTone(p.status)} glow={p.status === 'healthy'} />
                      {p.status}
                    </span>
                  </td>
                  <td className="px-3 py-2.5 font-mono tabular-nums text-muted">
                    {p.latencyMs ? `${p.latencyMs}ms` : '—'}
                  </td>
                  <td className="px-3 py-2.5 text-right" onClick={(e) => e.stopPropagation()}>
                    <div className="flex items-center justify-end gap-1.5">
                      <button
                        onClick={() => void runTest(p.id)}
                        disabled={test.isPending}
                        className="rounded-[var(--radius)] border border-border2 px-2 py-1 text-[11px] font-semibold text-muted hover:bg-elev hover:text-text disabled:opacity-40"
                        title="Test proxy"
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
            <TextInput autoFocus value={form.label} placeholder="residential-eu-2" onChange={(e) => setForm((f) => ({ ...f, label: e.target.value }))} />
          </Field>
          <Field label="URL">
            <TextInput value={form.url} placeholder="http://host:8080 or socks5://host:1080" onChange={(e) => setForm((f) => ({ ...f, url: e.target.value }))} />
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
                <TextInput type="password" value={form.password} onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))} />
              </Field>
            </div>
          ) : null}
        </div>
      </Dialog>
    </PageShell>
  );
}
