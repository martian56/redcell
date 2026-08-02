import type { ReactNode } from 'react';
import { SEVERITIES, sevVar } from '@/lib/format';
import { Pill } from '@/components/ui/primitives';
import type { ProxyHealth, ServerStatus, Session } from '@redcell/api-client';

export function Section({
  title,
  action,
  children,
}: {
  title: string;
  action?: ReactNode;
  children: ReactNode;
}) {
  return (
    <section className="flex flex-col gap-3">
      <div className="flex items-center gap-2">
        <h3 className="font-mono text-[11px] font-bold uppercase tracking-[0.14em] text-muted">{title}</h3>
        {action ? <div className="ml-auto">{action}</div> : null}
      </div>
      {children}
    </section>
  );
}

export function StatTile({ k, v, children }: { k: string; v: string; children?: ReactNode }) {
  return (
    <div className="rounded-[var(--radius)] border border-border bg-panel p-4">
      <div className="font-mono text-[10px] uppercase tracking-wider text-faint">{k}</div>
      <div className="mt-1 font-mono text-2xl tabular-nums">{v}</div>
      {children}
    </div>
  );
}

export function SessionCard({ s, onClick }: { s: Session; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="flex flex-col gap-3 rounded-[var(--radius)] border border-border bg-panel p-4 text-left transition hover:border-border2 hover:bg-panel2"
    >
      <div className="flex items-start gap-2">
        <div className="flex min-w-0 flex-col">
          <span className="truncate text-[13px] font-bold">{s.name}</span>
          <span className="text-[11px] text-faint">{s.client}</span>
        </div>
        <Pill className="ml-auto" tone={s.status === 'active' ? 'live' : 'muted'}>
          {s.status}
        </Pill>
      </div>
      <div className="truncate font-mono text-[11px] text-muted">
        {s.targets[0] ?? s.scope[0] ?? '—'}
      </div>
      <div className="flex items-center gap-3">
        <span className="font-mono text-[11px] text-faint">{s.findingsCount} findings</span>
        <div className="ml-auto flex items-center gap-2">
          {SEVERITIES.map((sev) =>
            s.severityCounts[sev] > 0 ? (
              <span key={sev} className="font-mono text-[10px] font-bold" style={{ color: sevVar(sev) }}>
                {s.severityCounts[sev]}
              </span>
            ) : null,
          )}
        </div>
      </div>
    </button>
  );
}

export function serverTone(status: ServerStatus): string {
  return status === 'connected'
    ? 'var(--color-live)'
    : status === 'error' || status === 'offline'
      ? 'var(--color-crit)'
      : status === 'provisioning'
        ? 'var(--color-med)'
        : 'var(--color-faint)';
}

export function proxyTone(status: ProxyHealth): string {
  return status === 'healthy'
    ? 'var(--color-live)'
    : status === 'dead'
      ? 'var(--color-crit)'
      : 'var(--color-faint)';
}

export const th =
  'sticky top-0 z-10 bg-bg2 px-3 py-2 text-left font-mono text-[9.5px] font-bold uppercase tracking-wider text-faint border-b border-border';
