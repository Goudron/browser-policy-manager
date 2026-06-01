# Locale Ownership

Date: `2026-06-01`

Backlog item: `GLOC-705`

Applies to locales: `en`, `ru`, `de`, `zh-CN`, `fr`, `es-ES`

Primary runbook: `docs/locale_update_runbook_2026-06-01.md`

Primary glossary: `docs/ui_locale_glossary_global_2026-05-29.md`

## Current Ownership Model

BPM is currently maintained by a single project maintainer, Valery Ledovskoy, with AI-assisted
implementation and review during development. There is no separate translator team, localization vendor, or open community translation process for this project at the time of the `0.8.0` locale expansion.

## Responsibilities

| Area | Owner | Current process |
|---|---|---|
| English source copy | Project maintainer | Write or approve source strings in `app/i18n/en.json` before localization. |
| Russian localization | Project maintainer | Manual review against product intent and Mozilla/SUMO terminology where applicable. |
| German localization | Project maintainer | Manual review with glossary, Pontoon/SUMO evidence, locale tests, and browser QA. |
| Simplified Chinese localization | Project maintainer | Manual review with glossary, Pontoon/SUMO evidence, script/layout checks, locale tests, and browser QA. |
| French localization | Project maintainer | Manual review with glossary, Pontoon/SUMO evidence, locale tests, and browser QA. |
| Spanish (Spain) localization | Project maintainer | Manual review with glossary, Pontoon/SUMO evidence, locale tests, and browser QA. |
| Glossary and terminology decisions | Project maintainer | Record accepted terms in `docs/ui_locale_glossary_global_2026-05-29.md`. |
| Locale QA and release readiness | Project maintainer | Follow `docs/locale_update_runbook_2026-06-01.md` before release. |

## External Contributions

External or community translation contributions are not a separate maintained workflow yet. If a
future contributor proposes locale copy, the project should treat it as a normal code/documentation
change owned by the project maintainer until a dedicated contribution policy exists.

Before accepting external locale text:

- compare it against the English source intent;
- verify Mozilla and Firefox terms through Pontoon/SUMO when applicable;
- preserve placeholders and technical identifiers exactly;
- run the locale quality tests and relevant browser QA from the runbook;
- update the global glossary or audit notes when a term decision changes.

## Drift Policy

Locale drift is handled during ordinary feature work. Any pull or local change that adds, removes,
or changes an English UI string must update all active runtime catalogs in the same change, or record
why a locale is intentionally left as `TBD`/`needs-review` in the global glossary or an audit note.

A locale remains first-class only while it:

- has key parity with English;
- has placeholder parity with English;
- keeps documented technical identifiers stable;
- passes accidental-English guards;
- follows the current global glossary;
- passes relevant browser workflow and viewport checks when visible UI changes.

## Future Revisit Trigger

Revisit this ownership document if BPM adds regular external contributors, a translation platform,
community localization intake, or a release process that delegates locale review outside the single
maintainer workflow.
