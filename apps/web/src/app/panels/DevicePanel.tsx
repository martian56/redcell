import { useCallback, useEffect, useRef, useState } from 'react';
import { useUI } from '@/store/ui';
import { useApi } from '@/lib/api';
import { Button, Empty } from '@/components/ui/primitives';

type Status = 'connecting' | 'live' | 'disconnected' | 'error';

export function DevicePanel() {
  const sessionId = useUI((s) => s.activeSessionId);
  const api = useApi();
  const imgRef = useRef<HTMLImageElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const urlRef = useRef<string | null>(null);
  const operatorRef = useRef(false);
  const [status, setStatus] = useState<Status>('connecting');
  const [operator, setOperator] = useState(false);

  const teardown = useCallback(() => {
    try {
      wsRef.current?.close();
    } catch {
      /* already gone */
    }
    wsRef.current = null;
    if (urlRef.current) {
      URL.revokeObjectURL(urlRef.current);
      urlRef.current = null;
    }
  }, []);

  const connect = useCallback(() => {
    if (!sessionId) return;
    teardown();
    setStatus('connecting');
    const ws = new WebSocket(api.device.screenUrl(sessionId));
    ws.binaryType = 'arraybuffer';
    ws.onopen = () => setStatus('live');
    ws.onerror = () => setStatus('error');
    ws.onclose = () => setStatus('disconnected');
    ws.onmessage = (ev) => {
      if (!(ev.data instanceof ArrayBuffer) || !imgRef.current) return;
      const url = URL.createObjectURL(new Blob([ev.data], { type: 'image/png' }));
      imgRef.current.src = url;
      if (urlRef.current) URL.revokeObjectURL(urlRef.current);
      urlRef.current = url;
      setStatus('live');
    };
    wsRef.current = ws;
  }, [sessionId, api, teardown]);

  useEffect(() => {
    connect();
    return teardown;
  }, [connect, teardown]);

  const send = (action: Record<string, unknown>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) wsRef.current.send(JSON.stringify(action));
  };

  const onScreenClick = (e: React.MouseEvent<HTMLImageElement>) => {
    const img = imgRef.current;
    if (!operatorRef.current || !img || !img.naturalWidth) return;
    const rect = img.getBoundingClientRect();
    const scale = Math.min(rect.width / img.naturalWidth, rect.height / img.naturalHeight);
    const shownW = img.naturalWidth * scale;
    const shownH = img.naturalHeight * scale;
    const offX = (rect.width - shownW) / 2;
    const offY = (rect.height - shownH) / 2;
    const x = (e.clientX - rect.left - offX) / scale;
    const y = (e.clientY - rect.top - offY) / scale;
    if (x < 0 || y < 0 || x > img.naturalWidth || y > img.naturalHeight) return;
    send({ type: 'tap', x: Math.round(x), y: Math.round(y) });
  };

  const onKey = (e: React.KeyboardEvent) => {
    if (!operatorRef.current) return;
    if (e.key === 'Backspace') send({ type: 'key', key: 'KEYCODE_DEL' });
    else if (e.key === 'Enter') send({ type: 'key', key: 'KEYCODE_ENTER' });
    else if (e.key.length === 1) send({ type: 'text', text: e.key });
    else return;
    e.preventDefault();
  };

  const toggleControl = () => {
    const next = !operator;
    operatorRef.current = next;
    setOperator(next);
  };

  if (!sessionId) return <Empty>No active session.</Empty>;

  return (
    <div className="flex h-full flex-col">
      <div className="flex flex-none items-center gap-2 border-b border-border bg-bg2 px-3 py-2">
        <span className="font-mono text-[10px] uppercase tracking-wider text-faint">Device</span>
        <span className="min-w-0 truncate font-mono text-[10px] text-muted">
          {status === 'disconnected' || status === 'error'
            ? 'device not up yet (it boots on the first mobile run; Reconnect to retry)'
            : status}
          {operator ? ' · you have control' : ''}
        </span>
        {status === 'live' ? (
          <Button variant="subtle" className="ml-auto h-6 flex-none px-2 text-[11px]" onClick={toggleControl}>
            {operator ? 'Release control' : 'Take control'}
          </Button>
        ) : (
          <Button variant="subtle" className="ml-auto h-6 flex-none px-2 text-[11px]" onClick={connect}>
            Reconnect
          </Button>
        )}
      </div>
      <div
        className="grid min-h-0 flex-1 place-items-center bg-black p-2 outline-none"
        tabIndex={0}
        onKeyDown={onKey}
      >
        <img
          ref={imgRef}
          alt="Android device screen"
          className="max-h-full max-w-full object-contain"
          style={{ cursor: operator ? 'crosshair' : 'default' }}
          onClick={onScreenClick}
        />
      </div>
    </div>
  );
}
