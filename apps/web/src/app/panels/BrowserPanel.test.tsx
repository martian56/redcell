import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';

// Stub noVNC: fire 'connect' as soon as the panel registers for it, so the panel
// reaches the connected state without a real socket.
vi.mock('@novnc/novnc', () => ({
  default: class {
    viewOnly = true;
    scaleViewport = true;
    addEventListener(type: string, cb: () => void) {
      if (type === 'connect') cb();
    }
    removeEventListener() {}
    disconnect() {}
  },
}));

const start = vi.fn(async () => ({ ok: true }));
const control = vi.fn(async () => ({ owner: 'operator' }));
// Stable object, mirrors the real singleton client, so the effect doesn't re-run every render.
const apiObj = { browser: { start, control, vncUrl: (id: string) => `ws://x/api/v1/ws/browser/${id}` } };
vi.mock('@/lib/api', () => ({ useApi: () => apiObj }));
vi.mock('@/store/ui', () => ({
  useUI: (sel: (s: { activeSessionId: string }) => unknown) => sel({ activeSessionId: 'ses-1' }),
}));

import { BrowserPanel } from './BrowserPanel';

describe('BrowserPanel', () => {
  it('starts the browser on mount and toggles operator control once connected', async () => {
    render(<BrowserPanel />);
    // Auto-connect on mount calls start, then noVNC connects -> Take control shows.
    const takeBtn = await screen.findByRole('button', { name: /take control/i });
    expect(start).toHaveBeenCalledWith('ses-1');
    fireEvent.click(takeBtn);
    expect(await screen.findByRole('button', { name: /release control/i })).toBeInTheDocument();
    expect(control).toHaveBeenCalledWith('ses-1', 'operator');
  });
});
