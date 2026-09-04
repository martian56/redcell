import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';

const nav = vi.fn();
vi.mock('react-router-dom', () => ({ useNavigate: () => nav }));
vi.mock('@/features/hooks', () => ({
  useSessions: () => ({ data: [{ id: 'ses-42', name: 'Acme External', client: 'Acme Corp', targets: ['acme.com'] }] }),
  useServers: () => ({ data: [{ id: 'srv-1', name: 'kali-eu', host: '10.0.0.5' }] }),
  useProxies: () => ({ data: [{ id: 'px-1', label: 'burp', url: 'http://127.0.0.1:8080' }] }),
}));

import { CommandPalette } from './CommandPalette';

describe('CommandPalette', () => {
  it('shows pages by default and jumps to a matching session on Enter', () => {
    render(<CommandPalette open onClose={() => {}} />);
    expect(screen.getByText('Overview')).toBeTruthy();
    expect(screen.queryByText('Acme External')).toBeNull();

    const input = screen.getByPlaceholderText(/search sessions/i);
    fireEvent.change(input, { target: { value: 'acme' } });
    expect(screen.getByText('Acme External')).toBeTruthy();

    fireEvent.keyDown(input, { key: 'Enter' });
    expect(nav).toHaveBeenCalledWith('/sessions/ses-42');
  });

  it('finds a server by its host and a proxy by its url', () => {
    render(<CommandPalette open onClose={() => {}} />);
    const input = screen.getByPlaceholderText(/search sessions/i);
    fireEvent.change(input, { target: { value: '10.0.0.5' } });
    expect(screen.getByText('kali-eu')).toBeTruthy();
    fireEvent.change(input, { target: { value: '8080' } });
    expect(screen.getByText('burp')).toBeTruthy();
  });
});
