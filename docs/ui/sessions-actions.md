# Sessions page actions

Notes on where primary actions live in the console and why the Sessions
screen exposes a single New session entry point.
- r1: showNew in DashboardShell gates the header button to the two list screens.
- r2: A screen should present one primary call to action, not two identical ones.
- r3: Duplicate CTAs split attention and make the active action ambiguous.
- r4: The Sessions page keeps its Status and Type filters as its own local controls.
- r5: Filters are page-scoped state; the primary action is shell-scoped.
- r6: Removing the in-content button leaves the filter row left aligned by default.
