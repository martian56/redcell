import { useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import { SECONDARY_NAV } from './nav';

interface VersionInfo {
  current?: string;
  latest?: string | null;
  updateAvailable?: boolean;
}

export function MobileDrawer({
  open,
  onClose,
  version,
  onUpdate,
  onToggleTheme,
  onSignOut,
}: {
  open: boolean;
  onClose: () => void;
  version?: VersionInfo;
  onUpdate: () => void;
  onToggleTheme: () => void;
  onSignOut: () => void;
}) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', onKey);
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', onKey);
      document.body.style.overflow = prevOverflow;
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="mdrawer-backdrop" onMouseDown={onClose}>
      <aside
        className="mdrawer"
        role="dialog"
        aria-modal="true"
        aria-label="Menu"
        onMouseDown={(e) => e.stopPropagation()}
      >
        <div className="mdrawer-head">
          <span className="logo" />
          <span className="nm">REDCELL</span>
          {version?.current ? (
            <span className="ver">{version.current === 'dev' ? 'dev' : `v${version.current}`}</span>
          ) : null}
          {version?.updateAvailable ? (
            <button
              type="button"
              className="upd-badge"
              onClick={() => {
                onClose();
                onUpdate();
              }}
              title={`Update available: ${version.latest}`}
            >
              Update
            </button>
          ) : null}
        </div>
        <nav className="mdrawer-nav" aria-label="Secondary">
          {SECONDARY_NAV.map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              onClick={onClose}
              className={({ isActive }) => `mdrawer-item${isActive ? ' on' : ''}`}
            >
              {n.icon}
              <span>{n.label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="mdrawer-foot">
          <button type="button" className="mdrawer-item" onClick={onToggleTheme}>
            Toggle theme
          </button>
          <button
            type="button"
            className="mdrawer-item"
            onClick={() => {
              onClose();
              onSignOut();
            }}
          >
            Sign out
          </button>
        </div>
      </aside>
    </div>
  );
}
