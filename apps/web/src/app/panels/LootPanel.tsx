import { useUI } from '@/store/ui';
import { useLoot } from '@/features/hooks';
import { timeAgo } from '@/lib/format';
import { Empty, Spinner } from '@/components/ui/primitives';
import type { LootKind } from '@redcell/api-client';

const KIND_TONE: Record<LootKind, string> = {
  credential: 'var(--color-accent)',
  token: 'var(--color-med)',
  hash: 'var(--color-low)',
  file: 'var(--color-live)',
};

const th =
  'sticky top-0 z-10 bg-bg2 px-3 py-2 text-left font-mono text-[9.5px] font-bold uppercase tracking-wider text-faint border-b border-border';

export function LootPanel() {
  const engId = useUI((s) => s.activeSessionId);
  const { data, isLoading } = useLoot(engId);

  if (isLoading) return <div className="grid h-full place-items-center"><Spinner /></div>;
  if (!data || data.length === 0) return <Empty>No loot collected yet.</Empty>;

  return (
    <div className="h-full overflow-auto">
      <table className="w-full border-collapse text-xs">
        <thead>
          <tr>
            <th className={th}>Kind</th>
            <th className={th}>Label</th>
            <th className={th}>Value</th>
            <th className={th}>Source</th>
            <th className={th}>When</th>
          </tr>
        </thead>
        <tbody>
          {data.map((l) => (
            <tr key={l.id} className="border-b border-border hover:bg-panel2">
              <td className="px-3 py-2">
                <span
                  className="rounded-[4px] px-2 py-0.5 font-mono text-[10px] font-bold uppercase"
                  style={{
                    color: KIND_TONE[l.kind],
                    backgroundColor: `color-mix(in srgb, ${KIND_TONE[l.kind]} 16%, transparent)`,
                  }}
                >
                  {l.kind}
                </span>
              </td>
              <td className="px-3 py-2 font-mono text-text">{l.label}</td>
              <td className="max-w-[180px] truncate px-3 py-2 font-mono text-faint">{l.value}</td>
              <td className="px-3 py-2 font-mono text-[11px] text-muted">{l.source}</td>
              <td className="px-3 py-2 font-mono text-[11px] text-faint">{timeAgo(l.ts)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
