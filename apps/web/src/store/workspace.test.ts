import { beforeEach, describe, expect, it } from 'vitest';
import { getLeaves } from 'react-mosaic-component';
import { useWorkspace, usedPanels } from './workspace';

beforeEach(() => {
  useWorkspace.getState().applyKind('network');
  useWorkspace.getState().reset();
});

function tileWith(panel: string): string {
  const entry = Object.entries(useWorkspace.getState().tiles).find(([, t]) => t.panels.includes(panel as never));
  if (!entry) throw new Error(`no tile with ${panel}`);
  return entry[0];
}

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
    const id = tileWith('agents');
    useWorkspace.getState().addTab(id, 'reports');
    const t = useWorkspace.getState().tiles[id]!;
    expect(t.panels).toContain('reports');
    expect(t.active).toBe('reports');
  });

  it('setActive switches the active tab', () => {
    const id = tileWith('loot');
    useWorkspace.getState().setActive(id, 'loot');
    expect(useWorkspace.getState().tiles[id]!.active).toBe('loot');
  });

  it('closeTab removes a panel but keeps the tile while others remain', () => {
    const id = tileWith('proxy');
    useWorkspace.getState().closeTab(id, 'proxy');
    const t = useWorkspace.getState().tiles[id]!;
    expect(t.panels).not.toContain('proxy');
    expect(t.panels.length).toBeGreaterThan(0);
  });

  it('setLayout prunes duplicate leaves so mosaic never gets a bad tree', () => {
    const id = tileWith('agents');
    useWorkspace.getState().setLayout({ direction: 'row', splitPercentage: 50, first: id, second: id });
    expect(getLeaves(useWorkspace.getState().layout)).toEqual([id]);
  });

  it('setLayout prunes tiles that are no longer in the layout', () => {
    const id = tileWith('agents');
    useWorkspace.getState().setLayout(id);
    expect(Object.keys(useWorkspace.getState().tiles)).toEqual([id]);
  });

  it('applyKind swaps to the kind default and hides irrelevant panels', () => {
    useWorkspace.getState().applyKind('code');
    const used = usedPanels(useWorkspace.getState().tiles);
    expect(used.has('reports')).toBe(true);
    expect(used.has('proxy')).toBe(false);
    expect(used.has('browser')).toBe(false);
  });
});
