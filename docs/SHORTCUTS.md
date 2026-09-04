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
