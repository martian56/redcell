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
  | 'browser'
  | 'device';

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
  device: 'Device',
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
  'device',
];

export type TileId = string;
export interface Tile {
  panels: PanelId[];
  active: PanelId;
}
type Node = MosaicNode<TileId>;

type KindLayoutSpec = PanelId[][][]; // columns -> tiles -> tabs

export const KIND_LAYOUTS: Record<string, KindLayoutSpec> = {
  network: [
    [['agents'], ['feed']],
    [['findings', 'context'], ['terminals', 'browser']],
    [['chat'], ['surface', 'loot', 'listeners', 'proxy']],
  ],
  code: [
    [['agents'], ['feed']],
    [['findings', 'context'], ['terminals']],
    [['chat'], ['reports']],
  ],
  mobile: [
    [['agents'], ['feed']],
    [['findings', 'context'], ['terminals', 'device']],
    [['chat'], ['reports']],
  ],
  osint: [
    [['agents'], ['feed']],
    [['findings', 'context']],
    [['chat'], ['reports']],
  ],
};
KIND_LAYOUTS.general = KIND_LAYOUTS.network!;

export const KIND_PANELS: Record<string, PanelId[]> = Object.fromEntries(
  Object.entries(KIND_LAYOUTS).map(([k, cols]) => [k, [...new Set(cols.flat().flat())]]),
);

function foldTree(nodes: Node[], direction: 'row' | 'column'): Node {
  return nodes.reduce((acc, node, i) =>
    i === 0 ? node : { direction, first: acc, second: node, splitPercentage: (i / (i + 1)) * 100 });
}

function buildFromSpec(kind: string, spec: KindLayoutSpec): { tiles: Record<TileId, Tile>; layout: Node } {
  const tiles: Record<TileId, Tile> = {};
  const columns: Node[] = spec.map((col, ci) =>
    foldTree(
      col.map((tabs, ti) => {
        const id = `${kind}-${ci}-${ti}`;
        tiles[id] = { panels: [...tabs], active: tabs[0]! };
        return id;
      }),
      'column',
    ),
  );
  const layout =
    columns.length <= 1
      ? columns[0]!
      : { direction: 'row' as const, splitPercentage: 22, first: columns[0]!, second: foldTree(columns.slice(1), 'row') };
  return { tiles, layout };
}

const DEFAULT_KIND = 'network';
const _NET = buildFromSpec(DEFAULT_KIND, KIND_LAYOUTS[DEFAULT_KIND]!);
const DEFAULT_TILES = _NET.tiles;
const DEFAULT_LAYOUT = _NET.layout;

function defaultsForKind(kind: string): { tiles: Record<TileId, Tile>; layout: Node } {
  const k = KIND_LAYOUTS[kind] ? kind : DEFAULT_KIND;
  return buildFromSpec(k, KIND_LAYOUTS[k]!);
}

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
  kind: string;
  layout: Node | null;
  tiles: Record<TileId, Tile>;
  setLayout: (n: Node | null) => void;
  reset: () => void;
  applyKind: (kind: string) => void;
  addPanelAsTile: (id: PanelId) => void;
  showPanel: (id: PanelId) => void;
  addTab: (tileId: TileId, id: PanelId) => void;
  closeTab: (tileId: TileId, id: PanelId) => void;
  setActive: (tileId: TileId, id: PanelId) => void;
}

export const useWorkspace = create<WorkspaceState>()(
  persist(
    (set) => ({
      kind: DEFAULT_KIND,
      layout: DEFAULT_LAYOUT,
      tiles: structuredClone(DEFAULT_TILES),
      setLayout: (layout) =>
        set((s) => {
          const next = hasDuplicateLeaves(layout) ? dedupeLeaves(layout) : layout;
          return { layout: next, tiles: pruneTiles(s.tiles, next) };
        }),
      reset: () => set((s) => defaultsForKind(s.kind)),
      applyKind: (kind) =>
        set((s) => (kind === s.kind ? {} : { kind, ...defaultsForKind(kind) })),
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
      name: 'redcell.workspace.v5',
      merge: (persisted, current) => {
        const p = (persisted ?? {}) as Partial<WorkspaceState>;
        const kind = p.kind ?? current.kind;
        const layout = p.layout !== undefined ? p.layout : current.layout;
        const tiles = p.tiles ?? current.tiles;
        if (!consistent(layout ?? null, tiles ?? {})) {
          return { ...current, ...p, kind, ...defaultsForKind(kind) };
        }
        return { ...current, ...p, kind, layout: layout ?? null, tiles };
      },
    },
  ),
);

export function usedPanels(tiles: Record<TileId, Tile>): Set<PanelId> {
  return usedPanelSet(tiles);
}
