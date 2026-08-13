import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { getLeaves, type MosaicNode } from 'react-mosaic-component';

// Tiling workspace: panels live in a binary tree; closing a tile grows its sibling.
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
  agents: 'Agent graph',
  feed: 'Live activity',
  findings: 'Findings',
  terminals: 'Terminals',
  context: 'Context',
  listeners: 'Listeners',
  proxy: 'Proxy',
  chat: 'Chat / Steer',
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

type Node = MosaicNode<PanelId>;

const DEFAULT_LAYOUT: Node = {
  direction: 'row',
  splitPercentage: 64,
  first: { direction: 'column', splitPercentage: 58, first: 'agents', second: 'feed' },
  second: { direction: 'column', splitPercentage: 52, first: 'findings', second: 'context' },
};

// react-mosaic crashes if a leaf id appears twice. A bad drag or adding an
// already-visible panel can produce that, and it persists, so every later render
// (including a brand-new session) white-screens. These keep the tree valid.
function hasDuplicateLeaves(node: Node | null): boolean {
  if (node == null) return false;
  const leaves = getLeaves(node);
  return new Set(leaves).size !== leaves.length;
}

function dedupeLeaves(node: Node | null, seen: Set<PanelId> = new Set()): Node | null {
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

interface WorkspaceState {
  layout: Node | null;
  setLayout: (n: Node | null) => void;
  reset: () => void;
  addPanel: (id: PanelId) => void;
  showPanel: (id: PanelId) => void;
}

export const useWorkspace = create<WorkspaceState>()(
  persist(
    (set) => ({
      layout: DEFAULT_LAYOUT,
      setLayout: (layout) =>
        set({ layout: hasDuplicateLeaves(layout) ? dedupeLeaves(layout) : layout }),
      reset: () => set({ layout: DEFAULT_LAYOUT }),
      addPanel: (id) =>
        set((s) => {
          const leaves = s.layout ? getLeaves(s.layout) : [];
          if (leaves.includes(id)) return {};
          return {
            layout: s.layout
              ? { direction: 'row', first: s.layout, second: id, splitPercentage: 76 }
              : id,
          };
        }),
      showPanel: (id) =>
        set((s) => {
          const leaves = s.layout ? getLeaves(s.layout) : [];
          if (leaves.includes(id)) return {};
          return {
            layout: s.layout
              ? { direction: 'row', first: s.layout, second: id, splitPercentage: 72 }
              : id,
          };
        }),
    }),
    {
      name: 'redcell.workspace.v3',
      // Heal an already-corrupted persisted layout (duplicate leaves) on load,
      // so a stuck browser recovers on the next reload instead of crashing.
      merge: (persisted, current) => {
        const p = (persisted ?? {}) as Partial<WorkspaceState>;
        const layout = p.layout !== undefined ? p.layout : current.layout;
        return {
          ...current,
          ...p,
          layout: hasDuplicateLeaves(layout ?? null) ? dedupeLeaves(layout ?? null) : layout,
        };
      },
    },
  ),
);
