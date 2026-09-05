import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';

vi.mock('./panels/PanelView', () => ({
  PanelView: ({ id }: { id: string }) => <div data-testid="panel">{id}</div>,
}));

import { MobileWorkspace } from './MobileWorkspace';

describe('MobileWorkspace', () => {
  it('shows the agents panel by default', () => {
    render(<MobileWorkspace />);
    expect(screen.getByTestId('panel')).toHaveTextContent('agents');
    expect(screen.getByRole('tab', { name: 'Agents' })).toHaveAttribute('aria-selected', 'true');
  });

  it('switches the visible panel when another tab is tapped', () => {
    render(<MobileWorkspace />);
    fireEvent.click(screen.getByRole('tab', { name: 'Findings' }));
    expect(screen.getByTestId('panel')).toHaveTextContent('findings');
    expect(screen.getByRole('tab', { name: 'Findings' })).toHaveAttribute('aria-selected', 'true');
  });
});
