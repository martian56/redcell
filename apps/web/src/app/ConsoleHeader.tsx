import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getLeaves } from 'react-mosaic-component';
import { useRun, useRunControls, useSession } from '@/features/hooks';
import { PANEL_LABELS, SWAPPABLE, useWorkspace } from '@/store/workspace';
import { fmtTokens } from '@/lib/format';
import { Dropdown } from '@/components/ui/Dropdown';
import { NewRunDialog } from './NewRunDialog';

export function ConsoleHeader({ sessionId }: { sessionId: string | null }) {
  const nav = useNavigate();
  const { data: session } = useSession(sessionId);
  const runId = session?.activeRunId ?? null;
  const { data: run } = useRun(runId);
  const controls = useRunControls();
  const layout = useWorkspace((s) => s.layout);
  const addPanel = useWorkspace((s) => s.addPanel);
  const reset = useWorkspace((s) => s.reset);
  const [newRun, setNewRun] = useState(false);

  const visible = new Set(layout ? getLeaves(layout) : []);
  const addable = SWAPPABLE.filter((id) => !visible.has(id));

  const status = run?.status ?? 'queued';
  const isRunning = status === 'running';
  const canResume = ['paused', 'failed', 'stopped'].includes(status);
  const canStop = status === 'running' || status === 'paused';
  const busy = controls.pause.isPending || controls.resume.isPending || controls.stop.isPending;
  const pillCls = isRunning ? '' : status === 'paused' ? 'paused' : 'stopped';
  const pillTxt = isRunning
    ? `Live · ${run?.phase ?? 'run'}`
    : status === 'paused'
      ? 'Paused'
      : status === 'completed'
        ? 'Completed'
        : status === 'failed'
          ? 'Failed'
          : status === 'stopped'
            ? 'Stopped'
            : 'Queued';

  return (
    <>
      <div className="crumb">
        <b>{session?.name ?? 'Session'}</b>
        {session?.client && (
          <>
            <span className="s">/</span>
            <span className="cl">{session.client}</span>
          </>
        )}
      </div>
      {run && (
        <span className={`pill ${pillCls}`}>
          <span className="d" />
          {pillTxt}
        </span>
      )}
      <div className="grow" />
      {run && (
        <span className="spend tab">
          {fmtTokens(run.tokens)} tok · <b>${run.costUsd.toFixed(2)}</b>
        </span>
      )}
      {run && (
        <button
          className="btn"
          disabled={busy || (!isRunning && !canResume) || !runId}
          onClick={() => runId && (isRunning ? controls.pause.mutate(runId) : controls.resume.mutate(runId))}
        >
          {isRunning ? 'Pause' : 'Resume'}
        </button>
      )}
      {run && (
        <button className="btn danger" disabled={busy || !canStop || !runId} onClick={() => runId && controls.stop.mutate(runId)}>
          Stop
        </button>
      )}
      <button className="btn pri" onClick={() => setNewRun(true)}>
        <svg viewBox="0 0 24 24">
          <path d="M12 5v14M5 12h14" />
        </svg>
        New run
      </button>
      <button className="btn" onClick={() => nav('/reports')}>
        Report
      </button>
      <Dropdown
        align="right"
        width={210}
        options={[
          ...addable.map((id) => ({ value: id, label: `Add ${PANEL_LABELS[id]}` })),
          { value: '__reset', label: 'Reset layout' },
        ]}
        onChange={(v) => (v === '__reset' ? reset() : addPanel(v as (typeof SWAPPABLE)[number]))}
        trigger={
          <span className="iconbtn" title="Layout & panels">
            <svg viewBox="0 0 24 24">
              <rect x="3" y="4" width="18" height="16" rx="2" />
              <path d="M15 4v16" />
            </svg>
          </span>
        }
      />
      <NewRunDialog open={newRun} onClose={() => setNewRun(false)} sessionId={sessionId} />
    </>
  );
}
