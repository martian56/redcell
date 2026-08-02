import { useUI } from '@/store/ui';
import { useRunEvents } from '@/features/hooks';
import { hhmmss } from '@/lib/format';
import { Empty } from '@/components/ui/primitives';
import type { EventType } from '@redcell/api-client';

const TAG: Record<EventType, { label: string; color: string }> = {
  tool: { label: 'TOOL', color: 'var(--color-low)' },
  finding: { label: 'FIND', color: 'var(--color-accent)' },
  net: { label: 'NET', color: 'var(--color-live)' },
  steer: { label: 'STEER', color: 'var(--color-med)' },
  error: { label: 'ERR', color: 'var(--color-crit)' },
};

export function LiveFeedPanel() {
  const runId = useUI((s) => s.activeRunId);
  const events = useRunEvents(runId, 80);

  if (!runId) return <Empty>No active run.</Empty>;
  if (events.length === 0) return <Empty>Waiting for activity…</Empty>;

  return (
    <div className="h-full overflow-auto">
      {events.map((e) => {
        const t = TAG[e.type];
        return (
          <div
            key={e.id}
            className="grid grid-cols-[58px_96px_1fr] items-baseline gap-3 border-b border-border px-3 py-1.5 text-xs hover:bg-panel2"
          >
            <span className="font-mono text-[11px] text-faint">{hhmmss(e.ts)}</span>
            <span className="truncate font-mono text-[11px] text-muted">{e.source}</span>
            <span className="text-text">
              <span
                className="mr-2 rounded-[3px] px-1.5 py-0.5 font-mono text-[9px] font-bold"
                style={{ color: t.color, backgroundColor: `color-mix(in srgb, ${t.color} 18%, transparent)` }}
              >
                {t.label}
              </span>
              {e.text}
            </span>
          </div>
        );
      })}
    </div>
  );
}
