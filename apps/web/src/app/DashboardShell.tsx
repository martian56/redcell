import { useEffect, useRef, useState } from 'react';
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useQueries } from '@tanstack/react-query';
import type { Session } from '@redcell/api-client';
import { useApi } from '@/lib/api';
import { useSessions, useVersion } from '@/features/hooks';
import { useSession } from '@/store/session';
import { toggleTheme } from '@/lib/theme';
import { CommandPalette } from './CommandPalette';
import { ConsoleHeader } from './ConsoleHeader';
import { UpdateDialog } from './UpdateDialog';
import { MobileNav } from './MobileNav';
import { MobileDrawer } from './MobileDrawer';
import { SIDEBAR_GROUPS } from './nav';

function ActiveRunRow({ session, onClick }: { session: Session; onClick: () => void }) {
  return (
    <button type="button" className="run live" onClick={onClick} title={`${session.name} · ${session.client}`}>
      <span className="d" />
      <span className="rt">
        {session.name} <span style={{ color: 'var(--tx-4)' }}>· {session.client}</span>
      </span>
    </button>
  );
}

const TITLES: Record<string, [string, string]> = {
  '/overview': ['Overview', '· all engagements'],
  '/sessions': ['Sessions', '· engagements'],
  '/sessions/new': ['New session', '· plan an assessment'],
  '/findings': ['Findings', '· triage'],
  '/reports': ['Reports', '· export & hand off'],
  '/servers': ['Servers', '· execution hosts'],
  '/proxies': ['Proxies', '· egress'],
  '/settings': ['Settings', ''],
};

function useOutside<T extends HTMLElement = HTMLElement>(onClose: () => void) {
  const ref = useRef<T>(null);
  useEffect(() => {
    const h = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose();
    };
    document.addEventListener('mousedown', h);
    return () => document.removeEventListener('mousedown', h);
  }, [onClose]);
  return ref;
}

export function DashboardShell() {
  const api = useApi();
  const signOut = useSession((s) => s.signOut);
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const { data: sessions } = useSessions();
  const { data: version } = useVersion();
  const candidates = (sessions ?? []).filter((s) => s.status === 'active' && s.activeRunId);
  const runQueries = useQueries({
    queries: candidates.map((s) => ({
      queryKey: ['run', s.activeRunId],
      queryFn: () => api.runs.get(s.activeRunId as string),
      enabled: !!s.activeRunId,
      refetchInterval: 5000,
    })),
  });
  const activeRuns = candidates.filter((_, i) => runQueries[i]?.data?.status === 'running').slice(0, 8);

  const [collapsed, setCollapsed] = useState(() => {
    try {
      return localStorage.getItem('rc-sidebar') === 'collapsed';
    } catch {
      return false;
    }
  });
  const [palette, setPalette] = useState(false);
  const [updating, setUpdating] = useState(false);
  const [drawer, setDrawer] = useState(false);
  const [menu, setMenu] = useState<'user' | null>(null);
  const [, force] = useState(0);
  const userRef = useOutside<HTMLSpanElement>(() => setMenu((m) => (m === 'user' ? null : m)));

  useEffect(() => {
    try {
      localStorage.setItem('rc-sidebar', collapsed ? 'collapsed' : 'expanded');
    } catch {
      // ignore
    }
  }, [collapsed]);

  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setPalette(true);
      }
    };
    document.addEventListener('keydown', h);
    return () => document.removeEventListener('keydown', h);
  }, []);

  useEffect(() => {
    if (!menu) return;
    const h = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setMenu(null);
    };
    document.addEventListener('keydown', h);
    return () => document.removeEventListener('keydown', h);
  }, [menu]);

  const onSignOut = async () => {
    await api.auth.logout().catch(() => undefined);
    signOut();
    navigate('/overview');
  };
  const flipTheme = () => {
    toggleTheme();
    force((n) => n + 1);
    setMenu(null);
  };

  const consoleMatch = pathname.match(/^\/sessions\/([^/]+)$/);
  const consoleId = consoleMatch && consoleMatch[1] !== 'new' ? consoleMatch[1] : null;
  const fallbackTitle: [string, string] = pathname.startsWith('/servers/')
    ? ['Server', '· execution host']
    : pathname.startsWith('/proxies/')
      ? ['Proxy', '· egress']
      : ['REDCELL', ''];
  const [title, sub] = TITLES[pathname] ?? fallbackTitle;
  const showNew = pathname === '/overview' || pathname === '/sessions';

  return (
    <div className={`app-shell${collapsed ? ' collapsed' : ''}`}>
      <aside className="side">
        <div className="ws">
          <span className="logo" />
          <span className="nm">REDCELL</span>
          {version?.current ? (
            <span className="ver">{version.current === 'dev' ? 'dev' : `v${version.current}`}</span>
          ) : null}
          {version?.updateAvailable ? (
            <button type="button" className="upd-badge"
              onClick={() => setUpdating(true)}
              title={`Update available: ${version.latest}`}
            >
              Update
            </button>
          ) : null}
        </div>
        <button type="button" className="search" onClick={() => setPalette(true)}>
          <svg viewBox="0 0 24 24">
            <circle cx="11" cy="11" r="7" />
            <path d="M20 20l-3-3" />
          </svg>
          Search
          <span className="kbd">⌘K</span>
        </button>
        <div className="side-scroll">
          {SIDEBAR_GROUPS.map((g, i) => (
            <div key={g.label ?? i} className="nav">
              {g.label && <div className="sec-h">{g.label}</div>}
              {g.items.map((n) => (
                <NavLink
                  key={n.to}
                  to={n.to}
                  end={n.end}
                  className={({ isActive }) => `ni${isActive ? ' on' : ''}`}
                >
                  {n.icon}
                  {n.label}
                </NavLink>
              ))}
            </div>
          ))}
          {activeRuns.length > 0 && (
            <div className="nav">
              <div className="sec-h">Active runs</div>
              {activeRuns.map((s) => (
                <ActiveRunRow key={s.id} session={s} onClick={() => navigate(`/sessions/${s.id}`)} />
              ))}
            </div>
          )}
        </div>
        <div className="side-foot">
          <span className="menu-wrap" style={{ width: '100%' }} ref={userRef}>
            <button type="button" className="userbtn"
              onClick={() => setMenu((m) => (m === 'user' ? null : 'user'))}
              aria-haspopup="menu"
              aria-expanded={menu === 'user'}
            >
              <span className="avatar" />
              <div style={{ flex: 1 }}>
                <div className="u">admin</div>
                <div className="e">operator</div>
              </div>
              <svg className="caret" viewBox="0 0 24 24">
                <path d="M8 15l4-4 4 4" />
              </svg>
            </button>
            <div className="menu up" role="menu" style={{ display: menu === 'user' ? 'block' : 'none', width: '100%' }}>
              <button type="button" className="menu-item" onClick={flipTheme}>
                Toggle theme
              </button>
              <div className="menu-sep" />
              <button type="button" className="menu-item" onClick={onSignOut}>
                Sign out
              </button>
            </div>
          </span>
        </div>
      </aside>

      <div className="main-pad">
        <section className="main-card">
        <header className="head">
          <button type="button"
            className="iconbtn"
            onClick={() => setCollapsed((v) => !v)}
            title={collapsed ? 'Show sidebar' : 'Hide sidebar'}
            aria-label={collapsed ? 'Show sidebar' : 'Hide sidebar'}
          >
            <svg viewBox="0 0 24 24">
              <rect x="3" y="4" width="18" height="16" rx="2" />
              <path d="M9 4v16" />
            </svg>
          </button>
          {consoleId ? (
            <ConsoleHeader sessionId={consoleId} />
          ) : (
            <>
              <h1>{title}</h1>
              {sub && <span className="sub">{sub}</span>}
              <div className="grow" />
              {showNew && (
                <button type="button" className="btn pri" onClick={() => navigate('/sessions/new')}>
                  <svg viewBox="0 0 24 24">
                    <path d="M12 5v14M5 12h14" />
                  </svg>
                  New session
                </button>
              )}
            </>
          )}
          <button type="button" className="iconbtn" onClick={flipTheme} title="Toggle theme" aria-label="Toggle theme">
            <svg viewBox="0 0 24 24">
              <path d="M12 3v2M12 19v2M5 5l1.5 1.5M17.5 17.5L19 19M3 12h2M19 12h2M5 19l1.5-1.5M17.5 6.5L19 5M12 8a4 4 0 100 8 4 4 0 000-8z" />
            </svg>
          </button>
        </header>
        <div className={consoleId ? 'console-body' : 'body-normal'}>
          <Outlet />
        </div>
        </section>
      </div>

      <MobileNav onMore={() => setDrawer(true)} />
      <MobileDrawer
        open={drawer}
        onClose={() => setDrawer(false)}
        version={version}
        onUpdate={() => setUpdating(true)}
        onToggleTheme={flipTheme}
        onSignOut={onSignOut}
      />

      {palette ? <CommandPalette open onClose={() => setPalette(false)} /> : null}
      <UpdateDialog open={updating} onClose={() => setUpdating(false)} target={version?.latest} />
    </div>
  );
}
