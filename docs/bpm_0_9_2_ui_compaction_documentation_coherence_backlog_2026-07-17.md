# BPM 0.9.2 UI Compaction And Documentation Coherence Backlog

Date: 2026-07-17

This backlog defines the BPM 0.9.2 work for making the product interface substantially more compact,
with an approximate fivefold reduction in non-essential explanatory UI copy and the space it consumes.
The work covers Library, Guided editor, All settings, JSON editor, the shared editor chrome, adjacent
Compare UI, and the documentation portal. Explanations that belong in product documentation move
there; ambiguous controls receive localized, keyboard-accessible circled-info links to stable BPM
documentation targets where needed.

The documentation portal becomes an integral BPM surface. Its product header, visual language,
locale and theme controls, responsive behavior, and version ownership must match the main product
UI. BPM has one product version: documentation may carry derived artifact metadata for compatibility,
but it must not display or maintain an independent documentation version.

Product source, UI copy, README, changelog, and maintained documentation use English as the primary
product language. Maintainer chat may be Russian, but implementation copy must not switch to Russian
unless the task is explicitly about Russian localization. English remains the source locale; `ru`,
`de`, `zh-CN`, `fr`, and `es-ES` must ship content-equivalent peers written according to each
language's own documentation conventions rather than as grammatical copies of English.

## Scope Summary

- Target BPM version: `0.9.2`.
- Compact epic id: `BPM092`.
- Scope boundary: product UI copy reduction and layout compaction; shared editor chrome redesign;
  contextual documentation links; documentation header and theme convergence; single BPM version
  ownership; documentation search-filter state stability; audience-facing DITA cleanup; localized
  title and prose quality; Firefox 153 three-channel schema refresh with dual ESR support; focused
  contracts, browser checks, README, changelog, and release metadata.
- Release risk: high, because the work changes shared templates and CSS, three editor modes, Library,
  Compare, schema conversion/loading/migration, three Firefox channels, six UI locale catalogs,
  generated documentation shell code, search state, six DITA locale trees, UI-target maps,
  documentation tests, and browser-visible responsive behavior.
- Primary outcome: Library and all three profile editors expose labels, values, actions, and current
  state without repeating nearby meaning or surrounding routine controls with instructional prose.
- Density outcome: measured non-essential explanatory prose and its occupied layout area are reduced
  to roughly one fifth of the accepted baseline in aggregate across the primary product surfaces;
  per-surface exceptions require a recorded safety, accessibility, or unavoidable-comprehension reason.
- Documentation outcome: moving between BPM and its documentation no longer feels like entering a
  separate product, and documentation content addresses users, administrators, DevOps operators, and
  API integrators rather than the BPM maintainer or the implementation backlog.
- Search outcome: submitting, restoring, clearing, or rendering a documentation search never opens
  an advanced filter panel that the user left collapsed.
- Follow-up UI outcome: the shared header shows the supported Firefox Release/ESR versions beside
  the BPM version and renders the profile count as two concise, localized lines; Library actions and
  filters follow the profile-table reading order; Guided step content retains a consistent inner
  left inset after layout compaction.
- Schema outcome: BPM supports Firefox Release 153, ESR 153.0, and ESR 140.13 as distinct channels;
  Release 152 profiles upgrade to Release 153 and ESR 140.12 profiles upgrade to ESR 140.13 without
  treating either supported ESR as an alias of the other.

## Current-State Assessment

- BPM 0.9.1 is the current product version in package metadata and active product/documentation
  contracts. The 0.9.2 transition must preserve 0.9.1 as release history rather than rewriting it.
- The main product already renders one shared Jinja header through
  `app/templates/profiles/_page_header.html`, but that header includes a product subtitle plus
  explanatory locale and theme hints. For example, the locale control displays both the label and
  the redundant explanation "UI language".
- The Library and editor catalogs contain many visible `subtitle`, `hint`, `body`, `copy`, `note`,
  and helper strings. The Library guidance equivalent to "Open an existing profile or start a new
  draft..." is a confirmed example of routine workflow prose that belongs in documentation, not in
  the persistent interface.
- The shared editor chrome currently repeats profile name, ID, schema, state, validation state, mode
  explanations, and save-first guidance across a large panel. Each of the three editor routes inherits
  this vertical cost before its actual work area begins.
- Guided editor templates contain dense section introductions, preset descriptions, field hints, and
  outcome explanations. All settings has route, mode, list, category, review, context, and utility
  explanatory blocks. JSON editor repeats its purpose and workflow around an already self-describing
  editor. A classification contract is needed so removing prose does not also remove functional state,
  consequences, validation, or accessible names.
- Compare is not one of the three editor types, but it is an adjacent user-visible BPM surface and must
  follow the same no-duplicate-copy rule instead of retaining a visibly older density model.
- The documentation portal currently builds a separate header inside
  `documentation/tools/build_docs.py`. It uses documentation-specific markup and shows localized text
  such as `BPM 0.9.1 · Documentation 0.9.1`, while the main UI uses the shared compact product header.
- Documentation version values are repeated in visible labels, generated manifest/search fields,
  fixtures, state keys, and validation code. They must be audited before collapsing ownership to the
  BPM version so compatibility contracts are changed deliberately rather than by string replacement.
- Documentation search currently calls its expansion function after filter changes, Enter, submit,
  and URL-state hydration. Therefore a query or result render can reopen filters even when the user
  intentionally collapsed them.
- Follow-up visual review found that the compact header lost the supported Firefox version pair and
  collapsed the profile count into an ungrammatical line, Library filters precede its action block
  instead of the table they affect, and Guided content begins flush against its content column after
  copy removal.
- The current schema-update workflow assumes exactly one Release/ESR pair. Firefox 153 starts a
  transition period in which BPM must support Release 153 and two distinct ESR channels, so the
  converter, schema registry, migration rules, UI labels, locale catalogs, and product documentation
  need an explicit three-channel contract.
- Product DITA contains maintainer-facing recovery wording such as "for maintainer review". Some
  Administrator topics describe work as "planned but not implemented yet" or as future-release work;
  supported and unsupported boundaries are useful, but project-progress narration is not.
- Russian task titles include direct infinitive calques such as `Изменить язык интерфейса`,
  `Сохранить изменения профиля`, and `Открыть сохраненный профиль в редакторе`. Russian documentation
  normally needs nominal headings such as `Изменение языка интерфейса`. Other locales require their
  own editorial review rather than inheriting the English title grammar mechanically.

## Non-Goals And Assumptions

- Do not change profile persistence, API semantics, Firefox schema behavior, CIS logic, import/export
  formats, validation rules, or search ranking merely to simplify presentation. The explicit Firefox
  153 three-channel support work in Milestone 12 is the sole exception and must follow its reviewed
  support-and-migration matrix.
- Do not interpret compactness as removal of control labels, current values, actionable validation,
  error details, destructive-action consequences, conflict recovery, meaningful empty states, loading
  state, unsaved-change warnings, or screen-reader-only names and announcements.
- Do not hide required safety or accessibility information behind hover-only tooltips. Circled-info
  links must be keyboard reachable, have localized accessible names, and resolve without JavaScript
  to stable, locale-aware BPM documentation targets.
- Do not require every individual screen to hit an exact 80% reduction. The approximate fivefold goal
  is an aggregate direction with per-surface budgets; safety, accessibility, and irreducible domain
  meaning take precedence and must be recorded as explicit exceptions.
- Do not rebuild the profile editors, documentation portal, DITA toolchain, navigation tree, search
  index, or locale architecture from scratch. Reuse the established ownership boundaries unless a
  recorded contract proves a narrow shared component is required.
- Do not remove filter capabilities, facets, deterministic offline search, search URL state, recent
  query behavior, or result accessibility while fixing filter-panel expansion.
- Do not remove honest support boundaries from Administrator/DevOps documentation. Rewrite them as
  current supported/unsupported product facts, without speaking to the maintainer, narrating backlog
  progress, or promising a future release.
- Do not blanket-remove the word "developer" where API integrators are the real audience. Remove only
  maintainer-directed, repository-internal, or implementation-status content from product docs.
- Do not force Russian nominal-heading grammar onto German, French, Spanish, or Chinese. Each locale
  needs a recorded native documentation-title convention and a human review outcome.
- Do not translate stable identifiers, commands, paths, JSON keys, API routes, Firefox policy IDs,
  CIS recommendation IDs, product names, brand names, or allowlisted abbreviations.
- Do not hand-edit `documentation/build/`, generated locale catalogs, caches, screenshots, or other
  generated output. Change owned sources and regenerate through maintained commands.
- Assume all six active locales are release deliverables and that browser/Selenium checks require
  immediate sandbox escalation during backlog execution.

## Model And Reasoning Calibration

Task models were checked on 2026-07-17 against the official GPT-5.6 model guidance. `GPT-5.6 Luna`
is used for deterministic metadata, index, and command tasks; `GPT-5.6 Terra` is the minimum for
focused UI, documentation, localization, and test work. No task currently requires `GPT-5.6 Sol` as
its safe minimum: the architecture is broad but already bounded by established BPM patterns and is
split into focused tasks. Reasoning uses only `Light`, `Medium`, `High`, and `Extra High` as required
by the project runbook.

## Milestone 1: Version Transition And Release Anchors

Goal: establish `0.9.2` as the active target and make version ownership explicit before UI or
documentation implementation begins.

| ID | Task | Essence | Model | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- | --- |
| `BPM092-M1-01` | Update product version surfaces to `0.9.2`. | Move package metadata, application settings, docs-index heading, active architecture/release-readiness anchors, UI-visible product version, tests, and release constants to the target version. | GPT-5.6 Luna | Light | Runtime, package metadata, tests, main UI, docs index, active release evidence, and derived documentation metadata agree on `0.9.2`; `0.9.1` remains only in history, archives, versioned contracts, or explicit migration context. |
| `BPM092-M1-02` | Refresh local editable-package metadata. | Reinstall or refresh the editable BPM package metadata after the version transition. | GPT-5.6 Luna | Light | `pip show browser-policy-manager` and equivalent local probes report `0.9.2` with no stale editable `0.9.1` metadata. |
| `BPM092-M1-03` | Check external workflow dependency currency. | Review Python, frontend vendor packages, documentation toolchain components, browser drivers, and test/dev dependencies relevant to this epic. | GPT-5.6 Terra | Medium | A bounded note records every pin/minimum; necessary updates are implemented and verified here or split into an approved pre-feature task, and no floating upgrade is hidden in UI or docs work. |
| `BPM092-M1-04` | Open the `0.9.2` changelog entry. | Add a non-final target-version section while preserving older release history. | GPT-5.6 Luna | Light | `CHANGELOG.md` contains a `0.9.2` landing section above older entries and no previous release note is overwritten. |
| `BPM092-M1-05` | Guard README against target-version copy. | Keep README as durable current-state product documentation rather than a release tracker. | GPT-5.6 Luna | Light | README has no `0.9.2` target anchor, planned-for-version copy, release-history entry, or completion placeholder. |
| `BPM092-M1-06` | Record the 0.9.2 release contract. | Map UI density, header parity, version ownership, search state, editorial, locale, documentation, and browser deliverables to evidence and commands. | GPT-5.6 Terra | High | A maintained contract identifies each release blocker, evidence owner, focused check, and final gate, including explicit exceptions to the density target. |
| `BPM092-M1-07` | Audit active release naming and duplicated documentation version sources. | Find active code, docs, fixtures, and release-readiness text that treats `0.9.1` as current or documentation version as independently owned. | GPT-5.6 Terra | Medium | A bounded update list separates active sources from historical/versioned records and classifies each documentation-version field as remove, derive, or retain-for-compatibility. |

## Milestone 2: Baseline Inventory And Compaction Contracts

Goal: turn "remove everything unnecessary" and "roughly five times smaller" into auditable rules
before changing shared templates or locale strings.

| ID | Task | Essence | Model | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- | --- |
| `BPM092-M2-01` | Inventory rendered explanatory UI copy. | Capture visible headings, labels, prose, hints, duplicate status, and occupied regions for Library, Guided, All settings, JSON, Compare, and documentation at representative states and viewports. | GPT-5.6 Terra | High | The inventory maps every rendered prose node to its source template/key and records word count plus layout footprint without scanning generated/vendor output. |
| `BPM092-M2-02` | Define the UI copy classification contract. | Classify text as essential label/value/action/state, safety/recovery/accessibility, removable explanation, duplicate meaning, or documentation candidate. | GPT-5.6 Terra | High | Every inventoried item has one disposition; the contract explicitly protects errors, validation, consequences, conflict recovery, empty/loading state, accessible names, and domain distinctions. |
| `BPM092-M2-03` | Define per-surface density budgets. | Translate the approximate fivefold goal into aggregate and per-surface budgets for explanatory words, prose nodes, header/editor-chrome height, and first-work-area position. | GPT-5.6 Terra | High | The aggregate target is about 20% of baseline non-essential prose/area; each exception names the protected information and reason, and no safety/accessibility text counts as removable debt. |
| `BPM092-M2-04` | Map removed explanations to documentation. | Determine which removed strings need no replacement, which existing DITA topic is sufficient, and which genuine comprehension gap needs a new localized topic or circled-info target. | GPT-5.6 Terra | High | A locale-aware UI-target map covers every required help link, avoids link proliferation, and never moves essential inline feedback into documentation. |
| `BPM092-M2-05` | Define the unified BPM header contract. | Specify one semantic, visual, responsive, locale, theme, product-name, product-version, browser-title, and navigation contract for main UI and documentation. | GPT-5.6 Terra | High | The contract defines normalized DOM roles/slots, browser-title naming, token ownership, focus order, narrow layouts, active-surface behavior, and how the generated portal proves parity with the Jinja header. |
| `BPM092-M2-06` | Define the documentation audience and editorial contract. | Separate user/admin/DevOps/API-integrator content from maintainer instructions and implementation-progress narration. | GPT-5.6 Terra | High | The contract preserves current support boundaries, forbids maintainer address and roadmap narration in product DITA, and defines locale-specific title/prose review evidence. |
| `BPM092-M2-07` | Define documentation search panel state. | Make advanced-filter visibility an independent user-controlled state rather than a side effect of query/results/filter data. | GPT-5.6 Terra | Medium | Only the explicit filter toggle changes expansion; submit, Enter, clear, result render, URL hydration, browser history, and active filters preserve the user's collapsed/expanded choice. |
| `BPM092-M2-08` | Add baseline guard tests and fixtures. | Encode the accepted inventory, density measurements, copy dispositions, header contract, search state, and editorial rules before implementation where practical. | GPT-5.6 Terra | High | Focused tests fail for reintroduced explanatory blocks, unclassified visible prose, header drift, independent visible docs version, search-triggered expansion, and unreviewed maintainer/progress language. |

## Milestone 3: Shared Product Header And Compact UI Foundations

Goal: reduce persistent chrome once and give every BPM surface the same compact, accessible frame.

| ID | Task | Essence | Model | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- | --- |
| `BPM092-M3-01` | Compact the shared main UI header. | Remove the persistent product subtitle and redundant locale/theme explanations while preserving product identity, BPM version, documentation access, and required workspace state. | GPT-5.6 Terra | Medium | Library, Guided, All settings, JSON, and Compare render the accepted compact header with no duplicate label/explanation pairs. |
| `BPM092-M3-02` | Compact locale and theme controls. | Use concise visible labels or accessible names and a single control value for language and theme. | GPT-5.6 Terra | Medium | Controls remain understandable, keyboard reachable, screen-reader named, touch usable, and stable across all six locales without helper-line height. |
| `BPM092-M3-03` | Establish shared compact spacing and typography tokens. | Consolidate header, section, field, action, status, and help-link density rules in maintained CSS ownership. | GPT-5.6 Terra | High | All primary surfaces use coherent compact tokens; focus rings, target sizes, contrast, zoom, reduced motion, and long localized labels remain usable. |
| `BPM092-M3-04` | Remove obsolete shared copy and layout hooks. | Delete retired English source strings, localized peers, catalog-order entries, selectors, and DOM wrappers after consumers move. | GPT-5.6 Luna | Medium | Locale catalogs remain parity-complete, no active code references removed keys/classes, and hidden duplicate prose is not retained except legitimate accessible text. |
| `BPM092-M3-05` | Verify the shared header across states and viewports. | Add focused template, locale, accessibility, and browser checks for the compact main header. | GPT-5.6 Terra | High | All routes, six locales, light/dark/system themes, desktop/narrow widths, 200% zoom, and keyboard focus order pass without overflow or lost functionality. |
| `BPM092-M3-06` | Restore compact header version and profile-count semantics. | Show the supported Firefox Release/ESR version pair next to the BPM version and render the workspace profile count as two localized lines rather than an interleaved label/count phrase. | GPT-5.6 Terra | High | Header version data comes from the supported schema catalog, count grammar is correct in every locale, and Library, Guided, All settings, JSON, and Compare retain a compact responsive header. |
| `BPM092-M3-07` | Clarify and reflow supported Firefox versions in the shared header. | Render a localized statement about Firefox ESR and Release support below the BPM title, at version-scale typography, with mobile-safe wrapping. | GPT-5.6 Terra | High | The BPM name remains the sole large heading; every locale shows the current-release support statement and schema-derived ESR/Release pair on the second line; narrow layouts have no overflow. |

## Milestone 4: Library And Adjacent Compare Compaction

Goal: make profile discovery and comparison start with data and actions instead of explanatory panels.

| ID | Task | Essence | Model | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- | --- |
| `BPM092-M4-01` | Compact the Library heading, filters, and actions. | Remove Library workflow narration and duplicate filter/action headings; keep concise search, filter, sort, import, refresh, and new-draft controls. | GPT-5.6 Terra | High | The first profile rows appear materially earlier, all filters/actions remain named, and the accepted Library density budget passes. |
| `BPM092-M4-02` | Compact profile rows and lifecycle presentation. | Remove repeated row hints and redundant lifecycle prose while preserving name, schema, note, timestamps, state, validation, and actions. | GPT-5.6 Terra | High | Active/archived/current/invalid distinctions and destructive affordances remain unambiguous without instructional text on every row. |
| `BPM092-M4-03` | Simplify Library empty, clone, and destructive states. | Keep only actionable empty-state, clone-origin, conflict, archive/restore, and permanent-delete information. | GPT-5.6 Terra | High | Routine guidance moves to docs, but confirmations still state consequences and recovery where recovery exists; clone identity and name-conflict handling remain clear. |
| `BPM092-M4-04` | Align Compare with the compact UI contract. | Remove duplicate comparison introductions and selection instructions while retaining both profile selectors, differences, empty results, and state/value semantics. | GPT-5.6 Terra | Medium | Compare looks native to 0.9.2, meets the same header/density rules, and no comparison meaning or keyboard path is lost. |
| `BPM092-M4-05` | Verify Library and Compare behavior visually. | Run focused DOM, locale, responsive, and browser checks for populated, empty, filtered, archived, clone, and comparison states. | GPT-5.6 Terra | High | Functional workflows pass in all six locales and representative viewports; compact layout has no truncation, overlap, accidental hidden state, or unexplained icon-only action. |
| `BPM092-M4-06` | Reorder and compact Library controls. | Place refresh, new-draft, compare, and import actions before the filters; make the actions a compact responsive row or grid and put search, filters, and sort immediately above the profile table. | GPT-5.6 Terra | High | On desktop the control order is actions, filters, table; actions do not occupy one full row each, narrow layouts remain touch usable, and filters still update the table correctly. |

## Milestone 5: Shared Editor Chrome Compaction

Goal: replace the large profile/mode panel inherited by all three editors with the smallest useful
profile-context and action bar.

| ID | Task | Essence | Model | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- | --- |
| `BPM092-M5-01` | Redesign profile context as a compact bar. | Present current editor mode, profile name, schema selector/value, dirty/saved state, and essential actions without repeated ID/schema/context panels. | GPT-5.6 Terra | High | Guided, All settings, and JSON expose one compact context bar; repeated metadata is removed and the actual editor begins within the accepted vertical budget. |
| `BPM092-M5-02` | Compact cross-editor mode switching. | Replace three explanatory mode cards and their parent explanation with concise localized mode links/tabs and clear current state. | GPT-5.6 Terra | High | Guided, All settings, and JSON are directly reachable, current mode is programmatically exposed, and no mode description paragraph remains in persistent chrome. |
| `BPM092-M5-03` | Preserve unsaved-draft mode gating accessibly. | Replace the long save-first paragraph with concise disabled-state semantics and contextual help only if the reason is not otherwise clear. | GPT-5.6 Terra | Medium | Users and assistive technology can tell why unavailable modes cannot open and what action enables them without a persistent explanatory block. |
| `BPM092-M5-04` | Deduplicate editor status and lifecycle details. | Keep authoritative validation, saved/dirty, archived, clone-origin, and compliance state once; remove repeated summaries and instructional review prose. | GPT-5.6 Terra | High | State remains live and actionable, lifecycle/compliance facts are available when relevant, and schema/ID/state are not repeated in multiple editor-chrome regions. |
| `BPM092-M5-05` | Verify shared editor chrome in every route state. | Add focused tests for new/saved/clone/archived/dirty/invalid profiles across Guided, All settings, and JSON. | GPT-5.6 Terra | High | All three routes share the compact contract across six locales and narrow/desktop viewports; save, validate, format where applicable, and mode navigation still work. |

## Milestone 6: Guided Editor Compaction And Context Help

Goal: let controls, choices, and outcomes carry the Guided workflow while documentation owns routine
instruction and background explanation.

| ID | Task | Essence | Model | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- | --- |
| `BPM092-M6-01` | Apply copy dispositions to Guided sections. | Remove redundant section introductions, workflow narration, field hints, outcome prose, and repeated fine-tuning instructions according to the approved inventory. | GPT-5.6 Terra | High | Every removed/retained Guided string matches the classification contract and the aggregate Guided density budget passes. |
| `BPM092-M6-02` | Compact presets, toggles, and choice cards. | Prefer clear labels and current values over label-plus-paragraph cards; retain short differentiators only when options would otherwise be ambiguous. | GPT-5.6 Terra | High | Presets remain distinguishable without repetitive prose, selected state is obvious, and long localized labels wrap without recreating large cards. |
| `BPM092-M6-03` | Simplify step and section layout. | Reduce nested cards, duplicate kickers/headings, and empty spacing after copy removal while preserving progressive disclosure and task order. | GPT-5.6 Terra | High | Guided navigation, recommended/additional/raw boundaries, focus movement, and responsive flow remain intact with materially more controls visible per viewport. |
| `BPM092-M6-04` | Add only required Guided context links. | Connect ambiguous concepts to existing localized DITA targets and request new topics only for confirmed coverage gaps. | GPT-5.6 Terra | High | Circled-info links are sparse, consistent, accessible, locale aware, valid in every generated manifest, and do not duplicate obvious labels. |
| `BPM092-M6-05` | Clean Guided locale catalogs. | Remove retired keys and review retained concise labels across English plus five localized peers. | GPT-5.6 Terra | High | Catalog parity, placeholders, terminology, natural localized phrasing, and overflow contracts pass with no untranslated explanatory remnants. |
| `BPM092-M6-06` | Verify Guided workflows after compaction. | Run focused unit/contract and browser scenarios for every step, presets, manual controls, validation, save, and export. | GPT-5.6 Terra | Extra High | Guided behavior is unchanged, density evidence passes, and all six locales work at desktop/narrow widths without missing consequences or inaccessible help. |
| `BPM092-M6-07` | Restore Guided content inset. | Apply one shared inner left inset to the main content area of every Guided step after the stepper, without restoring retired explanatory containers. | GPT-5.6 Terra | Medium | Step headings, fields, cards, disclosures, review, and export content align to the same readable inset on desktop and narrow layouts; step navigation and horizontal-overflow checks remain green. |

## Milestone 7: All Settings Compaction And Context Help

Goal: make the full visual catalog dense enough for large inventories without weakening technical
state, validation, source, or detailed setting meaning.

| ID | Task | Essence | Model | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- | --- |
| `BPM092-M7-01` | Compact route, mode, filter, and inventory chrome. | Remove route/list explanations and mode-card bodies; retain Review, Configured, Catalog, search, source/state filters, counts, and pagination. | GPT-5.6 Terra | High | The settings inventory begins earlier, modes and filters remain self-evident, and counts/state are not duplicated in prose and badges. |
| `BPM092-M7-02` | Compact category and domain navigation. | Remove category/body paragraphs where names and counts provide sufficient distinction; use help only for genuine domain ambiguity. | GPT-5.6 Terra | High | Category scanning is denser, configured/attention/available meaning remains exposed, and each navigation target is accessible. |
| `BPM092-M7-03` | Compact review queues and setting details. | Remove routine handoff instructions and repeated review descriptions while preserving reasons, source, current value, schema support, validation, and available actions. | GPT-5.6 Terra | High | Technical review remains trustworthy and actionable for CIS/manual/raw/unknown/deprecated/invalid states without generic instructional prose. |
| `BPM092-M7-04` | Remove redundant context and utility walkthroughs. | Eliminate profile-details/JSON/validation step cards and explanations already represented by editor navigation and actions. | GPT-5.6 Terra | Medium | All settings no longer contains a parallel user manual; necessary cross-editor actions remain directly reachable and correctly labeled. |
| `BPM092-M7-05` | Complete setting-level contextual documentation coverage. | Reuse the existing per-setting help contract and add/update localized targets only where compaction exposes a real comprehension gap. | GPT-5.6 Terra | High | Every displayed policy/preference keeps a valid help disposition, missing targets fail closed, and help icons do not crowd rows or replace technical state. |
| `BPM092-M7-06` | Verify enterprise-scale All Settings behavior. | Run focused data, locale, accessibility, performance, and browser checks with large inventories and every review state. | GPT-5.6 Terra | Extra High | Search, filters, bounded lists, details, edits, reset/remove, raw fallback, contextual help, and responsive layout pass with the accepted density budget. |

## Milestone 8: JSON Editor Compaction

Goal: let the document editor dominate the route while retaining exact, actionable document state.

| ID | Task | Essence | Model | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- | --- |
| `BPM092-M8-01` | Remove redundant JSON editor introductions. | Delete the route-purpose paragraph, repeated document-view note, and explanations already covered by the JSON label and documentation. | GPT-5.6 Terra | Medium | The editor appears materially earlier and no persistent prose explains that a JSON editor edits `policies.json`. |
| `BPM092-M8-02` | Compact JSON actions and status. | Keep format, validate, save, download/export, dirty state, and precise parse/validation feedback in one concise action/status area. | GPT-5.6 Terra | High | Actions and state are shown once; success/error messages remain actionable and screen-reader announcements remain correct. |
| `BPM092-M8-03` | Add only required JSON context links. | Link import/export, schema validation, raw/unknown keys, and recovery documentation where an inline explanation was removed and ambiguity remains. | GPT-5.6 Terra | Medium | Links use the shared circled-info component, resolve in all locales, and do not obscure the editor or duplicate nearby actions. |
| `BPM092-M8-04` | Verify JSON editor workflows and density. | Run focused tests for valid/invalid JSON, formatting, schema errors, dirty navigation, save, download, locale, and responsive layout. | GPT-5.6 Terra | High | JSON behavior and Monaco accessibility remain intact, the route passes its compactness budget, and editor height is not consumed by empty retired containers. |

## Milestone 9: Unified Documentation Shell And Stable Search Filters

Goal: make documentation visibly and behaviorally part of BPM, with one product header and user-owned
advanced-filter visibility.

| ID | Task | Essence | Model | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- | --- |
| `BPM092-M9-01` | Implement product-header parity in generated documentation. | Make the portal shell emit the same normalized brand/title/version, locale/theme controls, action slots, focus order, and responsive structure as the shared main UI header. | GPT-5.6 Terra | High | Contract tests compare normalized semantics/slots and browser checks show an identical product header across Library, all three editors, Compare, and documentation. |
| `BPM092-M9-02` | Remove independent visible documentation versioning. | Delete labels such as `Documentation 0.9.1` and derive any compatibility-required artifact/search version from the single BPM product version source. | GPT-5.6 Terra | High | No page displays a separate docs version, no hand-maintained docs-version constant can drift, retained schema fields are derived and documented as compatibility metadata only, and `make docs-install-dev` installs the current portal artifact before handoff. |
| `BPM092-M9-03` | Converge documentation and product visual tokens. | Share or deterministically mirror header, control, focus, color, typography, spacing, border, and elevation decisions without editing generated output. | GPT-5.6 Terra | High | Documentation looks continuous with BPM in light/dark/system themes and at narrow widths; content-specific tree/article/search styles remain usable. |
| `BPM092-M9-04` | Align documentation header locale and theme behavior. | Use the same localized labels/accessible names, stored theme convention, option order, and long-label handling as product UI. | GPT-5.6 Terra | High | Six locales and three theme modes behave consistently across product/docs transitions with no duplicate explanation lines or lost selection. |
| `BPM092-M9-05` | Decouple search execution from filter expansion. | Remove implicit expansion from filter change, Enter, submit, clear, initial URL/recent-query hydration, results, and history updates. | GPT-5.6 Terra | High | A collapsed advanced panel stays collapsed through every search lifecycle event; an expanded panel stays expanded until the user toggles it. |
| `BPM092-M9-06` | Expose active filters while the panel is collapsed. | Add a compact localized active-filter count/summary and clear affordance if hidden active filters would otherwise be surprising. | GPT-5.6 Terra | Medium | Users can detect and clear active filters without forced expansion; screen readers receive the same state and result updates. |
| `BPM092-M9-07` | Verify documentation shell and search behavior. | Add unit/contract and real-browser coverage for headers, version ownership, themes, locales, search keyboard paths, URL/history state, filters, and CSP/offline behavior. | GPT-5.6 Terra | Extra High | All six locales pass desktop/narrow browser scenarios; no search event reopens filters, result ranking stays unchanged, and the portal remains deterministic and offline. |

## Milestone 10: Product Documentation Audience And Locale Editorial Quality

Goal: make product documentation speak naturally to its real audiences and remove source-language
grammar copied into localized headings.

| ID | Task | Essence | Model | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- | --- |
| `BPM092-M10-01` | Inventory maintainer and implementation-status leakage. | Audit English DITA and localized peers for maintainer address, repository/build internals presented to users, progress narration, planned/not-implemented phrasing, and future-release promises. | GPT-5.6 Terra | High | Each finding records guide, audience, locale peers, and disposition: remove, rewrite as current support boundary, move to maintainer docs, or retain as genuine API-integrator content. |
| `BPM092-M10-02` | Rewrite the English source for audience ownership. | Replace maintainer-review instructions and project-progress narration with user/admin/DevOps/support actions and current supported/unsupported facts. | GPT-5.6 Terra | High | English DITA contains no maintainer-directed or backlog-status prose; troubleshooting gives a real escalation role/evidence path and admin boundaries remain accurate without release promises. |
| `BPM092-M10-03` | Propagate audience-safe content to localized peers. | Update Russian, German, Chinese, French, and Spanish topics from the accepted English meaning using locale terminology authorities. | GPT-5.6 Terra | High | All locale peers are content-equivalent, natural, placeholder-safe, and free of translated maintainer/progress narration. |
| `BPM092-M10-04` | Define locale-specific heading and instruction style. | Record title grammar, capitalization, punctuation, imperative/nominal conventions, and UI-name treatment independently for each active locale. | GPT-5.6 Terra | High | The policy cites authoritative language/product conventions where available and explicitly rejects word-for-word transfer of English grammar. |
| `BPM092-M10-05` | Normalize Russian documentation headings. | Replace infinitive-calque task titles with idiomatic Russian nominal headings and fix adjacent agreement, aspect, punctuation, and UI terminology. | GPT-5.6 Terra | High | Cases including `Изменить язык интерфейса` become idiomatic headings such as `Изменение языка интерфейса`; a human Russian review records all accepted exceptions. |
| `BPM092-M10-06` | Review German editorial style. | Audit German headings and nearby instructions against the recorded German convention rather than copying English or Russian grammar. | GPT-5.6 Terra | High | German has a reviewed findings list, corrected source topics, and explicit evidence that imperative/nominal choices, capitalization, punctuation, and UI names are native and consistent. |
| `BPM092-M10-07` | Review Simplified Chinese editorial style. | Audit Simplified Chinese headings and nearby instructions against the recorded Chinese convention rather than copying English or Russian grammar. | GPT-5.6 Terra | High | Simplified Chinese has a reviewed findings list, corrected source topics, and explicit evidence that title structure, punctuation, terminology, and UI names are native and consistent. |
| `BPM092-M10-08` | Review French editorial style. | Audit French headings and nearby instructions against the recorded French convention rather than copying English or Russian grammar. | GPT-5.6 Terra | High | French has a reviewed findings list, corrected source topics, and explicit evidence that infinitive/nominal choices, capitalization, punctuation, and UI names are native and consistent. |
| `BPM092-M10-09` | Review Spanish editorial style. | Audit Spanish headings and nearby instructions against the recorded Spanish convention rather than copying English or Russian grammar. | GPT-5.6 Terra | High | Spanish has a reviewed findings list, corrected source topics, and explicit evidence that infinitive/nominal choices, capitalization, punctuation, and UI names are native and consistent. |
| `BPM092-M10-10` | Preserve stable navigation, search, and theme parity after editorial changes. | Regenerate titles, navigation labels, search documents, aliases, manifests, and UI targets without changing stable topic IDs/URLs; mirror the primary UI light/dark palette in the documentation shell and active navigation states. | GPT-5.6 Terra | High | Old valid targets remain resolvable or explicitly redirected, changed titles are searchable in every locale, contextual help links do not break, and active documentation-tree items use the primary UI’s translucent selected surface with readable theme-native text rather than white text on a light-green fill. |
| `BPM092-M10-11` | Add editorial drift gates and human QA evidence. | Add fail-closed inventories/tests for forbidden audience leakage and require recorded locale review for title/prose conventions that automation cannot judge. | GPT-5.6 Terra | High | Contracts catch known regressions without banning legitimate support/API terms; the release command is blocked until all six recorded human reviews are explicitly accepted. |

## Milestone 11: Product Documentation, README, And Maintenance Gates

Goal: make documentation sufficient for the compact UI and teach future changes not to reintroduce
the removed prose or editorial defects.

| ID | Task | Essence | Model | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- | --- |
| `BPM092-M11-01` | Update user documentation for the compact UI. | Revise Library, Guided, All settings, JSON, Compare, locale/theme, validation, editor switching, supported Firefox versions, profile-count presentation, and compact Library control order to match the shipped UI. | GPT-5.6 Terra | High | Users can complete every changed workflow from documentation without relying on text removed from the UI; obsolete screenshots/labels are corrected or blocked explicitly. |
| `BPM092-M11-02` | Author confirmed context-help gaps. | Add only the DITA topics/sections proven missing by the M2 help map and produce all six locale peers. | GPT-5.6 Terra | High | Every new circled-info target has audience-appropriate source, localized peers, stable IDs, navigation/search ownership, and focused tests. |
| `BPM092-M11-03` | Refresh UI-target maps, manifests, search, and screenshot evidence. | Regenerate documentation-owned target/search metadata and recapture only screenshots invalidated by changed visible UI. | GPT-5.6 Terra | High | All links resolve, manifests/search indexes are current, screenshot policy is satisfied, and generated output is produced only by maintained commands. |
| `BPM092-M11-04` | Update UI-copy and documentation authoring guidance. | Document the compact-copy classification, contextual-help threshold, product-audience boundary, single-version rule, and locale-specific heading review. | GPT-5.6 Terra | High | Maintained authoring/runbook guidance prevents explanatory copy, duplicate docs versioning, maintainer address, and English-grammar calques from returning silently. |
| `BPM092-M11-05` | Update locale and documentation drift gates. | Extend locale, screenshots, links/manifest/publishing, schema/CIS, Administrator/DevOps, integration, update, and release procedures where this epic changes their evidence. | GPT-5.6 Terra | High | Relevant runbooks require UI-copy classification, help-target parity, audience/style review, header parity, single-version derivation, and collapsed-filter regression checks. |
| `BPM092-M11-06` | Refresh README durable current-state copy if needed. | Update only descriptions of the now-compact UI and integrated documentation surface that remain durable product facts. | GPT-5.6 Terra | Medium | README is accurate after implementation, contains no release history or target marker, and preserves maintainer copyright plus email-topic/message-theme information. |
| `BPM092-M11-07` | Update the maintained docs index. | Register new maintained contracts, audits, and runbooks and keep generated product documentation outside the index. | GPT-5.6 Luna | Light | `docs/docs-index.md` lists every maintained file exactly once with a valid status and working relative link. |
| `BPM092-M11-08` | Run focused documentation completion checks. | Build all locales and validate DITA, editorial evidence, links, manifests, search, screenshots, contextual targets, header parity, version ownership, and authoring gates. | GPT-5.6 Terra | Extra High | The dedicated documentation milestone is complete and every focused documentation command passes before final quality begins. |
| `BPM092-M11-09` | Install the current documentation artifact for maintainer `make dev`. | After every change to product-documentation source, build tooling, generated-shell behavior, or a served documentation version surface, run `make docs-install-dev` before handoff. | GPT-5.6 Terra | Medium | The artifact consumed by the maintainer's subsequent `make dev` is rebuilt from the current source, reports the single current BPM version, and the task report records the successful install command. |

## Milestone 12: Firefox 153 Schema Refresh And Dual-ESR Support

Goal: replace the Firefox 152 / ESR 140.12 support pair with exactly three first-class BPM schema
channels: Firefox Release 153, Firefox ESR 153.0, and Firefox ESR 140.13. The two ESR channels are
concurrently supported; neither is a migration alias for the other.

| ID | Task | Essence | Model | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- | --- |
| `BPM092-M12-01` | Establish the Firefox 153 three-channel contract. | Verify the official Mozilla source artifacts and define the authoritative channel, provenance, compatibility-diff, UI-label, and persisted-profile migration matrix for `release-153`, `esr-153.0`, and `esr-140.13`. | GPT-5.6 Terra | High | The reviewed matrix distinguishes all three schemas; `release-152 → release-153` and `esr-140.12 → esr-140.13` are the automatic upgrade paths; `esr-153.0` is never an automatic ESR target; source provenance and policy differences are recorded. |
| `BPM092-M12-02` | Generate and load the three supported schemas. | Extend the converter and schema-loading contracts from one Release/one ESR pair to the declared three-channel matrix; generate each bundled schema from verified upstream input. | GPT-5.6 Terra | Extra High | `release-153`, `esr-153.0`, and `esr-140.13` have independent bundled JSON, exact metadata/provenance, loader support, and focused regression tests; no schema is copied or relabelled and no retired schema remains supported. |
| `BPM092-M12-03` | Migrate profile storage and runtime normalization. | Add the Alembic and runtime mappings specified by the approved matrix while preserving valid profiles already on either supported ESR. | GPT-5.6 Terra | Extra High | Existing `release-152` profiles migrate to `release-153`, `esr-140.12` profiles migrate to `esr-140.13`, valid `esr-153.0` and `esr-140.13` profiles remain unchanged, and Library GET remains read-only. |
| `BPM092-M12-04` | Expose the three-channel matrix in product UI and locales. | Update header, selectors, Library/filter/Compare/editor behavior, All settings availability, policy placement decisions, and all six source/runtime locale catalogs for the exact supported matrix. | GPT-5.6 Terra | High | Every product surface presents the three human-readable schemas consistently, each policy is available only on supported channels, no locale has an English fallback, and Guided remains scenario-first. |
| `BPM092-M12-04-01` | Close Firefox 153 nested-policy coverage gaps. | Reconcile release notes and Firefox Admin Docs with generated schemas, add every omitted documented nested field, localize its UI labels, and prove channel-specific availability before documentation work. | GPT-5.6 Terra | High | `ExtensionSettings.allowed_permissions` and the related Firefox 153 controls are accepted only by Release 153 and ESR 153.0, rejected by ESR 140.13, have six localized labels, and the converter regression identifies each documented nested field. |
| `BPM092-M12-05` | Update Firefox 153 user and administrator documentation. | Revise README and all affected six-locale DITA topics, schema guidance, policy targets, manifests/search, screenshots, and contextual-help dispositions for Release 153 plus both ESRs. | GPT-5.6 Terra | High | Documentation describes the exact three-channel support matrix and migration behavior, all links/artifacts are current across locales, and `make docs-install-dev` installs the artifact for the maintainer's next `make dev`. |
| `BPM092-M12-06` | Prove the dual-ESR schema refresh. | Run focused converter, schema, migration, loader, policy-placement, locale, documentation, and browser checks before final release quality. | GPT-5.6 Terra | Extra High | All three schemas validate with their intended coverage; migration and locale/docs drift contracts pass; targeted product and documentation browser smoke is green; remaining final-quality checks have no schema-refresh exception. |

## Milestone 13: Final Quality, Release Documentation, And Handoff

Goal: prove the compact UI and documentation coherence epic is complete, accessible, maintainable,
and releasable.

| ID | Task | Essence | Model | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- | --- |
| `BPM092-M13-01` | Run static typing. | Execute `make typecheck` after implementation and focused checks. | GPT-5.6 Luna | Light | Mypy passes with no new suppression hiding UI, documentation runtime, or search-state defects. |
| `BPM092-M13-02` | Run lint. | Execute `make lint` across maintained product and documentation tooling sources. | GPT-5.6 Luna | Light | Ruff passes; generated/vendor output remains excluded only by existing explicit ownership rules. |
| `BPM092-M13-03` | Run the complete pytest suite. | Execute `pytest -q` after focused suites pass. | GPT-5.6 Terra | Medium | The complete default suite passes with no unreviewed skip, xfail, or marker change added for this epic. |
| `BPM092-M13-04` | Run full code-surface coverage. | Execute `make coverage` and inspect product plus documentation-owned reports. | GPT-5.6 Terra | High | Covered code surface is 100%; falling below 100% is not accepted as known debt - add focused tests, remove dead code, or eliminate unreachable paths. |
| `BPM092-M13-05` | Run full documentation release validation. | Execute the clean documentation build and non-browser release gates for all six locales. | GPT-5.6 Terra | High | DITA, audience/style evidence, links, targets, manifests, search, screenshots, parity, accessibility, header, version, provenance, and drift contracts pass. |
| `BPM092-M13-06` | Verify locale quality and compact-copy parity. | Run catalog generation, locale parity, placeholder, terminology, visible-English, title-style, and viewport checks. | GPT-5.6 Terra | High | English plus five localized UI/docs peers are complete and natural, with no retired prose, untranslated copy, grammar-calque finding, or overflow regression left open. |
| `BPM092-M13-07` | Run Chromium/Selenium product and documentation smoke. | Execute `make test-ui` plus dedicated documentation browser checks with immediate sandbox escalation and no sandboxed trial. | GPT-5.6 Terra | Extra High | Library, Guided, All settings, JSON, Compare, unified headers, context help, search-filter persistence, themes, locales, zoom, keyboard paths, and representative workflows pass. |
| `BPM092-M13-08` | Verify the documentation-update milestones. | Confirm every M11 and M12 documentation task and its focused evidence is complete before release handoff. | GPT-5.6 Terra | Medium | Compact-UI and schema-refresh docs, context topics, targets, screenshots, authoring rules, runbooks, README decision, docs index, documentation install, and documentation checks are linked from release evidence. |
| `BPM092-M13-09` | Finalize the `0.9.2` changelog entry. | Record shipped UI compaction, unified documentation shell/version, search-state fix, editorial/localization cleanup, and Firefox 153 dual-ESR support. | GPT-5.6 Luna | Light | The entry describes actual shipped behavior and quality evidence, preserves all older history, and contains no unverified completion claim. |
| `BPM092-M13-10` | Verify README release boundaries. | Confirm README describes only durable current product state after any M11/M12 refresh. | GPT-5.6 Luna | Light | README has no target-version anchor, release-history entry, planned-for-version text, or completion placeholder and retains required footer/email-topic content. |
| `BPM092-M13-11` | Verify maintained drift procedures. | Check schema, CIS, locale, Administrator/DevOps deployment and integration, update, documentation publishing, and release procedures affected by this epic. | GPT-5.6 Terra | Medium | Procedures fail closed for changed compact-copy, contextual-link, header/version, search-state, locale-style, screenshot/documentation, and three-channel schema drift. |
| `BPM092-M13-12` | Reconcile the docs index after final changes. | Ensure final maintained evidence is indexed once with the correct status. | GPT-5.6 Luna | Light | The index has no missing, stale, or duplicate maintained path and excludes generated/local artifacts. |
| `BPM092-M13-13` | Create the completed-epic git commit. | Commit only reviewed 0.9.2 changes after all final checks pass. | GPT-5.6 Luna | Light | The commit excludes unrelated work, caches, secrets, generated build output outside policy, and local browser artifacts. |
| `BPM092-M13-14` | Provide the maintainer-run push command. | Print the exact command the maintainer should run manually. | GPT-5.6 Luna | Light | The assistant does not push; final handoff includes the exact `git push` command and concise passed-check summary. |

## Execution Protocol

When executing this backlog interactively:

1. Show exactly one next task with its ID, essence, acceptance, minimum model, and minimal reasoning.
2. Wait for explicit maintainer approval.
3. Execute only that approved task.
4. Report changed files and checks passed.
5. Show the next task for approval.

Do not start implementing a backlog task merely because this backlog exists.

Browser/Selenium commands must be run with immediate sandbox escalation during backlog execution;
do not attempt a sandboxed browser run first. Do not push from backlog execution. Create the final
commit only when its task is separately approved, then print the exact push command for the maintainer.

## Backlog Creation Acceptance Checklist

- Target BPM version is normalized as `0.9.2`; compact epic id is `BPM092`.
- Task IDs follow `BPM092-M<milestone>-<two digits>` and milestones are grouped by product meaning.
- Every task names exactly one minimum model and one allowed reasoning level.
- Model calibration uses current GPT-5.6 Luna/Terra/Sol guidance; Luna is used for deterministic work,
  Terra is the normal engineering minimum, and no unjustified Sol assignment is present.
- M1 includes product version transition, editable-package refresh, dependency currency, changelog,
  README guard, release contract, and active release/version-source audit.
- M2 defines protected copy, density budgets, contextual-help mapping, unified header, documentation
  audience/style, search state, and baseline guards before implementation.
- Library, Guided, All settings, JSON, shared editor chrome, Compare, and documentation each have an
  explicit implementation and verification boundary.
- The approximate fivefold target is measurable but cannot override safety, accessibility, errors,
  validation, consequences, recovery, state, or irreducible domain meaning.
- Documentation uses one BPM product version; any retained artifact field is derived and not displayed
  as an independent documentation version.
- Search execution never changes advanced-filter visibility chosen by the user.
- Documentation editorial work removes maintainer/progress narration while preserving honest current
  support boundaries and legitimate API-integrator content.
- Russian heading cleanup uses idiomatic nominal forms; every other locale follows its own reviewed
  convention rather than a mechanical Russian or English grammar rule.
- A dedicated documentation-update milestone precedes final quality and covers DITA peers, targets,
  manifests/search, screenshots, runbooks, README decision, docs index, and focused checks.
- Final quality includes mypy, ruff, `pytest -q`, coverage-to-100%, complete documentation validation,
  locale/editorial gates, and Selenium/Chromium smoke with immediate escalation.
- Final quality verifies documentation completion, changelog, README boundaries, maintained drift
  procedures, docs index, git commit, and maintainer-run push handoff.
- README work preserves maintainer copyright and email-topic/message-theme information and forbids
  release history, active-version markers, and planned/completion placeholders.
- Changelog work preserves all previous release history.
- Product language remains English while maintainer chat may be Russian.
- Assumptions and non-goals are explicit, and every backlog task requires separate user approval.
