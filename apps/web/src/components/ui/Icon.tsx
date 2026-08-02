import type { ReactNode } from 'react';

// Hand-drawn icon set.
export type IconName =
  | 'overview'
  | 'agents'
  | 'findings'
  | 'terminals'
  | 'listeners'
  | 'proxy'
  | 'surface'
  | 'loot'
  | 'reports'
  | 'settings'
  | 'engagements'
  | 'chevronDown'
  | 'chevronLeft'
  | 'chevronRight'
  | 'close'
  | 'plus'
  | 'pause'
  | 'stop'
  | 'steer'
  | 'sidebar'
  | 'user'
  | 'search'
  | 'server'
  | 'logout'
  | 'dot';

const paths: Record<IconName, ReactNode> = {
  overview: (
    <>
      <rect x="3" y="3" width="7" height="7" rx="1.5" />
      <rect x="14" y="3" width="7" height="7" rx="1.5" />
      <rect x="3" y="14" width="7" height="7" rx="1.5" />
      <rect x="14" y="14" width="7" height="7" rx="1.5" />
    </>
  ),
  agents: (
    <>
      <circle cx="5" cy="6" r="2.4" />
      <circle cx="18" cy="12" r="2.4" />
      <circle cx="5" cy="18" r="2.4" />
      <path d="M7.2 7.2 15.8 11M7.2 16.8 15.8 13" />
    </>
  ),
  findings: (
    <>
      <path d="M12 3l7 3v5c0 4-3 6.5-7 7.8C8 17.5 5 15 5 11V6z" />
      <path d="M12 8.5v3.5M12 15h.01" />
    </>
  ),
  terminals: (
    <>
      <rect x="3" y="4" width="18" height="16" rx="2.5" />
      <path d="M7 10l3 2-3 2M13 14h4" />
    </>
  ),
  listeners: (
    <>
      <circle cx="12" cy="12" r="1.8" fill="currentColor" stroke="none" />
      <path d="M8.5 8.5a5 5 0 000 7M15.5 8.5a5 5 0 010 7M6 6a8 8 0 000 12M18 6a8 8 0 010 12" />
    </>
  ),
  proxy: <path d="M4 8h13l-3-3M20 16H7l3 3" />,
  surface: (
    <>
      <circle cx="12" cy="12" r="8" />
      <circle cx="12" cy="12" r="3" />
      <path d="M12 2v3M12 19v3M2 12h3M19 12h3" />
    </>
  ),
  loot: (
    <>
      <circle cx="8" cy="8" r="4" />
      <path d="M11 11l8 8M16 16l2-2M18 18l2-2" />
    </>
  ),
  reports: (
    <>
      <path d="M6 3h8l4 4v14H6z" />
      <path d="M14 3v4h4M9 12h6M9 16h6" />
    </>
  ),
  settings: (
    <>
      <circle cx="12" cy="12" r="3.2" />
      <path d="M12 2v3M12 19v3M22 12h-3M5 12H2M19 5l-2 2M7 17l-2 2M19 19l-2-2M7 7 5 5" />
    </>
  ),
  engagements: (
    <>
      <path d="M12 3l9 5-9 5-9-5z" />
      <path d="M3 12l9 5 9-5M3 16l9 5 9-5" />
    </>
  ),
  chevronDown: <path d="M6 9l6 6 6-6" />,
  chevronLeft: <path d="M15 6l-6 6 6 6" />,
  chevronRight: <path d="M9 6l6 6-6 6" />,
  close: <path d="M6 6l12 12M18 6L6 18" />,
  plus: <path d="M12 5v14M5 12h14" />,
  pause: (
    <>
      <rect x="6" y="5" width="4" height="14" rx="1" fill="currentColor" stroke="none" />
      <rect x="14" y="5" width="4" height="14" rx="1" fill="currentColor" stroke="none" />
    </>
  ),
  stop: <rect x="6" y="6" width="12" height="12" rx="1.5" fill="currentColor" stroke="none" />,
  steer: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M15.5 8.5l-2 5-5 2 2-5z" fill="currentColor" stroke="none" />
    </>
  ),
  sidebar: (
    <>
      <rect x="3" y="4" width="18" height="16" rx="2" />
      <path d="M9 4v16" />
    </>
  ),
  user: (
    <>
      <circle cx="12" cy="8" r="3.5" />
      <path d="M5 20a7 7 0 0114 0" />
    </>
  ),
  search: (
    <>
      <circle cx="11" cy="11" r="6" />
      <path d="M20 20l-3.5-3.5" />
    </>
  ),
  server: (
    <>
      <rect x="3" y="4" width="18" height="7" rx="1.6" />
      <rect x="3" y="13" width="18" height="7" rx="1.6" />
      <path d="M7 7.5h.01M7 16.5h.01" />
    </>
  ),
  logout: (
    <>
      <path d="M9 4H6a2 2 0 00-2 2v12a2 2 0 002 2h3" />
      <path d="M15 12H3.5M13 8l4 4-4 4" />
    </>
  ),
  dot: <circle cx="12" cy="12" r="4" fill="currentColor" stroke="none" />,
};

export function Icon({
  name,
  size = 16,
  strokeWidth = 1.7,
  className,
}: {
  name: IconName;
  size?: number;
  strokeWidth?: number;
  className?: string;
}) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      {paths[name]}
    </svg>
  );
}
