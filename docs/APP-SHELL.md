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

The shell is `apps/web/src/app/DashboardShell.tsx`; its styles are in `apps/web/src/styles/design.css`.

- Add a nav item by extending the groups list with a route, label, and icon.

- Add a menu by wrapping its trigger and menu in one element, putting the outside-click ref on that wrapper, and toggling an open state.

- A menu inside the sidebar must stay within the 236px width; do not rely on it overflowing, because the sidebar clips overflow.

## Verifying shell changes

Verify layout changes in a browser, not only with a build. Positioning, clipping, and z-index cannot be checked by type or unit tests. Append `?demo=1` to load the shell without a backend.

## Troubleshooting

**A sidebar menu looks cut off.** It extends past the 236px sidebar and is clipped by `overflow: hidden`. Anchor it so it stays within the sidebar.

**A menu appears under the main content.** Its z-index is too low, or it overflows into the main area. Raise the z-index and keep it inside its region.

**A menu will not close on outside click.** The outside-click ref is on the trigger only, not the wrapper that includes the menu.

**Sidebar content peeks out when collapsed.** Something inside the sidebar escapes `overflow: hidden`; keep sidebar content within the column.

**Collapse state resets on reload.** localStorage may be blocked; the shell falls back to expanded.

## FAQ

**What happened to the workspace switcher?** It was a placeholder for a single workspace and was removed. If multi-workspace support lands later, a switcher can return.

**Where is the theme stored?** It is applied via a data attribute on the root and persisted, and re-applied before paint to avoid a flash.

**Does collapsing hide the brand header?** Yes; the whole sidebar is hidden when collapsed.

**Is the shell responsive?** The main content is fluid; the sidebar is a fixed width you can collapse.

## Structure at a glance

- `.ws` - the brand header (logo and name)

- `.search` - opens the command palette

- `.side-scroll` - the scrollable navigation area

- `.side-foot` - the user menu

- `.main-pad` / `.main-card` - the floating content card

- `.head` - the card header with title and actions

## Menu positioning reference

- Default: opens below the trigger, left-aligned.

- Right-aligned: aligns the menu's right edge to the trigger.

- Upward: opens above the trigger (used by the footer user menu).

## Z-index notes

Menus sit above the shell chrome and the main card so an open menu is never obscured.

## Glossary

- **Shell** - the persistent sidebar and header around every page.

- **Main card** - the floating content area to the right of the sidebar.

- **Dropdown / menu** - a small floating list anchored to a trigger.

## References

- `apps/web/src/app/DashboardShell.tsx` - the shell component.

- `apps/web/src/styles/design.css` - shell, sidebar, and menu styles.

- [SHORTCUTS.md](SHORTCUTS.md) - the command palette and keyboard navigation.

- [UPDATING.md](UPDATING.md) - in-app updates.

- Issue #76 - removing the placeholder workspace switcher.

## Notes

REDCELL is single-operator: one admin account, one workspace. That is why a workspace switcher added no value.

Theme has two entry points now (header and user menu); removing the switcher removed a third, redundant one.

The brand header is now a plain label, so it no longer needs a positioning context or hover affordance.

The user menu is the only dropdown in the sidebar, and it opens upward within the footer width.

When collapsed, the brand header disappears with the rest of the sidebar.

The brand header is a natural place to surface the running version and update state; that is tracked separately.

## See also

- [DEPLOY.md](DEPLOY.md) for running the console.

## Summary

Sidebar plus floating card. The header is a plain brand label; the only sidebar menu is the user menu. Verify layout in a browser.

## Outside-click hook

A small generic hook attaches a `mousedown` listener and closes the menu when the click falls outside the wrapping element. Put its ref on the element that contains both the trigger and the menu.

## Escape to close

A document-level `keydown` listener closes any open shell menu on Escape while a menu is open.

## Collapse persistence

The collapse flag is read from localStorage on first render and written whenever it changes, wrapped in try/catch so a blocked storage does not break the shell.

## Active runs source

The list comes from active sessions with a running run; each run's status is polled, and only running ones are shown.

## Active link styling

Navigation uses the router's active state to highlight the current page; the Overview link matches exactly so it does not stay highlighted on sub-routes.

## Palette mounting

The command palette is mounted only while open, so its data queries fire on open rather than during normal dashboard use.

## Console header

On a session route the card header is replaced by the console header (status, metrics, run controls); elsewhere it shows the page title and actions.

## Theme tokens

Shell colors come from CSS variables, so both themes and the light/dark toggle work without per-component overrides.

## Fixed sidebar width

The 236px sidebar is fixed, so sidebar content has a predictable width and never depends on the viewport.

## Consistent controls

The shell avoids native popovers; menus are custom so they match the theme and behave consistently.

## Keep it simple

The header stays a label unless there is a real control to add; extra chrome in the sidebar is easy to add and hard to justify.

## Search shortcut

Cmd/Ctrl+K opens the palette from anywhere via a document key listener, in addition to the Search button.

## Sign out

Signing out from the user menu clears the session and returns to Overview (which redirects to login).

## Operator identity

The footer shows the operator name and role; there is a single operator account.

## Brand mark

The logo is a small accent square next to the REDCELL wordmark; it is decorative.

## Version and updates in the sidebar

The brand header shows the running version next to REDCELL, for example `v0.3.5`. A locally built image without a baked version reads `dev`.

The version comes from `/system/version` via the `useVersion` query, which also reports the latest release and whether an update is available.

When an update is available, an Update pill appears next to the version. Its tooltip names the target version.

Clicking the pill takes you to Settings, where the update can be applied. (A follow-up wires it to an in-place progress panel.)

The version query refetches periodically, so the pill appears on its own shortly after a new release is published.

The latest-release lookup is cached briefly on the server, so a brand-new release can take a few minutes to surface. See [UPDATING.md](UPDATING.md).

The version is always shown; only the Update pill is conditional. This keeps the running version visible at a glance.

The version sits right after the REDCELL wordmark; the Update pill is pushed to the right of the header.

The version uses the monospace font in a muted color; the pill uses the accent color so it reads as an action.

### Why show the version

Operators need to know what build is running when reporting an issue or confirming an update landed. Putting it in the sidebar makes it visible on every screen.

The version is only shown after login; the login page never reveals it. See [PRE-AUTH-SURFACE.md](PRE-AUTH-SURFACE.md).

### dev vs a release build

A released image bakes its version in, so the sidebar shows `vX.Y.Z`. A local or unversioned build shows `dev`, and no update is ever offered for a `dev` build.

### The update flow from the sidebar

1. The version query reports `updateAvailable`.
2. The Update pill appears next to the version.
3. Selecting it opens the update path (Settings today, an in-place panel next).
4. After the update, the version updates and the pill goes away.

### Behavior details

The query refetches on an interval and is cached, so it does not hammer the endpoint but still notices a new release quickly.

Until the first version response arrives, neither the version nor the pill is shown, so there is no flicker of placeholder text.

When the sidebar is collapsed, the version and pill are hidden with the rest of the header.

If the version endpoint is unreachable, the header simply omits the version rather than showing an error.

### Accessibility

The Update pill is a real button with a descriptive title naming the target version, so its purpose is clear on hover and to assistive tech.

It is keyboard focusable and activates on Enter or Space like any button.

### For contributors

The version comes from `useVersion` in `apps/web/src/features/hooks.ts`; the display lives in the `.ws` header in `DashboardShell.tsx`.

Format the version as `dev` when the current value is `dev`, otherwise prefix with `v`.

Render the version whenever a value exists, and the pill only when `updateAvailable` is true.

Keep the version muted and the pill in the accent color; the pill uses `margin-left: auto` to sit at the right of the header.

### Verifying

In mock mode the version query returns a sample with an update available, so the version and the pill both render for a quick visual check.

On a real deployment, the pill appears once a newer release is published and the server's cached lookup refreshes.

Confirm the header does not overflow: logo, name, version, and pill should all fit within the 236px sidebar.

### Troubleshooting the version display

**No version shown.** The version endpoint is unreachable or still loading. Check the API is up and reachable from the browser.

**Shows `dev`.** The running image has no baked version. Only released images carry one; deploy a release to see a version.

**No Update pill after a release.** The server caches the latest-release lookup for a few minutes; wait, then reload.

**Pill stays after updating.** The app may be showing a stale query; a reload after the update clears it, and the update flow reloads for you.

**Header looks crowded.** A very long version string plus the pill could wrap; the version is compact by design to avoid this.

### FAQ

**Where does the number come from?** The image's baked `REDCELL_VERSION`, surfaced by the API and read by the sidebar.

**How does it know a newer version exists?** The API compares the running version to the latest GitHub release.

**What does clicking the pill do?** It takes you to Settings to apply the update; a later change opens an in-place progress panel.

**Can I hide the version?** It is intentionally always visible after login; there is no toggle.

### References

- `apps/web/src/app/DashboardShell.tsx` - the sidebar header and version display.

- `apps/web/src/features/hooks.ts` - `useVersion`.

- `apps/api/app/routers/system.py` - the version endpoint.

- [UPDATING.md](UPDATING.md) - how updates work end to end.

- Issue #77 - the sidebar version and update indicator.

### Notes

The version is deliberately understated so it informs without competing with navigation.

The Update pill is the one accent element in the header, drawing the eye only when action is useful.

Because there is a single operator, any signed-in user is the admin who can apply the update.

The `v` prefix is added in the UI; the API reports the bare number, and the latest release tag keeps its own `v`.

Comparison is numeric per version segment, so `v0.10.0` is correctly newer than `v0.9.0`.

The periodic refetch is light and cached server-side, so it is safe to leave the app open.

Settings also shows the version and an update control, so the sidebar and Settings stay consistent.

A progress panel that opens on update is tracked separately; the sidebar pill will open it once it lands.

## Related

- [DEPLOY.md](DEPLOY.md) - deploying and updating from the shell.

- [SHORTCUTS.md](SHORTCUTS.md) - the command palette.

The pill's tooltip reads "Update available: <version>", so hovering confirms the target before you act.

If the latest release cannot be determined, no update is offered and only the current version shows.

When current equals latest, there is no pill; the sidebar just shows the version.

The indicator only appears for a newer release, never for an older one.

Only the latest published release is considered; drafts and prereleases are ignored by the check.

A transient network error during the version check leaves the last known state until the next refetch.

The header renders immediately; the version fills in when its query resolves.

Logo, wordmark, version, and pill are sized to fit the 236px sidebar without wrapping.

Both the muted version and the accent pill use theme tokens, so they adapt to light and dark.

The pill has comfortable padding so it is an easy click target despite its small text.

Linking to Settings keeps a single place to review the update before applying it.

The same version value powers both the sidebar and the Settings display, so they never disagree.

Applying the update is admin-gated on the server, independent of where the click originates.

Seeing the version flip after an update is a quick confirmation the update succeeded.

The update flow reloads the app so the new web bundle and version are picked up.

The server caches the latest-release lookup for a few minutes to respect API rate limits.

A dev build never nags for updates, which keeps local development quiet.

Because the query is shared and cached, multiple views do not multiply the number of checks.

The current version is shown without a tooltip; the pill carries the target in its tooltip.

Placing the version in the header, not the footer, keeps it near the product identity.

Only two small elements were added; the header stays uncluttered.

If multiple workspaces ever return, the version can sit alongside a workspace label here.

Layout is verified in a browser; the value and pill logic can be checked in mock mode.

In short: the sidebar always shows the running version, and offers a one-click path to update when a newer release exists.

The Update pill participates in normal tab order, so keyboard users reach it after the header controls.

In dark mode the accent pill keeps sufficient contrast against the sidebar background.

The wordmark and version never truncate at the default width; only extreme custom fonts would risk it.

The pill is a styled button, not a native control, matching the rest of the console.
