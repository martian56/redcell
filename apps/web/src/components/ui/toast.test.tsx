import { afterEach, describe, expect, it } from 'vitest';
import { act, fireEvent, render, screen } from '@testing-library/react';
import { Toaster, notifyToast, useToasts } from './toast';

afterEach(() => {
  act(() => useToasts.setState({ toasts: [] }));
});

describe('Toaster', () => {
  it('shows a toast and dismisses it via the close button', () => {
    render(<Toaster />);
    act(() => notifyToast({ title: 'Saved', durationMs: 0 }));
    expect(screen.getByText('Saved')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /dismiss notification/i }));
    expect(screen.queryByText('Saved')).not.toBeInTheDocument();
  });

  it('runs the click action without the close button firing it', () => {
    let clicked = 0;
    render(<Toaster />);
    act(() => notifyToast({ title: 'Open run', durationMs: 0, onClick: () => (clicked += 1) }));

    fireEvent.click(screen.getByRole('button', { name: /dismiss notification/i }));
    expect(clicked).toBe(0);
    expect(screen.queryByText('Open run')).not.toBeInTheDocument();
  });
});
