# Simplified Chinese Script Audit

Backlog item: `GLOC-504`
Date: 2026-05-30

## Scope

- Locale checked: Simplified Chinese (`zh-CN`).
- Desktop viewport: 1440 x 1200.
- Mobile viewport: 390 x 900.
- Routes checked: Library, Guided editor, All settings, JSON editor, and new-profile Guided editor.
- Script-specific focus: CJK line breaking, density, punctuation, button labels, table/card scan
  behavior, horizontal overflow, and clipped controls.

## Findings

- Chromium/Selenium found no horizontal page overflow and no clipped visible controls in the audited
  desktop or mobile routes.
- Library, Guided editor, JSON editor, and new-profile Guided editor were clean after the script
  pass.
- The initial pass found Simplified Chinese strings that still mixed ordinary English prose into
  visible UI labels, especially Library helper copy, Guided step controls, progress labels, baseline
  summary copy, and All settings preference cards.
- The All settings pass also exposed three known-preference cards that still depended on English
  fallback labels from the Python settings catalog.

## Changes

- Reworked visible `zh-CN` copy for the primary Library, Guided editor, All settings, JSON editor,
  step progress, step actions, compare, baseline, and preference-card surfaces.
- Added i18n keys for the known-preference cards that were previously fallback-only:
  top-sites rows, address-bar quick actions, and notification permission default.
- Wired those known-preference cards to the new `label_key` and `description_key` values in the
  Firefox settings catalog.
- Kept product and technical terms in Latin where the locale contract already allows them, such as
  `Firefox`, `Mozilla`, `JSON`, `policies.json`, `CIS`, `ESR`, `Release`, `DNS`, `HTTPS`, `VPN`,
  `IP`, `AI`, and `Cookie`.

## Verification

Chromium/Selenium local audit result before the final server restart:

- Library desktop/mobile: clean.
- Guided editor desktop/mobile: clean.
- All settings desktop/mobile: layout clean; remaining mixed English was isolated to the
  fallback-only known-preference cards fixed in this task.
- JSON editor desktop/mobile: clean.
- New-profile Guided editor desktop/mobile: clean.

Screenshots and JSON reports were captured under:

- `/tmp/bpm-gloc504-zh-cn-audit-final`
- `/tmp/bpm-gloc504-zh-cn-audit-final2`

The final post-restart browser rerun could not be completed in this session because further external
Chromium/ChromeDriver escalation was blocked by the environment usage limit. Contract tests cover the
fresh catalog and settings-catalog wiring added after that browser pass.
