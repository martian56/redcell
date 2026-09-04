# The operator console shell

How the console is laid out: a sidebar and a floating main card, with the shared menu and dropdown behavior.

## Layout

The shell is a two-column grid: a fixed 236px sidebar and the main area. Collapsing the sidebar sets its column to 0.

The main area is a floating card with its own header and body, padded away from the edges.

## Sidebar

The sidebar uses `overflow: hidden` so it clips cleanly when collapsed. That means anything inside it, including dropdowns, must stay within the sidebar's width or it gets clipped.

Top to bottom: the workspace header, the search button, the navigation groups, the active-runs list, and the user menu at the foot.

## Workspace switcher

The header shows the workspace name with a caret. The caret opens a small menu (the workspace and a theme toggle).

The menu is anchored to the header (`.ws` is the positioning context) and spans within the sidebar, so it never extends into the main content or gets clipped.

The caret rotates when the menu is open, and the button carries `aria-haspopup` and `aria-expanded`.

## Menus and dropdowns

A menu opens from its trigger and closes on Escape, on selecting an item, or on a click outside (a shared outside-click hook).

Menus are absolutely positioned relative to their trigger's wrapper. By default a menu opens below-left; modifiers open it right-aligned or upward.
