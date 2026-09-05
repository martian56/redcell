export interface NavItem {
  to: string;
  label: string;
  icon: JSX.Element;
  end?: boolean;
}

export const NAV_ICONS = {
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
  more: (
    <svg viewBox="0 0 24 24">
      <circle cx="5" cy="12" r="1.6" />
      <circle cx="12" cy="12" r="1.6" />
      <circle cx="19" cy="12" r="1.6" />
    </svg>
  ),
};

export const PRIMARY_NAV: NavItem[] = [
  { to: '/overview', label: 'Overview', icon: NAV_ICONS.overview },
  { to: '/sessions', label: 'Sessions', icon: NAV_ICONS.sessions, end: true },
  { to: '/findings', label: 'Findings', icon: NAV_ICONS.findings },
  { to: '/reports', label: 'Reports', icon: NAV_ICONS.reports },
];

export const SECONDARY_NAV: NavItem[] = [
  { to: '/servers', label: 'Servers', icon: NAV_ICONS.servers },
  { to: '/proxies', label: 'Proxies', icon: NAV_ICONS.proxies },
  { to: '/settings', label: 'Settings', icon: NAV_ICONS.settings },
];

export const SIDEBAR_GROUPS: { label?: string; items: NavItem[] }[] = [
  { items: PRIMARY_NAV },
  { label: 'Infrastructure', items: SECONDARY_NAV },
];
