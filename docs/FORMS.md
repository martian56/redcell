# Form controls

The console uses a small set of custom form controls so inputs look and behave consistently, in both themes.

## The controls

- **Text input / textarea** - styled fields with theme-aware borders and focus.

- **Segmented buttons** - a small set of mutually exclusive options shown inline.

- **Combobox** - a searchable dropdown that replaces native selects when the list is long or benefits from search.

## The searchable combobox

The combobox is a button that opens a popover with a search field and a filtered, paginated list of options.

It replaces the native select so the list is searchable, styled to match the app, and consistent across the console.

It is generic over the option type: you provide the items and functions to derive a key, a label, and an optional sublabel.

It lives in `apps/web/src/components/ui/Combobox.tsx`.

## Combobox API

- `items` - the array of options.

- `current` - the selected option (used to highlight it).

- `getKey` - a stable key for each option.

- `getLabel` - the primary text shown for an option.

- `getSublabel` - optional secondary text under the label.

- `onSelect` - called with the chosen option.

- `trigger` - the element that opens the popover; use `SelectTrigger` for a select look.

- `placeholder` - the search field placeholder.

- `pageSize` - how many options per page before paging controls appear.

- `width` - popover width when not full-width.

- `block` - make the trigger and popover full-width, for form fields.

## SelectTrigger

`SelectTrigger` (in `components/ui/fields`) renders a select-styled box with a chevron, so a combobox reads as a dropdown.

## Using it in a form field

Wrap it in a field with a label, pass `block`, and give it a `SelectTrigger` showing the current selection.

## Behavior

Clicking the trigger opens the popover and focuses the search field.

Typing filters options by label and sublabel, case-insensitively.

Long lists paginate; prev/next controls appear when there is more than one page.

Selecting an option calls onSelect and closes the popover.

The popover closes on Escape or a click outside.

The current selection is highlighted in the list.

When nothing matches, the popover shows a no-matches message.

## Combobox vs native select vs free text

Use the **combobox** when the list is more than a handful of options or benefits from search (providers, models).

A short, fixed set that never needs search can stay a simple control, but prefer the combobox for consistency.

Keep a **free-text input** as a fallback when there is no list to choose from (for example a provider that lists no models).

## Where it is used

- Settings: the Provider and Model selectors for the default model.

- New run: the model picker.

## This change

Issue #79 replaced the native Provider and Model selects in Settings with the combobox, so both are searchable and match the rest of the console.

It reuses the existing combobox rather than adding a new one, so there is a single component to maintain.

The free-text model input is kept for providers that list no models.

## Accessibility

The trigger is a button with an expanded state; the popover is a listbox and options carry a selected state.

Focus moves to the search field on open, and the list is reachable by keyboard.

Escape closes the popover and returns control to the page.

## For contributors

Because the combobox is generic, pass your option type directly and supply getKey/getLabel; no wrapper types are needed.

Pass current so the active option is highlighted; it is matched by getKey.

Render the current value inside SelectTrigger so the closed state shows the selection.

Use block inside form fields so the control fills the column.

## Verifying

Open the control, type to filter, and confirm selecting an option updates the field.

Verify in a browser; the popover, search, and pagination are layout behavior.

## Troubleshooting

**Popover does not open.** The trigger must be inside the combobox; pass it via the trigger prop, not as a sibling.

**Search does not filter.** getLabel (and getSublabel) feed the filter; make sure they return the searchable text.

**Selection is not highlighted.** current must be an item whose getKey matches an option in the list.

**Popover is clipped.** It opens within the surrounding card; keep the field away from the very bottom, or the card should allow it to show.

**Popover is too narrow.** Pass block for form fields, or set width for a floating trigger.

## FAQ

**Why not a native select?** Native selects are not searchable and are hard to style consistently across platforms.

**Does it handle long lists?** Yes; it paginates and filters, so hundreds of options stay usable.

**Is it keyboard friendly?** Yes; open, type to filter, and select without the mouse.

**What if there is no list?** Use a plain input; the Settings model field does this when a provider lists no models.

## References

- `apps/web/src/components/ui/Combobox.tsx` - the component.

- `apps/web/src/components/ui/fields.tsx` - SelectTrigger and field helpers.

- `apps/web/src/app/pages/SettingsPage.tsx` - the Provider and Model usage.

- Issue #79 - the Settings combobox.

## Notes

The combobox is presentation-agnostic: it does not assume what an option is, only how to key, label, and select it.

Sublabels are handy for disambiguating similar options, like a model's provider.

Pagination keeps the popover short even with a large catalog.

Filtering resets to the first page so results are always visible.

The trigger and popover share the field width in block mode, so they line up with other inputs.

Selecting a provider also resets the model to that provider's first model, keeping the pair valid.

The model field falls back to free text so unusual or self-hosted model names can still be entered.

Because it is one shared component, improvements to search or keyboard handling benefit every usage at once.

The control is theme-aware; its popover, borders, and text use the same tokens as the rest of the console.

It closes on outside click, so it behaves like other menus in the app.

The search is a plain substring match, which is predictable and fast for these lists.

No native select styling hacks are needed, so the look is identical on every platform.

The combobox is small and composable, so new selectors can adopt it with a few lines.

Keeping selectors consistent makes the settings feel of a piece with the rest of the console.

## Related

- [APP-SHELL.md](APP-SHELL.md) - menus and dropdown behavior.

- [SHORTCUTS.md](SHORTCUTS.md) - the command palette, which is also a searchable popover.

## Summary

Prefer the searchable combobox over native selects; it is consistent, keyboard friendly, and scales to long lists, with free text as the fallback.

## See also

- Settings is where the combobox is most visible today.

The goal is simple: choosing a provider or model should feel as quick as searching for it.

That is the combobox: search, pick, done, consistent everywhere it appears.

## Popover positioning

A dropdown positioned inside its container is clipped when an ancestor uses `overflow: hidden` or scrolls. On the Settings page the cards clip their contents, which cut the combobox list off at the card's bottom edge.

To avoid this, the combobox popover is rendered in a portal on `document.body` with fixed positioning, so it escapes every overflow-hidden or scrolling ancestor.

The position is computed from the trigger's bounding rect: the popover opens just below the trigger, aligned to its left, and matches its width in block mode.

When there is not enough room below, it flips to open above the trigger instead of running off the screen.

It repositions on scroll and resize while open, so it stays anchored to the trigger as the page moves.

Because the popover is outside the trigger's DOM subtree, the outside-click handler ignores clicks inside the popover as well, so selecting an option does not close it prematurely.

The popover uses a high z-index so it sits above cards and even above a modal dialog it may be opened from.

This is why the same combobox works both on the Settings page and inside the New run dialog.

### How it works

On open, the trigger's rect is measured and the popover's fixed coordinates are set from it.

The popover is rendered through a portal, so it lives at the end of the body rather than inside the clipped card.

A capture-phase scroll listener and a resize listener re-measure and reposition while the popover is open.

Two refs, one on the trigger wrapper and one on the popover, let the outside-click handler treat both as inside.

The width follows the trigger in block mode, so the popover lines up with the field.

### For contributors

You do not need to do anything special to use it in a clipped container; the portal handles that.

Prefer block inside form fields so the popover matches the field width.

If you build another floating control, follow the same pattern: portal to the body, position from the trigger, and reposition on scroll and resize.

Keep the popover's z-index above dialogs so it is usable from within a modal.

Measure the trigger rect on open and on every reposition, not once, so the popover tracks layout changes.

Include the popover in the outside-click check, or clicking an option will close the popover before the click registers.

### Troubleshooting

**Dropdown is cut off.** It is being clipped by an overflow-hidden ancestor; it should be portaled to the body, not positioned inside the container.

**Dropdown is in the wrong place.** The trigger rect was not re-measured; reposition on open and on scroll/resize.

**Dropdown closes when clicking an option.** The outside-click check does not include the portaled popover; add its ref to the check.

**Dropdown runs off the bottom.** Enable the flip so it opens above the trigger when space below is tight.

**Dropdown appears behind a dialog.** Raise its z-index above the dialog's overlay.

### Verifying

Open the control inside a card and confirm the list shows fully, past the card's edge, on top of other content.

Check the popover's parent is the body and its position is fixed.

Scroll the page with the popover open and confirm it follows the trigger.

Selecting an option should update the field and close the popover.

### This fix
