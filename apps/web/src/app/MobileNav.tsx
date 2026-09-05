import { NavLink } from 'react-router-dom';
import { NAV_ICONS, PRIMARY_NAV } from './nav';

export function MobileNav({ onMore }: { onMore: () => void }) {
  return (
    <nav className="mnav" aria-label="Primary">
      {PRIMARY_NAV.map((n) => (
        <NavLink
          key={n.to}
          to={n.to}
          end={n.end}
          className={({ isActive }) => `mnav-tab${isActive ? ' on' : ''}`}
        >
          {n.icon}
          <span>{n.label}</span>
        </NavLink>
      ))}
      <button type="button" className="mnav-tab" onClick={onMore}>
        {NAV_ICONS.more}
        <span>More</span>
      </button>
    </nav>
  );
}
