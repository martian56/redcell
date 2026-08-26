import { beforeEach, describe, expect, it } from 'vitest';
import { getLeaves } from 'react-mosaic-component';
import { useWorkspace, usedPanels } from './workspace';

beforeEach(() => useWorkspace.getState().reset());

describe('useWorkspace', () => {
  it('resets to tiles that contain the default panels', () => {
    const used = usedPanels(useWorkspace.getState().tiles);
    expect(used.has('agents')).toBe(true);
    expect(used.has('findings')).toBe(true);
    expect(getLeaves(useWorkspace.getState().layout).length).toBeGreaterThan(0);
  });

  it('addPanelAsTile grafts a new tile for an unused panel', () => {
    useWorkspace.getState().addPanelAsTile('reports');
    const s = useWorkspace.getState();
    expect(usedPanels(s.tiles).has('reports')).toBe(true);
    const entry = Object.entries(s.tiles).find(([, t]) => t.panels.includes('reports'));
    expect(entry?.[1].panels).toEqual(['reports']);
    expect(getLeaves(s.layout)).toContain(entry?.[0]);
  });

  it('addPanelAsTile is a no-op when the panel is already visible', () => {
    const before = useWorkspace.getState().layout;
    useWorkspace.getState().addPanelAsTile('findings');
    expect(useWorkspace.getState().layout).toBe(before);
  });

  it('addTab adds a panel as a tab to an existing tile and activates it', () => {
    useWorkspace.getState().addTab('t_agents', 'reports');
    const t = useWorkspace.getState().tiles['t_agents']!;
    expect(t.panels).toContain('reports');
    expect(t.active).toBe('reports');
  });

  it('setActive switches the active tab', () => {
    useWorkspace.getState().setActive('t_data', 'loot');
    expect(useWorkspace.getState().tiles['t_data']!.active).toBe('loot');
  });

  it('closeTab removes a panel but keeps the tile while others remain', () => {
    useWorkspace.getState().closeTab('t_data', 'proxy');
    const t = useWorkspace.getState().tiles['t_data']!;
    expect(t.panels).not.toContain('proxy');
    expect(t.panels.length).toBeGreaterThan(0);
  });

  it('setLayout prunes duplicate leaves so mosaic never gets a bad tree', () => {
    useWorkspace.getState().setLayout({ direction: 'row', splitPercentage: 50, first: 't_agents', second: 't_agents' });
    expect(getLeaves(useWorkspace.getState().layout)).toEqual(['t_agents']);
  });

  it('setLayout prunes tiles that are no longer in the layout', () => {
    useWorkspace.getState().setLayout('t_agents');
    expect(Object.keys(useWorkspace.getState().tiles)).toEqual(['t_agents']);
  });
});
