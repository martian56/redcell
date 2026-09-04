import { useEffect, useMemo, useState } from 'react';
import type { Finding, Severity } from '@redcell/api-client';
import { useFindings, useSessions, useSetFindingStatus } from '@/features/hooks';
import { SEVERITIES, sevVar } from '@/lib/format';
import { toast } from '@/components/ui/toast';
import { FilterMenu, onActivate } from './shared';

const SEV_LABEL: Record<Severity, string> = {
  critical: 'Critical',
  high: 'High',
  medium: 'Medium',
  low: 'Low',
  info: 'Info',
};
const sevRank: Record<Severity, number> = { critical: 0, high: 1, medium: 2, low: 3, info: 4 };
const shortId = (id: string) => id.replace(/^find-|^f-/, '').slice(0, 6);

export function FindingsPage() {
  const { data: sessions } = useSessions();
  const list = useMemo(() => sessions ?? [], [sessions]);

  const [sessionId, setSessionId] = useState('');
  const [sev, setSev] = useState('all');
  const [status, setStatus] = useState('all');
  const [selId, setSelId] = useState<string | null>(null);

  useEffect(() => {
    if (!sessionId && list.length) {
      const best = [...list].sort((a, b) => b.findingsCount - a.findingsCount)[0];
      if (best) setSessionId(best.id);
    }
  }, [list, sessionId]);

  const { data: findings } = useFindings(sessionId || null);
  const setStatusM = useSetFindingStatus();

  const filtered = useMemo(() => {
    return (findings ?? [])
      .filter((f) => (sev === 'all' || f.severity === sev) && (status === 'all' || f.status === status))
      .sort((a, b) => sevRank[a.severity] - sevRank[b.severity] || b.cvss - a.cvss);
  }, [findings, sev, status]);

  useEffect(() => {
    if (filtered.length && !filtered.some((f) => f.id === selId)) setSelId(filtered[0]!.id);
  }, [filtered, selId]);

  const sel = filtered.find((f) => f.id === selId) ?? null;

  const counts: Record<string, number> = {};
  filtered.forEach((f) => (counts[f.severity] = (counts[f.severity] ?? 0) + 1));

  const act = async (f: Finding, next: 'verified' | 'dismissed' | 'candidate') => {
    try {
      await setStatusM.mutateAsync({ id: f.id, status: next });
      toast(
        next === 'verified' ? 'Finding verified' : next === 'dismissed' ? 'Finding dismissed' : 'Finding restored',
        next === 'dismissed' ? 'warning' : 'success',
      );
    } catch {
      toast('Could not update the finding', 'error');
    }
  };

  let lastSev: string | null = null;

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
        <FilterMenu
          prefix="Severity: "
          value={sev}
          onChange={setSev}
          options={[{ value: 'all', label: 'All' }, ...SEVERITIES.map((s) => ({ value: s, label: SEV_LABEL[s] }))]}
        />
        <FilterMenu
          prefix="Status: "
          value={status}
          onChange={setStatus}
          options={[
            { value: 'all', label: 'All' },
            { value: 'verified', label: 'Verified' },
            { value: 'candidate', label: 'Candidate' },
            { value: 'dismissed', label: 'Dismissed' },
          ]}
        />
      </div>
      <div className="tri">
        <div className="card">
          <div style={{ padding: 0 }}>
            {filtered.length === 0 ? (
              <div className="meta" style={{ padding: '22px', textAlign: 'center' }}>
                No findings match.
              </div>
            ) : (
              filtered.map((f) => {
                const head =
                  f.severity !== lastSev ? (
                    <div className="grp" key={`g-${f.severity}`}>
                      <span className="gs" style={{ background: sevVar(f.severity) }} />
                      {SEV_LABEL[f.severity]} <span className="gc">{counts[f.severity]}</span>
                    </div>
                  ) : null;
                lastSev = f.severity;
                return (
                  <div key={f.id}>
                    {head}
                    <div
                      className={`fitem${f.id === selId ? ' sel' : ''}${f.status === 'dismissed' ? ' dismissed' : ''}`}
                      role="button"
                      tabIndex={0}
                      onClick={() => setSelId(f.id)}
                      onKeyDown={onActivate(() => setSelId(f.id))}
                    >
                      <span className={`sev ${f.severity}`} />
                      <span className="fid mono">{shortId(f.id)}</span>
                      <span className="ftt">{f.title}</span>
                      <span className="floc mono">{f.location.split('· ').pop()}</span>
                      <span className="fcv tab">{f.cvss.toFixed(1)}</span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
        <div className="detail">
          <div className="card">
            <div className="card-b">
              {!sel ? (
                <div className="meta" style={{ padding: 10 }}>
                  Select a finding.
                </div>
              ) : (
                <>
                  <span className="tagpill" style={{ background: sevVar(sel.severity) }}>
                    {sel.severity.toUpperCase()} · {sel.cvss.toFixed(1)}
                  </span>
                  <div className="dh" style={{ marginTop: 10 }}>
                    {sel.title}
                  </div>
                  <div className="kv">
                    <span className="k">Finding</span>
                    <span className="v mono">{shortId(sel.id)}</span>
                  </div>
                  <div className="kv">
                    <span className="k">Location</span>
                    <span className="v mono">{sel.location}</span>
                  </div>
                  {sel.cwe && (
                    <div className="kv">
                      <span className="k">CWE</span>
                      <span className="v">{sel.cwe}</span>
                    </div>
                  )}
                  <div className="kv">
                    <span className="k">Status</span>
                    <span
                      className="v"
                      style={{
                        textTransform: 'capitalize',
                        color: sel.status === 'verified' ? 'var(--ok)' : sel.status === 'dismissed' ? 'var(--tx-4)' : 'var(--tx-2)',
                      }}
                    >
                      {sel.status}
                    </span>
                  </div>
                  {sel.remediation && (
                    <p style={{ fontSize: '12.5px', color: 'var(--tx-2)', lineHeight: 1.55, margin: '14px 0 4px' }}>
                      {sel.remediation}
                    </p>
                  )}
                  <div style={{ display: 'flex', gap: 8, marginTop: 14 }}>
                    <button type="button"
                      className="btn pri sm"
                      style={{ flex: 1, justifyContent: 'center' }}
                      disabled={setStatusM.isPending}
                      onClick={() => void act(sel, 'verified')}
                    >
                      {sel.status === 'verified' ? 'Verified' : 'Verify'}
                    </button>
                    <button type="button"
                      className="btn sm"
                      disabled={setStatusM.isPending}
                      onClick={() => void act(sel, sel.status === 'dismissed' ? 'candidate' : 'dismissed')}
                    >
                      {sel.status === 'dismissed' ? 'Restore' : 'Dismiss'}
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
