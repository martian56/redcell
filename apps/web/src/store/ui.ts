import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type Selection = { type: 'finding'; id: string } | { type: 'agent'; id: string } | null;

// Active session/run come from the URL; only the selection is persisted.
interface UIState {
  activeSessionId: string | null;
  setActiveSession: (id: string | null) => void;
  activeRunId: string | null;
  setActiveRun: (id: string | null) => void;
  selection: Selection;
  select: (s: Selection) => void;
}

export const useUI = create<UIState>()(
  persist(
    (set) => ({
      activeSessionId: null,
      setActiveSession: (activeSessionId) => set({ activeSessionId }),
      activeRunId: null,
      setActiveRun: (activeRunId) => set({ activeRunId }),
      selection: null,
      select: (selection) => set({ selection }),
    }),
    { name: 'redcell.ui', partialize: (s) => ({ selection: s.selection }) },
  ),
);
