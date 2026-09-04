import { useState } from 'react';
import { useVersion } from '@/features/hooks';
import { UpdateDialog } from './UpdateDialog';

export function UpdateBanner() {
  const { data: v } = useVersion();
  const [open, setOpen] = useState(false);
  if (!v) return null;
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
          <button type="button" className="btn pri sm" onClick={() => setOpen(true)}>
            Update now
          </button>
        </div>
      ) : (
        <span className="meta">Up to date</span>
      )}
      <UpdateDialog open={open} onClose={() => setOpen(false)} target={v.latest} />
    </div>
  );
}
