# Locale Screenshot Pack Audit - 2026-05-30

Backlog item: `GLOC-603`

Scope: screenshot pack for the six active UI locales across the primary profile routes.

## Screenshot Pack

Output directory: `docs/screenshots/gloc603_2026-05-30`

Locales:

- `en`
- `ru`
- `de`
- `zh-CN`
- `fr`
- `es-ES`

Routes:

- Library: `/profiles`
- Guided editor: `/profiles/1/edit`
- All settings: `/profiles/1/settings`
- JSON editor: `/profiles/1/json`

Viewports:

- Desktop: 1440 px wide
- Mobile: 390 px wide

Generated artifacts:

- 48 route screenshots: 6 locales x 4 routes x 2 viewports
- 6 locale contact sheets: one PNG and one HTML review sheet per locale
- `manifest.json` with locale, route, viewport, path, document language, and measured width metadata

## Visual Localization Review

The screenshots confirm that the six locale modes render across the primary routes and fit the
captured desktop and mobile widths. The contact-sheet white area is review-sheet whitespace around
fixed screenshots, not application overflow.

Not every non-English locale is fully localized in the visual surface yet.

| Locale | Visual result | Notes |
| --- | --- | --- |
| `en` | Source language | English is expected. |
| `ru` | Mostly localized | Expected English remains for `Browser Policy Manager`, test profile data, policy identifiers, JSON keys, Firefox/Release labels, and other technical allowlist terms. |
| `zh-CN` | Mostly localized | The scenario-card English island from the earlier screenshot is fixed. Expected English remains for product/test/technical strings. |
| `de` | Mixed | Several visible first-pass UI strings still remain in English or partly English, especially route chrome, scenario text, and profile/editor controls. |
| `fr` | Mixed | Several visible first-pass UI strings still remain in English or partly English, especially route chrome, scenario text, and profile/editor controls. |
| `es-ES` | Mixed | Several visible first-pass UI strings still remain in English or partly English, especially route chrome, scenario text, and profile/editor controls. |

Expected English follows `docs/locale_visible_english_allowlists_2026-05-30.md`: product names,
policy identifiers, JSON field names, test data, browser/version labels, and schema terminology can
remain in English where the locale contract allows them. Ordinary prose and command labels should
not remain English after locale QA.

## Follow-Up

The screenshot pack is complete for `GLOC-603`. The visual review exposes a translation-quality gap
for `de`, `fr`, and `es-ES`; this is catalog content work, not a screenshot-generation or layout
blocker.
