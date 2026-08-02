import { create } from 'zustand';

// Active terminal tab per session. Output/scrollback lives in the xterm
// instance (see panels/Terminal.tsx).
interface ShellsState {
  active: string | null;
  setActive: (id: string | null) => void;
}

export const useShells = create<ShellsState>((set) => ({
  active: null,
  setActive: (active) => set({ active }),
}));
