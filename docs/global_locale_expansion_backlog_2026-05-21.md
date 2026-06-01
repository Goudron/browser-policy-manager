# Global Locale Expansion Backlog

Date: `2026-05-21`

This backlog captures the epic for expanding BPM localization from `en` and `ru` to six
globally important Firefox locales:

- `en`
- `ru`
- `de`
- `zh-CN`
- `fr`
- `es-ES`

The goal is not only to add translated JSON catalogs, but to bring the new locales to the same
product quality level as English and Russian: terminology, runtime coverage, layout behavior,
browser QA, and regression checks must all be treated as part of the feature.

## Operating Principles

1. Keep English as the source product language.
   All product copy starts from `app/i18n/en.json` and English documentation/backlog text.

2. Treat each added locale as first-class.
   No new locale should ship with incomplete strings, obvious machine-translation artifacts,
   broken grammar around placeholders, or layout overflow in primary workflows.

3. Follow Mozilla terminology where applicable.
   For Firefox, Mozilla, browser UI, account, add-on, privacy, permission, update, translation,
   and policy-related terms, verify the target-language wording against Mozilla Pontoon and SUMO
   style before freezing translations.

4. Preserve technical identifiers.
   Firefox policy keys, JSON keys, API paths, URLs, schema identifiers, extension IDs, and literal
   values such as `true` / `false` remain untranslated unless the UI is explicitly describing them
   in prose.

5. Design for locale length and script differences.
   German, French, and Spanish strings may be significantly longer than English. Simplified
   Chinese has different line-breaking and density behavior. The UI must remain usable in all six
   locales.

6. Locale expansion must update tests and tooling.
   The runtime i18n contract, locale completeness checks, accidental-English guards, browser UI
   smoke flows, and README-supported-locale documentation all need to move together.

## Reasoning Level Guide For GPT-5.5

- `low`: deterministic file updates, small docs edits, narrow test updates.
- `medium`: locale catalog plumbing, straightforward translation QA, routine viewport fixes.
- `high`: multi-surface UI copy/layout changes, browser QA, terminology decisions across several
  product areas.
- `extra high`: architecture-level i18n changes, automated terminology tooling, broad responsive
  redesign, or ML-assisted localization QA workflows.

## Milestone 0: Scope And Locale Infrastructure

Goal: make the product explicitly know about the target six-locale set before translation work
begins.

| ID | Task | Scope | Acceptance | Reasoning |
|---|---|---|---|---|
| GLOC-001 | Define supported locale matrix | Record the target locale set, display names, BCP 47 tags, fallback behavior, and browser-language matching rules. | A maintainer-facing note or config source clearly lists `en`, `ru`, `de`, `zh-CN`, `fr`, and `es-ES`. | medium |
| GLOC-002 | Audit current locale loading assumptions | Review `/i18n/{locale}.json`, locale picker code, static bootstrap, tests, and templates for hardcoded `en`/`ru` assumptions. | Every place that assumes two locales is listed with an implementation decision. | medium |
| GLOC-003 | Add locale option metadata | Add labels and locale-picker entries for German, Simplified Chinese, French, and Spanish. | The picker can display all six locales with native-language labels and stable locale codes. | medium |
| GLOC-004 | Update locale fallback behavior | Ensure unsupported or regional browser locales fall back predictably, for example `de-AT` -> `de`, `fr-CA` -> `fr`, `es-MX` -> `es-ES` or configured fallback. | Browser/system locale selection resolves consistently and is covered by tests. | high |
| GLOC-005 | Update supported-locale documentation | Update README and relevant docs to describe all six supported locales and the English source-language policy. | Documentation no longer says only English and Russian are supported. | low |

## Milestone 1: Translation Source Preparation

Goal: prepare clean source strings and translation guidance before creating new locale catalogs.

| ID | Task | Scope | Acceptance | Reasoning |
|---|---|---|---|---|
| GLOC-101 | Freeze source string inventory | Export or snapshot the current `en.json` keys, placeholders, HTML-sensitive fragments, and technical allowlist patterns. | Translators/reviewers have a stable source inventory for the first locale expansion pass. | medium |
| GLOC-102 | Normalize source copy before translation | Review English strings for ambiguity, hidden grammar assumptions, concatenation risks, and placeholder wording that may not translate well. | Source strings are translator-friendly and avoid avoidable locale-specific ambiguity. | high |
| GLOC-103 | Build shared terminology sheet | Extend the current EN/RU glossary into a six-locale terminology sheet covering product modes, profile lifecycle, Firefox concepts, policy editing, CIS, and validation terms. | A glossary exists with source terms and columns/placeholders for `de`, `zh-CN`, `fr`, and `es-ES`. | high |
| GLOC-104 | Define Mozilla terminology verification workflow | Document how maintainers should verify Firefox/Mozilla terms in Pontoon and SUMO for each target locale. | The workflow is clear enough to repeat during future schema and UI copy changes. | medium |
| GLOC-105 | Define placeholder and identifier rules | Record rules for preserving `{placeholders}`, policy keys, preference keys, API paths, JSON values, and brand names in each locale. | Locale reviewers can distinguish translation defects from valid technical English. | medium |

## Milestone 2: New Locale Catalogs

Goal: add complete first-class locale catalogs for `de`, `zh-CN`, `fr`, and `es-ES`.

| ID | Task | Scope | Acceptance | Reasoning |
|---|---|---|---|---|
| GLOC-201 | Add German locale catalog | Create `app/i18n/de.json` from the source inventory with Mozilla-style terminology. | German locale is complete, valid JSON, placeholder-safe, and selectable. | high |
| GLOC-202 | Add Simplified Chinese locale catalog | Create `app/i18n/zh-CN.json` from the source inventory with Mozilla-style terminology. | Simplified Chinese locale is complete, valid JSON, placeholder-safe, and selectable. | high |
| GLOC-203 | Add French locale catalog | Create `app/i18n/fr.json` from the source inventory with Mozilla-style terminology. | French locale is complete, valid JSON, placeholder-safe, and selectable. | high |
| GLOC-204 | Add Spanish locale catalog | Create `app/i18n/es-ES.json` from the source inventory with Mozilla-style terminology. | Spanish locale is complete, valid JSON, placeholder-safe, and selectable. | high |
| GLOC-205 | Verify placeholder parity | Check every locale has the same interpolation placeholders as English for each key. | Tests fail if a locale drops, renames, or adds unexpected placeholders. | medium |
| GLOC-206 | Verify key parity | Ensure all six locale files have identical key sets unless an explicit locale-only exception is documented. | Missing and extra keys fail the locale contract test. | medium |
| GLOC-207 | Verify JSON and encoding safety | Confirm all locale catalogs are UTF-8 JSON, load through the existing `/i18n/{locale}.json` endpoint, and do not require escaping workarounds. | Locale files load in tests and in browser flows. | low |

## Milestone 3: Mozilla Terminology QA

Goal: keep Firefox-related wording aligned with Mozilla language conventions, not generic or
literal translations.

| ID | Task | Scope | Acceptance | Reasoning |
|---|---|---|---|---|
| GLOC-301 | Audit German Mozilla terminology | Verify terms for Firefox Home, Mozilla account, add-ons, cookies, permissions, privacy, updates, translation, and policy-related browser surfaces against Pontoon/SUMO. | German terminology issues are fixed or documented with rationale. | high |
| GLOC-302 | Audit Simplified Chinese Mozilla terminology | Verify the same Firefox/Mozilla term set against Pontoon/SUMO for `zh-CN`. | Simplified Chinese terminology issues are fixed or documented with rationale. | high |
| GLOC-303 | Audit French Mozilla terminology | Verify the same Firefox/Mozilla term set against Pontoon/SUMO for `fr`. | French terminology issues are fixed or documented with rationale. | high |
| GLOC-304 | Audit Spanish Mozilla terminology | Verify the same Firefox/Mozilla term set against Pontoon/SUMO for `es-ES`. | Spanish terminology issues are fixed or documented with rationale. | high |
| GLOC-305 | Update glossary from QA findings | Feed verified terms and accepted exceptions back into the project glossary. | Future UI copy changes have a maintained multilingual terminology reference. | medium |
| GLOC-306 | Add locale-specific allowlists | Extend accidental-English/technical-token tests so each locale allows valid identifiers and brands without allowing untranslated prose. | The guard catches obvious untranslated English while preserving technical identifiers. | high |

## Milestone 4: Runtime I18n Coverage

Goal: ensure dynamic UI strings and generated text work in all six locales.

| ID | Task | Scope | Acceptance | Reasoning |
|---|---|---|---|---|
| GLOC-401 | Extend runtime i18n contract tests | Update tests that scan templates and JavaScript for `data-i18n`, `t("profiles...")`, placeholder, title, and ARIA locale keys. | Every referenced key exists in all six locale catalogs. | medium |
| GLOC-402 | Audit runtime-generated counts | Review plural/count strings in Library, Guided editor, All settings, CIS summaries, and export review. | Count text is grammatical enough for all target locales or moved to safer wording. | high |
| GLOC-403 | Audit validation and error text | Check API/browser validation messages, import errors, JSON errors, and save/conflict states for locale coverage. | Common error paths do not fall back to English unexpectedly. | medium |
| GLOC-404 | Audit search and filter labels | Verify All settings search, filter chips, review cards, schema badges, and setting detail panels use locale-backed strings. | All settings remains fully localized in all six locales. | medium |
| GLOC-405 | Audit browser-generated date/time text | Review timestamps, relative time, and locale-sensitive formatting in Library and editor metadata. | Date/time text is either localized via browser APIs or intentionally neutral. | medium |

## Milestone 5: UI Layout And Script QA

Goal: adapt BPM UI so all six locales fit cleanly across desktop and mobile.

| ID | Task | Scope | Acceptance | Reasoning |
|---|---|---|---|---|
| GLOC-501 | German overflow pass | Test German strings across Library, Guided editor, All settings, JSON editor, modals, buttons, and cards. | No horizontal page overflow, clipped buttons, or unreadable wrapped labels at supported viewport widths. | high |
| GLOC-502 | French overflow pass | Test French strings across the same primary surfaces. | No horizontal page overflow, clipped buttons, or unreadable wrapped labels at supported viewport widths. | high |
| GLOC-503 | Spanish overflow pass | Test Spanish strings across the same primary surfaces. | No horizontal page overflow, clipped buttons, or unreadable wrapped labels at supported viewport widths. | high |
| GLOC-504 | Simplified Chinese script pass | Test `zh-CN` line breaking, density, punctuation, button labels, and table/card scan behavior. | Chinese UI is readable and does not rely on Latin spacing assumptions. | high |
| GLOC-505 | Locale picker layout pass | Verify native locale names fit in desktop and mobile controls. | Locale picker remains usable with all six options. | medium |
| GLOC-506 | Responsive CSS fixes for long labels | Adjust buttons, segmented controls, cards, table cells, and review panels where new locale strings expose fragile sizing. | Fixes are generic and do not special-case one locale unless necessary. | high |
| GLOC-507 | CJK font and fallback check | Confirm current font stack renders Simplified Chinese acceptably on expected deployment platforms. | CJK text is legible, does not produce tofu boxes, and has acceptable line height. | medium |

## Milestone 6: Browser QA And Screenshots

Goal: prove the six-locale UI works in realistic browser flows, not only through JSON checks.

| ID | Task | Scope | Acceptance | Reasoning |
|---|---|---|---|---|
| GLOC-601 | Extend Chromium locale smoke matrix | Add browser flows for `de`, `zh-CN`, `fr`, and `es-ES` across Library, Guided editor, All settings, and JSON editor. | Smoke tests load all primary routes in every locale. | high |
| GLOC-602 | Add viewport overflow assertions | Extend browser checks to assert document width does not exceed viewport width for every target locale and primary route. | Locale regressions fail when the UI creates horizontal overflow. | medium |
| GLOC-603 | Capture screenshot pack | Generate desktop and mobile screenshots for all six locales and core routes. | Reviewers can inspect locale-specific layout and terminology visually. | medium |
| GLOC-604 | Add locale switching regression | Verify switching between all six locales updates visible UI without stale text from the previous locale. | Locale switching is reliable without full page reload assumptions unless reload is intended. | high |
| GLOC-605 | Add import/edit/export localized workflow QA | Run a representative profile workflow in each locale: create/import, edit a guided setting, edit All settings, validate, export. | Core workflow remains usable and localized in every locale. | high |

## Milestone 7: Documentation And Release Readiness

Goal: make the locale expansion maintainable after the first release.

| ID | Task | Scope | Acceptance | Reasoning |
|---|---|---|---|---|
| GLOC-701 | Update README localization section | Document all six supported locales, source-language policy, and Mozilla terminology expectations. | README accurately describes the supported locale set. | low |
| GLOC-702 | Update locale glossary document | Replace the EN/RU-only glossary with a multilingual glossary or add a new six-locale glossary. | Maintainers have one current terminology reference. | medium |
| GLOC-703 | Add locale-update runbook | Document how to add/edit locale strings, verify Pontoon/SUMO terminology, run tests, and perform browser QA. | Future localization changes have a repeatable process. | medium |
| GLOC-704 | Update changelog release notes | Add a release note for the four new first-class locales and related QA/tooling. | Release notes communicate the localization expansion clearly. | low |
| GLOC-705 | Define ongoing locale ownership | Record whether translations are maintained internally, reviewed manually, or prepared for external translator/community contribution. | Maintenance expectations are explicit before new strings start drifting. | medium |

## Recommended Implementation Order

1. `GLOC-001` through `GLOC-005`
2. `GLOC-101` through `GLOC-105`
3. `GLOC-201` through `GLOC-207`
4. `GLOC-301` through `GLOC-306`
5. `GLOC-401` through `GLOC-405`
6. `GLOC-501` through `GLOC-507`
7. `GLOC-601` through `GLOC-605`
8. `GLOC-701` through `GLOC-705`

The order intentionally separates infrastructure, translation, terminology QA, runtime coverage,
layout hardening, browser QA, and release documentation so each one-off task can be reviewed
without hiding translation quality problems inside broad implementation work.
