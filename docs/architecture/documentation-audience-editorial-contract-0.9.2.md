# BPM 0.9.2 Documentation Audience And Editorial Contract

Date: 2026-07-17
Status: active contract
Backlog item: `BPM092-M2-06`

## Audience Boundary

Product documentation is written for the person using, operating, integrating, or reviewing BPM.
It is not a conversation with the project developer and not an implementation diary.

| Audience | DITA audience and content purpose | Must include | Must not include |
| --- | --- | --- | --- |
| User | `user` | UI task, expected result, relevant state/consequence, recovery where the user can act. | Maintainer procedure, source-tree/internal artifact instruction, roadmap, or generic product tutorial pasted into every route. |
| Administrator / DevOps | `administrator devops` | Deployment, operation, update, probe, rollback, support boundary, and environment prerequisites. | Claims of packaged/service/HA support that BPM does not provide, or instructions addressed to a developer. |
| API integrator | `integrator` (normally with `administrator devops`) | API contract, authentication/authorization boundary, request/result semantics, idempotency/concurrency or error/recovery behavior where applicable. | An undocumented endpoint promise, implementation status commentary, or product-user instructions unrelated to the API. |
| Security reviewer | `security-reviewer` where technically necessary | CIS/policy evidence, source/provenance, compliance limitation, and verification boundary. | A claim that BPM certification or export proves runtime compliance. |

Audience attributes are intentional metadata, not a substitute for readable prose. A topic may name
multiple real audiences, but its title, prerequisites, steps, results, and warnings must be useful
to each named audience.

## Product Documentation Rules

1. Address the relevant reader by role only when it clarifies the action: for example,
   “Administrators run …” or “If the API client receives …”. Do not address “the maintainer”,
   “the developer”, “the implementer”, or a backlog/task owner in rendered product documentation.
2. State the current supported boundary as a product fact: for example, a documented source-install
   scope, unsupported native service, or verified platform boundary. Do not write “not implemented
   yet”, “planned”, “will be replaced”, “this task adds”, “we have done”, or release-progress notes.
3. Do not expose source-workflow labels, local artifact paths, generated-output instructions, test
   commands, or review ownership to end users unless the topic is specifically for an
   administrator/DevOps/API-integrator and the item is a supported operational command.
4. Keep task instructions complete where they are needed: prerequisite, action, expected result,
   warning/consequence, and recovery remain in the topic. Compact UI work is not permission to
   delete user-facing documentation explanations.
5. Product documentation uses current UI names, one BPM product version, and manifest-backed
   links. It does not display a separately owned documentation version.
6. Maintained engineering material—backlogs, release contracts, audits, source-generation notes,
   evidence records, and runbooks—belongs outside rendered product DITA and may address maintainers
   when its audience is explicitly internal.

## Editorial Dispositions

| Finding in product DITA or portal chrome | Required disposition |
| --- | --- |
| Direct address to developer/maintainer, review assignment, task/backlog narration, or “we implemented” prose | Remove or rewrite for the actual user/admin/DevOps/API audience. |
| “Not yet”, “planned”, “future”, “will be replaced”, or other implementation-progress narration | Remove. If a limitation matters, replace it with a precise present-tense supported/unsupported boundary and available recovery path. |
| Unsupported-production or conditional-host boundary | Retain as a factual limitation, with no roadmap promise and no claim that unverified evidence proves support. |
| UI tutorial text duplicated from a control label/action | Remove from UI; retain or improve the corresponding task topic when the workflow needs explanation. |
| Technical/API/compliance condition required to make a safe decision | Retain, using concise role-appropriate prose. |
| Internal source path, test command, or generated-artifact detail in user documentation | Remove or replace with the supported user/admin action; retain only in internal runbooks/evidence. |

## Locale And Title Quality

English source is not a grammar template for other locales. Every visible title, short description,
heading, caption, alt text, button/label, empty/error/recovery state, and contextual-help label is
reviewed in `en`, `ru`, `de`, `zh-CN`, `fr`, and `es-ES`.

The normative per-locale grammar, capitalization, punctuation, title, instruction, and UI-name
rules are in the [locale editorial style policy](documentation-locale-editorial-style-0.9.2.md).
That policy cites the terminology authority and available language references; it explicitly
prohibits word-for-word transfer of English grammar.

- Russian documentation headings use idiomatic nominal forms for reference/task titles where that
  is the natural convention, for example `Изменение языка интерфейса`, not the English-calqued
  infinitive `Изменить язык интерфейса`. An imperative is allowed only where native Russian
  procedure style makes it clearly appropriate.
- German, Simplified Chinese, French, and Spanish follow their own reviewed technical-writing and
  heading conventions. They must not mechanically imitate English word order or Russian nominal
  style.
- Allowed residual English is limited to brands, standard abbreviations, identifiers, commands,
  paths, APIs, and deliberate placeholders covered by the locale terminology authority. Ordinary
  English prose, half-translated constructions, and false cognates fail review.
- Localized text must preserve placeholders, policy identifiers, command literals, link targets,
  and the same user-visible meaning without artificially increasing UI density.

## Required Review Evidence

M10 records a locale-aware editorial review with, for every changed or flagged topic:

1. topic ID, DITA path, audience metadata, locale, and visible element type;
2. finding category: audience, maintainer/progress narration, title style, ordinary-English carryover,
   terminology, support-boundary accuracy, or UI-name drift;
3. before/after text summary and the native-language rationale; and
4. reviewer role or accountable locale-review source, result, and any accepted factual boundary.

Automated checks cover structural audience metadata, prohibited high-signal narration, source/built
locale parity, placeholders, target/link validity, and visible-English regressions. Human-oriented
review is still required to establish natural heading/prose quality; a passing string scan is not
evidence that a translation reads naturally.

## Release Conditions

M10 may close only when product DITA and generated portal chrome contain no unreviewed
maintainer/developer address or implementation-progress narration, all factual support boundaries
remain accurate, and every active locale has recorded title/prose review evidence. M11 updates the
authoring/runbook guidance so that the boundary remains enforceable.
