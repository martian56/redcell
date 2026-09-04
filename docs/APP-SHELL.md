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
