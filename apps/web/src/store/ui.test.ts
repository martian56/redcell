import { beforeEach, describe, expect, it } from 'vitest';
import { useUI } from './ui';

beforeEach(() => useUI.setState({ activeSessionId: null, activeRunId: null, selection: null }));

describe('useUI', () => {
  it('tracks the active session and run', () => {
    useUI.getState().setActiveSession('ses-1');
    useUI.getState().setActiveRun('run-1');
    expect(useUI.getState().activeSessionId).toBe('ses-1');
    expect(useUI.getState().activeRunId).toBe('run-1');
  });

  it('holds the current selection and clears it', () => {
    useUI.getState().select({ type: 'finding', id: 'f-1' });
    expect(useUI.getState().selection).toEqual({ type: 'finding', id: 'f-1' });
    useUI.getState().select(null);
    expect(useUI.getState().selection).toBeNull();
  });
});
