# Mobile responsive design

Goal: the operator console works as a mobile app on phones (bottom tab
bar, overflow drawer, reflowed pages, sheet dialogs) while the desktop
layout stays exactly as it is today.

## Core rule

Desktop CSS is never edited. Every mobile rule lives inside a
`@media (max-width: 768px)` block in `src/styles/mobile.css`, which is
imported last so its rules win at that width. Mobile-only DOM (bottom
nav, drawer) renders always but is `display: none` above 768px, so the
desktop tree is visually unchanged.

## Breakpoint

- Single breakpoint at `768px`. At or below it the app is "mobile".
- `useIsMobile()` (`src/lib/useIsMobile.ts`) exposes the same threshold
  to components that must branch behavior, not just styling.
- `MOBILE_MAX_WIDTH` is the shared source of truth for the number.

## Layers

- Safe-area insets are exposed as `--rc-safe-*` variables so fixed
  layers can pad around notches and home indicators.
- Reserved metrics: `--rc-bottom-nav-h`, `--rc-mobile-top-h`,
  `--rc-tap-min` (44px minimum touch target).
- `viewport-fit=cover` lets the page paint under the safe areas while
  the insets keep content clear of them.

## Navigation

- Desktop keeps its left sidebar.
- Mobile hides the sidebar and gains a fixed bottom tab bar with the
  primary destinations plus a More entry.
- More opens a slide-in drawer holding secondary destinations, the
  version and update control, theme toggle, and sign out.

## Pages and dialogs

- List tables reflow to stacked card lists; grids collapse to one
  column; wide tables that cannot become cards scroll horizontally
  inside their own container.
- Modal dialogs (New run, Update, Command palette) present as
  full-height bottom sheets on mobile.

## Rollout

Shipped across issues #90 through #101, one PR each, then release
v0.4.0. Each step is desktop-safe on its own so `main` stays
releasable throughout.
