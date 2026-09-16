import { useMemo } from 'react';
import { useUI } from '@/store/ui';
import { useIntel } from '@/features/hooks';
import { Empty, Spinner } from '@/components/ui/primitives';
import type { IntelEntity } from '@redcell/api-client';

const TYPE_TONE: Record<string, string> = {
  person: 'var(--color-accent)',
  email: 'var(--color-med)',
  username: 'var(--color-low)',
  org: 'var(--color-live)',
  profile: 'var(--color-med)',
  breach: 'var(--color-crit)',
  phone: 'var(--color-low)',
  domain: 'var(--color-live)',
  other: 'var(--color-faint)',
};

function tone(type: string): string {
  return TYPE_TONE[type] ?? 'var(--color-faint)';
}

export function IntelPanel() {
  const sessionId = useUI((s) => s.activeSessionId);
  const { data, isLoading } = useIntel(sessionId);

  const byId = useMemo(() => {
    const m = new Map<string, IntelEntity>();
    for (const e of data?.entities ?? []) m.set(e.id, e);
    return m;
  }, [data]);

  const relationsFor = (id: string) =>
    (data?.relations ?? [])
      .map((r) =>
        r.fromId === id
          ? { label: r.label, other: byId.get(r.toId) }
          : r.toId === id
            ? { label: `${r.label} ←`, other: byId.get(r.fromId) }
            : null,
      )
      .filter((x): x is { label: string; other: IntelEntity } => !!x && !!x.other);

  const groups = useMemo(() => {
    const g = new Map<string, IntelEntity[]>();
    for (const e of data?.entities ?? []) {
      if (!g.has(e.type)) g.set(e.type, []);
      g.get(e.type)!.push(e);
    }
    return [...g.entries()];
  }, [data]);

  if (isLoading) return <div className="grid h-full place-items-center"><Spinner /></div>;
  if (!data || data.entities.length === 0)
    return <Empty>No intel yet. OSINT runs record people, emails, usernames, orgs, and breaches here.</Empty>;

  return (
    <div className="h-full overflow-auto p-3">
      {groups.map(([type, ents]) => (
        <div key={type} className="mb-3">
          <div className="mb-1.5 flex items-center gap-2">
            <span
              className="rounded-[4px] px-2 py-0.5 font-mono text-[10px] font-bold uppercase"
              style={{ color: tone(type), backgroundColor: `color-mix(in srgb, ${tone(type)} 16%, transparent)` }}
            >
              {type}
            </span>
            <span className="font-mono text-[10px] text-faint">{ents.length}</span>
          </div>
          {ents.map((e) => {
            const rels = relationsFor(e.id);
            return (
              <div key={e.id} className="mb-1.5 rounded-[var(--radius)] border border-border bg-panel2 px-3 py-2">
                <div className="flex items-baseline gap-2">
                  <span className="min-w-0 flex-1 truncate font-mono text-xs text-text" data-tip={e.value}>
                    {e.value}
                  </span>
                  {e.source ? <span className="font-mono text-[10px] text-faint">{e.source}</span> : null}
                </div>
                {e.label ? <div className="mt-0.5 text-[11px] text-muted">{e.label}</div> : null}
                {rels.length ? (
                  <div className="mt-1 flex flex-col gap-0.5">
                    {rels.map((r, i) => (
                      <div key={i} className="font-mono text-[10.5px] text-faint">
                        <span className="text-muted">{r.label}</span> {r.other.value}
                      </div>
                    ))}
                  </div>
                ) : null}
              </div>
            );
          })}
        </div>
      ))}
    </div>
  );
}
