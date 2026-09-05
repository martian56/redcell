import { useCallback, useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { useNavigate } from 'react-router-dom';
import type { Notification, NotificationKind } from '@redcell/api-client';
import {
  useMarkAllNotificationsRead,
  useMarkNotificationRead,
  useNotifications,
} from '@/features/hooks';
import { timeAgo } from '@/lib/format';

const WIDTH = 320;

function KindIcon({ kind }: { kind: NotificationKind }) {
  switch (kind) {
    case 'run_completed':
      return (
        <svg viewBox="0 0 24 24">
          <path d="M20 6L9 17l-5-5" />
        </svg>
      );
    case 'run_failed':
      return (
        <svg viewBox="0 0 24 24">
          <path d="M12 8v5M12 16h.01M10.3 3.9 2.4 18a2 2 0 0 0 1.7 3h15.8a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z" />
        </svg>
      );
    case 'finding':
      return (
        <svg viewBox="0 0 24 24">
          <path d="M12 3l8 4v5c0 5-3.5 8-8 9-4.5-1-8-4-8-9V7z" />
        </svg>
      );
    case 'report_ready':
      return (
        <svg viewBox="0 0 24 24">
          <path d="M6 3h9l4 4v14H6z" />
          <path d="M14 3v5h5" />
        </svg>
      );
    default:
      return (
        <svg viewBox="0 0 24 24">
          <rect x="3" y="4" width="18" height="7" rx="1.5" />
          <rect x="3" y="13" width="18" height="7" rx="1.5" />
        </svg>
      );
  }
}

export function NotificationRow({
  n,
  onOpen,
}: {
  n: Notification;
  onOpen: (n: Notification) => void;
}) {
  return (
    <button
      type="button"
      className={`ntf-item${n.read ? '' : ' unread'}`}
      onClick={() => onOpen(n)}
    >
      <span className={`ntf-ic ${n.kind}`}>
        <KindIcon kind={n.kind} />
      </span>
      <span className="ntf-b">
        <span className="ntf-it-title">{n.title}</span>
        {n.body ? <span className="ntf-it-sub">{n.body}</span> : null}
        <span className="ntf-it-time">{timeAgo(n.createdAt)}</span>
      </span>
      {!n.read ? <span className="ntf-unread" /> : null}
    </button>
  );
}

export function NotificationsBell() {
  const { data: feed } = useNotifications();
  const markRead = useMarkNotificationRead();
  const markAll = useMarkAllNotificationsRead();
  const navigate = useNavigate();

  const unread = feed?.unread ?? 0;
  const items = feed?.items ?? [];

  const wrapRef = useRef<HTMLDivElement>(null);
  const popRef = useRef<HTMLDivElement>(null);
  const [pos, setPos] = useState<{ left: number; bottom: number } | null>(null);
  const open = pos !== null;

  const place = useCallback(() => {
    const el = wrapRef.current;
    if (!el) return;
    const r = el.getBoundingClientRect();
    const left = Math.max(8, Math.min(r.left, window.innerWidth - WIDTH - 8));
    setPos({ left, bottom: window.innerHeight - r.top + 6 });
  }, []);
  const close = useCallback(() => setPos(null), []);

  useEffect(() => {
    if (!open) return;
    const onDown = (e: MouseEvent) => {
      const t = e.target as Node;
      if (wrapRef.current?.contains(t) || popRef.current?.contains(t)) return;
      close();
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') close();
    };
    document.addEventListener('mousedown', onDown);
    document.addEventListener('keydown', onKey);
    window.addEventListener('resize', close);
    return () => {
      document.removeEventListener('mousedown', onDown);
      document.removeEventListener('keydown', onKey);
      window.removeEventListener('resize', close);
    };
  }, [open, close]);

  const openItem = (id: string, link?: string) => {
    markRead.mutate(id);
    close();
    if (link) navigate(`/${link}`);
  };

  return (
    <div ref={wrapRef} className="ntf-wrap">
      <button
        type="button"
        className={`ntf-btn${open ? ' on' : ''}`}
        aria-label={unread ? `${unread} unread notifications` : 'Notifications'}
        aria-expanded={open}
        title={unread ? `${unread} unread` : 'Notifications'}
        onClick={() => (open ? close() : place())}
      >
        <svg viewBox="0 0 24 24">
          <path d="M18 8a6 6 0 1 0-12 0c0 7-3 9-3 9h18s-3-2-3-9M13.7 21a2 2 0 0 1-3.4 0" />
        </svg>
        {unread > 0 ? <span className="ntf-dot" /> : null}
      </button>
      {open && pos
        ? createPortal(
            <div
              ref={popRef}
              className="ntf-panel"
              style={{ position: 'fixed', left: pos.left, bottom: pos.bottom, width: WIDTH }}
            >
              <div className="ntf-head">
                <span className="ntf-title">Notifications</span>
                <button
                  type="button"
                  className="ntf-all"
                  disabled={unread === 0}
                  onClick={() => markAll.mutate()}
                >
                  Mark all read
                </button>
              </div>
              <div className="ntf-list">
                {items.length === 0 ? (
                  <div className="ntf-empty">Nothing yet. Runs, findings and reports show up here.</div>
                ) : (
                  items.slice(0, 12).map((n) => (
                    <NotificationRow key={n.id} n={n} onOpen={(x) => openItem(x.id, x.link)} />
                  ))
                )}
              </div>
              <button
                type="button"
                className="ntf-foot"
                onClick={() => {
                  close();
                  navigate('/notifications');
                }}
              >
                See all notifications
              </button>
            </div>,
            document.body,
          )
        : null}
    </div>
  );
}
