import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { MobileNav } from './MobileNav';

describe('MobileNav', () => {
  it('renders the primary destinations as tab links', () => {
    render(
      <MemoryRouter>
        <MobileNav />
      </MemoryRouter>,
    );
    for (const label of ['Overview', 'Sessions', 'Findings', 'Reports']) {
      expect(screen.getByRole('link', { name: label })).toBeInTheDocument();
    }
  });

  it('marks the active route', () => {
    render(
      <MemoryRouter initialEntries={['/findings']}>
        <MobileNav />
      </MemoryRouter>,
    );
    expect(screen.getByRole('link', { name: 'Findings' }).className).toContain('on');
  });
});
