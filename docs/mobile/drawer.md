# Mobile overflow drawer

Notes on the slide-in drawer that holds secondary navigation and account
actions on mobile.
- r1: The drawer holds Servers, Proxies, and Settings.
- r2: The drawer also holds the version and update-available control.
- r3: The drawer also holds the theme toggle and sign out.
- r4: It reuses SECONDARY_NAV from the shared nav module.
- r5: It reuses the shell sign-out, theme, version, and update handlers.
- r6: Escape closes the drawer.
- r7: Tapping the backdrop closes the drawer.
- r8: Body scroll is locked while the drawer is open.
- r9: Selecting a destination closes the drawer and navigates.
- r10: The drawer slides in from the left edge.
- r11: The slide animation is disabled under prefers-reduced-motion.
- r12: The panel pads around the safe-area insets.
- r13: Each row honors the 44px minimum touch target.
- r14: The drawer sits above the bottom bar and below modal dialogs.
- r15: The update control opens the progress dialog and closes the drawer.
- r16: The More tab in the bottom bar opens the overflow drawer.
- r17: The drawer holds Servers, Proxies, and Settings.
