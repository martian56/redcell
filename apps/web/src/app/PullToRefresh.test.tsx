import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

vi.mock('@/lib/useIsMobile', () => ({ useIsMobile: () => true }));

import { PullToRefresh } from './PullToRefresh';

describe('PullToRefresh', () => {
  it('renders children inside the scroll container with a pull indicator', () => {
    const qc = new QueryClient();
    const { container } = render(
      <QueryClientProvider client={qc}>
        <PullToRefresh className="body-normal">
          <p>content</p>
        </PullToRefresh>
      </QueryClientProvider>,
    );
    expect(screen.getByText('content')).toBeInTheDocument();
    expect(container.querySelector('.body-normal .ptr')).not.toBeNull();
  });
});
