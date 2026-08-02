import { useNavigate } from 'react-router-dom';
import { useProxies, useServers, useSessions } from '@/features/hooks';
import { Button, StatusDot } from '@/components/ui/primitives';
import { PageShell } from './PageShell';
import { Section, SessionCard, StatTile, proxyTone, serverTone } from './parts';

function LinkBtn({ onClick, children }: { onClick: () => void; children: string }) {
  return (
    <button onClick={onClick} className="font-mono text-[11px] font-semibold text-accent hover:brightness-125">
      {children}
    </button>
  );
}

export function OverviewPage() {
  const nav = useNavigate();
  const { data: sessions } = useSessions();
  const { data: servers } = useServers();
  const { data: proxies } = useProxies();

  const list = sessions ?? [];
  const activeCount = list.filter((s) => s.status === 'active').length;
  const totalFindings = list.reduce((a, s) => a + s.findingsCount, 0);
  const serversOnline = (servers ?? []).filter((s) => s.status === 'connected').length;
  const proxiesHealthy = (proxies ?? []).filter((p) => p.status === 'healthy').length;

  return (
    <PageShell title="Overview" subtitle="Everything across your operations">
      <div className="grid gap-6 p-5">
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          <StatTile k="Active sessions" v={String(activeCount)} />
          <StatTile k="Servers online" v={`${serversOnline}/${(servers ?? []).length}`} />
          <StatTile k="Proxies healthy" v={`${proxiesHealthy}/${(proxies ?? []).length}`} />
          <StatTile k="Total findings" v={String(totalFindings)} />
        </div>

        <Section title="Recent sessions" action={<LinkBtn onClick={() => nav('/sessions')}>All sessions</LinkBtn>}>
          <div className="grid grid-cols-[repeat(auto-fill,minmax(280px,1fr))] gap-3">
            {list.slice(0, 6).map((s) => (
              <SessionCard key={s.id} s={s} onClick={() => nav(`/sessions/${s.id}`)} />
            ))}
          </div>
        </Section>

        <div className="grid gap-6 lg:grid-cols-2">
          <Section title="Servers" action={<LinkBtn onClick={() => nav('/servers')}>Manage</LinkBtn>}>
            <div className="flex flex-col gap-2">
              {(servers ?? []).map((s) => (
                <div
                  key={s.id}
                  className="flex items-center gap-3 rounded-[var(--radius)] border border-border bg-panel px-3 py-2.5"
                >
                  <StatusDot color={serverTone(s.status)} glow={s.status === 'connected'} />
                  <span className="font-mono text-xs text-text">{s.name}</span>
                  <span className="font-mono text-[11px] text-faint">{s.host}</span>
                  <span className="ml-auto font-mono text-[11px] text-muted">{s.region ?? '—'}</span>
                </div>
              ))}
            </div>
          </Section>
          <Section title="Proxies" action={<LinkBtn onClick={() => nav('/proxies')}>Manage</LinkBtn>}>
            <div className="flex flex-col gap-2">
              {(proxies ?? []).map((p) => (
                <div
                  key={p.id}
                  className="flex items-center gap-3 rounded-[var(--radius)] border border-border bg-panel px-3 py-2.5"
                >
                  <StatusDot color={proxyTone(p.status)} glow={p.status === 'healthy'} />
                  <span className="font-mono text-xs text-text">{p.label}</span>
                  <span className="truncate font-mono text-[11px] text-faint">{p.url}</span>
                  <span className="ml-auto font-mono text-[11px] tabular-nums text-muted">
                    {p.latencyMs ? `${p.latencyMs}ms` : '—'}
                  </span>
                </div>
              ))}
            </div>
          </Section>
        </div>

        <div className="pb-4">
          <Button variant="primary" onClick={() => nav('/sessions')}>
            Open a session
          </Button>
        </div>
      </div>
    </PageShell>
  );
}
