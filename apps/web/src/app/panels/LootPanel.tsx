import { useState } from 'react';
import { useUI } from '@/store/ui';
import { useLoot } from '@/features/hooks';
import { timeAgo } from '@/lib/format';
import { Empty, Spinner } from '@/components/ui/primitives';
import { Select } from '@/components/ui/Dropdown';
import { toast } from '@/components/ui/toast';
import type { LootKind } from '@redcell/api-client';

async function copyValue(value: string) {
  if (!value) return;
  try {
    await navigator.clipboard.writeText(value);
    toast('Copied to clipboard', 'success');
  } catch {
    toast('Could not copy to clipboard', 'error');
  }
}

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
  const [kind, setKind] = useState('');

  if (isLoading) return <div className="grid h-full place-items-center"><Spinner /></div>;
  if (!data || data.length === 0) return <Empty>No loot collected yet.</Empty>;

  const filtered = kind ? data.filter((l) => l.kind === kind) : data;

  return (
    <div className="flex h-full flex-col">
      <div className="flex flex-none items-center gap-2 border-b border-border bg-bg2 px-3 py-1.5">
        <span className="font-mono text-[10px] uppercase tracking-wider text-faint">Loot</span>
        <div className="ml-auto w-32 flex-none">
          <Select
            value={kind}
            onChange={setKind}
            placeholder="Kind"
            className="!h-7 !py-0 !text-[11px]"
            options={[
              { value: '', label: 'All kinds' },
              ...['credential', 'token', 'hash', 'file'].map((k) => ({ value: k, label: k })),
            ]}
          />
        </div>
      </div>
      <div className="min-h-0 flex-1 overflow-auto">
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
          {filtered.map((l) => (
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
              <td className="px-3 py-2">
                {l.value ? (
                  <button
                    type="button"
                    data-tip={`${l.value}\n\nClick to copy`}
                    aria-label="Copy value to clipboard"
                    onClick={() => void copyValue(l.value)}
                    className="block max-w-[180px] cursor-pointer truncate text-left font-mono text-faint hover:text-text"
                  >
                    {l.value}
                  </button>
                ) : (
                  <span className="font-mono text-faint">—</span>
                )}
              </td>
              <td className="px-3 py-2 font-mono text-[11px] text-muted">{l.source}</td>
              <td className="px-3 py-2 font-mono text-[11px] text-faint">{timeAgo(l.ts)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {filtered.length === 0 ? <Empty>No loot of that kind.</Empty> : null}
      </div>
    </div>
  );
}
