# German Overflow Audit

Backlog item: `GLOC-501`
Date: 2026-05-30

## Scope

- Desktop viewport: 1440 x 1200.
- Mobile viewport: 390 x 900.
- Routes checked in German: Library, Guided editor, All settings, JSON editor, and new-profile
  Guided editor.

## Findings

- Library and JSON editor fit without horizontal overflow.
- Mobile Guided editor and new-profile routes had a small page overflow from the settings search
  shell because the shell used `width: 100%` with content-box padding.
- All settings desktop could clip the table surface when policy/category/value labels were long.
- Stepper description text used a two-line clamp, which could visibly cut German copy.

## Changes

- Made the settings search shell use border-box sizing.
- Reduced rigid All settings table column minimums so the list can share space with the detail panel
  without clipping.
- Removed the stepper copy clamp and kept normal wrapping with hyphenation.

## Verification

Chromium/Selenium local audit after the fixes:

- Full German pass: Library, Guided editor, All settings, JSON editor, new-profile editor on desktop
  and mobile.
- Final focused pass: Guided editor and new-profile editor on desktop and mobile.
- Result: no page-width offenders and no clipped visible text in the audited German routes.

Screenshots were captured under `/tmp/bpm-gloc501-de-audit-after` and
`/tmp/bpm-gloc501-de-audit-final` during the local audit run.
