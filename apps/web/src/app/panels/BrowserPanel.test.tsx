import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';

// noVNC opens a real WebSocket; stub it so the panel mounts without a socket.
vi.mock('@novnc/novnc', () => ({
  default: class {
    viewOnly = true;
    scaleViewport = true;
    addEventListener() {}
    removeEventListener() {}
    disconnect() {}
  },
}));

const control = vi.fn(async () => ({ owner: 'operator' }));
vi.mock('@/lib/api', () => ({
  useApi: () => ({
    browser: { control, vncUrl: (id: string) => `ws://x/api/v1/ws/browser/${id}` },
  }),
}));
vi.mock('@/store/ui', () => ({
  useUI: (sel: (s: { activeSessionId: string }) => unknown) => sel({ activeSessionId: 'ses-1' }),
}));

import { BrowserPanel } from './BrowserPanel';

describe('BrowserPanel', () => {
  it('renders and toggles operator control', async () => {
    render(<BrowserPanel />);
    fireEvent.click(screen.getByRole('button', { name: /take control/i }));
    // Label flips only after control() resolves and the state update renders.
    expect(await screen.findByRole('button', { name: /release control/i })).toBeInTheDocument();
    expect(control).toHaveBeenCalledWith('ses-1', 'operator');
  });
});
