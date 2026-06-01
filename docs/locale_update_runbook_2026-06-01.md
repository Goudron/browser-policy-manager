# Locale Update Runbook

Date: `2026-06-01`

Backlog item: `GLOC-703`

Applies to locales: `en`, `ru`, `de`, `zh-CN`, `fr`, `es-ES`

Primary glossary: `docs/ui_locale_glossary_global_2026-05-29.md`

Mozilla terminology workflow: `docs/mozilla_terminology_verification_workflow_2026-05-29.md`

Placeholder and identifier rules: `docs/locale_placeholder_identifier_rules_2026-05-29.md`

Visible English allowlists: `docs/locale_visible_english_allowlists_2026-05-30.md`

Locale ownership: `docs/locale_ownership_2026-06-01.md`

## Goal

Use this runbook whenever BPM UI copy, locale catalogs, Mozilla terminology, or locale QA
contracts change. The goal is to keep every locale first-class: complete keys, preserved
placeholders, Mozilla-style terms, no accidental English prose, and no browser workflow regressions.

## 1. Define The Change

1. Decide whether the change starts from English source copy or from a target-locale correction.
2. If English source copy changes, update `app/i18n/en.json` first and treat it as the source of
   truth for the other catalogs.
3. If a target locale changes without an English source change, record why the locale-specific term
   is being corrected.
4. Check whether the change touches Firefox, Mozilla, browser UI, account, add-on, privacy,
   permission, update, translation, AI, VPN, policy, preference, CIS, validation, or export terms.

## 2. Check Terminology Before Editing Broadly

1. Start from `docs/ui_locale_glossary_global_2026-05-29.md`.
2. If the term is already present and marked as accepted, reuse the glossary wording.
3. If the term is missing, `TBD`, or ambiguous, follow
   `docs/mozilla_terminology_verification_workflow_2026-05-29.md`.
4. Verify Mozilla terms in Pontoon and SUMO before freezing the target wording.
5. Record any new accepted term in the global glossary, not in the historical EN/RU glossary.
6. If Pontoon and SUMO do not provide target-locale evidence, record the fallback decision in the
   relevant locale audit note or a new audit note.

## 3. Edit Locale Catalogs

1. Keep all active catalog files in sync:
   - `app/i18n/en.json`
   - `app/i18n/ru.json`
   - `app/i18n/de.json`
   - `app/i18n/zh-CN.json`
   - `app/i18n/fr.json`
   - `app/i18n/es-ES.json`
2. Preserve key order when practical so diffs remain reviewable.
3. Preserve placeholders exactly, including braces and casing.
4. Preserve policy keys, preference keys, file names, API paths, URLs, extension IDs, JSON literals,
   schema labels, and brand names according to
   `docs/locale_placeholder_identifier_rules_2026-05-29.md`.
5. Do not leave ordinary English prose in non-English catalogs. English is allowed only when it is a
   documented brand, technical token, or locale-specific exception from the glossary/allowlist.
6. Keep copyright and license identity stable across locales:
   - `Browser Policy Manager`
   - `Valery Ledovskoy` / `Валерий Ледовской`
   - `Mozilla Public License 2.0`

## 4. Update Documentation Evidence

Update documentation when the change affects terminology, QA expectations, or release behavior:

| Change type | Documentation target |
|---|---|
| New or changed Mozilla/Firefox term | `docs/ui_locale_glossary_global_2026-05-29.md` and the relevant locale audit note |
| Placeholder, identifier, or technical-token rule | `docs/locale_placeholder_identifier_rules_2026-05-29.md` |
| Accidental-English exception | `docs/locale_visible_english_allowlists_2026-05-30.md` |
| Runtime/browser workflow QA change | the relevant `docs/*_audit_*.md` file for that backlog item |
| Release-facing locale support change | `README.md` and release notes/changelog when present |

## 5. Run Fast Locale Checks

Run the narrow locale checks first:

```bash
.venv/bin/pytest -q tests/test_locale_catalogs.py tests/test_locale_visible_english_allowlists.py tests/test_ui_runtime_i18n_contract.py
```

When the change affects glossary, terminology, or locale documentation, also run:

```bash
.venv/bin/pytest -q tests/test_ui_locale_glossary.py
```

When the change affects All settings search/filter strings or runtime-generated counts, also run:

```bash
.venv/bin/pytest -q tests/test_all_settings_search_filter_i18n.py tests/test_runtime_count_i18n.py
```

## 6. Run Browser And Workflow QA When UI Surfaces Change

Use browser or workflow checks when the change affects visible UI layout, locale switching,
import/edit/export, or route-specific strings:

```bash
.venv/bin/pytest -q tests/test_chromium_locale_smoke_matrix_contract.py tests/test_locale_viewport_overflow_contract.py
```

For locale switching and localized profile workflows:

```bash
.venv/bin/pytest -q tests/test_locale_switching_regression_contract.py tests/test_localized_import_edit_export_workflow_contract.py
```

For a focused runtime workflow check after profile UI changes:

```bash
.venv/bin/pytest -q tests/test_web_profiles_page.py tests/test_ui_smoke_profile_workflow.py
```

## 7. Final Quality Gate

Before merging or tagging a locale release, run the standard project gate:

```bash
.venv/bin/mypy app
.venv/bin/ruff check .
.venv/bin/pytest -q --cov=app --cov-report=term-missing
```

The expected coverage result for the app surface is `TOTAL 100%`. If coverage drops below 100%,
add or update tests before accepting the locale change.

## 8. Review Checklist

- English source copy is clear and translator-friendly.
- Every active locale has the same key set as English.
- Placeholder sets match English for every changed key.
- Technical identifiers are preserved exactly.
- Mozilla terms match the global glossary or have fresh Pontoon/SUMO evidence.
- Non-English catalogs do not contain accidental English prose.
- Locale-specific English exceptions are documented in the allowlist.
- Browser-visible strings fit primary desktop and mobile surfaces when layout is affected.
- README or release notes are updated when supported-locale behavior changes.

## 9. Handoff Notes

When handing a locale change to review, include:

- the affected locale codes;
- whether English source copy changed;
- the glossary rows or audit notes touched;
- the exact pytest/mypy/ruff commands run;
- any browser QA or screenshot review performed;
- any known `TBD` or `needs-review` terminology left intentionally unresolved.

## 10. Ownership

Current locale ownership is documented in `docs/locale_ownership_2026-06-01.md`. BPM currently uses
a single-maintainer, manual-review model for all six active locales. External or community translation contributions are not a separate maintained workflow yet; treat any proposed locale copy
as a normal project change that must pass this runbook before acceptance.
