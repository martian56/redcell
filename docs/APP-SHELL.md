# The operator console shell

How the console is laid out: a sidebar and a floating main card, with the shared menu and dropdown behavior.

## Layout

The shell is a two-column grid: a fixed 236px sidebar and the main area. Collapsing the sidebar sets its column to 0.

The main area is a floating card with its own header and body, padded away from the edges.

## Sidebar

The sidebar uses `overflow: hidden` so it clips cleanly when collapsed. That means anything inside it, including dropdowns, must stay within the sidebar's width or it gets clipped.

Top to bottom: the workspace header, the search button, the navigation groups, the active-runs list, and the user menu at the foot.
