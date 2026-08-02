import { cn } from '@/lib/cn';
import { useUI } from '@/store/ui';
import { useFindings, useVerifyFinding } from '@/features/hooks';
import { Button, Empty, SeverityTag, Spinner } from '@/components/ui/primitives';

export function FindingsPanel() {
  const engId = useUI((s) => s.activeSessionId);
  const selection = useUI((s) => s.selection);
  const select = useUI((s) => s.select);
  const { data, isLoading } = useFindings(engId);
  const verify = useVerifyFinding();

  if (isLoading) return <div className="grid h-full place-items-center"><Spinner /></div>;
  if (!data || data.length === 0) return <Empty>No findings yet.</Empty>;

  const th = 'sticky top-0 z-10 bg-bg2 px-3 py-2 text-left font-mono text-[9.5px] font-bold uppercase tracking-wider text-faint border-b border-border';

  return (
    <div className="h-full overflow-auto">
      <table className="w-full border-collapse text-xs">
        <thead>
          <tr>
            <th className={th}>ID</th>
            <th className={th}>Sev</th>
            <th className={th}>Title</th>
            <th className={th}>Location</th>
            <th className={th}>Status</th>
            <th className={th} />
          </tr>
        </thead>
        <tbody>
          {data.map((f) => {
            const active = selection?.type === 'finding' && selection.id === f.id;
            return (
              <tr
                key={f.id}
                onClick={() => select({ type: 'finding', id: f.id })}
                className={cn('cursor-pointer border-b border-border hover:bg-panel2', active && 'bg-panel2')}
              >
                <td className="px-3 py-2 font-mono text-[11px] text-faint">{f.id}</td>
                <td className="px-3 py-2"><SeverityTag sev={f.severity} cvss={f.cvss} /></td>
                <td className="px-3 py-2 text-text">{f.title}</td>
                <td className="px-3 py-2 font-mono text-faint">{f.location}</td>
                <td className="px-3 py-2">
                  {f.status === 'verified' ? (
                    <span className="font-mono text-[11px] font-bold text-live">✓ verified</span>
                  ) : (
                    <span className="font-mono text-[11px] text-faint">{f.status}</span>
                  )}
                </td>
                <td className="px-3 py-2 text-right">
                  {f.status !== 'verified' && (
                    <Button
                      variant="subtle"
                      className="h-6 px-2 text-[11px]"
                      disabled={verify.isPending}
                      onClick={(e) => {
                        e.stopPropagation();
                        verify.mutate(f.id);
                      }}
                    >
                      Verify
                    </Button>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
