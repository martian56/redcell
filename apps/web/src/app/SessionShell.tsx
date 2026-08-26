import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useUI } from '@/store/ui';
import { useRun, useRunControls, useSession } from '@/features/hooks';
import { fmtTokens } from '@/lib/format';
import { Spinner } from '@/components/ui/primitives';
import { toggleTheme } from '@/lib/theme';
import { AgentGraphPanel } from './panels/AgentGraphPanel';
import { LiveFeedPanel } from './panels/LiveFeedPanel';
import { FindingsPanel } from './panels/FindingsPanel';
import { ChatPanel } from './panels/ChatPanel';
import { TerminalsPanel } from './panels/TerminalsPanel';
import { BrowserPanel } from './panels/BrowserPanel';
import { AttackSurfacePanel } from './panels/AttackSurfacePanel';
import { LootPanel } from './panels/LootPanel';
import { ListenersPanel } from './panels/ListenersPanel';
import { ProxyPanel } from './panels/ProxyPanel';

type ShellTab = 'terminals' | 'browser';
type DataTab = 'surface' | 'loot' | 'listeners' | 'proxy';

export function SessionShell() {
  const { id } = useParams();
  const nav = useNavigate();
  const setActiveSession = useUI((s) => s.setActiveSession);
  const setActiveRun = useUI((s) => s.setActiveRun);
  const { data: session, isLoading } = useSession(id ?? null);
  const runId = session?.activeRunId ?? null;
  const { data: run } = useRun(runId);
  const controls = useRunControls();

  const [shellTab, setShellTab] = useState<ShellTab>('terminals');
  const [dataTab, setDataTab] = useState<DataTab>('surface');

  useEffect(() => {
    setActiveSession(id ?? null);
  }, [id, setActiveSession]);
  useEffect(() => {
    if (session) setActiveRun(session.activeRunId ?? null);
  }, [session, setActiveRun]);

  const status = run?.status ?? 'queued';
  const isRunning = status === 'running';
  const canResume = ['paused', 'failed', 'stopped'].includes(status);
  const canStop = status === 'running' || status === 'paused';
  const pillCls = isRunning ? '' : status === 'paused' ? 'paused' : 'stopped';
  const pillTxt = isRunning ? `Live · ${run?.phase ?? 'run'}` : status === 'paused' ? 'Paused' : status === 'completed' ? 'Completed' : 'Stopped';
  const busy = controls.pause.isPending || controls.resume.isPending || controls.stop.isPending;

  if (isLoading && !session) {
    return (
      <div className="cconsole">
        <div className="grid h-full place-items-center">
          <Spinner />
        </div>
      </div>
    );
  }

  return (
    <div className="cconsole">
      <header className="head">
        <button className="iconbtn" onClick={() => nav('/sessions')} title="Back to sessions" aria-label="Back">
          <svg viewBox="0 0 24 24">
            <path d="M15 6l-6 6 6 6" />
          </svg>
        </button>
        <div className="crumb">
          <b>{session?.name}</b>
          <span className="s">/</span>
          <span className="cl">{session?.client}</span>
          {run && (
            <>
              <span className="s">/</span>
              <span className="cl">run</span>
            </>
          )}
        </div>
        <span className={`pill ${pillCls}`}>
          <span className="d" />
          {pillTxt}
        </span>
        <div className="grow" />
        {run && (
          <span className="spend tab">
            {fmtTokens(run.tokens)} tok · <b>${run.costUsd.toFixed(2)}</b>
          </span>
        )}
        <button
          className="btn"
          disabled={busy || (!isRunning && !canResume) || !runId}
          onClick={() => runId && (isRunning ? controls.pause.mutate(runId) : controls.resume.mutate(runId))}
        >
          {isRunning ? 'Pause' : 'Resume'}
        </button>
        <button className="btn danger" disabled={busy || !canStop || !runId} onClick={() => runId && controls.stop.mutate(runId)}>
          Stop
        </button>
        <button className="btn pri" onClick={() => nav('/reports')}>
          Report
        </button>
        <button className="iconbtn" onClick={toggleTheme} title="Toggle theme" aria-label="Toggle theme">
          <svg viewBox="0 0 24 24">
            <path d="M12 3v2M12 19v2M5 5l1.5 1.5M17.5 17.5L19 19M3 12h2M19 12h2M5 19l1.5-1.5M17.5 6.5L19 5M12 8a4 4 0 100 8 4 4 0 000-8z" />
          </svg>
        </button>
      </header>

      <div className="cmosaic">
        <div className="ccol">
          <section className="cpanel" style={{ flex: '0 0 42%' }}>
            <div className="ph">
              <span className="t">Agents</span>
            </div>
            <div className="pb">
              <AgentGraphPanel />
            </div>
          </section>
          <section className="cpanel">
            <div className="ph">
              <span className="t">Activity</span>
            </div>
            <div className="pb">
              <LiveFeedPanel />
            </div>
          </section>
        </div>

        <div className="ccol">
          <section className="cpanel" style={{ flex: '0 0 52%' }}>
            <div className="ph">
              <span className="t">Findings</span>
            </div>
            <div className="pb">
              <FindingsPanel />
            </div>
          </section>
          <section className="cpanel">
            <div className="ptabs">
              <button className={`ptab${shellTab === 'terminals' ? ' on' : ''}`} onClick={() => setShellTab('terminals')}>
                Terminals
              </button>
              <button className={`ptab${shellTab === 'browser' ? ' on' : ''}`} onClick={() => setShellTab('browser')}>
                Browser
              </button>
            </div>
            <div className="pb" style={{ display: 'flex', flexDirection: 'column' }}>
              {shellTab === 'terminals' ? <TerminalsPanel /> : <BrowserPanel />}
            </div>
          </section>
        </div>

        <div className="ccol">
          <section className="cpanel" style={{ flex: '0 0 55%' }}>
            <div className="ph">
              <span className="t">Chat</span>
              <span className="sp" />
              <span className="n">steers the orchestrator</span>
            </div>
            <div style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
              <ChatPanel />
            </div>
          </section>
          <section className="cpanel">
            <div className="ptabs">
              <button className={`ptab${dataTab === 'surface' ? ' on' : ''}`} onClick={() => setDataTab('surface')}>
                Attack surface
              </button>
              <button className={`ptab${dataTab === 'loot' ? ' on' : ''}`} onClick={() => setDataTab('loot')}>
                Loot
              </button>
              <button className={`ptab${dataTab === 'listeners' ? ' on' : ''}`} onClick={() => setDataTab('listeners')}>
                Listeners
              </button>
              <button className={`ptab${dataTab === 'proxy' ? ' on' : ''}`} onClick={() => setDataTab('proxy')}>
                Proxy
              </button>
            </div>
            <div className="pb" style={{ display: 'flex', flexDirection: 'column' }}>
              {dataTab === 'surface' && <AttackSurfacePanel />}
              {dataTab === 'loot' && <LootPanel />}
              {dataTab === 'listeners' && <ListenersPanel />}
              {dataTab === 'proxy' && <ProxyPanel />}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
