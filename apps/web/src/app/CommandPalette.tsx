import { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';

interface Cmd {
  to: string;
  label: string;
  path: string;
}

const CMDS: Cmd[] = [
  { to: '/overview', label: 'Overview', path: 'M3 3h8v8H3zM13 3h8v5h-8zM13 11h8v10h-8zM3 14h8v7H3z' },
  { to: '/sessions', label: 'Sessions', path: 'M4 6h16M4 12h16M4 18h16' },
  { to: '/sessions/new', label: 'New session', path: 'M12 5v14M5 12h14' },
  { to: '/findings', label: 'Findings', path: 'M12 3l8 4v5c0 5-3.5 8-8 9-4.5-1-8-4-8-9V7z' },
  { to: '/reports', label: 'Reports', path: 'M6 3h9l4 4v14H6z' },
  { to: '/servers', label: 'Servers', path: 'M3 4h18v7H3zM3 13h18v7H3z' },
  { to: '/proxies', label: 'Proxies', path: 'M4 12h16' },
  { to: '/settings', label: 'Settings', path: 'M12 9a3 3 0 100 6 3 3 0 000-6z' },
];

export function CommandPalette({ open, onClose }: { open: boolean; onClose: () => void }) {
  const navigate = useNavigate();
  const [q, setQ] = useState('');
  const [active, setActive] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const items = useMemo(
    () => CMDS.filter((c) => c.label.toLowerCase().includes(q.toLowerCase())),
    [q],
  );

  useEffect(() => {
    if (open) {
      setQ('');
      setActive(0);
      queueMicrotask(() => inputRef.current?.focus());
    }
  }, [open]);

  useEffect(() => setActive(0), [q]);

  if (!open) return null;

  const choose = (c?: Cmd) => {
    const target = c ?? items[active] ?? items[0];
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
            placeholder="Go to or search…"
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
            items.map((c, i) => (
              <button
                key={c.to}
                className={`palette-item${i === active ? ' act' : ''}`}
                onMouseEnter={() => setActive(i)}
                onClick={() => choose(c)}
              >
                <svg viewBox="0 0 24 24">
                  <path d={c.path} />
                </svg>
                {c.label}
              </button>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
