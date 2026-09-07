import { useEffect, useRef, useState, type ReactNode } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useIsMobile } from '@/lib/useIsMobile';

const THRESHOLD = 70;
const MAX = 110;
const DAMP = 0.5;

export function PullToRefresh({ className, children }: { className?: string; children: ReactNode }) {
  const isMobile = useIsMobile();
  const qc = useQueryClient();
  const ref = useRef<HTMLDivElement>(null);
  const startY = useRef<number | null>(null);
  const pullRef = useRef(0);
  const refreshingRef = useRef(false);
  const [pull, setPull] = useState(0);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el || !isMobile) return;

    const setDist = (v: number) => {
      pullRef.current = v;
      setPull(v);
    };

    const onStart = (e: TouchEvent) => {
      const t = e.touches[0];
      startY.current = t && el.scrollTop <= 0 && !refreshingRef.current ? t.clientY : null;
    };
    const onMove = (e: TouchEvent) => {
      const t = e.touches[0];
      if (startY.current === null || !t) return;
      if (el.scrollTop > 0) {
        startY.current = null;
        setDist(0);
        return;
      }
      const dy = t.clientY - startY.current;
      if (dy <= 0) {
        setDist(0);
        return;
      }
      const dist = Math.min(MAX, dy * DAMP);
      setDist(dist);
      if (dist > 4) e.preventDefault();
    };
    const onEnd = () => {
      if (startY.current === null) return;
      startY.current = null;
      if (pullRef.current < THRESHOLD) {
        setDist(0);
        return;
      }
      refreshingRef.current = true;
      setRefreshing(true);
      setDist(THRESHOLD);
      void qc.invalidateQueries().finally(() => {
        refreshingRef.current = false;
        setRefreshing(false);
        setDist(0);
      });
    };
    const onCancel = () => {
      startY.current = null;
      setDist(0);
    };

    el.addEventListener('touchstart', onStart, { passive: true });
    el.addEventListener('touchmove', onMove, { passive: false });
    el.addEventListener('touchend', onEnd);
    el.addEventListener('touchcancel', onCancel);
    return () => {
      el.removeEventListener('touchstart', onStart);
      el.removeEventListener('touchmove', onMove);
      el.removeEventListener('touchend', onEnd);
      el.removeEventListener('touchcancel', onCancel);
    };
  }, [isMobile, qc]);

  return (
    <div ref={ref} className={className}>
      <div className="ptr" style={{ height: pull, opacity: pull > 8 ? 1 : 0 }}>
        <span
          className={`ptr-spin${refreshing ? ' on' : ''}`}
          style={refreshing ? undefined : { transform: `rotate(${Math.round(pull * 2.6)}deg)` }}
        />
      </div>
      {children}
    </div>
  );
}
