import { NavLink } from 'react-router-dom';
import { PRIMARY_NAV } from './nav';

export function MobileNav() {
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
    </nav>
  );
}
