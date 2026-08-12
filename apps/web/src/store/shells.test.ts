import { beforeEach, describe, expect, it } from 'vitest';
import { useShells } from './shells';

beforeEach(() => useShells.setState({ active: null }));

describe('useShells', () => {
  it('tracks the active terminal tab', () => {
    expect(useShells.getState().active).toBeNull();
    useShells.getState().setActive('sh-1');
    expect(useShells.getState().active).toBe('sh-1');
    useShells.getState().setActive(null);
    expect(useShells.getState().active).toBeNull();
  });
});
