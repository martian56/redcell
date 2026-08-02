import { useUI } from '@/store/ui';
import { useProxy } from '@/features/hooks';
import { timeAgo } from '@/lib/format';
import { Empty, Spinner } from '@/components/ui/primitives';

const th =
  'sticky top-0 z-10 bg-bg2 px-3 py-2 text-left font-mono text-[9.5px] font-bold uppercase tracking-wider text-faint border-b border-border';

function statusTone(status: number): string {
  if (status >= 500) return 'var(--color-crit)';
  if (status >= 400) return 'var(--color-med)';
  return 'var(--color-live)';
}

export function ProxyPanel() {
  const engId = useUI((s) => s.activeSessionId);
  const { data, isLoading } = useProxy(engId);

  if (isLoading) return <div className="grid h-full place-items-center"><Spinner /></div>;
  if (!data || data.length === 0) return <Empty>No proxy history.</Empty>;

  return (
    <div className="h-full overflow-auto">
      <table className="w-full border-collapse text-xs">
        <thead>
          <tr>
            <th className={th}>#</th>
            <th className={th}>Method</th>
            <th className={th}>URL</th>
            <th className={th}>Status</th>
            <th className={th}>Len</th>
            <th className={th}>When</th>
          </tr>
        </thead>
        <tbody>
          {data.map((p) => (
            <tr key={p.id} className="border-b border-border hover:bg-panel2">
              <td className="px-3 py-2 font-mono text-[11px] text-faint">{p.id}</td>
              <td className="px-3 py-2 font-mono text-muted">{p.method}</td>
              <td className="px-3 py-2 font-mono text-faint">{p.url}</td>
              <td className="px-3 py-2">
                <span
                  className="rounded-[4px] px-2 py-0.5 font-mono text-[10.5px] font-extrabold"
                  style={{
                    color: statusTone(p.status),
                    backgroundColor: `color-mix(in srgb, ${statusTone(p.status)} 16%, transparent)`,
                  }}
                >
                  {p.status}
                </span>
              </td>
              <td className="px-3 py-2 font-mono tabular-nums text-muted">{p.length}</td>
              <td className="px-3 py-2 font-mono text-[11px] text-faint">{timeAgo(p.ts)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
