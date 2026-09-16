import { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';

interface TipState {
  text: string;
  x: number;
  y: number;
  place: 'top' | 'bottom';
}

export function TooltipLayer() {
  const [tip, setTip] = useState<TipState | null>(null);
  const currentRef = useRef<Element | null>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    const clearTimer = () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
    };
    const hide = () => {
      clearTimer();
      currentRef.current = null;
      setTip(null);
    };
    const show = (el: Element, delay: number) => {
      const text = el.getAttribute('data-tip');
      if (!text) return;
      currentRef.current = el;
      clearTimer();
      timerRef.current = setTimeout(() => {
        if (currentRef.current !== el || !el.isConnected) return;
        const r = el.getBoundingClientRect();
        const place: TipState['place'] = r.top < 56 ? 'bottom' : 'top';
        setTip({
          text,
          x: Math.round(r.left + r.width / 2),
          y: Math.round(place === 'top' ? r.top : r.bottom),
          place,
        });
      }, delay);
    };
    const target = (e: Event) => (e.target instanceof Element ? e.target.closest('[data-tip]') : null);

    const onOver = (e: MouseEvent) => {
      const el = target(e);
      if (el) {
        if (el !== currentRef.current) show(el, 400);
      } else if (currentRef.current) {
        hide();
      }
    };
    const onFocusIn = (e: FocusEvent) => {
      const el = target(e);
      if (el) show(el, 0);
    };
    const onScrollOrKey = (e: Event) => {
      if (e.type === 'keydown' && (e as KeyboardEvent).key !== 'Escape') return;
      hide();
    };

    document.addEventListener('mouseover', onOver, true);
    document.addEventListener('focusin', onFocusIn, true);
    document.addEventListener('focusout', hide, true);
    window.addEventListener('scroll', onScrollOrKey, true);
    document.addEventListener('keydown', onScrollOrKey, true);
    return () => {
      clearTimer();
      document.removeEventListener('mouseover', onOver, true);
      document.removeEventListener('focusin', onFocusIn, true);
      document.removeEventListener('focusout', hide, true);
      window.removeEventListener('scroll', onScrollOrKey, true);
      document.removeEventListener('keydown', onScrollOrKey, true);
    };
  }, []);

  if (!tip) return null;
  return createPortal(
    <div
      role="tooltip"
      style={{
        position: 'fixed',
        left: tip.x,
        top: tip.y,
        transform: `translate(-50%, ${tip.place === 'top' ? 'calc(-100% - 7px)' : '7px'})`,
      }}
      className="pointer-events-none z-[10000] max-w-[280px] whitespace-pre-line rounded-[6px] border border-border2 bg-panel2 px-2 py-1 font-mono text-[11px] leading-snug text-text shadow-[var(--shadow)]"
    >
      {tip.text}
    </div>,
    document.body,
  );
}
