import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';

const mutateAsync = vi.fn(async () => ({ started: true, detail: 'Update started.' }));
vi.mock('@/features/hooks', () => ({
  useVersion: () => ({ data: { current: '0.3.2', latest: '0.3.3', updateAvailable: true } }),
  useSelfUpdate: () => ({ mutateAsync, isPending: false }),
}));

import { UpdateBanner } from './UpdateBanner';

describe('UpdateBanner', () => {
  it('shows current and latest, and triggers the update', async () => {
    render(<UpdateBanner />);
    expect(screen.getByText('0.3.2')).toBeTruthy();
    expect(screen.getByText('0.3.3')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: /update now/i }));
    expect(mutateAsync).toHaveBeenCalled();
    await waitFor(() => expect(screen.getByText(/update started/i)).toBeTruthy());
  });
});
