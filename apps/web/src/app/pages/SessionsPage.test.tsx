import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';

vi.mock('react-router-dom', () => ({ useNavigate: () => vi.fn() }));
vi.mock('@/features/hooks', () => ({
  useSessions: () => ({ data: [], isLoading: false }),
}));
vi.mock('./shared', () => ({
  FilterMenu: () => <div data-testid="filter" />,
  SessionRow: () => (
    <tr>
      <td>row</td>
    </tr>
  ),
}));

import { SessionsPage } from './SessionsPage';

describe('SessionsPage', () => {
  it('does not render its own New session button (the header owns it)', () => {
    render(<SessionsPage />);
    expect(screen.queryByRole('button', { name: /new session/i })).toBeNull();
    expect(screen.queryByText(/new session/i)).toBeNull();
  });

  it('keeps the status and type filters', () => {
    render(<SessionsPage />);
    expect(screen.getAllByTestId('filter')).toHaveLength(2);
  });
});
