import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { MobileNav } from './MobileNav';

describe('MobileNav', () => {
  it('renders the primary destinations as tab links', () => {
    render(
      <MemoryRouter>
        <MobileNav onMore={() => {}} />
      </MemoryRouter>,
    );
    for (const label of ['Overview', 'Sessions', 'Findings', 'Reports']) {
      expect(screen.getByRole('link', { name: label })).toBeInTheDocument();
    }
  });

  it('marks the active route', () => {
    render(
      <MemoryRouter initialEntries={['/findings']}>
        <MobileNav onMore={() => {}} />
      </MemoryRouter>,
    );
    expect(screen.getByRole('link', { name: 'Findings' }).className).toContain('on');
  });

  it('calls onMore when the More tab is tapped', () => {
    const onMore = vi.fn();
    render(
      <MemoryRouter>
        <MobileNav onMore={onMore} />
      </MemoryRouter>,
    );
    fireEvent.click(screen.getByRole('button', { name: 'More' }));
    expect(onMore).toHaveBeenCalledOnce();
  });
});
