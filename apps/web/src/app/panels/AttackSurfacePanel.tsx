import { useUI } from '@/store/ui';
import { useAttackSurface } from '@/features/hooks';
import { Empty, Spinner } from '@/components/ui/primitives';

const th =
  'sticky top-0 z-10 bg-bg2 px-3 py-2 text-left font-mono text-[9.5px] font-bold uppercase tracking-wider text-faint border-b border-border';

export function AttackSurfacePanel() {
  const engId = useUI((s) => s.activeSessionId);
  const { data, isLoading } = useAttackSurface(engId);

  if (isLoading) return <div className="grid h-full place-items-center"><Spinner /></div>;
  if (!data || data.length === 0) return <Empty>No hosts mapped yet.</Empty>;

  return (
    <div className="h-full overflow-auto">
      <table className="w-full border-collapse text-xs">
        <thead>
          <tr>
            <th className={th}>Host</th>
            <th className={th}>IP</th>
            <th className={th}>Ports</th>
            <th className={th}>Tech</th>
            <th className={th}>Source</th>
          </tr>
        </thead>
        <tbody>
          {data.map((h) => (
            <tr key={h.id} className="border-b border-border align-top hover:bg-panel2">
              <td className="px-3 py-2 font-mono text-text">{h.host}</td>
              <td className="px-3 py-2 font-mono text-faint">{h.ip ?? '—'}</td>
              <td className="px-3 py-2 font-mono text-muted">{h.ports.map((p) => p.port).join(', ')}</td>
              <td className="px-3 py-2">
                <div className="flex flex-wrap gap-1">
                  {h.tech.map((t) => (
                    <span key={t} className="rounded bg-elev px-1.5 py-0.5 text-[10px] text-muted">
                      {t}
                    </span>
                  ))}
                </div>
              </td>
              <td className="px-3 py-2 font-mono text-[11px] text-faint">{h.source}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
