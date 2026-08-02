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
  | 'reports';

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
];

type Node = MosaicNode<PanelId>;

const DEFAULT_LAYOUT: Node = {
  direction: 'row',
  splitPercentage: 64,
  first: { direction: 'column', splitPercentage: 58, first: 'agents', second: 'feed' },
  second: { direction: 'column', splitPercentage: 52, first: 'findings', second: 'context' },
};

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
      setLayout: (layout) => set({ layout }),
      reset: () => set({ layout: DEFAULT_LAYOUT }),
      addPanel: (id) =>
        set((s) => ({
          layout: s.layout
            ? { direction: 'row', first: s.layout, second: id, splitPercentage: 76 }
            : id,
        })),
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
    { name: 'redcell.workspace.v3' },
  ),
);
