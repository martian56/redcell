import { useNavigate } from 'react-router-dom';
import type { Session, Severity } from '@redcell/api-client';
import { useSessions } from '@/features/hooks';
import { SEVERITIES, sevVar, timeAgo } from '@/lib/format';
import { AreaChart } from '@/components/ui/AreaChart';

const SEV_LABEL: Record<Severity, string> = {
  critical: 'Critical',
  high: 'High',
  medium: 'Medium',
  low: 'Low',
  info: 'Info',
};

function sevBar(counts: Record<Severity, number>) {
  const bars = (['critical', 'high', 'medium', 'low'] as Severity[])
    .filter((s) => counts[s] > 0)
    .map((s) => (
      <i key={s} style={{ width: `${Math.min(counts[s] * 6 + 2, 40)}px`, background: sevVar(s) }} />
    ));
  return bars.length ? bars : <span className="z">·</span>;
}

function SessionRow({ s, onOpen }: { s: Session; onOpen: () => void }) {
  const dot = s.status === 'active' ? 'live' : 'done';
  return (
    <tr className="row" onClick={onOpen}>
      <td>
        <div className="name">
          <span className={`sd ${dot}`} />
          <span>
            <span className="nn">{s.name}</span> <span className="cl">/ {s.client}</span>
          </span>
        </div>
      </td>
      <td>
        <span className="kind" style={{ textTransform: 'capitalize' }}>
          {s.kind}
        </span>
      </td>
      <td>
        <span className={`status${s.status === 'active' ? ' live' : ''}`} style={{ textTransform: 'capitalize' }}>
          {s.status}
        </span>
      </td>
      <td>
        <div className="sevbar">{sevBar(s.severityCounts)}</div>
      </td>
      <td className="meta mono">{s.targets.length || '—'}</td>
      <td>
        <span className="model">{s.model ?? '—'}</span>
      </td>
      <td className="tright meta">{timeAgo(s.createdAt)}</td>
    </tr>
  );
}

export function OverviewPage() {
  const nav = useNavigate();
  const { data: sessions } = useSessions();
  const list = sessions ?? [];

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
          <button className="btn sm" style={{ marginLeft: 'auto' }} onClick={() => nav('/sessions')}>
            View all
          </button>
        </div>
        <div className="card-b" style={{ padding: '12px 2px 4px' }}>
          <table className="tbl">
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
              {list.slice(0, 8).map((s) => (
                <SessionRow key={s.id} s={s} onOpen={() => nav(`/sessions/${s.id}`)} />
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
