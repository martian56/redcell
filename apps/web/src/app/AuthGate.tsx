import { useEffect, useState, type ReactNode } from 'react';
import { useApi } from '@/lib/api';
import { useSession } from '@/store/session';
import { Button, Spinner } from '@/components/ui/primitives';

export function AuthGate({ children }: { children: ReactNode }) {
  const api = useApi();
  const authed = useSession((s) => s.authed);
  const markAuthed = useSession((s) => s.signIn);
  const signOut = useSession((s) => s.signOut);

  const [hint, setHint] = useState<string | undefined>();
  const [checking, setChecking] = useState(true);
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('admin');
  const [error, setError] = useState<string | undefined>();
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.auth
      .firstRun()
      .then((r) => setHint(r.adminPasswordHint))
      .catch(() => undefined);
  }, [api]);

  // Server cookie is the source of truth: clear a stale client flag so login
  // shows instead of a dashboard that 401s. ?demo=1 skips this for demos.
  useEffect(() => {
    if (new URLSearchParams(window.location.search).get('demo') === '1') {
      markAuthed();
      setChecking(false);
      return;
    }
    if (!useSession.getState().authed) {
      setChecking(false);
      return;
    }
    let cancelled = false;
    api.auth
      .me()
      .then(() => !cancelled && markAuthed())
      .catch(() => !cancelled && signOut())
      .finally(() => !cancelled && setChecking(false));
    return () => {
      cancelled = true;
    };
  }, [api, markAuthed, signOut]);

  const signIn = async () => {
    setBusy(true);
    setError(undefined);
    try {
      await api.auth.login(username, password);
      markAuthed();
    } catch {
      setError('Invalid credentials.');
    } finally {
      setBusy(false);
    }
  };

  if (checking) {
    return (
      <div className="grid h-screen w-screen place-items-center bg-bg">
        <Spinner />
      </div>
    );
  }

  if (authed) return <>{children}</>;

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !busy) void signIn();
  };

  return (
    <div
      className="grid h-screen w-screen place-items-center"
      style={{
        background:
          'radial-gradient(55% 45% at 50% 0%, rgba(255,51,68,0.10), transparent 70%), var(--color-bg)',
      }}
    >
      <div className="w-[410px] max-w-[92vw] overflow-hidden rounded-[var(--radius)] border border-border2 bg-panel shadow-[0_30px_90px_rgba(0,0,0,0.6)]">
        <div className="flex items-center gap-3 border-b border-border p-6">
          <span
            className="h-9 w-9 flex-none"
            style={{
              background: 'radial-gradient(120% 120% at 30% 20%, var(--color-accent), var(--color-accent-dim))',
              clipPath: 'polygon(50% 0, 100% 38%, 82% 100%, 18% 100%, 0 38%)',
              boxShadow: '0 0 22px rgba(255,51,68,0.28)',
            }}
          />
          <div>
            <div className="font-mono text-[17px] font-extrabold tracking-[0.22em]">
              RED<span className="text-accent">CELL</span>
            </div>
            <div className="font-mono text-[10.5px] tracking-wider text-faint">OPERATOR CONSOLE · v0.1</div>
          </div>
        </div>

        <div className="flex flex-col gap-4 p-6">
          {hint ? (
            <div className="rounded-[var(--radius)] border border-border2 bg-bg p-3 text-xs text-muted">
              <div className="mb-1.5 flex items-center gap-2 font-bold text-text">
                <span
                  className="rounded-full px-2 py-0.5 font-mono text-[9.5px] tracking-wider text-live"
                  style={{ backgroundColor: 'color-mix(in srgb, var(--color-live) 18%, transparent)' }}
                >
                  DEFAULT LOGIN
                </span>
                Change this in production
              </div>
              Sign in with{' '}
              <code className="rounded bg-accent-dim px-1.5 py-0.5 font-mono text-accent-ink">{hint}</code>. Override
              via the <code className="font-mono">REDCELL_ADMIN_*</code> environment variables.
            </div>
          ) : null}

          <label className="flex flex-col gap-1.5">
            <span className="font-mono text-[10px] uppercase tracking-[0.14em] text-faint">Username</span>
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              onKeyDown={onKeyDown}
              spellCheck={false}
              className="h-10 rounded-[var(--radius)] border border-border2 bg-bg px-3 font-mono text-[13px] text-text outline-none focus:border-accent"
            />
          </label>
          <label className="flex flex-col gap-1.5">
            <span className="font-mono text-[10px] uppercase tracking-[0.14em] text-faint">Password</span>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onKeyDown={onKeyDown}
              className="h-10 rounded-[var(--radius)] border border-border2 bg-bg px-3 font-mono text-[13px] text-text outline-none focus:border-accent"
            />
          </label>

          {error ? <span className="font-mono text-[11px] text-accent">{error}</span> : null}

          <Button variant="primary" className="h-10 justify-center" disabled={busy} onClick={signIn}>
            {busy ? <Spinner /> : 'Sign in'}
          </Button>
          <span className="font-mono text-[11px] text-faint">
            Console binds to 127.0.0.1. External access requires auth.
          </span>
        </div>
      </div>
    </div>
  );
}
