import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';

// Smoke test that the React Testing Library + jsdom harness renders and that
// the jest-dom matchers are wired up. Component tests can build on this.
function Hello({ name }: { name: string }) {
  return <p>Hello {name}</p>;
}

describe('testing-library harness', () => {
  it('renders a component into the DOM', () => {
    render(<Hello name="operator" />);
    expect(screen.getByText('Hello operator')).toBeInTheDocument();
  });
});
