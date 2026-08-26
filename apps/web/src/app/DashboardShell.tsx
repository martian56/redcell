import { useEffect, useRef, useState } from 'react';
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useApi } from '@/lib/api';
import { useSession } from '@/store/session';
import { toggleTheme } from '@/lib/theme';
import { CommandPalette } from './CommandPalette';
import { ConsoleHeader } from './ConsoleHeader';

interface NavItem {
  to: string;
  label: string;
  icon: JSX.Element;
  end?: boolean;
}

const I = {
  overview: (
    <svg viewBox="0 0 24 24">
      <rect x="3" y="3" width="8" height="8" rx="1.5" />
      <rect x="13" y="3" width="8" height="5" rx="1.5" />
      <rect x="13" y="11" width="8" height="10" rx="1.5" />
      <rect x="3" y="14" width="8" height="7" rx="1.5" />
    </svg>
  ),
  sessions: (
    <svg viewBox="0 0 24 24">
      <path d="M4 6h16M4 12h16M4 18h16" />
    </svg>
  ),
  servers: (
    <svg viewBox="0 0 24 24">
      <rect x="3" y="4" width="18" height="7" rx="1.5" />
      <rect x="3" y="13" width="18" height="7" rx="1.5" />
      <path d="M7 7.5h.01M7 16.5h.01" />
    </svg>
  ),
  proxies: (
    <svg viewBox="0 0 24 24">
      <path d="M4 12h16M4 12a8 8 0 0 1 8-8M20 12a8 8 0 0 1-8 8" />
    </svg>
  ),
  settings: (
    <svg viewBox="0 0 24 24">
      <circle cx="12" cy="12" r="3" />
      <path d="M12 2v3M12 19v3M2 12h3M19 12h3M5 5l2 2M17 17l2 2M5 19l2-2M17 7l2-2" />
    </svg>
  ),
  findings: (
    <svg viewBox="0 0 24 24">
      <path d="M12 3l8 4v5c0 5-3.5 8-8 9-4.5-1-8-4-8-9V7z" />
    </svg>
  ),
  reports: (
    <svg viewBox="0 0 24 24">
      <path d="M6 3h9l4 4v14H6z" />
      <path d="M14 3v5h5" />
    </svg>
  ),
};

const GROUPS: { label?: string; items: NavItem[] }[] = [
  {
    items: [
      { to: '/overview', label: 'Overview', icon: I.overview },
      { to: '/sessions', label: 'Sessions', icon: I.sessions, end: true },
      { to: '/findings', label: 'Findings', icon: I.findings },
      { to: '/reports', label: 'Reports', icon: I.reports },
    ],
  },
  {
    label: 'Infrastructure',
    items: [
      { to: '/servers', label: 'Servers', icon: I.servers },
      { to: '/proxies', label: 'Proxies', icon: I.proxies },
      { to: '/settings', label: 'Settings', icon: I.settings },
    ],
  },
];

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

function useOutside(onClose: () => void) {
  const ref = useRef<HTMLSpanElement>(null);
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

  const [collapsed, setCollapsed] = useState(() => {
    try {
      return localStorage.getItem('rc-sidebar') === 'collapsed';
    } catch {
      return false;
    }
  });
  const [palette, setPalette] = useState(false);
  const [menu, setMenu] = useState<'ws' | 'user' | null>(null);
  const [, force] = useState(0);
  const wsRef = useOutside(() => setMenu((m) => (m === 'ws' ? null : m)));
  const userRef = useOutside(() => setMenu((m) => (m === 'user' ? null : m)));

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
  const [title, sub] = TITLES[pathname] ?? [pathname.replace('/', '') || 'REDCELL', ''];
  const showNew = pathname === '/overview' || pathname === '/sessions';

  return (
    <div className={`app-shell${collapsed ? ' collapsed' : ''}`}>
      <aside className="side">
        <div className="ws">
          <span className="logo" />
          <span className="nm">REDCELL</span>
          <span className="menu-wrap" ref={wsRef}>
            <button
              className="iconbtn"
              style={{ width: 24, height: 24, color: 'var(--tx-3)' }}
              onClick={() => setMenu((m) => (m === 'ws' ? null : 'ws'))}
              aria-label="Workspace menu"
            >
              <svg className="caret" viewBox="0 0 24 24">
                <path d="M8 9l4 4 4-4" />
              </svg>
            </button>
            <div className={`menu${menu === 'ws' ? '' : ''}`} style={{ display: menu === 'ws' ? 'block' : 'none' }}>
              <div className="menu-label">Workspace</div>
              <button className="menu-item sel">
                REDCELL<span className="ck">✓</span>
              </button>
              <div className="menu-sep" />
              <button className="menu-item" onClick={flipTheme}>
                Toggle theme
              </button>
            </div>
          </span>
        </div>
        <button className="search" onClick={() => setPalette(true)}>
          <svg viewBox="0 0 24 24">
            <circle cx="11" cy="11" r="7" />
            <path d="M20 20l-3-3" />
          </svg>
          Search
          <span className="kbd">⌘K</span>
        </button>
        <div className="side-scroll">
          {GROUPS.map((g, i) => (
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
        </div>
        <div className="side-foot">
          <span className="menu-wrap" style={{ width: '100%' }} ref={userRef}>
            <button className="userbtn" onClick={() => setMenu((m) => (m === 'user' ? null : 'user'))}>
              <span className="avatar" />
              <div style={{ flex: 1 }}>
                <div className="u">admin</div>
                <div className="e">operator</div>
              </div>
              <svg className="caret" viewBox="0 0 24 24">
                <path d="M8 15l4-4 4 4" />
              </svg>
            </button>
            <div className="menu up" style={{ display: menu === 'user' ? 'block' : 'none', width: '100%' }}>
              <button className="menu-item" onClick={flipTheme}>
                Toggle theme
              </button>
              <div className="menu-sep" />
              <button className="menu-item" onClick={onSignOut}>
                Sign out
              </button>
            </div>
          </span>
        </div>
      </aside>

      <div className="main-pad">
        <section className="main-card">
        <header className="head">
          <button
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
                <button className="btn pri" onClick={() => navigate('/sessions/new')}>
                  <svg viewBox="0 0 24 24">
                    <path d="M12 5v14M5 12h14" />
                  </svg>
                  New session
                </button>
              )}
            </>
          )}
          <button className="iconbtn" onClick={flipTheme} title="Toggle theme" aria-label="Toggle theme">
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

      <CommandPalette open={palette} onClose={() => setPalette(false)} />
    </div>
  );
}
