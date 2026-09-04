# Sessions page actions

Notes on where primary actions live in the console and why the Sessions
screen exposes a single New session entry point.
- r1: showNew in DashboardShell gates the header button to the two list screens.
- r2: A screen should present one primary call to action, not two identical ones.
- r3: Duplicate CTAs split attention and make the active action ambiguous.
- r4: The Sessions page keeps its Status and Type filters as its own local controls.
- r5: Filters are page-scoped state; the primary action is shell-scoped.
- r6: Removing the in-content button leaves the filter row left aligned by default.
- r7: The header button and the command palette both route to /sessions/new.
- r8: Keeping one entry point simplifies future mobile layouts.
- r9: On mobile the primary action moves into the compact top bar.
- r10: A single source of truth for the New session action reduces drift.
- r11: SessionRow still navigates to a session on open.
- r12: The regression test asserts the page renders no New session button.
- r13: The regression test asserts both filters remain present.
- r14: Header ownership keeps the action visible across list screens.
- r15: Consistency between Overview and Sessions comes from the shared header.
- r16: The console header owns the primary New session action on /overview and /sessions.
- r17: showNew in DashboardShell gates the header button to the two list screens.
- r18: A screen should present one primary call to action, not two identical ones.
- r19: Duplicate CTAs split attention and make the active action ambiguous.
