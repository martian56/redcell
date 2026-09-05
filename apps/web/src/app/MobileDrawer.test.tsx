import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { MobileDrawer } from './MobileDrawer';

function renderDrawer(props: Partial<Parameters<typeof MobileDrawer>[0]> = {}) {
  const base = {
    open: true,
    onClose: vi.fn(),
    onUpdate: vi.fn(),
    onToggleTheme: vi.fn(),
    onSignOut: vi.fn(),
  };
  const merged = { ...base, ...props };
  render(
    <MemoryRouter>
      <MobileDrawer {...merged} />
    </MemoryRouter>,
  );
  return merged;
}

describe('MobileDrawer', () => {
  it('renders nothing when closed', () => {
    renderDrawer({ open: false });
    expect(screen.queryByRole('dialog')).toBeNull();
  });

  it('shows the secondary destinations and actions when open', () => {
    renderDrawer();
    expect(screen.getByRole('link', { name: 'Servers' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Proxies' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Settings' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Toggle theme' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Sign out' })).toBeInTheDocument();
  });

  it('shows the Update control only when an update is available', () => {
    const { onUpdate, onClose } = renderDrawer({
      version: { current: '0.3.8', latest: 'v0.4.0', updateAvailable: true },
    });
    const btn = screen.getByRole('button', { name: 'Update' });
    fireEvent.click(btn);
    expect(onUpdate).toHaveBeenCalledOnce();
    expect(onClose).toHaveBeenCalledOnce();
  });

  it('hides the Update control when up to date', () => {
    renderDrawer({ version: { current: '0.4.0', updateAvailable: false } });
    expect(screen.queryByRole('button', { name: 'Update' })).toBeNull();
  });

  it('closes on Escape', () => {
    const { onClose } = renderDrawer();
    fireEvent.keyDown(document, { key: 'Escape' });
    expect(onClose).toHaveBeenCalled();
  });
});
