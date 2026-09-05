import { useNavigate } from 'react-router-dom';
import {
  useMarkAllNotificationsRead,
  useMarkNotificationRead,
  useNotifications,
} from '@/features/hooks';
import { NotificationRow } from '../NotificationsBell';

export function NotificationsPage() {
  const { data: feed, isLoading } = useNotifications();
  const markRead = useMarkNotificationRead();
  const markAll = useMarkAllNotificationsRead();
  const navigate = useNavigate();

  const items = feed?.items ?? [];
  const unread = feed?.unread ?? 0;

  return (
    <div className="wrap">
      <div className="filters">
        <div className="grow" />
        <button
          type="button"
          className="btn sm"
          disabled={unread === 0}
          onClick={() => markAll.mutate()}
        >
          Mark all read
        </button>
      </div>
      <div className="card">
        <div className="card-b" style={{ padding: 0 }}>
          {isLoading ? (
            <div className="meta" style={{ padding: '22px', textAlign: 'center' }}>
              Loading…
            </div>
          ) : items.length === 0 ? (
            <div className="meta" style={{ padding: '22px', textAlign: 'center' }}>
              No notifications yet. Runs, findings and reports show up here.
            </div>
          ) : (
            items.map((n) => (
              <NotificationRow
                key={n.id}
                n={n}
                onOpen={(x) => {
                  markRead.mutate(x.id);
                  if (x.link) navigate(`/${x.link}`);
                }}
              />
            ))
          )}
        </div>
      </div>
    </div>
  );
}
