import { Fragment, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useProxies, useServers, useSessions } from '@/features/hooks';

type Group = 'Actions' | 'Pages' | 'Sessions' | 'Servers' | 'Proxies';
type IconKey =
  | 'overview' | 'sessions' | 'new' | 'findings' | 'reports' | 'servers' | 'proxies' | 'settings'
  | 'session' | 'server' | 'proxy';

interface Item {
  id: string;
  group: Group;
  label: string;
  sub?: string;
  to: string;
  icon: IconKey;
  keywords?: string;
}

function Icon({ name }: { name: IconKey }) {
  switch (name) {
    case 'overview':
      return (
        <>
          <rect x="3" y="3" width="7" height="7" rx="1" />
          <rect x="14" y="3" width="7" height="7" rx="1" />
          <rect x="14" y="14" width="7" height="7" rx="1" />
          <rect x="3" y="14" width="7" height="7" rx="1" />
        </>
      );
    case 'sessions':
      return <path d="M4 6h16M4 12h16M4 18h10" />;
    case 'new':
      return <path d="M12 5v14M5 12h14" />;
    case 'findings':
      return <path d="M12 3l8 4v5c0 5-3.5 8-8 9-4.5-1-8-4-8-9V7z" />;
    case 'reports':
      return (
        <>
          <path d="M7 3h7l5 5v13H7z" />
          <path d="M14 3v5h5" />
          <path d="M9.5 13h5M9.5 17h5" />
        </>
      );
    case 'servers':
      return (
        <>
          <rect x="3" y="4" width="18" height="7" rx="1" />
          <rect x="3" y="13" width="18" height="7" rx="1" />
          <path d="M7 7.5h.01M7 16.5h.01" />
        </>
      );
    case 'proxies':
      return <path d="M4 8h12l-3-3M20 16H8l3 3" />;
    case 'settings':
      return (
        <>
          <circle cx="12" cy="12" r="3" />
          <path d="M12 2v3M12 19v3M2 12h3M19 12h3M5 5l2 2M17 17l2 2M19 5l-2 2M7 17l-2 2" />
        </>
      );
    case 'session':
      return (
        <>
          <circle cx="12" cy="12" r="8" />
          <circle cx="12" cy="12" r="3" />
        </>
      );
    case 'server':
      return (
        <>
          <rect x="4" y="5" width="16" height="14" rx="1.5" />
          <path d="M8 9h.01M8 13h.01" />
        </>
      );
    case 'proxy':
      return (
        <>
          <circle cx="12" cy="12" r="8" />
          <path d="M4 12h16M12 4c3 3 3 13 0 16M12 4c-3 3-3 13 0 16" />
        </>
      );
    default:
      return null;
  }
}

const ACTIONS: Item[] = [
  { id: 'a-new', group: 'Actions', label: 'New session', sub: 'Plan a new engagement', to: '/sessions/new', icon: 'new' },
];

const PAGES: Item[] = [
  { id: 'p-overview', group: 'Pages', label: 'Overview', to: '/overview', icon: 'overview' },
  { id: 'p-sessions', group: 'Pages', label: 'Sessions', to: '/sessions', icon: 'sessions' },
  { id: 'p-findings', group: 'Pages', label: 'Findings', to: '/findings', icon: 'findings' },
  { id: 'p-reports', group: 'Pages', label: 'Reports', to: '/reports', icon: 'reports' },
  { id: 'p-servers', group: 'Pages', label: 'Servers', to: '/servers', icon: 'servers' },
  { id: 'p-proxies', group: 'Pages', label: 'Proxies', to: '/proxies', icon: 'proxies' },
  { id: 'p-settings', group: 'Pages', label: 'Settings', to: '/settings', icon: 'settings' },
];

export function CommandPalette({ open, onClose }: { open: boolean; onClose: () => void }) {
  const navigate = useNavigate();
  const { data: sessions } = useSessions();
  const { data: servers } = useServers();
  const { data: proxies } = useProxies();
  const [q, setQ] = useState('');
  const [active, setActive] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const entities = useMemo<Item[]>(
    () => [
      ...(sessions ?? []).map((s) => ({
        id: `s-${s.id}`, group: 'Sessions' as const, label: s.name, sub: s.client,
        to: `/sessions/${s.id}`, icon: 'session' as const,
        keywords: [s.client, ...(s.targets ?? [])].join(' '),
      })),
      ...(servers ?? []).map((s) => ({
        id: `sv-${s.id}`, group: 'Servers' as const, label: s.name, sub: s.host,
        to: `/servers/${s.id}`, icon: 'server' as const, keywords: s.host,
      })),
      ...(proxies ?? []).map((p) => ({
        id: `px-${p.id}`, group: 'Proxies' as const, label: p.label, sub: p.url,
        to: `/proxies/${p.id}`, icon: 'proxy' as const, keywords: p.url,
      })),
    ],
    [sessions, servers, proxies],
  );

  const items = useMemo(() => {
    const query = q.trim().toLowerCase();
    if (!query) return [...ACTIONS, ...PAGES];
    const hit = (it: Item) => `${it.label} ${it.sub ?? ''} ${it.keywords ?? ''}`.toLowerCase().includes(query);
    return [...ACTIONS, ...PAGES, ...entities].filter(hit).slice(0, 50);
  }, [q, entities]);

  useEffect(() => {
    if (open) {
      setQ('');
      setActive(0);
      queueMicrotask(() => inputRef.current?.focus());
    }
  }, [open]);

  useEffect(() => setActive(0), [q]);

  if (!open) return null;

  const choose = (it?: Item) => {
    const target = it ?? items[active] ?? items[0];
    if (target) {
      navigate(target.to);
      onClose();
    }
  };

  return (
    <div className="overlay on" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal palette" role="dialog" aria-label="Command palette">
        <div className="palette-in">
          <svg viewBox="0 0 24 24">
            <circle cx="11" cy="11" r="7" />
            <path d="M20 20l-3-3" />
          </svg>
          <input
            ref={inputRef}
            value={q}
            placeholder="Search sessions, servers, proxies, or go to a page…"
            onChange={(e) => setQ(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') choose();
              else if (e.key === 'Escape') onClose();
              else if (e.key === 'ArrowDown') {
                e.preventDefault();
                setActive((a) => (a + 1) % Math.max(items.length, 1));
              } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                setActive((a) => (a - 1 + items.length) % Math.max(items.length, 1));
              }
            }}
          />
        </div>
        <div className="palette-list">
          {items.length === 0 ? (
            <div className="meta" style={{ padding: '14px' }}>
              No matches.
            </div>
          ) : (
            items.map((c, i) => {
              const header = i === 0 || items[i - 1]!.group !== c.group;
              return (
                <Fragment key={c.id}>
                  {header ? <div className="palette-group">{c.group}</div> : null}
                  <button
                    type="button"
                    className={`palette-item${i === active ? ' act' : ''}`}
                    onMouseEnter={() => setActive(i)}
                    onClick={() => choose(c)}
                  >
                    <svg viewBox="0 0 24 24">
                      <Icon name={c.icon} />
                    </svg>
                    <span className="txt">
                      <span className="lbl">{c.label}</span>
                      {c.sub ? <span className="sub">{c.sub}</span> : null}
                    </span>
                  </button>
                </Fragment>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
