# Command palette and shortcuts

The command palette is the fastest way to move around the console and jump straight to a session, server, or proxy.

## Opening it

Press Cmd+K (macOS) or Ctrl+K (Windows and Linux) from anywhere in the console.

Press Escape or click outside to close it.

## What it searches

- **Pages** - Overview, Sessions, Findings, Reports, Servers, Proxies, Settings.
- **Actions** - New session, and other quick actions.
- **Sessions** - by name, client, or a target in scope.
- **Servers** - by name or host.
- **Proxies** - by label or url.

## Results are grouped

Matches are grouped under Actions, Pages, Sessions, Servers, and Proxies, each with its own header, so a long list stays readable.

## Keyboard navigation

- Arrow Down / Arrow Up move the selection, wrapping at the ends.
- Enter opens the highlighted result.
- Escape closes the palette without navigating.
- Hovering a result highlights it, so mouse and keyboard stay in sync.

## How matching works

Typing filters by a case-insensitive match across each item's label, secondary text, and keywords (a session's client and targets, a server's host, a proxy's url).

With an empty query the palette shows just the pages and actions, so it opens fast and uncluttered.

Results are capped so a very large workspace does not render a huge list at once. Narrow the query to find a specific item.

## Examples

- Type part of a session name or its client to jump into that session's console.

- Type a target domain or IP to find the session that has it in scope.

- Type a server's hostname to open that server.

- Type part of a proxy url to open that proxy.

- Type a page name (for example "settings") to go there.

## Icons

Each result carries an icon for its kind: a grid for Overview, a target for a session, a rack for servers, a relay for proxies, a gear for Settings, and so on. The icons are distinct so you can scan by shape.

## Extending the palette

The palette lives in `apps/web/src/app/CommandPalette.tsx`.

- To add a page, append an entry to the `PAGES` list with a route and an icon.

- To add an action, append to the `ACTIONS` list.

- To add an entity source, read a list hook and map its rows into items with a `group`, a `to` route, an icon, and `keywords` for search.

- To add an icon, add a case to the `Icon` component. Icons are stroked, so use simple outline shapes.

## Performance

The entity lists come from cached queries, so opening the palette does not fire new requests in the common case.

Filtering is a plain in-memory pass, and the result cap keeps rendering cheap.

## Why not findings and reports

Findings and reports are scoped to a session, so a global search would fan out a query per session. The palette searches sessions instead; open a session to reach its findings and reports.

## Design notes

The palette previously listed only static pages, and some icons were generic. This made it a page switcher rather than a way to find things.

Searching real entities turns it into a jump-to-anything tool, which is what a command palette is for.

## Keyboard reference

| Key | Action |
| --- | --- |
| Cmd/Ctrl + K | Open the palette |
| Type | Filter results |
| Arrow Down | Next result |
| Arrow Up | Previous result |
| Enter | Open the selection |
| Escape | Close the palette |

## Pages at a glance

- **Overview** - KPIs, activity, and recent sessions.
- **Sessions** - the list of engagements; open one for its console.
- **Findings** - triage across findings.
- **Reports** - generate and download engagement reports.
- **Servers** - execution servers and their health.
- **Proxies** - egress proxies and their health.
- **Settings** - provider keys, models, execution, and branding.

## Accessibility

The palette is a labelled dialog. Focus moves to the search input on open.
