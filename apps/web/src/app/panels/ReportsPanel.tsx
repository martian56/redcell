import { useState } from 'react';
import { cn } from '@/lib/cn';
import { useUI } from '@/store/ui';
import { useFindings, useReports, useCreateReport, useDeleteReport, useSession } from '@/features/hooks';
import { fileDownloadUrl } from '@/lib/api';
import { Button, Empty, StatusDot } from '@/components/ui/primitives';
import { Icon } from '@/components/ui/Icon';
import { toast } from '@/components/ui/toast';
import type { Report, ReportFormat } from '@redcell/api-client';

const ALL_FORMATS: ReportFormat[] = ['pdf', 'json', 'sarif'];
const STATUS_TONE: Record<Report['status'], string> = {
  draft: 'var(--color-faint)',
  generating: 'var(--color-med, #c99700)',
  ready: 'var(--color-live)',
  failed: 'var(--color-crit)',
};

function Stat({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex flex-col">
      <span className="font-mono text-[10px] uppercase tracking-wider text-faint">{k}</span>
      <span className="font-mono text-lg tabular-nums">{v}</span>
    </div>
  );
}

export function ReportsPanel() {
  const sid = useUI((s) => s.activeSessionId);
  const { data: session } = useSession(sid);
  const { data: findings } = useFindings(sid);
  const { data: reports } = useReports(sid);
  const create = useCreateReport(sid);
  const del = useDeleteReport(sid);

  const [title, setTitle] = useState('');
  const [formats, setFormats] = useState<ReportFormat[]>(ALL_FORMATS);

  const verified = findings?.filter((f) => f.status === 'verified').length ?? 0;
  const defaultTitle = session ? `${session.name} - Penetration Test Report` : 'Penetration Test Report';

  const toggle = (f: ReportFormat) =>
    setFormats((prev) => (prev.includes(f) ? prev.filter((x) => x !== f) : [...prev, f]));

  const generate = async () => {
    if (!sid || formats.length === 0) return;
    await create.mutateAsync({ title: title.trim() || defaultTitle, formats });
    setTitle('');
    toast('Generating report...', 'success');
  };

  return (
    <div className="h-full overflow-auto p-4">
      <div className="rounded-[var(--radius)] border border-border bg-panel2 p-5">
        <h3 className="text-sm font-bold">Generate session report</h3>
        <p className="mt-1.5 max-w-[62ch] text-xs text-muted">
          A complete report: executive summary, methodology (PTES / OWASP WSTG), findings with CVSS
          and evidence, attack surface, and remediation in priority order. Written by the session's model
          and cleaned up to read like a person wrote it.
        </p>
        <div className="mt-4 flex gap-8">
          <Stat k="Verified findings" v={String(verified)} />
          <Stat k="Total findings" v={String(findings?.length ?? 0)} />
        </div>
        <div className="mt-4 grid gap-2.5">
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder={defaultTitle}
            className="h-9 w-full rounded-[var(--radius)] border border-border2 bg-black px-3 text-[13px] text-text outline-none placeholder:text-faint focus:border-accent"
          />
          <div className="flex flex-wrap items-center gap-2">
            {ALL_FORMATS.map((f) => (
              <button
                key={f}
                onClick={() => toggle(f)}
                className={cn(
                  'rounded-[var(--radius)] border px-2.5 py-1 text-[11px] font-semibold uppercase',
                  formats.includes(f)
                    ? 'border-accent bg-accent-dim text-accent-ink'
                    : 'border-border2 text-muted hover:text-text',
                )}
              >
                {f}
              </button>
            ))}
            <div className="flex-1" />
            <Button variant="primary" disabled={!sid || create.isPending || formats.length === 0} onClick={generate}>
              <Icon name="reports" size={14} />
              Generate
            </Button>
          </div>
        </div>
      </div>

      <div className="mt-4">
        <div className="mb-2 font-mono text-[10px] uppercase tracking-[0.14em] text-faint">Reports</div>
        {!reports || reports.length === 0 ? (
          <Empty>No reports yet. Generate one above.</Empty>
        ) : (
          <div className="grid gap-2">
            {reports.map((r) => (
              <div key={r.id} className="rounded-[var(--radius)] border border-border bg-panel2 p-3">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="truncate text-[13px] font-semibold text-text">{r.title}</div>
                    <div className="mt-0.5 flex items-center gap-2 font-mono text-[10px] text-faint">
                      <StatusDot color={STATUS_TONE[r.status]} glow={r.status === 'generating'} />
                      {r.status}
                      <span>·</span>
                      {new Date(r.createdAt).toLocaleString()}
                    </div>
                  </div>
                  <button
                    onClick={() => del.mutate(r.id)}
                    title="Delete report"
                    className="flex-none p-1 text-faint hover:text-crit"
                  >
                    <Icon name="close" size={14} />
                  </button>
                </div>
                {r.status === 'ready' ? (
                  <div className="mt-2.5 flex flex-wrap gap-2">
                    {(Object.keys(r.artifacts) as ReportFormat[]).map((fmt) => (
                      <a
                        key={fmt}
                        href={fileDownloadUrl(r.artifacts[fmt] as string)}
                        target="_blank"
                        rel="noreferrer"
                        className="rounded-[var(--radius)] border border-border2 bg-panel px-2.5 py-1 text-[11px] font-semibold uppercase text-muted hover:bg-elev hover:text-text"
                      >
                        {fmt}
                      </a>
                    ))}
                  </div>
                ) : null}
                {r.status === 'failed' && r.error ? (
                  <div className="mt-2 rounded-[var(--radius)] border border-crit bg-panel px-2.5 py-1.5 font-mono text-[11px] text-crit">
                    {r.error}
                  </div>
                ) : null}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
