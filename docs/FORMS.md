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
