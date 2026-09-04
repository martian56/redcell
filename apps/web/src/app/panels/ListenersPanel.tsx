import { useQueryClient } from '@tanstack/react-query';
import { useUI } from '@/store/ui';
import { useApi } from '@/lib/api';
import { useListeners } from '@/features/hooks';
import { Button, Empty, Spinner, StatusDot } from '@/components/ui/primitives';

const th =
  'sticky top-0 z-10 bg-bg2 px-3 py-2 text-left font-mono text-[9.5px] font-bold uppercase tracking-wider text-faint border-b border-border';

export function ListenersPanel() {
  const engId = useUI((s) => s.activeSessionId);
  const { data, isLoading } = useListeners(engId);
  const api = useApi();
  const qc = useQueryClient();

  const start = async () => {
    if (!engId) return;
    await api.listeners.start(engId, { kind: 'tls', bind: '0.0.0.0:4445' });
    qc.invalidateQueries({ queryKey: ['listeners', engId] });
  };

  return (
    <div className="flex h-full flex-col">
      <div className="flex flex-none items-center gap-2 border-b border-border bg-bg2 px-3 py-2">
        <span className="font-mono text-[10px] uppercase tracking-wider text-faint">Catchers</span>
        <Button variant="subtle" className="ml-auto h-6 px-2 text-[11px]" onClick={start}>
          + New listener
        </Button>
      </div>
      <div className="min-h-0 flex-1 overflow-auto">
        {isLoading ? (
          <div className="grid h-full place-items-center"><Spinner /></div>
        ) : !data || data.length === 0 ? (
          <Empty>No listeners yet.</Empty>
        ) : (
          <table className="w-full border-collapse text-xs">
            <thead>
              <tr>
                <th className={th}>Bind</th>
                <th className={th}>Kind</th>
                <th className={th}>Status</th>
                <th className={th}>Sessions</th>
              </tr>
            </thead>
            <tbody>
              {data.map((l) => (
                <tr key={l.id} className="border-b border-border hover:bg-panel2">
                  <td className="px-3 py-2 font-mono text-text">{l.bind}</td>
                  <td className="px-3 py-2 font-mono uppercase text-muted">{l.kind}</td>
                  <td className="px-3 py-2">
                    <span className="inline-flex items-center gap-2 font-mono text-[11px]">
                      <StatusDot
                        color={l.status === 'listening' ? 'var(--color-live)' : 'var(--color-faint)'}
                        glow={l.status === 'listening'}
                      />
                      {l.status}
                    </span>
                  </td>
                  <td className="px-3 py-2 font-mono tabular-nums text-text">{l.sessions}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
