import { useEffect, useRef, useState } from 'react';
import { useApi } from '@/lib/api';

type Phase = 'starting' | 'applying' | 'reconnecting' | 'done' | 'error';

const STEPS: { key: Exclude<Phase, 'error'>; label: string }[] = [
  { key: 'starting', label: 'Starting the update' },
  { key: 'applying', label: 'Pulling images and restarting' },
  { key: 'reconnecting', label: 'Reconnecting to the console' },
  { key: 'done', label: 'Up to date' },
];
const ORDER: Phase[] = ['starting', 'applying', 'reconnecting', 'done'];

export function UpdateDialog({ open, onClose, target }: { open: boolean; onClose: () => void; target?: string | null }) {
  const api = useApi();
  const [phase, setPhase] = useState<Phase>('starting');
  const [detail, setDetail] = useState('');
  const started = useRef(false);

  useEffect(() => {
    if (!open) {
      started.current = false;
      setPhase('starting');
      setDetail('');
      return;
    }
    if (started.current) return;
    started.current = true;

    let cancelled = false;
    let polls = 0;
    const want = (target ?? '').replace(/^v/, '');

    const finish = () => {
      if (cancelled) return;
      setPhase('done');
      setDetail('The console will reload to finish.');
      setTimeout(() => !cancelled && window.location.reload(), 2500);
    };

    const poll = async () => {
      if (cancelled) return;
      polls += 1;
      try {
        const v = await api.system.version();
        if (!v.updateAvailable || (want && v.current === want)) {
          finish();
          return;
        }
        setPhase('applying');
        setDetail('Applying the new version...');
      } catch {
        setPhase('reconnecting');
        setDetail('The console is restarting...');
      }
      if (polls > 80) {
        setPhase('error');
        setDetail('This is taking longer than expected. Check the server, then reload.');
        return;
      }
      setTimeout(poll, 3000);
    };

    (async () => {
      setPhase('starting');
      setDetail('Requesting the update...');
      try {
        const r = await api.system.update();
        if (cancelled) return;
        setPhase('applying');
        setDetail(r.detail);
      } catch {
        if (cancelled) return;
        setPhase('error');
        setDetail('Could not start the update. In-app update may be disabled on this deployment.');
        return;
      }
      setTimeout(poll, 3000);
    })();

    return () => {
      cancelled = true;
    };
  }, [open, target, api]);

  if (!open) return null;

  const activeIdx = ORDER.indexOf(phase === 'error' ? 'applying' : phase);
  const dismissable = phase === 'done' || phase === 'error';

  return (
    <div className="overlay on" onMouseDown={(e) => e.target === e.currentTarget && dismissable && onClose()}>
      <div className="modal updmodal" role="dialog" aria-label="Update" aria-live="polite">
        <div className="updmodal-h">
          <h2>{phase === 'done' ? 'Updated' : phase === 'error' ? 'Update failed' : 'Updating REDCELL'}</h2>
          {target && phase !== 'error' ? <span className="updmodal-target">{target}</span> : null}
        </div>
        <div className="updsteps">
          {STEPS.map((s, i) => {
            const state =
              phase === 'error' && i >= activeIdx
                ? 'err'
                : phase === 'done' || i < activeIdx
                  ? 'done'
                  : i === activeIdx
                    ? 'active'
                    : 'idle';
            return (
              <div key={s.key} className={`updstep ${state}`}>
                <span className="updstep-dot">
                  {state === 'done' ? '✓' : state === 'err' ? '!' : state === 'active' ? <span className="updspin" /> : ''}
                </span>
                <span className="updstep-label">{s.label}</span>
              </div>
            );
          })}
        </div>
        {detail ? <p className="updmodal-detail">{detail}</p> : null}
        <div className="updmodal-foot">
          {phase === 'done' ? (
            <button type="button" className="btn pri sm" onClick={() => window.location.reload()}>
              Reload now
            </button>
          ) : phase === 'error' ? (
            <button type="button" className="btn sm" onClick={onClose}>
              Close
            </button>
          ) : (
            <span className="meta">You can keep working; the console reconnects on its own.</span>
          )}
        </div>
      </div>
    </div>
  );
}
