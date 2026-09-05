import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

const markRead = vi.fn();
const markAll = vi.fn();

vi.mock('@/features/hooks', () => ({
  useNotifications: () => ({
    data: {
      items: [
        {
          id: 'n1',
          kind: 'run_failed',
          title: 'Run failed',
          body: 'Globex run stopped.',
          link: 'sessions/s1',
          read: false,
          createdAt: new Date().toISOString(),
        },
      ],
      unread: 1,
    },
  }),
  useMarkNotificationRead: () => ({ mutate: markRead }),
  useMarkAllNotificationsRead: () => ({ mutate: markAll }),
}));

import { NotificationsBell } from './NotificationsBell';

describe('NotificationsBell', () => {
  it('opens the panel and lists notifications', () => {
    render(
      <MemoryRouter>
        <NotificationsBell />
      </MemoryRouter>,
    );
    fireEvent.click(screen.getByRole('button', { name: /unread notifications/i }));
    expect(screen.getByText('Run failed')).toBeInTheDocument();
    expect(screen.getByText('Globex run stopped.')).toBeInTheDocument();
  });

  it('marks all read from the panel', () => {
    render(
      <MemoryRouter>
        <NotificationsBell />
      </MemoryRouter>,
    );
    fireEvent.click(screen.getByRole('button', { name: /unread notifications/i }));
    fireEvent.click(screen.getByText('Mark all read'));
    expect(markAll).toHaveBeenCalled();
  });
});
