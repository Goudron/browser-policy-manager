# BPM 0.9.2 UI Compaction And Documentation Coherence Release Contract

Date: 2026-07-17

Backlog item: `BPM092-M1-06`

## Purpose

This contract defines the release-blocking outcomes for BPM 0.9.2. It maps the approved UI
compaction and documentation-coherence epic to maintained evidence and verification commands. It
is a planning and release-control document, not a claim that any open outcome has shipped.

BPM has one project maintainer. The owner column therefore names both the accountable maintainer
and the functional ownership area that must be reviewed. Ownership may be delegated later, but no
gate becomes ownerless.

The earlier approximate fivefold density figure is diagnostic only. The release objective is to
remove every classified non-essential explanatory node and every visible duplicate, not to stop at
an arbitrary percentage. It does not authorize removal of labels, values, actions, errors,
validation, state, destructive-action consequences, recovery paths, accessibility text, or
irreducible domain distinctions. Any exception must name the protected information and reason in
the M2 density evidence.

Documentation is product UI. It uses the BPM product version as its only visible version. Any
retained documentation artifact or compatibility field must derive from that source and must not
be presented as an independently owned documentation version.

## Blocking Gates

Every gate below is release-blocking. `Closed` means the recorded outcome and its required command
have passed for the completed scope; `Open` means implementation or verification remains. A
backlog checkbox, a manually opened page, or an ad hoc command does not close a gate.

| Gate | Required outcome | Accountable owner | Required evidence | Verification command | State |
| --- | --- | --- | --- | --- | --- |
| `BPM092-G01` | Package, runtime, active metadata, local editable metadata, and active-version tests agree on BPM 0.9.2; historical 0.9.1 records remain distinguishable from current sources. | Project maintainer - release metadata | `pyproject.toml`, current-system map, docs index, release-name audit, editable-package probe, and version tests. | `./.venv/bin/pytest -q tests/test_current_version_surfaces.py tests/test_bootstrap_config.py tests/test_docs_index.py` | Open |
| `BPM092-G02` | Dependency, frontend vendor, documentation toolchain, browser-driver, and test/dev currency is reviewed without hidden upgrades in feature work. | Project maintainer - dependency policy | [Dependency currency decision](dependency-currency-0.9.2.md), package manifests, lockfiles, and recorded deferred-update disposition. | `./.venv/bin/pytest -q tests/test_docs_index.py tests/test_current_version_surfaces.py::test_current_version_surfaces_follow_pyproject` | Closed |
| `BPM092-G03` | Changelog has a non-final 0.9.2 landing section while README remains durable current-state product documentation with no target-version or completion copy. | Project maintainer - release documentation | `CHANGELOG.md`, README guard assertions, and backlog/runbook release-boundary rules. | `./.venv/bin/pytest -q tests/test_current_version_surfaces.py tests/test_runbook_make_targets_contract.py::test_epic_backlog_creation_runbook_defines_versioned_backlog_contract` | Closed |
| `BPM092-G04` | The rendered-copy inventory, protected-copy dispositions, per-surface density budgets, contextual-help map, unified header contract, documentation audience/editorial contract, and search-panel-state contract exist before UI removal. | Project maintainer - UX and documentation architecture | M2 inventories, classifications, budgets, exception records, target map, header contract, editorial contract, state model, and focused guard fixtures. | `make test-ui`, `make test-docs-contract`, and focused M2 contract tests | Open |
| `BPM092-G05` | Shared product chrome, Library, Compare, and all three editor routes remove redundant explanation while preserving compact, accessible labels, actions, state, and safety feedback. | Project maintainer - BPM frontend UI | M3-M5 source changes, localized catalogs, density measurements, responsive/accessibility records, and route-state evidence. | `make test-ui` and focused M3-M5 tests | Open |
| `BPM092-G06` | Guided, All Settings, and JSON editors meet their approved density budgets and add circled-info targets only where the M2 map proves a genuine comprehension gap. | Project maintainer - editor UX and contextual help | M6-M8 measurements, localized UI strings, help-target dispositions, generated manifests, and workflow/browser evidence. | `make test-ui`, `make test-docs-contract`, and focused M6-M8 tests | Open |
| `BPM092-G07` | Documentation has the same normalized BPM header, visual system, locale/theme behavior, and product-version ownership as the main UI; no independently visible documentation version remains. | Project maintainer - documentation UI | M9 header/version/token contracts, generated portal evidence, source ownership records, six-locale checks, and browser parity results. | `make test-docs-ui`, `make test-docs-contract`, and `make test-docs-browser` | Open |
| `BPM092-G08` | Advanced search-filter visibility is controlled only by the explicit toggle; searches, URL/history hydration, results, clear, and active filters preserve the user's collapsed or expanded choice. | Project maintainer - documentation search | M2 state contract, M9 implementation/tests, keyboard/history evidence, and collapsed active-filter summary evidence. | `make test-docs`, `make test-docs-ui`, and `make test-docs-browser` | Open |
| `BPM092-G09` | Product documentation addresses users, administrators, DevOps, and API integrators rather than maintainers; all locales use reviewed natural titles and prose, including idiomatic Russian nominal headings. | Project maintainer - documentation editorial and localization | M10 audience inventory, terminology/style review, locale evidence, visible-English review, retained support-boundary record, and the fail-closed six-locale editorial sign-off registry. | `make test-locale-contract`, `make test-docs-contract`, focused M10 checks, and `make docs-release-check` | Open |
| `BPM092-G10` | Product documentation, contextual topics, target maps, manifests, search metadata, screenshots, authoring guidance, drift procedures, and docs index reflect the shipped compact UI. | Project maintainer - maintained documentation | [M13-08 documentation-update verification](documentation-update-milestone-verification-0.9.2.md), M11 DITA sources and locale peers, M12 Firefox 153 dual-ESR documentation, target/search/manifests, screenshot evidence, runbooks, README decision, and docs index. | `make docs-release-check`, `make test-docs-contract`, and `./.venv/bin/pytest -q tests/test_docs_index.py` | Closed |
| `BPM092-G11` | Static typing, lint, complete tests, 100% owned code coverage, documentation release validation, locale checks, and Chromium/Selenium smoke prove release quality. | Project maintainer - quality and release | M12 command records, coverage report, documentation/locale evidence, and browser results for product and documentation routes. | `make typecheck`, `make lint`, `pytest -q`, `make coverage`, `make docs-release-check`, `make test-ui`, and `make test-docs-browser` | Open |
| `BPM092-G12` | The final changelog records only shipped outcomes; README boundaries, maintained drift procedures, docs index, reviewed commit, and maintainer-run push handoff are complete. | Project maintainer - release handoff | Final M12-08 through M12-14 evidence, changelog review, README guard, [M13-11 drift-procedure verification](maintained-drift-procedures-verification-0.9.2.md), docs-index check, reviewed commit, and printed push command. | `./.venv/bin/pytest -q tests/test_current_version_surfaces.py tests/test_docs_index.py` and final M12 commands | Open |

## Evidence Handoff

| Backlog boundary | Release evidence owned by the boundary |
| --- | --- |
| M1 | Version anchors, editable-package metadata, dependency decision, changelog/README guard, this contract, and active-versus-historical naming audit. |
| M2 | Auditable baseline measurements and contracts that distinguish removable explanatory copy from protected information. |
| M3-M8 | Product UI implementation and focused evidence for shared chrome, Library, Compare, Guided, All Settings, JSON, accessibility, locales, and context help. |
| M9 | Generated documentation shell parity, single-version derivation, visual-token behavior, and persistent search-filter state. |
| M10 | User-facing audience/editorial and six-locale title/prose review evidence. |
| M11 | Updated DITA, localized help targets, generated metadata, screenshots, authoring/runbook drift controls, README decision, indexed maintained records, and the [M13-08 documentation-update verification](documentation-update-milestone-verification-0.9.2.md). |
| M12 | Firefox 153 three-channel documentation, schema guidance, targets, manifests/search, screenshots, contextual-help dispositions, focused evidence, and the [M13-08 documentation-update verification](documentation-update-milestone-verification-0.9.2.md). |

## Gate Closing Rules

1. A gate closes only after all required implementation and the named reproducible verification
   commands pass against the relevant clean generated-output state.
2. Every M2 `remove-explanation` node is removed and every `deduplicate` fact has one
   authoritative presentation. Word, node, and layout measurements are diagnostic evidence only;
   they do not permit a residual quota. A documented safety, accessibility, state, validation,
   recovery, or domain-meaning exception is outside density arithmetic and does not count as
   removable debt.
3. A removed explanation may be left without replacement when labels and context are sufficient.
   Contextual links are added only for an established comprehension gap and must be localized,
   keyboard accessible, manifest-valid, and sparse.
4. Documentation header parity is semantic and behavioral as well as visual: normalized slots,
   focus order, locale/theme controls, narrow layouts, browser title, and active-surface behavior
   must agree with the product header.
5. Search execution never changes advanced-filter expansion. Hidden active filters must remain
   discoverable and clearable without forcing the panel open.
6. Product DITA contains no address to the maintainer, implementation-progress narration, or
   roadmap language. Honest user/admin/DevOps/API support boundaries remain required.
7. All six locales require UI and documentation review. Russian headings use idiomatic nominal
   forms; other locales follow their own reviewed conventions rather than a mechanical translation
   rule. The editorial release-gate registry is fail-closed: each locale must contain an accepted
   review state and an acceptance marker in its review record before `make docs-release-check` can
   pass; pending manual review is never treated as acceptance.
8. Browser/Selenium validation covers Library, Guided, All Settings, JSON, Compare, documentation,
   unified headers, context help, themes, zoom, keyboard paths, locale behavior, and search-filter
   persistence. Browser evidence must record the relevant browser and driver versions.
9. Any change to compact-copy sources, header slots/tokens, routes, locale catalogs, documentation
   versions, help targets, manifests, search state, theme behavior, or screenshots reopens every
   gate whose evidence may be stale.
10. README remains current-state product documentation only. It cannot close a release gate by
    adding a target-version anchor, release history, plan, or completion placeholder.
11. No gate closes merely because its backlog task is marked complete. The final changelog is
    updated only with verified shipped behavior.

## Explicitly Deferred Outcomes

The following do not block 0.9.2 unless separately approved:

- a redesign unrelated to removing redundant explanatory UI copy or aligning documentation with
  the BPM product shell;
- dependency upgrades not accepted by the 0.9.2 dependency currency decision;
- new documentation topics not required by the approved contextual-help map;
- an independently branded documentation product, independently managed documentation version, or
  online/telemetry-backed search;
- removal of essential safety, validation, recovery, accessible, or domain-distinguishing text to
  satisfy a density measurement.

Adding a deferred outcome requires a separately approved backlog task or epic; it must not be
silently folded into a gate above.
