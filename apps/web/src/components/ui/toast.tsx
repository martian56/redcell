import { create } from 'zustand';
import { cn } from '@/lib/cn';

export type Tone = 'default' | 'success' | 'error' | 'warning' | 'critical' | 'info';

interface ToastItem {
  id: number;
  title: string;
  body?: string;
  tone: Tone;
  onClick?: () => void;
}

interface RichToast {
  title: string;
  body?: string;
  tone?: Tone;
  /** ms before auto-dismiss; 0 keeps it until clicked/dismissed. */
  durationMs?: number;
  onClick?: () => void;
}

interface ToastState {
  toasts: ToastItem[];
  push: (msg: string, tone?: Tone) => void;
  pushRich: (t: RichToast) => void;
  dismiss: (id: number) => void;
}

let seq = 1;

export const useToasts = create<ToastState>((set) => ({
  toasts: [],
  push: (msg, tone = 'default') => useToasts.getState().pushRich({ title: msg, tone }),
  pushRich: ({ title, body, tone = 'default', durationMs, onClick }) => {
    const id = seq++;
    set((s) => ({ toasts: [...s.toasts, { id, title, body, tone, onClick }] }));
    const ttl = durationMs ?? (tone === 'critical' ? 0 : tone === 'error' || tone === 'warning' ? 6000 : 4000);
    if (ttl > 0) setTimeout(() => set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })), ttl);
  },
  dismiss: (id) => set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),
}));

/** One-line toast helper (back-compat). */
export const toast = (msg: string, tone?: Tone) => useToasts.getState().push(msg, tone);
/** Rich toast: title + body, tone, click action, optional persistence. */
export const notifyToast = (t: RichToast) => useToasts.getState().pushRich(t);

// Dev-only: expose a toast trigger on window for manual/automated QA.
if (typeof window !== 'undefined' && import.meta.env.DEV) {
  (window as unknown as { __toast?: typeof notifyToast }).__toast = notifyToast;
}

const TONE_ACCENT: Record<Tone, string> = {
  default: 'var(--color-border2)',
  info: 'var(--color-blue, #5ab0ff)',
  success: 'var(--color-live)',
  warning: 'var(--color-warn, #ffcf4a)',
  error: 'var(--color-accent)',
  critical: 'var(--color-accent)',
};

const TONE_TEXT: Record<Tone, string> = {
  default: 'text-text',
  info: 'text-text',
  success: 'text-live',
  warning: 'text-[var(--color-warn,#ffcf4a)]',
  error: 'text-accent',
  critical: 'text-accent',
};

export function Toaster() {
  const toasts = useToasts((s) => s.toasts);
  const dismiss = useToasts((s) => s.dismiss);
  return (
    <div className="pointer-events-none fixed bottom-4 right-4 z-[100] flex w-[320px] max-w-[92vw] flex-col gap-2">
      {toasts.map((t) => (
        <button type="button"
          key={t.id}
          onClick={() => {
            t.onClick?.();
            dismiss(t.id);
          }}
          style={{ borderLeftColor: TONE_ACCENT[t.tone] }}
          className={cn(
            'toast-in pointer-events-auto w-full rounded-[var(--radius)] border border-border2 border-l-2 bg-panel2 px-3.5 py-2.5 text-left shadow-[0_12px_32px_rgba(0,0,0,0.55)]',
            t.tone === 'critical' && 'toast-pulse',
          )}
        >
          <div className={cn('text-xs font-semibold', TONE_TEXT[t.tone])}>{t.title}</div>
          {t.body ? <div className="mt-0.5 text-[11px] leading-snug text-muted">{t.body}</div> : null}
        </button>
      ))}
    </div>
  );
}
