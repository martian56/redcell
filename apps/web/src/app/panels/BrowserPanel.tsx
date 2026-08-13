import { useCallback, useEffect, useRef, useState } from 'react';
import RFB from '@novnc/novnc';
import { useUI } from '@/store/ui';
import { useApi } from '@/lib/api';
import { Button, Empty } from '@/components/ui/primitives';

type Status = 'idle' | 'starting' | 'connecting' | 'connected' | 'disconnected' | 'error';

export function BrowserPanel() {
  const sessionId = useUI((s) => s.activeSessionId);
  const api = useApi();
  const screenRef = useRef<HTMLDivElement>(null);
  const rfbRef = useRef<RFB | null>(null);
  const operatorRef = useRef(false);
  const busyRef = useRef(false);
  const sessionIdRef = useRef(sessionId);
  const [status, setStatus] = useState<Status>('idle');
  const [detail, setDetail] = useState('');
  const [operator, setOperator] = useState(false);

  useEffect(() => {
    sessionIdRef.current = sessionId;
  }, [sessionId]);

  const teardown = useCallback(() => {
    try {
      rfbRef.current?.disconnect();
    } catch {
      /* already gone */
    }
    rfbRef.current = null;
  }, []);

  const connect = useCallback(async () => {
    if (!sessionId || !screenRef.current) return;
    teardown();
    // Ownership is per session: never carry the previous session's control state over.
    operatorRef.current = false;
    setOperator(false);
    setDetail('');
    setStatus('starting');
    const started = await api.browser
      .start(sessionId)
      .catch(() => ({ ok: false, detail: 'could not reach the API' }));
    // Bail if the session changed while we were starting.
    if (sessionId !== sessionIdRef.current) return;
    if (!started.ok) {
      setStatus('error');
      setDetail(started.detail || 'could not start the browser (is a run active?)');
      return;
    }
    setStatus('connecting');
    try {
      const rfb = new RFB(screenRef.current, api.browser.vncUrl(sessionId), { shared: true });
      rfb.viewOnly = true; // view-only until the operator explicitly takes control of THIS session
      rfb.scaleViewport = true;
      rfb.addEventListener('connect', () => setStatus('connected'));
      rfb.addEventListener('disconnect', () => setStatus('disconnected'));
      rfbRef.current = rfb;
    } catch {
      setStatus('error');
      setDetail('VNC connection failed');
    }
  }, [sessionId, api, teardown]);

  useEffect(() => {
    void connect();
    return teardown;
  }, [connect, teardown]);

  const toggleControl = async () => {
    if (!sessionId || busyRef.current) return;
    const target = sessionId;
    const rfb = rfbRef.current;
    const next = !operator;
    busyRef.current = true;
    try {
      await api.browser.control(target, next ? 'operator' : 'agent');
      // Only apply if the same session and the same RFB instance are still live.
      if (sessionIdRef.current !== target || rfbRef.current !== rfb || !rfb) return;
      operatorRef.current = next;
      rfb.viewOnly = !next;
      setOperator(next);
    } finally {
      busyRef.current = false;
    }
  };

  if (!sessionId) return <Empty>No active session.</Empty>;

  return (
    <div className="flex h-full flex-col">
      <div className="flex flex-none items-center gap-2 border-b border-border bg-bg2 px-3 py-2">
        <span className="font-mono text-[10px] uppercase tracking-wider text-faint">Browser</span>
        <span className="min-w-0 truncate font-mono text-[10px] text-muted">
          {status}
          {operator ? ' · you have control' : ''}
          {detail ? ` · ${detail}` : ''}
        </span>
        {status === 'connected' ? (
          <Button variant="subtle" className="ml-auto h-6 flex-none px-2 text-[11px]" onClick={toggleControl}>
            {operator ? 'Release control' : 'Take control'}
          </Button>
        ) : (
          <Button
            variant="subtle"
            className="ml-auto h-6 flex-none px-2 text-[11px]"
            disabled={status === 'starting' || status === 'connecting'}
            onClick={() => void connect()}
          >
            Connect
          </Button>
        )}
      </div>
      <div ref={screenRef} className="min-h-0 flex-1 bg-black" />
    </div>
  );
}
