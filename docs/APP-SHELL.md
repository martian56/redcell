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

Because the sidebar clips overflow, a sidebar menu must be anchored so it stays inside the sidebar. The workspace menu spans the header width; the user menu spans the footer width.

Menus sit above surrounding content via z-index. Keep menu z-index above the main card so an overlapping menu is never painted under it.

## Collapsing the sidebar

The header toggle hides the sidebar (grid column to 0). The choice is stored in localStorage and restored on load.

The sidebar's `overflow: hidden` is what makes the collapse look clean, which is why menus inside it must not rely on overflowing.

## Header

The main card header shows the page title (or the console header on a session) and page actions such as New session and the theme toggle.

The first header button toggles the sidebar.

## Theme

Theme can be toggled from the header, the workspace menu, or the user menu. The choice is applied via a data attribute and persisted.

## Search

The Search button opens the command palette (Cmd/Ctrl+K). See [SHORTCUTS.md](SHORTCUTS.md).

## Active runs

Below the navigation, sessions whose run is currently running are listed for quick access. The list is capped and polls run status.

## User menu

The footer shows the operator and opens an upward menu with a theme toggle and sign out. It spans the footer width, staying inside the sidebar.

## Accessibility

Menu triggers use `aria-haspopup` and `aria-expanded`; menus use a menu role. Focus and keyboard access are preserved.

Icon-only buttons carry an `aria-label`.

## Fix: the workspace dropdown

The dropdown was positioned from the caret with `left: 0`, so a 180px menu started near the right of the sidebar and ran ~60px past its edge.

The sidebar's `overflow: hidden` then clipped the overflowing part, and it overlapped the main content, so it looked like it slid under the main card.

The menu is now anchored to the `.ws` header and spans within the sidebar, with a higher z-index. It stays fully inside the sidebar at any width.

## For contributors

The shell is `apps/web/src/app/DashboardShell.tsx`; its styles are in `apps/web/src/styles/design.css`.

- Add a nav item by extending the groups list with a route, label, and icon.

- Add a menu by giving its trigger a wrapper as the positioning context and toggling an open state.

- A menu inside the sidebar must be anchored so it stays within the 236px width; do not rely on it overflowing, because the sidebar clips overflow.

- Give menus a z-index above the main card so an overlapping menu is never painted under it.

- Reuse the outside-click hook and put its ref on the element that wraps both the trigger and the menu.

## Verifying shell changes

Verify layout changes in a browser, not only with a build. Positioning, clipping, and z-index cannot be checked by type or unit tests.

Append `?demo=1` to skip auth and load the shell with demo data for quick visual checks.

For a dropdown, measure its bounding box against the sidebar's to confirm it stays inside and is not clipped.

## Troubleshooting

**A sidebar dropdown looks cut off.** It extends past the 236px sidebar and is clipped by `overflow: hidden`. Anchor it so it stays within the sidebar.

**A menu appears under the main content.** Its z-index is too low, or it overflows into the main area. Raise the z-index and keep it inside its region.

**A menu will not close on outside click.** The outside-click ref is on the trigger only, not the wrapper that includes the menu.

**Sidebar content peeks out when collapsed.** Something inside the sidebar is escaping `overflow: hidden`; keep sidebar content within the column.

**Collapse state resets on reload.** localStorage may be blocked; the shell falls back to expanded.

## FAQ

**Can I have multiple workspaces?** The switcher is built for it; today there is a single REDCELL workspace.

**Where is the theme stored?** It is applied via a data attribute on the root and persisted, and re-applied before paint to avoid a flash.

**Does collapsing hide the workspace switcher?** Yes; the whole sidebar is hidden when collapsed.

**Is the shell responsive?** The main content is fluid; the sidebar is a fixed width you can collapse.

## Menu positioning reference

- Default: opens below the trigger, left-aligned.

- Right-aligned: aligns the menu's right edge to the trigger, opening leftward.

- Upward: opens above the trigger (used by the footer user menu).

- Header-spanning: the workspace menu spans the sidebar header width, anchored to `.ws`.

## Structure at a glance
