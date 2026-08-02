import { create } from 'zustand';
import { persist } from 'zustand/middleware';

// Persisted across refreshes. The server session cookie is the source of
// truth; this flag mirrors it client-side.
interface SessionState {
  authed: boolean;
  signIn: () => void;
  signOut: () => void;
}

export const useSession = create<SessionState>()(
  persist(
    (set) => ({
      authed: false,
      signIn: () => set({ authed: true }),
      signOut: () => set({ authed: false }),
    }),
    { name: 'redcell.session' },
  ),
);
