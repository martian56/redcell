import { create } from 'zustand';
import { persist } from 'zustand/middleware';

// Persisted agent-node positions, keyed by `${runId}:${agentId}`. Falls back to
// the computed layout when a node has no stored position.
interface GraphState {
  positions: Record<string, { x: number; y: number }>;
  setPos: (key: string, p: { x: number; y: number }) => void;
}

export const useGraph = create<GraphState>()(
  persist(
    (set) => ({
      positions: {},
      setPos: (key, p) => set((s) => ({ positions: { ...s.positions, [key]: p } })),
    }),
    { name: 'redcell.graph' },
  ),
);
