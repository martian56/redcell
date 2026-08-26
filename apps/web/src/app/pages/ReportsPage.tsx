import { useEffect, useMemo, useState } from 'react';
import type { ReportFormat, Severity } from '@redcell/api-client';
import { useCreateReport, useFindings, useReports, useSessions } from '@/features/hooks';
import { fileDownloadUrl } from '@/lib/api';
import { sevVar, timeAgo } from '@/lib/format';
import { toast } from '@/components/ui/toast';
import { FilterMenu } from './shared';

const ALL_FORMATS: ReportFormat[] = ['pdf', 'json', 'sarif'];
const sevRank: Record<Severity, number> = { critical: 0, high: 1, medium: 2, low: 3, info: 4 };

export function ReportsPage() {
  const { data: sessions } = useSessions();
  const list = useMemo(() => sessions ?? [], [sessions]);
  const [sessionId, setSessionId] = useState('');

  useEffect(() => {
    if (!sessionId && list.length) {
      const best = [...list].sort((a, b) => b.findingsCount - a.findingsCount)[0];
      if (best) setSessionId(best.id);
    }
  }, [list, sessionId]);

  const { data: reports } = useReports(sessionId || null);
  const { data: findings } = useFindings(sessionId || null);
  const create = useCreateReport(sessionId || null);
  const session = list.find((s) => s.id === sessionId);

  const top = useMemo(
    () => [...(findings ?? [])].sort((a, b) => sevRank[a.severity] - sevRank[b.severity] || b.cvss - a.cvss).slice(0, 6),
    [findings],
  );

  const generate = async () => {
    if (!sessionId) return;
    await create.mutateAsync({ title: `${session?.name ?? 'Session'} — Assessment`, formats: ALL_FORMATS });
    toast('Report queued', 'success');
  };

  const rows = reports ?? [];

  return (
    <div className="wrap">
      <div className="filters">
        <FilterMenu
          prefix="Session: "
          value={sessionId}
          onChange={setSessionId}
          icon
          options={list.map((s) => ({ value: s.id, label: s.name }))}
        />
      </div>
      <div className="split" style={{ gridTemplateColumns: '1fr 1.1fr' }}>
        <div className="card">
          <div className="card-h">
            <h3>Reports</h3>
            <span className="cs">· {rows.length}</span>
            <button className="btn pri sm" style={{ marginLeft: 'auto' }} disabled={!sessionId || create.isPending} onClick={generate}>
              <svg viewBox="0 0 24 24">
                <path d="M12 5v14M5 12h14" />
              </svg>
              Generate
            </button>
          </div>
          <div className="card-b" style={{ padding: '8px 2px 4px' }}>
            <table className="tbl">
              <thead>
                <tr>
                  <th>Title</th>
                  <th>Formats</th>
                  <th>Status</th>
                  <th className="tright">Generated</th>
                </tr>
              </thead>
              <tbody>
                {rows.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="meta" style={{ padding: '22px', textAlign: 'center' }}>
                      No reports yet. Generate one from this session.
                    </td>
                  </tr>
                ) : (
                  rows.map((r) => (
                    <tr key={r.id}>
                      <td>
                        <span className="nn" style={{ fontWeight: 510 }}>
                          {r.title}
                        </span>
                      </td>
                      <td>
                        {(Object.keys(r.artifacts) as ReportFormat[]).length
                          ? (Object.keys(r.artifacts) as ReportFormat[]).map((f) => (
                              <a key={f} className="fmt" href={fileDownloadUrl(r.artifacts[f] as string)}>
                                {f.toUpperCase()}
                              </a>
                            ))
                          : r.formats.map((f) => (
                              <span key={f} className="fmt">
                                {f.toUpperCase()}
                              </span>
                            ))}
                      </td>
                      <td>
                        {r.status === 'ready' ? (
                          <span className="status ok">Ready</span>
                        ) : (
                          <span className="meta">{r.status === 'generating' ? 'Generating…' : r.status}</span>
                        )}
                      </td>
                      <td className="tright meta">{timeAgo(r.createdAt)}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div className="doc">
          <h4>{session ? `${session.client} — ${session.name}` : 'Assessment report'}</h4>
          <div className="by">
            Prepared by REDCELL · {session ? `${session.findingsCount} findings` : '—'}
          </div>
          <h5>Executive summary</h5>
          {session && session.findingsCount > 0
            ? `The assessment recorded ${session.findingsCount} findings across ${session.targets.length || 'the'} target(s), including ${
                session.severityCounts.critical + session.severityCounts.high
              } of critical or high severity that warrant prompt remediation.`
            : 'No findings recorded for this session yet.'}
          <h5>Findings by priority</h5>
          {top.length === 0 ? (
            <div className="meta">Nothing to report.</div>
          ) : (
            top.map((f) => (
              <div className="findline" key={f.id}>
                <span className="sev" style={{ width: 8, height: 8, borderRadius: '50%', background: sevVar(f.severity) }} />
                <span style={{ flex: 1, color: 'var(--tx)' }}>{f.title}</span>
                <span className="mono" style={{ color: 'var(--tx-3)' }}>
                  {f.cvss.toFixed(1)}
                </span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
