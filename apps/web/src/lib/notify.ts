// Web Notification helper for critical run events when the tab is unfocused.
// No service worker or VAPID needed: the page is open, just not focused.

export type NotifyPermission = 'default' | 'granted' | 'denied' | 'unsupported';

export function notifySupported(): boolean {
  return typeof window !== 'undefined' && 'Notification' in window;
}

export function notifyPermission(): NotifyPermission {
  if (!notifySupported()) return 'unsupported';
  return Notification.permission as NotifyPermission;
}

export async function requestNotifyPermission(): Promise<NotifyPermission> {
  if (!notifySupported()) return 'unsupported';
  if (Notification.permission !== 'default') return Notification.permission as NotifyPermission;
  try {
    return (await Notification.requestPermission()) as NotifyPermission;
  } catch {
    return notifyPermission();
  }
}

/** True when the tab is not the focused screen. */
export function tabUnfocused(): boolean {
  if (typeof document === 'undefined') return false;
  return document.hidden || !document.hasFocus();
}

interface BrowserNotifyOptions {
  body?: string;
  /** Coalesce repeats: a new notification with the same tag replaces the old. */
  tag?: string;
  /** Keep the notification up until dismissed (for questions/critical). */
  requireInteraction?: boolean;
  onClick?: () => void;
  /** Fire even when the tab IS focused (default: only when unfocused). */
  force?: boolean;
}

export function browserNotify(title: string, opts: BrowserNotifyOptions = {}): void {
  if (!notifySupported() || Notification.permission !== 'granted') return;
  if (!opts.force && !tabUnfocused()) return;
  try {
    const n = new Notification(title, {
      body: opts.body,
      tag: opts.tag,
      requireInteraction: opts.requireInteraction,
      icon: '/favicon.svg',
      silent: false,
    });
    n.onclick = () => {
      window.focus();
      opts.onClick?.();
      n.close();
    };
  } catch {
    /* notification construction can throw on some platforms; ignore */
  }
}
