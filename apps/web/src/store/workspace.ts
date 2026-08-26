import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { getLeaves, type MosaicNode } from 'react-mosaic-component';

export type PanelId =
  | 'agents'
  | 'feed'
  | 'findings'
  | 'terminals'
  | 'context'
  | 'listeners'
  | 'proxy'
  | 'chat'
  | 'surface'
  | 'loot'
  | 'reports'
  | 'browser';

export const PANEL_LABELS: Record<PanelId, string> = {
  agents: 'Agents',
  feed: 'Activity',
  findings: 'Findings',
  terminals: 'Terminals',
  context: 'Context',
  listeners: 'Listeners',
  proxy: 'Proxy',
  chat: 'Chat',
  surface: 'Attack surface',
  loot: 'Loot & creds',
  reports: 'Reports',
  browser: 'Browser',
};

export const SWAPPABLE: PanelId[] = [
  'agents',
  'feed',
  'findings',
  'terminals',
  'context',
  'chat',
  'surface',
  'loot',
  'listeners',
  'proxy',
  'reports',
  'browser',
];

export type TileId = string;
export interface Tile {
  panels: PanelId[];
  active: PanelId;
}
type Node = MosaicNode<TileId>;

const DEFAULT_TILES: Record<TileId, Tile> = {
  t_agents: { panels: ['agents'], active: 'agents' },
  t_feed: { panels: ['feed'], active: 'feed' },
  t_findings: { panels: ['findings', 'context'], active: 'findings' },
  t_shell: { panels: ['terminals', 'browser'], active: 'terminals' },
  t_chat: { panels: ['chat'], active: 'chat' },
  t_data: { panels: ['surface', 'loot', 'listeners', 'proxy'], active: 'surface' },
};

const DEFAULT_LAYOUT: Node = {
  direction: 'row',
  splitPercentage: 22,
  first: { direction: 'column', splitPercentage: 44, first: 't_agents', second: 't_feed' },
  second: {
    direction: 'row',
    splitPercentage: 64,
    first: { direction: 'column', splitPercentage: 54, first: 't_findings', second: 't_shell' },
    second: { direction: 'column', splitPercentage: 56, first: 't_chat', second: 't_data' },
  },
};

function newTileId(): TileId {
  return 'tile-' + Math.random().toString(36).slice(2, 9);
}

function hasDuplicateLeaves(node: Node | null): boolean {
  if (node == null) return false;
  const leaves = getLeaves(node);
  return new Set(leaves).size !== leaves.length;
}

function dedupeLeaves(node: Node | null, seen: Set<TileId> = new Set()): Node | null {
  if (node == null) return null;
  if (typeof node === 'string') {
    if (seen.has(node)) return null;
    seen.add(node);
    return node;
  }
  const first = dedupeLeaves(node.first, seen);
  const second = dedupeLeaves(node.second, seen);
  if (first && second) return { ...node, first, second };
  return first ?? second ?? null;
}

function usedPanelSet(tiles: Record<TileId, Tile>): Set<PanelId> {
  return new Set(Object.values(tiles).flatMap((t) => t.panels));
}

function pruneTiles(tiles: Record<TileId, Tile>, layout: Node | null): Record<TileId, Tile> {
  const leaves = new Set(layout ? getLeaves(layout) : []);
  const out: Record<TileId, Tile> = {};
  for (const id of leaves) if (tiles[id]) out[id] = tiles[id]!;
  return out;
}

function consistent(layout: Node | null, tiles: Record<TileId, Tile>): boolean {
  if (layout == null) return Object.keys(tiles).length === 0;
  if (hasDuplicateLeaves(layout)) return false;
  const leaves = getLeaves(layout);
  return leaves.every((id) => tiles[id] && tiles[id]!.panels.length > 0);
}

interface WorkspaceState {
  layout: Node | null;
  tiles: Record<TileId, Tile>;
  setLayout: (n: Node | null) => void;
  reset: () => void;
  addPanelAsTile: (id: PanelId) => void;
  showPanel: (id: PanelId) => void;
  addTab: (tileId: TileId, id: PanelId) => void;
  closeTab: (tileId: TileId, id: PanelId) => void;
  setActive: (tileId: TileId, id: PanelId) => void;
}

export const useWorkspace = create<WorkspaceState>()(
  persist(
    (set) => ({
      layout: DEFAULT_LAYOUT,
      tiles: structuredClone(DEFAULT_TILES),
      setLayout: (layout) =>
        set((s) => {
          const next = hasDuplicateLeaves(layout) ? dedupeLeaves(layout) : layout;
          return { layout: next, tiles: pruneTiles(s.tiles, next) };
        }),
      reset: () => set({ layout: DEFAULT_LAYOUT, tiles: structuredClone(DEFAULT_TILES) }),
      addPanelAsTile: (id) =>
        set((s) => {
          if (usedPanelSet(s.tiles).has(id)) return {};
          const tid = newTileId();
          return {
            tiles: { ...s.tiles, [tid]: { panels: [id], active: id } },
            layout: s.layout ? { direction: 'row', first: s.layout, second: tid, splitPercentage: 74 } : tid,
          };
        }),
      showPanel: (id) =>
        set((s) => {
          if (usedPanelSet(s.tiles).has(id)) return {};
          const tid = newTileId();
          return {
            tiles: { ...s.tiles, [tid]: { panels: [id], active: id } },
            layout: s.layout ? { direction: 'row', first: s.layout, second: tid, splitPercentage: 72 } : tid,
          };
        }),
      addTab: (tileId, id) =>
        set((s) => {
          if (usedPanelSet(s.tiles).has(id)) return {};
          const t = s.tiles[tileId];
          if (!t) return {};
          return { tiles: { ...s.tiles, [tileId]: { panels: [...t.panels, id], active: id } } };
        }),
      closeTab: (tileId, id) =>
        set((s) => {
          const t = s.tiles[tileId];
          if (!t) return {};
          const panels = t.panels.filter((p) => p !== id);
          if (panels.length === 0) return {};
          const active = t.active === id ? panels[0]! : t.active;
          return { tiles: { ...s.tiles, [tileId]: { panels, active } } };
        }),
      setActive: (tileId, id) =>
        set((s) => {
          const t = s.tiles[tileId];
          if (!t) return {};
          return { tiles: { ...s.tiles, [tileId]: { ...t, active: id } } };
        }),
    }),
    {
      name: 'redcell.workspace.v4',
      merge: (persisted, current) => {
        const p = (persisted ?? {}) as Partial<WorkspaceState>;
        const layout = p.layout !== undefined ? p.layout : current.layout;
        const tiles = p.tiles ?? current.tiles;
        if (!consistent(layout ?? null, tiles ?? {})) {
          return { ...current, ...p, layout: DEFAULT_LAYOUT, tiles: structuredClone(DEFAULT_TILES) };
        }
        return { ...current, ...p, layout: layout ?? null, tiles };
      },
    },
  ),
);

export function usedPanels(tiles: Record<TileId, Tile>): Set<PanelId> {
  return usedPanelSet(tiles);
}
