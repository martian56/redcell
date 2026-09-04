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
