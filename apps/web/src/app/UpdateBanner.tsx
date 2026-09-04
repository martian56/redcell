import { useState } from 'react';
import { useSelfUpdate, useVersion } from '@/features/hooks';

export function UpdateBanner() {
  const { data: v } = useVersion();
  const update = useSelfUpdate();
  const [msg, setMsg] = useState<string | null>(null);
  if (!v) return null;
  const onUpdate = async () => {
    setMsg(null);
    try {
      const r = await update.mutateAsync();
      setMsg(r.detail);
    } catch {
      setMsg('In-app update is not available on this deployment.');
    }
  };
  return (
    <div className="updbar">
      <div className="updbar-v">
        <span className="meta">Version</span>
        <span className="mono">{v.current}</span>
      </div>
      {v.updateAvailable ? (
        <div className="updbar-act">
          <span>
            Update available: <b className="mono">{v.latest}</b>
          </span>
          <button type="button" className="btn pri sm" disabled={update.isPending} onClick={onUpdate}>
            {update.isPending ? 'Starting…' : 'Update now'}
          </button>
        </div>
      ) : (
        <span className="meta">Up to date</span>
      )}
      {msg ? <span className="meta updbar-msg">{msg}</span> : null}
    </div>
  );
}
