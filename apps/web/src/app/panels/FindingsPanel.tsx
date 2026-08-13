import { useMemo } from 'react';
import type { Finding, FindingStatus } from '@redcell/api-client';
import { cn } from '@/lib/cn';
import { useUI } from '@/store/ui';
import { useFindings, useMergeFindings, useSetFindingStatus } from '@/features/hooks';
import { Button, Empty, SeverityTag, Spinner } from '@/components/ui/primitives';

// Group active findings that likely describe the same issue: same location and
// either the same title or the same CWE. The first in each group (most recent)
// is the canonical record; the rest are duplicates the operator can merge in.
function duplicateGroups(findings: Finding[]) {
  const active = findings.filter((f) => f.status !== 'dismissed');
  const parent = new Map<string, string>(active.map((f) => [f.id, f.id]));
  const find = (x: string): string => {
    let r = x;
    while (parent.get(r) !== r) r = parent.get(r)!;
    while (parent.get(x) !== r) {
      const next = parent.get(x)!;
      parent.set(x, r);
      x = next;
    }
    return r;
  };
  const union = (a: string, b: string) => parent.set(find(a), find(b));
  for (let i = 0; i < active.length; i++) {
    for (let j = i + 1; j < active.length; j++) {
      const a = active[i]!;
      const b = active[j]!;
      const sameLoc = !!a.location && a.location.toLowerCase() === b.location.toLowerCase();
      if (!sameLoc) continue;
      const sameTitle = a.title.toLowerCase() === b.title.toLowerCase();
      const sameCwe = !!a.cwe && a.cwe === b.cwe;
      if (sameTitle || sameCwe) union(a.id, b.id);
    }
  }
  const byRoot = new Map<string, Finding[]>();
  for (const f of active) {
    const r = find(f.id);
    (byRoot.get(r) ?? byRoot.set(r, []).get(r)!).push(f);
  }
  const dupsOf = new Map<string, string[]>();
  const isDup = new Set<string>();
  for (const group of byRoot.values()) {
    if (group.length < 2) continue;
    const [canonical, ...rest] = group;
    dupsOf.set(canonical!.id, rest.map((r) => r.id));
    rest.forEach((r) => isDup.add(r.id));
  }
  return { dupsOf, isDup };
}

export function FindingsPanel() {
  const engId = useUI((s) => s.activeSessionId);
  const selection = useUI((s) => s.selection);
  const select = useUI((s) => s.select);
  const { data, isLoading } = useFindings(engId);
  const setStatus = useSetFindingStatus();
  const merge = useMergeFindings();
  const busy = setStatus.isPending || merge.isPending;

  const { dupsOf, isDup } = useMemo(() => duplicateGroups(data ?? []), [data]);

  if (isLoading) return <div className="grid h-full place-items-center"><Spinner /></div>;
  if (!data || data.length === 0) return <Empty>No findings yet.</Empty>;

  const th = 'sticky top-0 z-10 bg-bg2 px-3 py-2 text-left font-mono text-[9.5px] font-bold uppercase tracking-wider text-faint border-b border-border';

  const move = (e: React.MouseEvent, id: string, status: FindingStatus) => {
    e.stopPropagation();
    setStatus.mutate({ id, status });
  };

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
            const dupIds = dupsOf.get(f.id);
            const dismissed = f.status === 'dismissed';
            return (
              <tr
                key={f.id}
                onClick={() => select({ type: 'finding', id: f.id })}
                className={cn(
                  'cursor-pointer border-b border-border hover:bg-panel2',
                  active && 'bg-panel2',
                  dismissed && 'opacity-50',
                )}
              >
                <td className="px-3 py-2 font-mono text-[11px] text-faint">{f.id}</td>
                <td className="px-3 py-2"><SeverityTag sev={f.severity} cvss={f.cvss} /></td>
                <td className={cn('px-3 py-2 text-text', dismissed && 'line-through')}>{f.title}</td>
                <td className="px-3 py-2 font-mono text-faint">{f.location}</td>
                <td className="px-3 py-2 whitespace-nowrap">
                  {f.status === 'verified' ? (
                    <span className="font-mono text-[11px] font-bold text-live">✓ verified</span>
                  ) : dismissed ? (
                    <span className="font-mono text-[11px] text-faint">dismissed</span>
                  ) : (
                    <span className="font-mono text-[11px] text-faint">{f.status}</span>
                  )}
                  {isDup.has(f.id) && (
                    <span className="ml-2 rounded border border-border px-1 font-mono text-[9px] uppercase tracking-wider text-faint">
                      dup
                    </span>
                  )}
                </td>
                <td className="px-3 py-2 text-right whitespace-nowrap">
                  <div className="flex justify-end gap-1">
                    {dupIds && dupIds.length > 0 && (
                      <Button
                        variant="subtle"
                        className="h-6 px-2 text-[11px]"
                        disabled={busy}
                        onClick={(e) => {
                          e.stopPropagation();
                          merge.mutate({ primaryId: f.id, duplicateIds: dupIds });
                        }}
                        title="Dismiss the likely duplicates of this finding"
                      >
                        Merge {dupIds.length}
                      </Button>
                    )}
                    {f.status !== 'verified' && !dismissed && (
                      <Button variant="subtle" className="h-6 px-2 text-[11px]" disabled={busy}
                        onClick={(e) => move(e, f.id, 'verified')}>
                        Verify
                      </Button>
                    )}
                    {!dismissed ? (
                      <Button variant="subtle" className="h-6 px-2 text-[11px]" disabled={busy}
                        onClick={(e) => move(e, f.id, 'dismissed')}>
                        Dismiss
                      </Button>
                    ) : (
                      <Button variant="subtle" className="h-6 px-2 text-[11px]" disabled={busy}
                        onClick={(e) => move(e, f.id, 'candidate')}>
                        Reopen
                      </Button>
                    )}
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
