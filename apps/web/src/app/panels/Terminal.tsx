import { useEffect, useRef } from 'react';
import { acquireTerminal } from '@/lib/terminals';

export function Terminal({ shellId, prompt = 'operator@kali' }: { shellId: string; prompt?: string }) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const host = ref.current;
    if (!host) return;
    const { el, fit } = acquireTerminal(shellId, prompt);
    host.appendChild(el);

    const refit = () => {
      if (host.clientWidth > 0 && host.clientHeight > 0) fit.fit();
    };
    const raf = requestAnimationFrame(refit);
    const ro = new ResizeObserver(refit);
    ro.observe(host);

    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
      if (el.parentNode === host) host.removeChild(el);
    };
  }, [shellId, prompt]);

  return <div ref={ref} className="h-full w-full bg-black p-1.5" />;
}
