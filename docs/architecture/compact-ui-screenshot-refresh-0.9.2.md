# BPM 0.9.2 Compact UI Screenshot Refresh

Date: 2026-07-19
Status: automated capture complete; release review remains governed by locale sign-off
Backlog item: `BPM092-M11-03`

## Scope and capture

Only the five User Guide scenarios invalidated by compact UI changes were recaptured for all six
active locales: `library-overview`, `guided-editor-overview`, `all-settings-review`, `json-editor`,
and `compare-profiles`. This produced 30 PNG assets from localhost-only synthetic profiles.

The capture report is the generated, ignored local artifact
`documentation/reports/screenshots/bpm092-m11-03/user-guide-screenshots-0.9.1.json`. It records
30 captured of 30 expected rows, route, fixture state, viewport, theme, schema channel, asset path,
dimensions, and byte size for each row.

The capture uses the existing normalized matrix and updates only its matching assets under
`documentation/assets/screenshots/{locale}/`. It does not replace the historical full-matrix
report or create an unreviewed new screenshot scenario.

## Derived documentation outputs

`make docs-validate` regenerates the six-locale portal, manifest, UI target map, and search corpus
from the current DITA sources and refreshed assets. `make docs-install-dev` installs that result for
the maintainer's subsequent `make dev`.

## Visual and release boundary

An automated DOM probe for the Guided editor captured a zero horizontal scroll position and a
header inside the desktop viewport. The retained locale/editorial release gate still requires the
recorded human reviews; automated screenshot capture is not a substitute for those sign-offs.
