# The operator console shell

How the console is laid out: a sidebar and a floating main card, with the shared menu behavior.

## Layout

The shell is a two-column grid: a fixed 236px sidebar and the main area. Collapsing the sidebar sets its column to 0.

The main area is a floating card with its own header and body, padded away from the edges.

## Sidebar

The sidebar uses `overflow: hidden` so it clips cleanly when collapsed. Anything inside it must stay within its width.

Top to bottom: the brand header, the search button, the navigation groups, the active-runs list, and the user menu at the foot.

## Brand header

The header shows the REDCELL logo and name. It is a simple label, not a control.

It previously held a workspace switcher, but that only listed a single workspace and a theme toggle, so it was removed. The theme toggle lives in the header and the user menu.

## Search

The Search button opens the command palette (Cmd/Ctrl+K). See [SHORTCUTS.md](SHORTCUTS.md).

## Navigation

Navigation is grouped (Overview, Sessions, Findings, Reports, and an Infrastructure group for Servers, Proxies, and Settings). The active route is highlighted.

## Active runs

Below the navigation, sessions whose run is currently running are listed for quick access. The list is capped and polls run status, and is hidden when nothing is running.

## User menu

The footer shows the operator and opens an upward menu with a theme toggle and sign out. It spans the footer width, staying inside the sidebar, and closes on Escape or an outside click.

## Collapsing the sidebar

The header toggle hides the sidebar (grid column to 0). The choice is stored in localStorage and restored on load. The sidebar's `overflow: hidden` makes the collapse look clean.

## Header

The main card header shows the page title (or the console header on a session) and page actions such as New session and the theme toggle. The first button toggles the sidebar.

## Theme

Theme can be toggled from the header or the user menu. The choice is applied via a data attribute, persisted, and re-applied before paint to avoid a flash.

## Menus and dropdowns

A menu opens from its trigger and closes on Escape, on selecting an item, or on a click outside (a shared outside-click hook).

Because the sidebar clips overflow, a sidebar menu must be anchored so it stays inside the sidebar. The user menu spans the footer width and opens upward.

Menus sit above surrounding content via z-index; keep a menu's z-index above the main card so an overlapping menu is never painted under it.

## Accessibility

Menu triggers use `aria-haspopup` and `aria-expanded`, and menus use a menu role. Everything is keyboard reachable.

Icon-only buttons carry an `aria-label`.

## For contributors
