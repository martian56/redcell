import { beforeEach, describe, expect, it } from 'vitest';
import { getLeaves } from 'react-mosaic-component';
import { useWorkspace } from './workspace';

// Start every case from the default tiling layout.
beforeEach(() => useWorkspace.getState().reset());

describe('useWorkspace', () => {
  it('resets to a layout that contains the default panels', () => {
    const leaves = getLeaves(useWorkspace.getState().layout);
    expect(leaves).toContain('agents');
    expect(leaves).toContain('findings');
  });

  it('addPanel grafts a new tile onto the existing layout', () => {
    const before = useWorkspace.getState().layout;
    useWorkspace.getState().addPanel('loot');
    const layout = useWorkspace.getState().layout;
    expect(layout).toEqual({ direction: 'row', first: before, second: 'loot', splitPercentage: 76 });
    expect(getLeaves(layout)).toContain('loot');
  });

  it('addPanel seeds the layout from empty when there is none', () => {
    useWorkspace.getState().setLayout(null);
    useWorkspace.getState().addPanel('proxy');
    expect(useWorkspace.getState().layout).toBe('proxy');
  });

  it('showPanel is a no-op when the panel is already visible', () => {
    const before = useWorkspace.getState().layout;
    useWorkspace.getState().showPanel('agents');
    expect(useWorkspace.getState().layout).toBe(before);
  });

  it('showPanel adds a panel that is not yet visible', () => {
    useWorkspace.getState().showPanel('reports');
    expect(getLeaves(useWorkspace.getState().layout)).toContain('reports');
  });
});
