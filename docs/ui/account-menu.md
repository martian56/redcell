# Account menu

Notes on the bottom-of-sidebar account line and its dropdown.
- r1: It shows the signed-in username and role from auth.me.
- r2: Clicking it opens a dropdown that pops upward.
- r3: The dropdown has Settings, Toggle theme, and Sign out.
- r4: Menu icons are right aligned and muted.
- r5: The useMe hook reads the current user with react-query.
- r6: The dropdown closes on outside click and Escape.
- r7: Settings navigates to the settings page.
- r8: Sign out logs out and returns to the overview.
- r9: The notifications row is added with the notifications feature.
- r10: The account line is the dropdown trigger.
- r11: The menu keeps its existing pop animation and our colors.
- r12: The username falls back to admin when me is loading.
- r13: The role falls back to operator when me is loading.
- r14: The account line stays a single row with the caret.
- r15: Styles and colors are unchanged from the console theme.
- r16: The account line sits at the bottom of the sidebar.
