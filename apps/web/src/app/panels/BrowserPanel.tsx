import { useEffect, useRef, useState } from 'react';
import RFB from '@novnc/novnc';
import { useUI } from '@/store/ui';
import { useApi } from '@/lib/api';
import { Button, Empty } from '@/components/ui/primitives';

type Status = 'connecting' | 'connected' | 'disconnected';

export function BrowserPanel() {
  const sessionId = useUI((s) => s.activeSessionId);
  const api = useApi();
  const screenRef = useRef<HTMLDivElement>(null);
  const rfbRef = useRef<RFB | null>(null);
  const operatorRef = useRef(false);
  const [status, setStatus] = useState<Status>('connecting');
  const [operator, setOperator] = useState(false);

  useEffect(() => {
    if (!sessionId || !screenRef.current) return;
    setStatus('connecting');
    let rfb: RFB | null = null;
    try {
      rfb = new RFB(screenRef.current, api.browser.vncUrl(sessionId), { shared: true });
      rfb.viewOnly = !operatorRef.current;
      rfb.scaleViewport = true;
      rfb.addEventListener('connect', () => setStatus('connected'));
      rfb.addEventListener('disconnect', () => setStatus('disconnected'));
      rfbRef.current = rfb;
    } catch {
      setStatus('disconnected');
    }
    return () => {
      try {
        rfb?.disconnect();
      } catch {
        /* already gone */
      }
      rfbRef.current = null;
    };
  }, [sessionId, api]);

  const toggleControl = async () => {
    if (!sessionId) return;
    const next = !operator;
    await api.browser.control(sessionId, next ? 'operator' : 'agent');
    operatorRef.current = next;
    if (rfbRef.current) rfbRef.current.viewOnly = !next;
    setOperator(next);
  };

  if (!sessionId) return <Empty>No active session.</Empty>;

  return (
    <div className="flex h-full flex-col">
      <div className="flex flex-none items-center gap-2 border-b border-border bg-bg2 px-3 py-2">
        <span className="font-mono text-[10px] uppercase tracking-wider text-faint">Browser</span>
        <span className="font-mono text-[10px] text-muted">
          {status}
          {operator ? ' · you have control' : ''}
        </span>
        <Button variant="subtle" className="ml-auto h-6 px-2 text-[11px]" onClick={toggleControl}>
          {operator ? 'Release control' : 'Take control'}
        </Button>
      </div>
      <div ref={screenRef} className="min-h-0 flex-1 bg-black" />
    </div>
  );
}
