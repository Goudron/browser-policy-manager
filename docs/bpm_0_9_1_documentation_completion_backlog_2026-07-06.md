# BPM 0.9.1 Documentation Completion Backlog

Date: 2026-07-06

This backlog defines the BPM 0.9.1 work for finishing the documentation release quality loop after
the 0.9.0 documentation portal. The release removes the remaining screenshot blocker, makes the
documentation feel like the main BPM interface in light, dark, and system theme modes, reduces
documentation search and navigation friction, verifies that the documentation is sufficient for
real tasks, removes non-allowlisted English from localized copy, and adds per-setting documentation
links in All Settings.

Product source, UI copy, README, changelog, and maintained documentation stay in English.
Maintainer chat may be Russian, but implementation copy must not switch to Russian unless the task
is explicitly about localization. English remains the source locale; `ru`, `de`, `zh-CN`, `fr`, and
`es-ES` must ship content-equivalent localized peers. Localized UI and documentation may keep only
allowlisted technical identifiers, stable abbreviations, product names, brand names, commands,
paths, API names, schema keys, Firefox policy IDs, CIS recommendation IDs, and other terms that the
locale terminology policy explicitly permits.

## Scope Summary

- Target BPM version: `0.9.1`.
- Compact epic id: `BPM091`.
- Scope boundary: documentation visual polish, documentation search and navigation, topic-section
  hierarchy in the documentation tree, minimal
  User Guide screenshots for all active locales, main product light-theme tone adjustment,
  documentation sufficiency review, Administrator Guide Linux source-install coverage, terminology
  cleanup across localized product/documentation surfaces, All Settings per-setting documentation
  links, focused tests, README, changelog, and release metadata.
- Release risk: high, because the work crosses the generated documentation portal, main BPM CSS
  tokens, six locale catalogs, DITA topics, screenshot automation, documentation search, navigation
  contracts, All Settings row rendering, and contextual help target validation.
- Primary outcome: a user can open BPM documentation in the active locale, read it comfortably in
  light, dark, or system theme mode, navigate the guide tree through documents, sections, and topics
  without duplicate headings or broken return paths, search without a large default panel, follow
  localized filters, see minimal localized User Guide screenshots, and complete documented tasks with
  the expected result.
- Secondary outcome: All Settings users can open the Firefox setting or policy reference from any
  visible list row through the same circled-info contextual help style used elsewhere in BPM.

## Current-State Assessment

- BPM 0.9.0 introduced the product documentation portal, DITA source area, six-locale documentation
  output, deterministic search, manifest and UI-target maps, contextual help links, and isolated
  documentation tests.
- A screenshot release blocker remains for localized documentation. For 0.9.1, the blocker is
  intentionally narrowed to the minimum User Guide screenshot set across all active locales rather
  than a full guide-family screenshot matrix.
- The documentation portal is functional but still needs visual alignment with the main BPM
  interface and explicit light, dark, and system theme support that feels coherent with product UI.
- The main BPM light theme still uses too much pure white. The new light theme should use light gray
  surfaces as the primary background while preserving readable contrast and accessible focus states.
- Documentation search currently consumes too much vertical space on first load. It needs a compact
  one-line default state with an explicit expansion path for advanced filters and facets.
- Search filter labels are still visible in English in localized documentation. They need locale
  catalog ownership, translation, and parity tests like other product and documentation strings.
- Documentation guide names are duplicated in the page header and the left navigation. The
  navigation should become the single guide/topic structure: documentation home, then guide nodes,
  then topic nodes. Returning to higher levels, including the documentation root, is not always
  reliable today.
- After the first tree-navigation pass, each document can still contain a long flat topic list.
  The tree needs one more localized section level between document and topic nodes so users can
  scan large guides by intent rather than by a single long list.
- The existing documentation corpus needs a sufficiency review against real BPM workflows. The
  Administrator Guide must also document exact source-install command sequences for the five Linux
  distributions selected by a recorded, dated popularity decision during implementation.
- Non-English locales still contain visible English words that are not approved technical terms.
  Terminology cleanup must use the locale's Mozilla Pontoon and SUMO terminology where available,
  plus the maintained BPM glossary and allowlists.
- All Settings has contextual help for selected policy/CIS/validation/import/export contexts, but
  not a consistent per-setting row link for every displayed policy and setting.

## Non-Goals And Assumptions

- Do not rebuild the documentation portal architecture from scratch. Use the 0.9.0 DITA, manifest,
  search, runtime bridge, localization, screenshot, and test boundaries unless a task explicitly
  amends a contract.
- Do not expand the 0.9.1 screenshot scope to every guide family. The release blocker is removed by
  producing the minimum useful localized User Guide screenshot set, with future screenshot depth
  left to separate documentation work.
- Do not add an LLM, embeddings, RAG, generative answers, telemetry, hosted search, or runtime
  network dependency to documentation search.
- Do not introduce packaged installers, production service units, supported HA, reverse-proxy
  recipes, official restore automation, or distribution-specific package support as product
  capabilities. The Linux work documents source installation only.
- Do not claim that a Linux distribution ranking is timeless. The implementation task must record
  the dated source and selected five distributions before authoring exact commands; if public
  popularity data is ambiguous, maintainer approval of the selected set is required.
- Do not translate stable identifiers, commands, paths, JSON keys, API paths, Firefox policy IDs,
  CIS recommendation IDs, product names, brand names, or allowlisted abbreviations.
- Do not remove English from the English source locale. The anti-anglicism work applies to
  non-English localized UI and documentation surfaces.
- Assume all active locales are release deliverables: `en`, `ru`, `de`, `zh-CN`, `fr`, and `es-ES`.
- Assume browser UI and documentation screenshot tests require immediate sandbox escalation during
  backlog execution.

## Milestone 1: Version Transition And Release Anchors

Goal: establish `0.9.1` as the target version and record the release boundaries before
implementation begins.

| ID | Task | Essence | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- |
| `BPM091-M1-01` | Update product version surfaces to `0.9.1`. | Move package metadata, application settings, UI-visible version values, tests, and active release constants to the target version. | medium | Runtime, package metadata, tests, UI-visible version surfaces, and active documentation metadata agree on `0.9.1`; old versions remain only in history, archives, or explicit migration context. |
| `BPM091-M1-02` | Refresh local editable-package metadata for `0.9.1`. | Reinstall or refresh the editable BPM package metadata used by local probes after the version transition. | low | `pip show browser-policy-manager` and equivalent local environment checks report `0.9.1`; no stale editable metadata points to `0.9.0`. |
| `BPM091-M1-03` | Check external workflow dependency currency. | Review Python, frontend vendor packages, documentation toolchain components, browser-test drivers, and test/dev dependencies used by this epic. | medium | A bounded note records whether each relevant dependency stays pinned or needs a separately approved update; no floating upgrade is hidden inside feature work. |
| `BPM091-M1-04` | Open the `0.9.1` changelog entry. | Add the target-version release-note landing zone while preserving older history. | low | `CHANGELOG.md` contains a non-final `0.9.1` section above older entries and no previous release notes are overwritten. |
| `BPM091-M1-05` | Guard README against target-version copy. | Verify README stays current-state product documentation and does not identify `0.9.1` as an active target or reserve a version-specific placeholder. | low | README has no `0.9.1` target anchor, planned-for-version copy, or completion placeholder; any final README refresh remains limited to durable current-state product facts after implementation. |
| `BPM091-M1-06` | Record the 0.9.1 release contract. | Map every screenshot, theme, search, navigation, sufficiency, localization, and All Settings documentation-link deliverable to evidence and verification commands. | high | A maintained checklist names each release blocker, its owner, its focused checks, and the final release gate that proves it complete. |
| `BPM091-M1-07` | Audit active release-naming documentation. | Find active architecture, runbook, release-readiness, docs-index, and documentation metadata text that incorrectly treats `0.9.0` as the current target. | medium | A bounded update list is recorded; archive and historical references are excluded from the version transition. |

Evidence: `BPM091-M1-07` is recorded in
`docs/architecture/release-naming-audit-0.9.1.md`.

## Milestone 2: Baseline Audit And Contracts

Goal: convert the requested documentation fixes into explicit, testable contracts before changing
screenshots, UI, or localized content.

| ID | Task | Essence | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- |
| `BPM091-M2-01` | Audit the current documentation portal against 0.9.1 blockers. | Inspect the built portal, DITA source, manifest, search, navigation, screenshots, theme behavior, and localized output only where they affect this epic. | high | A maintained audit lists each confirmed gap, affected files or generated artifacts, and the focused task that will close it; unrelated 0.9.0 architecture work is not reopened. |
| `BPM091-M2-02` | Define the minimal User Guide screenshot matrix. | Select the smallest screenshot set that makes User Guide task flows understandable in all active locales. | high | The matrix names topic, locale, viewport, theme, fixture state, route, filename, caption, and alt-text key; Firefox Policy, CIS, API, and Administrator screenshots are explicitly out of scope unless needed by a User Guide task. |
| `BPM091-M2-03` | Define the documentation visual-theme contract. | Align portal surfaces, typography scale, controls, links, focus, code blocks, tables, notes, and screenshots with the main BPM UI. | high | The contract covers light, dark, and system theme modes, accessible contrast, reduced motion, print behavior, and the rule that light theme uses light-gray primary surfaces rather than pure white. |
| `BPM091-M2-04` | Define the documentation search and filter contract. | Specify compact default search, expansion behavior, localized filters, facet persistence, keyboard access, and empty-result recovery. | high | Search defaults to one line, expands deliberately, keeps deterministic ranking unchanged, and exposes every visible filter label through locale catalogs and parity tests. |
| `BPM091-M2-05` | Define the documentation tree-navigation contract. | Replace duplicated guide headings with a single hierarchical navigation model. | high | The contract defines documentation root, guide/document nodes, topic nodes, active state, breadcrumbs if retained, URL behavior, keyboard tree semantics, collapse/expand state, and reliable return to parent and root nodes. |
| `BPM091-M2-06` | Define the documentation sufficiency review protocol. | Turn "can the user complete the documented task" into repeatable review evidence. | high | Every guide family has a checklist for prerequisites, exact steps, expected result, recovery path, drift source, and focused verification; User Guide tasks and Administrator source-install tasks require hands-on execution or documented simulation evidence. |
| `BPM091-M2-07` | Define Linux distribution selection rules. | Establish how the five worldwide-popular Linux distributions for source-install docs will be selected. | medium | A dated evidence note names the source, ranking method, selected distributions, and maintainer approval if popularity data is ambiguous; command authoring cannot start until the set is recorded. |
| `BPM091-M2-08` | Define the All Settings row help-link contract. | Specify how every visible All Settings policy or setting row resolves to a Firefox documentation topic. | high | The contract covers policy IDs, managed preferences, generated/unknown/raw settings, missing docs, unavailable documentation artifacts, localized labels, row layout, keyboard access, and manifest target validation. |
| `BPM091-M2-09` | Add guarding tests for the new contracts. | Create focused failing or protective checks before implementation where practical. | high | Tests or fixtures fail for missing screenshot matrix rows, English filter labels in localized search, duplicate guide titles, broken root return, pure-white light theme surfaces, and All Settings rows without valid help-link disposition. |

Evidence: `BPM091-M2-01` is recorded in
`docs/architecture/documentation-portal-blocker-audit-0.9.1.md`.

Evidence: `BPM091-M2-02` is recorded in
`documentation/config/user-guide-screenshot-matrix-0.9.1.json`.

Evidence: `BPM091-M2-03` is recorded in
`docs/architecture/product-documentation-visual-theme-contract-0.9.1.md`.

Evidence: `BPM091-M2-04` is recorded in
`documentation/config/search-ui-filter-contract-0.9.1.json`.

Evidence: `BPM091-M2-05` is recorded in
`documentation/config/navigation-tree-contract-0.9.1.json`.

Evidence: `BPM091-M2-06` is recorded in
`documentation/config/documentation-sufficiency-review-protocol-0.9.1.json`.

Evidence: `BPM091-M2-07` is recorded in
`docs/architecture/linux-distribution-selection-0.9.1.md`.

Evidence: `BPM091-M2-08` is recorded in
`documentation/config/all-settings-row-help-link-contract-0.9.1.json`.

Evidence: `BPM091-M2-09` is recorded in
`documentation/config/documentation-polish-guardrails-0.9.1.json` and
`documentation/tests/contract/test_091_documentation_polish_guardrails.py`.

## Milestone 3: Visual Theme Alignment And Light-Theme Comfort

Goal: make documentation and the main product visually coherent while reducing the harshness of the
light theme across BPM.

| ID | Task | Essence | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- |
| `BPM091-M3-01` | Audit BPM and documentation theme tokens. | Identify pure-white surfaces, mismatched documentation tokens, insufficient contrast, and duplicated theme values. | medium | The audit names every active CSS token or selector that needs 0.9.1 work and excludes generated/vendor output. |
| `BPM091-M3-02` | Darken the main BPM light theme. | Change the default light-theme primary surfaces from white to comfortable light gray while preserving hierarchy. | high | Main application pages use non-white primary backgrounds and coherent panel/input/list surfaces; contrast, focus, disabled, warning, and destructive states still pass accessibility checks. |
| `BPM091-M3-03` | Align documentation theme tokens with BPM UI. | Reuse or mirror BPM visual decisions for docs shell, navigation, search, links, notes, code, tables, and controls. | high | Documentation pages look like part of BPM in light and dark mode without introducing a one-note palette or breaking generated HTML ownership rules. |
| `BPM091-M3-04` | Add or fix documentation system-theme support. | Respect OS color-scheme preference and explicit user theme selection consistently. | high | Documentation supports light, dark, and system modes; system mode follows `prefers-color-scheme`; explicit choices persist according to existing product conventions. |
| `BPM091-M3-05` | Verify theme behavior across locales and viewports. | Run focused visual, contrast, and layout checks after theme changes. | high | Desktop and narrow viewport checks pass for representative pages in all six locales; no text overlaps, illegible controls, or pure-white primary surfaces remain in light mode. |

Evidence: `BPM091-M3-01` is recorded in
`docs/architecture/bpm-documentation-theme-token-audit-0.9.1.md`.

Evidence: `BPM091-M3-02` is recorded in
`app/static/profiles_css/00-foundation.css`,
`app/static/profiles_css/10-library.css`,
`app/static/profiles_css/20-editor-wizard.css`,
`app/static/profiles_css/40-compact-shell.css`, and
`tests/test_light_theme_surface_contract_091.py`.

Evidence: `BPM091-M3-03` is recorded in
`documentation/assets/theme/bpm-docs.css` and
`tests/test_documentation_theme_alignment_091.py`.

Evidence: `BPM091-M3-04` is recorded in
`documentation/tools/build_docs.py`,
`documentation/assets/theme/bpm-docs.css`,
`documentation/assets/theme/bpm-docs-search.js`, and
`tests/test_documentation_system_theme_091.py`.

Evidence: `BPM091-M3-05` is recorded in
`documentation/tests/browser/test_documentation_portal_browser_smoke.py`.

## Milestone 4: Documentation Search And Navigation Usability

Goal: reduce first-load search clutter and make the documentation information architecture behave
like a reliable tree.

| ID | Task | Essence | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- |
| `BPM091-M4-01` | Collapse documentation search by default. | Render the search block as a compact one-line control until the user expands advanced options. | high | Initial portal pages show only the compact search row; expanding reveals filters/facets without layout jumps, lost query text, or keyboard traps. |
| `BPM091-M4-02` | Preserve deterministic search behavior after the compact UI change. | Keep index generation, normalization, ranking, and result contracts stable while changing only presentation and filter access. | medium | Existing search quality fixtures pass; result URLs, highlights, empty states, and locale-specific indexes are unchanged except for intended UI structure. |
| `BPM091-M4-03` | Localize documentation search filter labels. | Move every visible search filter, facet, scope, sort, and empty-state parameter label into locale-owned catalogs. | high | `ru`, `de`, `zh-CN`, `fr`, and `es-ES` no longer show English filter parameter labels except allowlisted identifiers; locale key and placeholder parity checks pass. |
| `BPM091-M4-04` | Remove duplicate document names from page headers. | Keep document/guide names in the left navigation tree instead of repeating them in the top page header. | medium | Documentation pages no longer duplicate guide names in both header and left list; topic titles and necessary breadcrumbs remain meaningful and accessible. |
| `BPM091-M4-05` | Implement the hierarchical documentation tree. | Show documentation home, guide/document nodes, and topic nodes as the primary left navigation model. | high | The tree exposes all publishable topics in stable order, supports expand/collapse, localized labels, current-topic highlighting, and keyboard navigation without relying on translated URLs. |
| `BPM091-M4-06` | Fix return-to-parent and return-to-root behavior. | Make navigation from topic to guide and from guide to documentation root reliable. | high | Direct URLs, in-app clicks, browser back/forward, breadcrumbs if retained, root tree node, and guide nodes consistently return to the expected parent or root page. |
| `BPM091-M4-07` | Add documentation navigation browser smoke. | Verify compact search and tree navigation in real rendered pages. | high | Browser smoke covers all six locales, root to guide to topic navigation, return to root, search expansion, localized filter labels, keyboard tree movement, and responsive layout. |

Evidence: `BPM091-M4-01` is recorded in
`documentation/tools/build_docs.py`,
`documentation/assets/theme/bpm-docs.css`,
`documentation/assets/theme/bpm-docs-search.js`, and
`tests/test_documentation_compact_search_091.py`.

Evidence: `BPM091-M4-02` is recorded in
`tests/test_documentation_search_behavior_stability_091.py`.

Evidence: `BPM091-M4-03` is recorded in
`documentation/tools/build_docs.py`,
`documentation/assets/theme/bpm-docs-search.js`, and
`tests/test_documentation_search_filter_localization_091.py`.

Evidence: `BPM091-M4-04` is recorded in
`documentation/tools/build_docs.py` and
`documentation/tests/unit/test_build_docs.py`.

Evidence: `BPM091-M4-05` is recorded in
`documentation/tools/build_docs.py`,
`documentation/assets/theme/bpm-docs.css`,
`documentation/assets/theme/bpm-docs-search.js`, and
`documentation/tests/unit/test_build_docs.py`.

Evidence: `BPM091-M4-06` is recorded in
`documentation/tools/build_docs.py`,
`documentation/assets/theme/bpm-docs-search.js`, and
`documentation/tests/unit/test_build_docs.py`.

Evidence: `BPM091-M4-07` is recorded in
`documentation/tests/browser/test_documentation_portal_browser_smoke.py`.

Evidence: `BPM091-M5-01` is recorded in
`documentation/config/user-guide-screenshot-matrix-0.9.1.json` and
`documentation/tests/contract/test_user_guide_screenshot_matrix.py`.

Evidence: `BPM091-M5-02` is recorded in
`documentation/tools/capture_user_guide_screenshots.py`,
`documentation/assets/screenshots/{en,ru,de,zh-CN,fr,es-ES}/`, and
`documentation/tests/contract/test_user_guide_screenshot_matrix.py`.

Evidence: `BPM091-M5-03` is recorded in
`documentation/config/user-guide-screenshot-matrix-0.9.1.json`,
`documentation/tests/contract/test_user_guide_screenshot_matrix.py`, and
`documentation/assets/screenshots/{en,ru,de,zh-CN,fr,es-ES}/`.

Evidence: `BPM091-M5-04` is recorded in
`documentation/src/dita/{en,ru,de,zh-CN,fr,es-ES}/maps/keys.ditamap`,
`documentation/src/dita/{en,ru,de,zh-CN,fr,es-ES}/user/ug-task-*.dita`,
`documentation/tools/build_docs.py`,
`documentation/assets/theme/bpm-docs.css`, and
`documentation/tests/contract/test_user_guide_screenshot_matrix.py`.

Evidence: `BPM091-M5-05` is recorded in
`documentation/config/user-guide-screenshot-visual-qa-0.9.1.json` and
`documentation/tests/contract/test_user_guide_screenshot_visual_qa.py`; visual QA covers all
matrix rows and is accepted after M7-05 regenerated all localized User Guide screenshots and closed
the non-allowlisted English screenshot findings.

Evidence: `BPM091-M7-01` is recorded in
`documentation/config/locale-visible-english-inventory-0.9.1.json` and
`documentation/tests/contract/test_locale_visible_english_inventory.py`; the inventory covers all
non-English locales and classifies each visible-English finding as replace, allowlist, brand,
identifier, command/path/API, abbreviation, or false positive.

Evidence: `BPM091-M7-02` is recorded in
`documentation/config/locale-terminology-authority-0.9.1.json` and
`documentation/tests/contract/test_locale_terminology_authority.py`; every replacement finding from
the visible-English inventory has Pontoon, SUMO, or maintainer-fallback terminology ready for the
M7-03 source replacement pass.

Evidence: `BPM091-M7-03` is recorded in
`documentation/config/locale-anglicism-replacement-0.9.1.json` and
`documentation/tests/contract/test_locale_anglicism_replacement.py`; M7-01 replacement findings are
removed from source and runtime locale catalogs, while the screenshot blocker remains open until
affected PNGs are regenerated and visually accepted.

Evidence: `BPM091-M7-04` is recorded in
`documentation/config/locale-anti-anglicism-guard-0.9.1.json` and
`documentation/tests/contract/test_locale_anti_anglicism_guard.py`; the guard protects closed M7-03
product catalog fragments, localized DITA documentation strings corrected during the pass, and
allowlisted technical English fixture behavior.

Evidence: `BPM091-M7-05` is recorded in
`documentation/config/locale-human-qa-0.9.1.json`,
`documentation/config/user-guide-screenshot-visual-qa-0.9.1.json`, and
`documentation/tests/contract/test_locale_human_qa.py`; human-oriented QA covers all five
non-English locales in the reviewed User Guide screenshot surfaces, closes the localized screenshot
release blockers after a fresh 36-row capture, and records remaining reviewed English only as
allowlisted brands, abbreviations, identifiers, commands, paths, APIs, or false positives.

Evidence: `BPM091-M8-01` is recorded in
`documentation/config/topic-section-hierarchy-audit-0.9.1.json` and
`documentation/tests/contract/test_topic_section_hierarchy_audit.py`; the audit reviews all five
documentation guide/document nodes, records exact DITA map topic counts and the twelve-topic
flat-list threshold, flags `user-guide` and `administrator-guide` for section grouping, and excludes
`cis-settings-guide`, `firefox-policy-guide`, and `api-integration-guide` as short enough.

Evidence: `BPM091-M8-02` is recorded in
`documentation/config/topic-section-taxonomy-0.9.1.json` and
`documentation/tests/contract/test_topic_section_taxonomy.py`; the taxonomy assigns all 90
`user-guide` topics and all 44 `administrator-guide` topics to exactly one stable localizable
section, preserves guide-map order, keeps every section at or below twelve topics, and records that
topic IDs, DITA keys, canonical URLs, manifest topic IDs, UI target IDs, search document IDs, and
contextual help targets must not change for grouping.

Evidence: `BPM091-M8-03` is implemented in
`documentation/tools/build_docs.py`, `documentation/assets/theme/bpm-docs-search.js`, and
`documentation/assets/theme/bpm-docs.css`, with the amended tree model recorded in
`documentation/config/navigation-tree-contract-0.9.1.json` and protected by
`documentation/tests/unit/test_build_docs.py` plus
`documentation/tests/contract/test_navigation_tree_contract.py`; taxonomy-owned documents render
`root -> document -> section -> topic`, direct topic pages expand their document and section,
short documents remain flat, and no topic URL or manifest identity changes.

Evidence: `BPM091-M8-04` is recorded in
`documentation/config/topic-section-labels-0.9.1.json` and
`documentation/tests/contract/test_topic_section_labels.py`, with runtime integration in
`documentation/tools/build_docs.py`; every one of the 21 taxonomy label keys owns reviewed values
for `en`, `ru`, `de`, `zh-CN`, `fr`, and `es-ES`, product locale terminology is reused for editor
modes, exact key/locale parity is fail-closed, and non-English section nodes cannot fall back to the
canonical English label.

Evidence: `BPM091-M8-05` is implemented in
`documentation/tests/browser/test_documentation_portal_browser_smoke.py`,
`documentation/tests/contract/test_navigation_tree_contract.py`, and
`documentation/tests/unit/test_build_docs.py`, with selected-ancestor protection in
`documentation/assets/theme/bpm-docs-search.js`; the six-locale Chromium/Selenium smoke covers
root focus, document and section expansion, localized section labels, active topic highlighting,
mouse and keyboard controls, parent/root return, 390 px layout, Administrator Guide sections, and
flat Firefox Policy Guide navigation. The focused smoke passes, and the complete documentation
browser suite passes with four tests after one confirmed transient new-tab timeout was rerun green.

Evidence: `BPM091-M6-01` is recorded in
`docs/architecture/user-guide-sufficiency-review-0.9.1.json` and
`documentation/tests/contract/test_user_guide_sufficiency_review.py`; the normalized review covers
all 62 User Guide task topics and 10 troubleshooting topics exactly once, resolves every protocol
field from the localized DITA task contract and workflow evidence, records eight passing Selenium
scenarios plus four passing save/export/conflict simulations, preserves six-locale execution-order
parity, and closes with no User Guide release blockers while explicitly excluding live Firefox
policy activation and operating-system-owned file-picker behavior.

Evidence: `BPM091-M6-02` is recorded in
`docs/architecture/firefox-cis-guide-sufficiency-review-0.9.1.json` and
`documentation/tests/contract/test_firefox_cis_guide_sufficiency_review.py`; eight representative
decision classes cover simple and complex policies, Release/ESR differences, managed preferences,
CIS Levels 1 and 2, nine manual-review paths, two provenance-only states, all 53 mapping examples,
and current Firefox keyrefs. The focused schema/generation and locale/workflow bundles pass 38 and
17 tests respectively, with no release blocker and with live-Firefox, CIS certification, and
persisted-exception boundaries stated explicitly.

Evidence: `BPM091-M6-03` is recorded in
`docs/architecture/administrator-devops-guide-sufficiency-review-0.9.1.json` and
`documentation/tests/contract/test_administrator_devops_guide_sufficiency_review.py`; the review
covers all 44 Administrator/DevOps topics across ten navigation sections and six locales, executes
current health/readiness, validation, import, and export behavior, and passes 235 focused
Administrator contracts plus 16 API/integration contracts. The accepted review intentionally keeps
two release blockers open: eight generic Linux/WSL source-install topics still lack exact
named-release command/transcript evidence required by `BPM091-M6-05` and `BPM091-M6-06`, and all
44 topics retain stale 0.9.0 metadata or wording assigned to `BPM091-M12-02`.

Evidence: `BPM091-M6-04` confirms the M2 selection rule in
`docs/architecture/linux-distribution-selection-0.9.1.md` and its focused contract
`tests/test_linux_distribution_selection_091.py`; maintainer approval is dated 2026-07-11, the
incorrect `M6-02` authoring gate is replaced by `M6-04 -> M6-05 -> M6-06`, and exact validation
targets are frozen as Ubuntu 26.04 LTS, Debian 13.5, Fedora Linux 44, Linux Mint 22.3, and the
Manjaro stable branch after its 2026-06-26 stable update.

Evidence: `BPM091-M6-05` is implemented by five end-to-end Administrator DITA tasks in every
supported locale, registered through the Administrator maps, keys, and topic-section taxonomy, with
the machine-readable command contract in
`documentation/config/linux-source-install-command-contract-0.9.1.json` and focused checks in
`documentation/tests/contract/test_linux_source_install_command_topics.py`. Ubuntu 26.04, Debian
13.5, Fedora 44, Linux Mint 22.3, and Manjaro stable each cover prerequisites, guarded checkout,
Python 3.14, editable install, migration, documentation validation/build, foreground start,
health/readiness, Profile Library response, logs, and stop/rollback boundaries. The 282-test focused
Administrator bundle, six-locale `make docs-validate`, and `make docs-build` pass; clean-target
execution remains explicitly owned by `BPM091-M6-06`.

Evidence: `BPM091-M6-06` is recorded in
`docs/architecture/linux-source-install-validation-0.9.1.json` and protected by
`documentation/tests/contract/test_linux_source_install_validation.py`. On the actual Ubuntu 26.04
maintainer host, installed prerequisite versions and Python 3.14.4 were recorded, a disposable
SQLite database migrated through the current head, the application started on isolated port 8791,
health/readiness returned their exact JSON contracts, `/profiles` returned 200, and `Ctrl+C`
produced a clean shutdown followed by a refused probe. The official CPython 3.14.6 archive passed
the documented SHA-256. Debian, Fedora, Linux Mint, and Manjaro passed command syntax/order and
official-source simulations, but no disposable runtime was available; therefore the accepted task
result remains `release_ready=false` until five complete clean-target transcripts exist.

Evidence: `BPM091-M6-07` is recorded in
`documentation/config/documentation-sufficiency-drift-guard-0.9.1.json` and enforced by
`documentation/tests/contract/test_documentation_sufficiency_drift.py`. The fail-closed guard
normalizes all three accepted sufficiency records, requires protocol fields and observable results,
checks localized task commands/recovery/related links, protects Linux command blocks, and verifies
that drift sources, evidence artifacts, pytest paths/nodes, and locale key targets still exist. Its
first run corrected stale All Settings, Firefox schema, and recovery-topic references; the complete
focused M6 bundle passes 66 tests while the M6-06 clean-target release blocker remains explicit.

Evidence: `BPM091-M9-01` is recorded in
`documentation/config/all-settings-documentation-target-audit-0.9.1.json` and protected by
`documentation/tests/contract/test_all_settings_documentation_target_audit.py`. The audit proves
that all 120 Release/ESR policy identities have generated `policy:*` targets, classifies all 62
known managed preferences as `missing_documentation` because `_build_target_map` currently emits no
`known-preference:*` targets, preserves links for schema-known raw-fallback/invalid/deprecated rows,
and assigns explicit `unsupported_unknown` no-link dispositions to unknown policy and preference
rows. It also separates editor-navigation targets from documentation targets and corrects the
pre-hierarchy implementation-task IDs in the M2-08 contract; the focused bundle passes 18 tests.

Evidence: `BPM091-M9-02` is implemented in
`documentation/config/all-settings-help-target-map-0.9.1.json`,
`documentation/tools/build_docs.py`, and
`documentation/tests/contract/test_all_settings_help_target_map.py`. The generator now emits and
fail-closed validates the exact union of 120 ESR/Release `policy:*` targets and all 62
`known-preference:*` targets, preserves case-sensitive Firefox preference IDs, maps known
preferences to the localized managed-preference safe-review reference, rejects missing/extra/
case-changed identities, and leaves editor aliases outside the documentation target namespace.
The target-map schema now accepts case-sensitive preference IDs. Focused contracts pass 28 tests,
manifest generation plus the new contract pass 7 tests, and full `make docs-validate` and
`make docs-build` produce 519 targets. The M9-01 missing-preference finding is closed; the separate
editor-target guard remains open for M9-03/M9-05.

Evidence: `BPM091-M9-03` is implemented by the validated row-target resolver in
`app/documentation/manifest.py`, settings-only context/embed wiring in
`app/web/profiles_context.py` and `app/templates/profiles/_page_catalog_scripts.html`, catalog and
bootstrap transport, sibling selection/help controls in `app/static/profiles_all_settings_list.js`,
matching search-result controls in `app/static/profiles_settings_search.js`, and fixed-width
desktop/mobile columns in the maintained CSS layers. Policy and known-preference links use only
manifest-resolved locale URLs, clicks on `i` do not select a row, and Review, Configured, Catalog,
search, collapsed, expanded, and paginated runtime paths retain bounded row counts and links.
`tests/test_all_settings_row_help_rendering_contract.py` plus focused resolver, route, Node-runtime,
keyboard, screen-reader, CSS, and responsive checks pass 42 tests; `make lint` passes. Explicit
unsupported/unavailable no-link states remain assigned to M9-05.

Evidence: `BPM091-M9-04` is implemented in the six source and generated runtime catalogs under
`app/i18n_src/*/common.json` and `app/i18n/*.json`, wired by
`app/static/profiles_all_settings_list.js` and `app/static/profiles_settings_search.js`, and
protected by `tests/test_all_settings_row_help_localization.py`. English, Russian, German,
Simplified Chinese, French, and Spanish provide locale-owned `{setting}` templates for opening,
missing, unavailable, raw-not-applicable, and unsupported-unknown documentation states; list and
search links use the dedicated open template for both title and accessible name. The focused
localization/rendering/anti-anglicism bundle passes 41 tests, locale catalogs rebuild reproducibly,
locale-quality reports no findings, and `make lint` passes.

Evidence: `BPM091-M9-05` is implemented by the documentation-artifact disposition resolver in
`app/documentation/manifest.py`, settings-page status transport, and the All Settings list/search
renderers. Unknown and unrecognized raw entries receive explicit localized no-link dispositions;
missing manifest targets and unavailable, stale, incomplete, or incompatible installed artifacts
render noninteractive circled-`i` indicators without `href`, while valid policy and known-preference
targets remain manifest-backed links. `tests/test_all_settings_row_help_states.py` protects the
runtime matrix; the broader All Settings bundle passes 58 tests, the documentation runtime-route
suite passes 21 tests, and `make lint` passes. Both M9 audit findings are now closed.

Evidence: `BPM091-M9-06` expands `tests/test_all_settings_row_help_states.py` across every
unavailable/stale/incomplete/incompatible artifact state and adds the dedicated Chromium scenario
`test_all_settings_row_help_links_cover_modes_locales_search_and_keyboard`. The browser smoke uses
a packaged manifest fixture and isolated legacy-profile database row to cover manifest-backed
policy and known-preference links, unknown and raw no-link rows, Review/Configured/Catalog modes,
list and search controls, Russian and long-label German copy, non-overlapping layout, separate
keyboard focus, Enter activation, and the localized `noopener` new-tab target. Focused DOM and
contract tests, the Chromium smoke, and `make lint` pass; Milestone 9 is complete.

Evidence: `BPM091-M10-01` is recorded in
`documentation/config/documentation-navigation-locale-completion-audit-0.9.1.json` and enforced by
`documentation/tests/contract/test_documentation_navigation_locale_completion_audit.py`. The audit
reproduces the missing independent sidebar scroll at 1366 px and 390 px: an expanded 183-node tree
produces 12,329 px/10,117 px sidebars with `overflow-y: visible`, no maximum height, and an
unchanged zero `scrollTop`. It records the six-locale compatibility-only API guide plus exact
Administrator Guide owners for all 13 migrated API topics, derives candidate UI-name authority
from runtime catalogs, and scans all 815 non-English DITA/map sources. The deterministic XML peer
comparison confirms 2,893 unchanged English prose fragments in 208 files and source-language UI
names in 225 files. Four release-blocking findings remain open for M10-02 through M10-06; five
focused contract tests pass.

Evidence: `BPM091-M10-02` is implemented in
`documentation/assets/theme/bpm-docs.css`, `documentation/assets/theme/bpm-docs-search.js`, and the
extended navigation-tree contract. Desktop sidebars are bounded to the dynamic viewport; narrow
sidebars remain non-sticky but use a 70dvh/32rem bound. Both own their vertical scrolling, contain
overscroll, reserve and style the scrollbar, wrap long localized labels, and suppress horizontal
overflow. Roving focus uses `preventScroll` and adjusts only sidebar `scrollTop`, so direct deep
topics, hash guide activation, and Arrow/Home/End navigation remain visible without moving the
article viewport. The dedicated desktop/narrow Chromium smoke and existing six-locale navigation
smoke pass; 23 focused contracts/unit tests, JS syntax, JSON, diff, and lint checks pass. The
sidebar audit finding is closed; three M10 blockers remain open.

Evidence: `BPM091-M10-03` removes the obsolete standalone API Integration Guide from the generator,
all six portal/key-map sets, localized landing sources, navigation and search contracts, active
sufficiency scope, and generated manifests. The former guide and landing addresses are deliberately
retired; all 15 `api-operation:*` targets now resolve directly to existing `admin-*` topics and the
generator fails closed if an Administrator Guide owner is missing. All 13 migrated API topic
families remain keyed and reachable in every localized Administrator Guide. Focused contracts and
unit tests pass, a complete six-locale build and `make docs-install-dev` succeed, and the six-locale
Chromium navigation smoke passes. The API-guide audit finding is closed; two M10 blockers remain.

Evidence: `BPM091-M10-04` is accepted in
`documentation/config/interface-name-authority-0.9.1.json`. The authority resolves 38 maintained
runtime keys across `en`, `ru`, `de`, `zh-CN`, `fr`, and `es-ES` for primary surfaces, All Settings
modes and sections, guided-workflow steps, settings categories, theme, and locale controls. Ten
historical documentation aliases, including Profile Library, Guided Editor, All Settings, JSON
Editor, and the three All Settings modes, have explicit canonical keys; five non-UI technical or
structural term classes are separately reviewed. Three runtime-catalog defects are fail-closed and
owned by M10-05 before documentation replacement. Focused authority, audit, terminology, metadata,
and current-version contracts pass; no interface name remains without an authority decision.

Evidence: `BPM091-M10-05` is accepted in
`documentation/config/interface-name-replacement-0.9.1.json`. All six DITA source locales,
localized User Guide navtitles, section-label taxonomy, active CIS/profile/screenshot fixtures,
and generated navigation/search surfaces now consume the maintained runtime-catalog names. The
task replaces 2,080 historical or source-locale UI-name occurrences, resolves all three M10-04
catalog findings plus seven additional malformed French, Spanish, and Chinese values, and preserves
the former `profile library` wording only as a query-only search alias. Source and installed scans
report zero forbidden aliases in visible topics, navigation, breadcrumbs, and search document
titles/bodies. All 625 documentation contracts, locale-catalog reproducibility, full six-locale
`make docs-install-dev`, and the six-locale Chromium navigation smoke pass. The UI-name blocker is
closed; only the full visible-English prose review remains open in M10.

Evidence: `BPM091-M10-06` is accepted in
`documentation/config/visible-english-prose-review-0.9.1.json`. The review covers all 805 current
non-English DITA/map sources and every visible title, navigation title, short description,
paragraph, command, table entry, direct note, caption, and alt-text block. Two bounded replacement
passes localize 10,410 structurally aligned visible blocks in 764 files across `ru`, `de`,
`zh-CN`, `fr`, and `es-ES`, then separately review all 36 structurally different source files;
exact peer comparison reports zero release-blocking long English carryover. The 28 remaining
high-signal scanner candidates are commands, paths, API/model/JSON/CIS identifiers, or three
reviewed German false positives, and four exact short peer matches are locale-language words or established
technical terms. Focused contracts validate the 805-file scope, exact-peer closure, residual
counts, allowlist ownership, and absence of temporary markers. All 630 documentation contracts and
all six browser smoke scenarios pass. The browser target keeps its shared generated portal on disk,
reuses it across scenarios, and bounds Chromium renderer/V8 memory so the gate does not exhaust
RAM-backed `/tmp`. The visible-English blocker is closed; M10-07 is next.

Evidence: `BPM091-M10-07` publishes one deterministic, schema-validated `navigation.json` for each
of the six locales and records its path, SHA-256, format version, and node count in the locale
manifest. Generated topic HTML now contains one bounded accessible navigation host with a
localized no-script root link instead of an embedded copy of the complete tree. The shared portal
runtime fetches only the same-locale, same-origin source, validates its identity, locale,
hierarchy, node count, and relative links, and builds escaped DOM nodes without inline code or CSP
relaxation. Existing root/document/section/topic activation, ancestor expansion, keyboard and
pointer behavior, collapse persistence, independent scrolling, and direct-topic reveal are
preserved. A missing source renders a localized unavailable state with a working root link and no
incoherent main-layout shift. Unit, schema, contract, JavaScript syntax, and the focused six-locale
Chromium navigation scenario pass; M10-08 is next.

Evidence: `BPM091-M10-08` is accepted in
`documentation/config/documentation-polish-regression-gates-0.9.1.json`. Ten fail-closed gates now
bind standalone API-guide retirement, unique Administrator Guide ownership of all 13 migrated API
topics, six-locale navigation-source completeness, manifest/hash/schema/hierarchy/label/URL
alignment, compact HTML tree hosts, locale-owned interface terminology, complete visible-English
review scope, and live bounded allowlists to the documentation release suite. File and archive
validation share one semantic navigation check, so a stale or altered `navigation.json` is rejected
even when its modified SHA-256 and node count are also written into the manifest. Mutation probes
reject stale hashes, removed topics, wrong locales, English root-label fallback, unsafe labels and
external URLs, and embedded HTML tree copies; reviewed BPM/CIS/API/DevOps labels remain accepted.
Focused gate/API/locale tests pass, real manifest generation and archive verification pass, and the
full documentation contract suite passes. M10-09 is next.

Evidence: `BPM091-M10-09` is accepted in
`documentation/config/documentation-navigation-language-browser-qa-0.9.1.json`. The maintained
matrix binds all six locales to exact DITA title/short-description/paragraph text and the runtime
catalog value for All settings, both desktop and narrow viewports, the four current guide nodes,
and the retired API-guide exclusion. The shared Chromium navigation scenario proves one successful
same-locale source load, direct root/document/section/topic activation, parent/root/history return,
corrected interface names, representative localized prose, and absence of frozen English source
sentences in every non-English locale. It then removes each locale's `navigation.json` in turn and
verifies the localized working fallback without article-column shift. The long-tree scenario uses
native wheel input and keyboard End in both viewports for every locale, keeps active items visible,
and proves sidebar scrolling does not move the article viewport. Both focused scenarios and the
complete six-scenario browser gate pass in a single-process, disk-backed Chromium run. Milestone 10
is complete; M11-01 is next.

## Milestone 5: Minimal User Guide Screenshots For All Locales

Goal: remove the screenshot release blocker by generating and integrating the basic localized User
Guide screenshots only.

| ID | Task | Essence | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- |
| `BPM091-M5-01` | Freeze screenshot fixture data and capture states. | Ensure each screenshot uses deterministic seed profiles, locale, route, theme, viewport, schema channel, and UI state. | high | Fixture setup is reproducible; screenshot failures name locale, topic, route, and state; no production database or local user data is required. |
| `BPM091-M5-02` | Generate the minimal User Guide screenshots for all six locales. | Capture the approved screenshot matrix in `en`, `ru`, `de`, `zh-CN`, `fr`, and `es-ES`. | extra high | Every matrix row has a current screenshot showing the matching locale and 0.9.1 UI; browser execution uses the dedicated immediately escalated screenshot command. |
| `BPM091-M5-03` | Optimize and normalize screenshot assets. | Keep generated images reviewable, deterministic where possible, and suitable for documentation output. | medium | Assets have approved dimensions, file names, compression, metadata handling, and storage location; oversized, stale, cross-locale, or orphaned images fail checks. |
| `BPM091-M5-04` | Integrate screenshots into User Guide topics. | Add stable image keys, localized captions, and localized alt text to the relevant User Guide topics. | high | Built documentation resolves the correct locale-specific image and text; no localized topic falls back to another locale's screenshot or alt text. |
| `BPM091-M5-05` | Run localized screenshot visual QA. | Manually or semi-automatically review the final screenshots for readability and locale correctness. | high | QA evidence covers all six locales, representative desktop and narrow layouts where included in the matrix, no clipped labels, no stale UI, and no English UI in non-English screenshots except allowlisted identifiers. |

## Milestone 6: Documentation Sufficiency And Linux Source-Install Coverage

Goal: prove the documentation lets users and administrators perform the documented work and obtain
the expected result.

| ID | Task | Essence | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- |
| `BPM091-M6-01` | Review User Guide task sufficiency. | Execute or simulate every primary User Guide workflow against the current BPM UI. | Extra High | Each task has prerequisites, exact steps, expected result, recovery path, and a successful execution record; omissions or stale UI references block release. |
| `BPM091-M6-02` | Review Firefox Policy and CIS guide sufficiency. | Verify that policy and CIS reference topics support practical configuration decisions without overstating guarantees. | High | Representative policies, managed preferences, CIS levels, manual-review states, examples, and links are accurate against current schemas and mappings. |
| `BPM091-M6-03` | Review Administrator and DevOps guide sufficiency. | Verify source deployment, update, health, troubleshooting, and integration workflows against current product behavior. | Extra High | A maintainer-readable review record proves the documented procedures reach the stated result or explicitly records a corrected limitation. |
| `BPM091-M6-04` | Select the five Linux distributions for source-install docs. | Use the M2 selection rules to choose the worldwide-popular distribution set for 0.9.1. | Medium | The selected five distributions, source date, evidence, and any maintainer approval are recorded before command topics are authored. |
| `BPM091-M6-05` | Author exact Linux source-install command sequences. | Add distribution-specific source-install steps for the selected five Linux distributions. | Extra High | Each selected distro has copy-pasteable commands for prerequisites, repository checkout, Python environment, dependency install, configuration, database/runtime setup, service start, health/readiness checks, log inspection, and first administrative smoke check. |
| `BPM091-M6-06` | Validate Linux source-install commands. | Check the command sequences with the safest practical automated and manual evidence. | High | Static command checks, container or clean-host evidence where available, health/readiness probe examples, and documented stop conditions pass for all selected distributions; unsupported production claims are absent. |
| `BPM091-M6-07` | Add sufficiency drift checks. | Make stale commands, missing expected results, and unverified task paths visible in future documentation updates. | High | Focused documentation tests or checklists fail when required procedure fields, command blocks, result assertions, or guide links are missing. |

## Milestone 7: Localization Terminology And Anti-Anglicism Cleanup

Goal: remove non-allowlisted English wording from localized UI and documentation while preserving
stable technical identifiers.

| ID | Task | Essence | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- |
| `BPM091-M7-01` | Inventory visible English in localized surfaces. | Scan localized BPM UI catalogs, documentation topics, documentation search UI, navigation, screenshots, captions, and alt text for English words and phrases. | high | A reviewable inventory classifies each finding as replace, allowlist, brand, identifier, command/path/API, abbreviation, or false positive for every non-English locale. |
| `BPM091-M7-02` | Update locale terminology sources. | Align BPM glossary and visible-English allowlists with Mozilla Pontoon and SUMO terminology for each locale. | high | Each replacement term has an authority note or maintainer-approved fallback; allowlists contain only stable technical English that should remain untranslated. |
| `BPM091-M7-03` | Replace non-allowlisted anglicisms in localized copy. | Update UI catalogs, DITA topics, search labels, navigation labels, captions, alt text, and help tooltips where English leaked into non-English locales. | high | `ru`, `de`, `zh-CN`, `fr`, and `es-ES` use established local terms; English remains only where the updated allowlist permits it. |
| `BPM091-M7-04` | Add anti-anglicism locale checks. | Extend locale validation so accidental English regressions are caught before release. | high | Checks fail on non-allowlisted English tokens in localized product and documentation strings while avoiding false failures for identifiers, commands, brands, and abbreviations. |
| `BPM091-M7-05` | Run human-oriented locale QA. | Review terminology, overflow, CJK layout, screenshot text, and search/filter copy in rendered pages. | extra high | Locale QA evidence covers all five non-English locales; every remaining English item is either fixed or explicitly allowlisted with rationale. |

## Milestone 8: Documentation Topic Section Hierarchy

Goal: add a localized section level between document nodes and topic nodes so long documentation
topic lists are grouped into easier-to-scan branches.

| ID | Task | Essence | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- |
| `BPM091-M8-01` | Audit long document topic lists. | Inspect generated guide/document trees and identify where a flat topic list is too long to navigate comfortably. | medium | A bounded audit names every guide/document that needs section grouping, records current topic counts, and excludes documents whose topic list is already short enough. |
| `BPM091-M8-02` | Define section taxonomy for each affected document. | Group topics by user intent, administrator workflow, reference area, or troubleshooting domain without changing stable topic URLs. | high | Every affected topic has exactly one section owner; section labels are stable, localizable, and consistent with existing guide terminology; no topic IDs or manifest targets are renamed only for grouping. |
| `BPM091-M8-03` | Implement section nodes in the documentation tree. | Extend the static portal tree builder so guide/document nodes expand to localized section nodes before topic nodes. | High | The sidebar renders root -> document -> section -> topic, preserves current-topic expansion, supports collapse/expand and keyboard navigation, and keeps direct topic links working. |
| `BPM091-M8-04` | Localize section labels and tree states. | Add locale-owned labels for the new section level and verify active/expanded states in all six locales. | High | `en`, `ru`, `de`, `zh-CN`, `fr`, and `es-ES` show localized section labels; no non-English tree section falls back to English except allowlisted identifiers. |
| `BPM091-M8-05` | Add section-level navigation tests and smoke coverage. | Protect root, document, section, and topic navigation behavior after adding the extra hierarchy level. | High | Contract/unit/browser checks cover root focus, document expansion, section expansion, active topic highlighting, parent/root return, responsive layout, and localized labels. |

## Milestone 9: All Settings Per-Setting Documentation Links

Goal: add a consistent circled-info link to every All Settings row so users can reach the relevant
Firefox setting or policy documentation.

| ID | Task | Essence | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- |
| `BPM091-M9-01` | Audit current All Settings documentation targets. | Compare All Settings inventory entries with Firefox Policy Guide topics, managed-preference references, and existing contextual help helpers. | High | Every policy, known managed preference, unknown/raw setting, and generated inventory entry has a documented target, fallback target, or explicit no-link disposition. |
| `BPM091-M9-02` | Generate or validate the per-setting help target map. | Tie All Settings entries to manifest-backed documentation targets without hardcoding translated URLs. | High | Target validation covers Release and ESR policy differences, managed preferences, aliases, removed/deprecated items, and missing documentation artifacts. |
| `BPM091-M9-03` | Render the circled-info link in All Settings rows. | Place the link to the right of each setting or policy row in the same style as existing BPM contextual documentation links. | High | Review, Configured, Catalog, search-result, and paginated/expanded row states show a stable accessible `i` link when a valid target exists, without shifting row layout or hiding primary actions. |
| `BPM091-M9-04` | Localize row help labels and tooltips. | Provide useful localized accessible names for the per-setting documentation links. | Medium | All six locale catalogs include labels/tooltips; no non-English locale shows accidental English except allowlisted identifiers. |
| `BPM091-M9-05` | Handle missing or unsupported documentation targets safely. | Avoid broken links when docs are unavailable, a setting is unknown, or a policy has no generated topic. | High | Rows omit or disable the help link according to the contract, expose no broken href, and show no noisy error state during normal editing. |
| `BPM091-M9-06` | Add All Settings help-link tests and smoke. | Protect the new row-level help behavior across modes and locales. | Extra High | Unit/DOM tests and Chromium smoke cover representative policies, known preferences, unknown/raw entries, all three modes, search results, long-label locales, keyboard access, and new-tab target behavior. |

## Milestone 10: Documentation Navigation, Guide Consolidation, And Locale Completion

Goal: remove the remaining navigation and localization defects before maintained documentation is
declared current: give the sidebar an independent scroll area, remove the obsolete standalone API
guide, and make every localized topic title and sentence use the corresponding BPM UI terminology.

| ID | Task | Essence | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- |
| `BPM091-M10-01` | Audit the remaining navigation, guide, and locale defects. | Freeze the affected sidebar layouts, standalone API-guide references, interface-name mismatches, and visible-English findings before editing generated/source ownership boundaries. | High | A bounded audit covers all six locales and every guide, identifies sidebar overflow at representative viewports, maps every API-guide topic/target to Administrator Guide ownership, and records every non-allowlisted English title or sentence with its source file and replacement authority. |
| `BPM091-M10-02` | Add independent scrolling to the documentation sidebar tree. | Keep the document/section/topic tree navigable without scrolling the article viewport. | High | Desktop and narrow layouts provide a visible, keyboard- and pointer-operable sidebar scroll area with bounded height; active direct-linked topics scroll into view; article and sidebar positions remain independent; no tree control, focus ring, long label, or horizontal content is clipped. |
| `BPM091-M10-03` | Remove the obsolete standalone API Integration Guide. | Publish API procedures only under the Administrator/DevOps Guide after confirming that re-homed topics are complete. | High | The aggregate portal, guide maps, navigation tree, search facets/indexes, manifests, guide selectors, and localized landing pages no longer expose a standalone API document; Administrator Guide retains every supported API workflow; old internal targets are redirected or deliberately retired without broken BPM context links. |
| `BPM091-M10-04` | Build the localized BPM interface-name authority map. | Derive documentation names for interfaces, modes, controls, and workflows from the runtime UI catalogs of each locale instead of translating English documentation labels independently. | High | The authority map covers all UI names used in topic titles, navigation labels, headings, captions, alt text, and prose, including All Settings; every entry points to a maintained locale-catalog key or an explicitly reviewed non-UI term. |
| `BPM091-M10-05` | Replace non-localized interface names in all documentation titles and navigation surfaces. | Make topic titles and generated navigation use the exact corresponding BPM UI term in each locale. | Extra High | All six locale sources, built topic titles, sidebar labels, breadcrumbs, search titles, captions, and cross-reference text match the authority map; Russian and other non-English locales contain no accidental `All Settings` or other source-locale UI names. |
| `BPM091-M10-06` | Perform a full visible-English review of localized documentation prose. | Review every non-English source topic rather than relying only on token scanning or the previous screenshot-oriented pass. | Extra High | Every title, paragraph, list item, note, warning, table cell, caption, alt text, search/navigation label, and generated visible string in `ru`, `de`, `zh-CN`, `fr`, and `es-ES` is reviewed; whole English sentences and fragments are replaced; remaining English is limited to recorded brands, identifiers, commands, paths, APIs, or established abbreviations. |
| `BPM091-M10-07` | Load the documentation tree from one generated navigation source per locale. | Stop embedding the complete localized document/section/topic tree into every HTML page; publish it once per locale and let the shared portal runtime construct the sidebar for the current URL. | High | Each locale publishes one deterministic, manifest-backed `navigation.json`; topic HTML contains only a bounded accessible sidebar host/fallback rather than a full duplicated tree; the shared script loads the same-origin source under `/help/`, renders escaped text without inline script/style or CSP relaxation, derives and expands the root/document/section/topic path from the canonical current URL, restores the correct active item and sidebar position for direct contextual links, preserves pointer and full keyboard/tree semantics, exposes a localized non-broken unavailable state when loading fails, and introduces no network dependency outside the installed documentation artifact. Contracts prove schema/locale/topic completeness and absence of embedded full-tree copies; browser checks cover loading, failure, direct-topic activation, navigation, narrow layout, and no incoherent layout shift. |
| `BPM091-M10-08` | Add fail-closed guide, navigation-source, and locale regression gates. | Prevent the API guide, duplicated/stale navigation trees, mismatched UI names, or unreviewed English prose from returning. | High | Contracts fail on standalone API-guide publication, missing Administrator API ownership, missing or stale per-locale navigation sources, embedded full-tree copies, navigation/manifest divergence, unsafe or fallback tree labels, UI-term/catalog divergence, English title/sentence leakage, locale fallback, missing review coverage, and stale allowlist entries while avoiding false failures for approved technical tokens. |
| `BPM091-M10-09` | Run six-locale navigation and language browser QA. | Verify the independently scrolling asynchronously loaded tree and corrected localized copy in rendered documentation. | Extra High | Chromium/Selenium covers successful and failed navigation-source loading, desktop and narrow sidebars, wheel/pointer and keyboard scrolling, direct-topic auto-reveal, root/parent return, absence of the API document, representative long trees, corrected interface names, and representative prose in all six locales with no overlap, incoherent loading shift, or English leakage. |

## Milestone 11: Live Source Installation Validation

Goal: execute the documented source-install procedures in disposable Docker environments for the
five frozen Linux targets, preserve complete evidence, investigate WSL only on genuine Windows
10/11 hosts, and retain the successfully installed Docker Engine, clean golden target images,
failed/evidence-needed containers, and dedicated network as bounded maintainer-approved
experimental tooling. Successful derivative install state may be removed by exact recorded identity
after evidence handoff without deleting its golden image.

| ID | Task | Essence | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- |
| `BPM091-M11-01` | Freeze the privileged validation and retained-environment contract. | Record host state, exact distro images, network/storage limits, evidence paths, privilege boundaries, rollback, and retained-tooling policy before Docker installation. | High | The maintainer approves the privileged boundary; pre-existing Docker state is distinguished from task-owned validation state and approved retained Docker tooling; five image/version identities match the M6 selection; commands cannot access user data or production services; failed-install rollback and final M11-resource inventory/handoff are explicit. |
| `BPM091-M11-02` | Install and verify Docker Engine for the validation run. | Install the minimum supported Docker components with maintainer-approved elevation and prove an isolated container can run. | High | Docker packages, daemon/runtime status, versions, repository source, group/socket permissions, disk usage, and a disposable smoke container are recorded; no unrelated host service or firewall setting is changed. |
| `BPM091-M11-03` | Build the clean-container source-install harness. | Convert the documented procedures into a repeatable runner that starts from each exact base image and captures every command, exit code, output, probe, and artifact. | Extra High | The harness uses fresh uniquely named containers, records container-only setup separately from documentation-owned commands, distinguishes container limitations from documentation defects, captures deterministic logs, stops and retains every attempt, and retries only in a new container without reusing installed state. |
| `BPM091-M11-04` | Validate Ubuntu 26.04 LTS installation live. | Execute the complete Ubuntu source-install procedure in its clean container. | Extra High | Prerequisites, checkout, Python environment, dependency install, configuration, migration, documentation build/install, BPM start, health/readiness/API/UI probes, log inspection, shutdown, and rerun behavior pass with a complete transcript or create an explicit blocking defect. |
| `BPM091-M11-05` | Validate Debian 13.5 installation live. | Execute the complete Debian source-install procedure in its clean container. | Extra High | The full documented Debian command sequence and observable results pass from a clean image, including BPM/documentation startup and shutdown, or the task records and fixes a reproducible blocking defect. |
| `BPM091-M11-06` | Validate Fedora Linux 44 installation live. | Execute the complete Fedora source-install procedure in its clean container. | Extra High | The full documented Fedora command sequence and observable results pass from a clean image, including package/Python differences and BPM/documentation probes, or the task records and fixes a reproducible blocking defect. |
| `BPM091-M11-07` | Validate Linux Mint 22.3 installation live. | Execute the complete Mint source-install procedure against a verified Mint-equivalent container image. | Extra High | The image provenance and Mint release identity are proven; the full documented sequence and probes pass without silently substituting Ubuntu behavior, or lack of a faithful image remains an explicit release blocker rather than simulated success. |
| `BPM091-M11-08` | Validate Manjaro stable installation live. | Execute the complete Manjaro stable source-install procedure against a pinned snapshot/container. | Extra High | Snapshot identity and package state are recorded; the full documented sequence, BPM/documentation probes, and shutdown pass, or image/runtime limitations remain an explicit release blocker rather than simulated success. |
| `BPM091-M11-09` | Reconcile Linux procedures with live evidence. | Correct commands, expected results, recovery steps, and limitations found by the five clean-container runs. | High | All six locale peers preserve command parity, every correction links to a transcript, clean reruns pass for changed procedures, and the sufficiency record no longer treats container simulation as clean-host evidence beyond its documented boundary. |
| `BPM091-M11-10` | Prepare a genuine WSL validation runner and feasibility record. | Reuse the source-install assertions on WSL without pretending that a Linux container can emulate the Windows kernel, WSL integration, or host networking. | High | The runner checks WSL version, distro identity, Windows build, systemd mode, filesystem location, localhost behavior, browser access, shutdown/restart, and evidence capture; it states that actual Windows hosts are required. |
| `BPM091-M11-11` | Validate the WSL procedure on Windows 10 when a host is available. | Run the documented workflow on an actual supported Windows 10 plus WSL environment. | Extra High | A real Windows build and WSL version are recorded and the full install/start/probe/restart/shutdown workflow passes; if no suitable host is supplied, the backlog records the unverified boundary and makes no Windows 10 validation claim. |
| `BPM091-M11-12` | Validate the WSL procedure on Windows 11 when a host is available. | Run the documented workflow on an actual supported Windows 11 plus WSL environment. | Extra High | A real Windows build and WSL version are recorded and the full install/start/probe/restart/shutdown workflow passes; if no suitable host is supplied, the backlog records the unverified boundary and makes no Windows 11 validation claim. |
| `BPM091-M11-13` | Stop, inventory, and hand off the validation environment. | Stop active validation processes and reconcile retained golden images, required containers, network, caches, derivative cleanup, and evidence without deleting the approved experimental environment. | High | Every M11 container is stopped and inventoried with image/run/target/attempt/disposition/evidence metadata; failed or evidence-needed attempts remain; successful derivative state is removed only by exact ID after handoff when useful; Docker Engine, repository/key, services, data roots, memberless group, clean target images, and dedicated network remain healthy; task-owned storage stays below 200,000,000,000 bytes with at least 20 GiB host-free; no user gains Docker-group membership and unrelated host state is unchanged. |
| `BPM091-M11-14` | Close the live-install evidence record. | Reconcile all five mandatory Linux outcomes and the conditional Windows 10/11 WSL outcomes with release readiness. | Extra High | Each Linux target has a clean-run transcript and final disposition; unresolved mandatory failures block release; WSL claims match actual-host evidence only; retained-environment inventory/handoff is complete; focused contracts link every documented command and expected result to retained evidence. |

Evidence: `BPM091-M11-01` is accepted in the machine-readable contract and maintainer-readable
decision record. The repeated read-only baseline proves Docker was absent on the Ubuntu 26.04
x86_64 host and records 224,906,842,112 free bytes (more than 200 GiB);
official-image digests are frozen for Ubuntu, Debian, and Fedora, a signed official ISO-derived
rootfs is required for Mint, and a pinned Manjaro seed requires a full stable update. Installation
is approved with strict isolation and persistent Docker retention after successful verification;
failed installation still rolls back fully. No privileged command or image pull has run yet.

Evidence: `BPM091-M11-02` installed exactly the five approved Docker packages from the signed
official `resolute/amd64` repository with no recommended packages or removals. Docker 29.6.1 and
containerd are active/enabled; the root-owned `0660` socket uses a memberless `docker` group and
the maintainer has no unprivileged access. The labeled `hello-world` amd64 smoke passed under the
approved CPU/RAM/PID/security limits, then its container, image, and network were removed. UFW and
nftables configuration hashes are unchanged, no unrelated persistent service setting changed,
more than 200 GiB remains free, and Docker is retained as approved tooling.

Evidence: `BPM091-M11-03` is accepted. The five-target harness extracts commands and stage order
from the English DITA topics, substitutes only the approved source-ref placeholder, records
container-only adapters separately, captures attempt-isolated plans/events/output/inspect/inventory,
and exposes no deletion path. The initial Ubuntu lifecycle attempt was retained after exposing a
PID 1/stop defect; a fresh second container passed Ubuntu 26.04 identity and exited `0`. A signed
official Linux Mint 22.3 Cinnamon ISO was verified against fingerprint and pinned SHA-256, its Zena
rootfs was imported without host mounts, and a fresh Mint container passed identity and exited `0`.
All four containers, both images, and the dedicated network are retained; every container is
stopped, retained Docker usage is about 3.23 GB, and 212,977,311,744 host bytes remain free.

## Milestone 12: Maintained Documentation, README, And Drift Gates

Goal: update maintained documentation after the feature work so the repository describes the actual
0.9.1 product state rather than the plan.

| ID | Task | Essence | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- |
| `BPM091-M12-01` | Refresh README current-state product documentation. | Describe the finished documentation UX, theme support, compact search, tree navigation, screenshots, Linux source-install coverage, localization quality, and All Settings help links without release-history phrasing. | Medium | README matches the implemented product, keeps primary product language English, preserves maintainer copyright and email-topic/message-theme information, and does not read like release notes. |
| `BPM091-M12-02` | Update product documentation for changed documentation UX. | Document how users navigate the independently scrolling documentation tree, use compact search and filters, switch themes, and follow per-setting All Settings help links. | High | User-facing topics describe the implemented behavior with all six localized peers, screenshots where in the approved matrix, no stale 0.9.0 portal instructions, and no reference to a standalone API guide. |
| `BPM091-M12-03` | Update screenshot and localization runbooks. | Record the minimal User Guide screenshot workflow and the anti-anglicism terminology workflow as maintained procedures. | Medium | Future documentation updates have explicit drift gates for screenshot matrix rows, localized captions/alt text, UI-catalog terminology authority, Pontoon/SUMO review, and visible-English allowlists. |
| `BPM091-M12-04` | Update documentation, schema, CIS, locale, and live-install drift gates. | Ensure changed docs/search/navigation/theme/link behavior and source-install evidence are covered by maintained update procedures. | High | Firefox schema, CIS, locale, Administrator/DevOps deployment, DevOps integration, update, and release procedures include the documentation and live-install drift checks introduced by this epic. |
| `BPM091-M12-05` | Close the 0.9.1 documentation sufficiency record. | Reconcile final guide coverage, screenshots, live Linux/WSL evidence, localization findings, search/navigation behavior, guide consolidation, and All Settings link mapping. | Extra High | Every requested 0.9.1 documentation outcome is complete or explicitly blocks release; the record names focused checks, retained transcripts, conditional WSL boundaries, and remaining non-goals. |
| `BPM091-M12-06` | Update docs index for maintained files. | Register any new or changed active architecture notes, runbooks, audits, and backlog files. | Light | `docs/docs-index.md` lists maintained documentation exactly once with correct status and keeps generated product docs, container state, and local artifacts out of the maintained index. |

## Milestone 13: Final Quality, Release Documentation, And Handoff

Goal: prove the 0.9.1 documentation completion epic is accurate, maintainable, and releasable.

| ID | Task | Essence | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- |
| `BPM091-M13-01` | Run static typing. | Execute `make typecheck` after implementation and focused documentation checks. | Light | Mypy passes with no new suppressions hiding documentation, theme, or All Settings defects. |
| `BPM091-M13-02` | Run lint. | Execute `make lint` across maintained product and documentation tooling sources. | Light | Ruff passes; generated/vendor output remains excluded by explicit ownership rules. |
| `BPM091-M13-03` | Run the complete pytest suite. | Execute `pytest -q` after focused suites pass. | Medium | The complete non-browser/non-live default suite passes with no unreviewed skips or xfails added for this epic. |
| `BPM091-M13-04` | Run full code-surface coverage. | Execute `make coverage` and inspect product plus documentation-owned reports. | High | Covered code surface is 100%; falling below 100% is not accepted as known debt - add focused tests, remove dead code, or eliminate unreachable paths. |
| `BPM091-M13-05` | Run full documentation validation. | Execute the complete documentation build and non-browser release gates from a clean output tree. | High | DITA, manifests, links, search indexes, screenshots, localized UI terminology, API-guide removal, sidebar navigation, live-install evidence, provenance, parity, accessibility, and sufficiency checks pass. |
| `BPM091-M13-06` | Run Chromium/Selenium BPM and documentation smoke. | Execute `make test-ui` and the dedicated documentation browser/screenshot suites with immediate sandbox escalation. | Extra High | Main BPM product logic, light/dark/system themes, compact search, independently scrolling tree, all six locales, screenshots, All Settings links, CSP, and `/docs` OpenAPI coexistence pass; no sandboxed browser trial run occurs first. |
| `BPM091-M13-07` | Verify implementation and maintained-documentation milestones. | Confirm M10, M11, and M12 are complete before release handoff. | Medium | Navigation/locale completion, guide consolidation, five-distro live evidence, conditional WSL boundaries, retained-container inventory, README, product documentation, runbooks, docs index, sufficiency record, and drift gates are complete and linked from release evidence. |
| `BPM091-M13-08` | Finalize the `0.9.1` changelog entry. | Record shipped documentation polish, navigation fixes, API-guide consolidation, localization cleanup, live source-install evidence, screenshots, and All Settings help links. | Light | The `0.9.1` changelog entry is complete, accurate, and preserves all previous release history. |
| `BPM091-M13-09` | Verify release-readiness procedures. | Check schema, CIS, locale, Administrator/DevOps deployment, DevOps integration, update, and release runbooks for the documentation drift gates changed by this epic. | Medium | Maintained runbooks require screenshot, locale terminology, documentation navigation, source-install/live-evidence, and per-setting help-link checks where relevant. |
| `BPM091-M13-10` | Create the completed-epic git commit. | Commit the approved 0.9.1 changes after all final checks pass. | Light | The commit contains only reviewed 0.9.1 work and no unrelated generated artifacts, caches, secrets, container state, or local screenshots outside the approved artifact policy. |
| `BPM091-M13-11` | Provide the maintainer-run push command. | Print the exact command the maintainer should run manually to push the completed branch. | Light | The assistant does not push; the final handoff includes the exact `git push` command and a concise summary of passed checks. |

## Execution Protocol

When executing this backlog interactively:

Unfinished-task reasoning levels are calibrated for `ChatGPT-5.6 Sol` and use only `Light`,
`Medium`, `High`, or `Extra High`. Completed tasks retain their historical planning values.

1. Show exactly one next task with its ID, essence, acceptance, and minimal reasoning.
2. Wait for explicit maintainer approval.
3. Execute only that approved task.
4. Report changed files and checks passed.
5. Show the next task for approval.

Do not start implementing a backlog task merely because this backlog exists.

## Backlog Creation Acceptance Checklist

- Target BPM version is present and normalized as `0.9.1`.
- Compact epic id is `BPM091`; task IDs follow `BPM091-M<milestone>-<two digits>`.
- Milestones are grouped by release anchors, contracts, visual/theme work, search/navigation,
  screenshots, sufficiency, localization, topic-section hierarchy, All Settings help links,
  final navigation/locale completion, live source-install validation, maintained documentation,
  and final quality.
- Every unfinished task is calibrated for `ChatGPT-5.6 Sol` with a `Light`, `Medium`, `High`, or
  `Extra High` minimal reasoning value; completed tasks may retain their historical planning value.
- The first milestone includes version transition, local editable-package metadata refresh,
  external dependency currency checks, changelog, README target-copy guard, release contract, and
  active release-name audit.
- Dedicated navigation/locale completion and live source-install milestones precede the maintained-
  documentation milestone and final quality.
- Final quality includes mypy, ruff, `pytest -q`, coverage-to-100%, documentation validation,
  Selenium/Chromium smoke with immediate escalation, documentation-update verification, changelog,
  docs index/runbook drift gates, commit, and maintainer-run push command.
- Browser UI, screenshot, Selenium, Docker installation, container execution, and host cleanup
  require the necessary approval/escalation during execution; browser commands are escalated
  immediately without a sandboxed trial run.
- README instructions preserve maintainer copyright and email-topic/message-theme information,
  avoid release-history phrasing, and forbid target-version anchors or placeholders.
- Changelog instructions preserve older version history.
- Product language remains English while maintainer chat may be Russian.
- Assumptions and non-goals are explicit, including the limited screenshot scope, the dated Linux
  distribution-selection requirement, mandatory clean-container evidence, genuine-Windows-only WSL
  claims, and bounded retention/inventory of the validation environment.
- Execution protocol requires explicit approval for each individual task.
