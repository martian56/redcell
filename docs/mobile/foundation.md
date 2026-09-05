# Mobile foundation notes

Rationale and mechanics of the responsive primitives introduced for the
mobile console. See DESIGN.md for the overall plan.
- r1: Desktop CSS is never edited, so the PC layout cannot regress.
- r2: mobile.css is imported last so its rules win at the mobile width.
- r3: useIsMobile reads the same 768px threshold via matchMedia.
- r4: MOBILE_MAX_WIDTH is the single source of truth for the breakpoint.
- r5: The hook is SSR safe and no-ops when matchMedia is unavailable.
- r6: The hook attaches one change listener and detaches it on unmount.
