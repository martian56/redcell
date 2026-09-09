import { useNavigate } from 'react-router-dom';
import type { Severity } from '@redcell/api-client';
import { useDismissSetupAction, useSessions, useSetupStatus } from '@/features/hooks';
import { SEVERITIES, sevVar, timeAgo } from '@/lib/format';
import { AreaChart } from '@/components/ui/AreaChart';
import { SessionRow } from './shared';

const SEV_LABEL: Record<Severity, string> = {
  critical: 'Critical',
  high: 'High',
  medium: 'Medium',
  low: 'Low',
  info: 'Info',
};

const RECOMMENDED: { key: string; satisfied: (s: { hasAiKey: boolean; hasNgrok: boolean }) => boolean; title: string; desc: string; cta: string }[] = [
  {
    key: 'ai-key',
    satisfied: (s) => s.hasAiKey,
    title: 'Add an AI provider key',
    desc: 'REDCELL needs a model provider key to run engagements. Add one to start a session.',
    cta: 'Add a key',
  },
  {
    key: 'ngrok',
    satisfied: (s) => s.hasNgrok,
    title: 'Connect ngrok for reverse shells',
    desc: 'Add an ngrok auth token to catch reverse shells with no open ports. Works on a free ngrok account.',
    cta: 'Add ngrok token',
  },
];

export function OverviewPage() {
  const nav = useNavigate();
  const { data: sessions } = useSessions();
  const { data: setup } = useSetupStatus();
  const dismissAction = useDismissSetupAction();
  const list = sessions ?? [];

  const recs = setup
    ? RECOMMENDED.filter((r) => !r.satisfied(setup) && !setup.dismissed.includes(r.key))
    : [];

  const activeCount = list.filter((s) => s.status === 'active').length;
  const totalFindings = list.reduce((a, s) => a + s.findingsCount, 0);
  const sevTotals = SEVERITIES.reduce(
    (acc, sev) => {
      acc[sev] = list.reduce((a, s) => a + (s.severityCounts[sev] ?? 0), 0);
      return acc;
    },
    {} as Record<Severity, number>,
  );
  const critHigh = sevTotals.critical + sevTotals.high;
  const sevMax = Math.max(1, ...SEVERITIES.map((s) => sevTotals[s]));

  const chron = [...list].sort((a, b) => a.createdAt.localeCompare(b.createdAt));
  let acc = 0;
  const series =
    chron.length >= 2
      ? chron.map((s) => {
          acc += s.findingsCount;
          return { label: timeAgo(s.createdAt), value: acc };
        })
      : [
          { label: 'start', value: 0 },
          { label: 'now', value: totalFindings },
        ];

  return (
    <div className="wrap">
      {recs.length > 0 && (
        <div className="card" style={{ marginBottom: 16 }}>
          <div className="card-h">
            <h3>Recommended actions</h3>
            <span className="cs">· finish setting up REDCELL</span>
          </div>
          <div className="card-b">
            {recs.map((r) => (
              <div className="formrow" key={r.key}>
                <div>
                  <div className="ft">{r.title}</div>
                  <div className="fd">{r.desc}</div>
                </div>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexShrink: 0 }}>
                  <button type="button" className="btn sm pri" onClick={() => nav('/settings')}>
                    {r.cta}
                  </button>
                  <button
                    type="button"
                    className="btn sm"
                    aria-label={`Dismiss: ${r.title}`}
                    disabled={dismissAction.isPending}
                    onClick={() => dismissAction.mutate(r.key)}
                  >
                    Dismiss
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="kpis">
        <div className="kpi">
          <span className="k">Active sessions</span>
          <div className="vrow">
            <span className="v">{activeCount}</span>
          </div>
          <span className="delta flat">{list.length} total</span>
        </div>
        <div className="kpi">
          <span className="k">Open findings</span>
          <div className="vrow">
            <span className="v">{totalFindings}</span>
          </div>
          <div className="sevmini">
            {SEVERITIES.filter((s) => sevTotals[s] > 0).map((s) => (
              <i key={s} style={{ background: sevVar(s), width: `${Math.max(8, (sevTotals[s] / totalFindings) * 120)}px` }} />
            ))}
          </div>
        </div>
        <div className="kpi">
          <span className="k">Critical &amp; high</span>
          <div className="vrow">
            <span className="v" style={{ color: 'var(--crit)' }}>
              {critHigh}
            </span>
          </div>
          <span className="delta warn">needs triage</span>
        </div>
        <div className="kpi">
          <span className="k">Sessions</span>
          <div className="vrow">
            <span className="v">{list.length}</span>
          </div>
          <span className="delta flat">{list.filter((s) => s.status === 'archived').length} archived</span>
        </div>
      </div>

      <div className="two">
        <div className="card">
          <div className="card-h">
            <h3>Findings discovered</h3>
            <span className="cs">· cumulative</span>
            <span className="rt">{totalFindings} total</span>
          </div>
          <div className="card-b">
            <AreaChart data={series} />
          </div>
        </div>
        <div className="card">
          <div className="card-h">
            <h3>By severity</h3>
            <span className="cs">· {totalFindings} open</span>
          </div>
          <div className="card-b">
            <div className="sevlist">
              {SEVERITIES.map((s) => (
                <div className="sevrow" key={s}>
                  <span className="sl">
                    <span className="sdq" style={{ background: sevVar(s) }} />
                    {SEV_LABEL[s]}
                  </span>
                  <div className="track">
                    <i style={{ width: `${(sevTotals[s] / sevMax) * 100}%`, background: sevVar(s) }} />
                  </div>
                  <span className="sc">{sevTotals[s]}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-h">
          <h3>Recent sessions</h3>
          <span className="cs">· {list.length}</span>
          <button type="button" className="btn sm" style={{ marginLeft: 'auto' }} onClick={() => nav('/sessions')}>
            View all
          </button>
        </div>
        <div className="card-b" style={{ padding: '12px 2px 4px' }}>
          <table className="tbl tbl-cards">
            <thead>
              <tr>
                <th>Session</th>
                <th>Type</th>
                <th>Status</th>
                <th>Findings</th>
                <th>Targets</th>
                <th>Model</th>
                <th className="tright">Last active</th>
              </tr>
            </thead>
            <tbody>
              {[...chron]
                .reverse()
                .slice(0, 8)
                .map((s) => (
                  <SessionRow key={s.id} s={s} onOpen={() => nav(`/sessions/${s.id}`)} />
                ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
