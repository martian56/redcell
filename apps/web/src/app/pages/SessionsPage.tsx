import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSessions } from '@/features/hooks';
import { SessionRow, FilterMenu } from './shared';

export function SessionsPage() {
  const nav = useNavigate();
  const { data: sessions, isLoading } = useSessions();
  const [status, setStatus] = useState('all');
  const [kind, setKind] = useState('all');

  const rows = (sessions ?? []).filter(
    (s) => (status === 'all' || s.status === status) && (kind === 'all' || s.kind === kind),
  );

  return (
    <div className="wrap">
      <div className="filters">
        <FilterMenu
          prefix="Status: "
          value={status}
          onChange={setStatus}
          icon
          options={[
            { value: 'all', label: 'All' },
            { value: 'active', label: 'Active' },
            { value: 'archived', label: 'Archived' },
          ]}
        />
        <FilterMenu
          prefix="Type: "
          value={kind}
          onChange={setKind}
          options={[
            { value: 'all', label: 'All' },
            { value: 'network', label: 'Network' },
            { value: 'code', label: 'Code scan' },
          ]}
        />
        <div className="grow" />
        <button className="btn pri sm" onClick={() => nav('/sessions/new')}>
          <svg viewBox="0 0 24 24">
            <path d="M12 5v14M5 12h14" />
          </svg>
          New session
        </button>
      </div>
      <div className="card">
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
              {isLoading ? (
                <tr>
                  <td colSpan={7} className="meta" style={{ padding: '22px', textAlign: 'center' }}>
                    Loading sessions…
                  </td>
                </tr>
              ) : rows.length === 0 ? (
                <tr>
                  <td colSpan={7} className="meta" style={{ padding: '22px', textAlign: 'center' }}>
                    No sessions match.
                  </td>
                </tr>
              ) : (
                rows.map((s) => <SessionRow key={s.id} s={s} onOpen={() => nav(`/sessions/${s.id}`)} />)
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
