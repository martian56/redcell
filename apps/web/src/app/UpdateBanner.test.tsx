import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';

const update = vi.fn(async () => ({ started: true, detail: 'Update started.' }));
const version = vi.fn(async () => ({ current: '0.3.2', latest: 'v0.3.3', updateAvailable: true }));
vi.mock('@/lib/api', () => ({ useApi: () => ({ system: { update, version } }) }));
vi.mock('@/features/hooks', () => ({
  useVersion: () => ({ data: { current: '0.3.2', latest: 'v0.3.3', updateAvailable: true } }),
}));

import { UpdateBanner } from './UpdateBanner';

describe('UpdateBanner', () => {
  it('shows the version and opens the update panel', async () => {
    render(<UpdateBanner />);
    expect(screen.getByText('0.3.2')).toBeTruthy();
    expect(screen.getByText('v0.3.3')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: /update now/i }));
    expect(screen.getByText('Updating REDCELL')).toBeTruthy();
    await waitFor(() => expect(update).toHaveBeenCalled());
  });
});
