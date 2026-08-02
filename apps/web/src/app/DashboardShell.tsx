import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { cn } from '@/lib/cn';
import { useApi } from '@/lib/api';
import { useSession } from '@/store/session';
import { Icon, type IconName } from '@/components/ui/Icon';

const NAV: { to: string; icon: IconName; label: string }[] = [
  { to: '/overview', icon: 'overview', label: 'Overview' },
  { to: '/sessions', icon: 'engagements', label: 'Sessions' },
  { to: '/servers', icon: 'server', label: 'Servers' },
  { to: '/proxies', icon: 'proxy', label: 'Proxies' },
];

function Logo() {
  return (
    <span
      className="h-[22px] w-[22px] flex-none"
      style={{
        background: 'radial-gradient(120% 120% at 30% 20%, var(--color-accent), var(--color-accent-dim))',
        clipPath: 'polygon(50% 0, 100% 38%, 82% 100%, 18% 100%, 0 38%)',
        boxShadow: '0 0 14px rgba(255,51,68,0.3)',
      }}
    />
  );
}

function Item({ to, icon, label }: { to: string; icon: IconName; label: string }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        cn(
          'flex w-full items-center gap-2.5 rounded-[var(--radius)] px-2.5 py-2 text-xs font-medium transition',
          isActive
            ? 'bg-accent-dim font-semibold text-accent-ink'
            : 'text-muted hover:bg-panel hover:text-text',
        )
      }
    >
      <Icon name={icon} size={17} />
      <span>{label}</span>
    </NavLink>
  );
}

export function DashboardShell() {
  const api = useApi();
  const signOut = useSession((s) => s.signOut);
  const navigate = useNavigate();

  const onSignOut = async () => {
    await api.auth.logout().catch(() => undefined);
    signOut();
    navigate('/overview');
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden">
      <aside className="flex w-[220px] flex-none flex-col border-r border-border bg-bg2">
        <div className="flex h-[52px] flex-none items-center gap-2.5 border-b border-border px-4">
          <Logo />
          <span className="font-mono text-[13px] font-extrabold tracking-[0.2em]">
            RED<span className="text-accent">CELL</span>
          </span>
        </div>
        <nav className="min-h-0 flex-1 overflow-auto p-2">
          {NAV.map((n) => (
            <Item key={n.to} {...n} />
          ))}
        </nav>
        <div className="flex-none border-t border-border p-2">
          <Item to="/settings" icon="settings" label="Settings" />
          <div className="mt-1 flex items-center gap-2.5 rounded-[var(--radius)] px-2.5 py-2">
            <span
              className="h-6 w-6 flex-none rounded-[5px]"
              style={{ background: 'conic-gradient(from 210deg, var(--color-accent), var(--color-faint))' }}
            />
            <span className="text-xs font-semibold text-muted">admin</span>
            <button
              onClick={onSignOut}
              title="Sign out"
              className="ml-auto grid h-7 w-7 place-items-center rounded-[var(--radius)] text-faint hover:bg-panel hover:text-text"
            >
              <Icon name="logout" size={15} />
            </button>
          </div>
        </div>
      </aside>
      <main className="min-w-0 flex-1 overflow-hidden">
        <Outlet />
      </main>
    </div>
  );
}
