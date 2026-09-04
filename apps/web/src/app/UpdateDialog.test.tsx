import { describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';

const { update, version } = vi.hoisted(() => ({
  update: vi.fn(async () => ({ started: true, detail: 'Update started.' })),
  version: vi.fn(async () => ({ current: '0.3.2', latest: 'v0.3.3', updateAvailable: true })),
}));
vi.mock('@/lib/api', () => ({ useApi: () => ({ system: { update, version } }) }));

import { UpdateDialog } from './UpdateDialog';

describe('UpdateDialog', () => {
  it('triggers the update and shows the progress steps', async () => {
    render(<UpdateDialog open onClose={() => {}} target="v0.3.3" />);
    expect(screen.getByText('Updating REDCELL')).toBeTruthy();
    expect(screen.getByText('Pulling images and restarting')).toBeTruthy();
    expect(screen.getByText('Up to date')).toBeTruthy();
    await waitFor(() => expect(update).toHaveBeenCalled());
  });

  it('renders nothing when closed', () => {
    const { container } = render(<UpdateDialog open={false} onClose={() => {}} target="v0.3.3" />);
    expect(container.firstChild).toBeNull();
  });
});
