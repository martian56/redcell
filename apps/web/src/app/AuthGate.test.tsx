import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';

vi.mock('@/lib/api', () => ({
  useApi: () => ({
    auth: {
      firstRun: vi.fn(async () => ({ adminPasswordHint: undefined })),
      me: vi.fn(async () => ({})),
      login: vi.fn(async () => ({})),
    },
  }),
}));

import { AuthGate } from './AuthGate';
import { useSession } from '@/store/session';

describe('AuthGate login screen', () => {
  it('does not disclose a version or a bind notice before auth', async () => {
    useSession.setState({ authed: false });
    render(
      <AuthGate>
        <div>secret dashboard</div>
      </AuthGate>,
    );
    await screen.findByRole('button', { name: /sign in/i });
    const text = document.body.textContent ?? '';
    expect(text).toContain('OPERATOR CONSOLE');
    expect(text).not.toMatch(/v\d+\.\d+/);
    expect(text).not.toContain('127.0.0.1');
    expect(screen.queryByText(/secret dashboard/i)).toBeNull();
  });
});
