# BPM 0.9.1 Documentation Completion Release Contract

Date: 2026-07-06

Backlog item: `BPM091-M1-06`

## Purpose

This contract defines the release-blocking outcomes for the BPM 0.9.1 documentation completion
epic. It is a maintained checklist for finishing the 0.9.0 documentation portal quality loop, not
a claim that the 0.9.1 work is already implemented.

BPM currently has one project maintainer. The owner column therefore names both the accountable
maintainer and the functional ownership area that must be reviewed. Ownership may be delegated
later, but no gate becomes ownerless.

Verification commands name implemented Make targets or exact focused checks. A missing command is a
failed release gate, not permission to verify the outcome manually and ship anyway. Generated
reports are release evidence and must remain outside hand-edited DITA source unless an approved
artifact policy says otherwise.

README is not a version surface. Version-specific planning, release status, and completion notes
belong in the backlog and `CHANGELOG.md`; README may change only for durable current-state product
facts after implementation.

## Blocking Gates

Every gate below is release-blocking. `Closed` means the recorded command passed for completed work;
`Open` means implementation or verification is still required.

| Gate | Required outcome | Accountable owner | Required evidence | Verification command | State |
| --- | --- | --- | --- | --- | --- |
| `DOC091-G01` | Package, runtime, active metadata, local editable package metadata, and version tests agree on BPM 0.9.1. | Project maintainer - release metadata | Version contract tests, `pip show browser-policy-manager`, and active release surfaces. | `pytest -q tests/integration/app/test_current_version_surfaces.py tests/unit/app/test_bootstrap_config.py::test_settings_version_matches_pyproject` | Closed |
| `DOC091-G02` | Dependency and toolchain currency is reviewed without hidden upgrades in feature work. | Project maintainer - dependency policy | `docs/architecture/dependency-currency-0.9.1.md` with Python, frontend, documentation toolchain, browser-driver, and test/dev decisions. | `pytest -q tests/contract/docs/general/test_docs_index.py tests/integration/app/test_current_version_surfaces.py::test_current_version_surfaces_follow_pyproject` | Closed |
| `DOC091-G03` | Changelog has a non-final 0.9.1 landing zone, while README has no target-version anchor, active-target note, planned-for-version copy, or completion placeholder. | Project maintainer - release documentation | Changelog entry, README guard assertions, and runbook rule forbidding README version anchors. | `pytest -q tests/integration/app/test_current_version_surfaces.py tests/contract/testing/test_runbook_make_targets_contract.py::test_epic_backlog_creation_runbook_defines_versioned_backlog_contract` | Closed |
| `DOC091-G04` | The minimal User Guide screenshot matrix is defined, captured, optimized, integrated, and reviewed for `en`, `ru`, `de`, `zh-CN`, `fr`, and `es-ES`. | Project maintainer - localized visual documentation | Screenshot matrix, deterministic fixtures, generated assets, captions, localized alt text, freshness/orphan/size reports, and visual QA record. | `./.venv/bin/pytest -q -m docs_contract documentation/tests/contract/test_user_guide_screenshot_matrix.py documentation/tests/contract/test_user_guide_screenshot_visual_qa.py` and `make test-docs-browser` | Closed |
| `DOC091-G05` | Documentation visual design matches the main BPM interface and supports light, dark, and system theme modes. | Project maintainer - documentation UI and accessibility | Theme contract, CSS/token review, rendered page evidence, contrast checks, responsive snapshots, and no pure-white primary light surfaces. | `make test-docs-ui`, `make test-docs-browser`, and `make docs-release-check` | Closed |
| `DOC091-G06` | Main BPM light theme uses comfortable light-gray primary surfaces instead of harsh white while preserving accessible contrast and focus states. | Project maintainer - BPM frontend UI | CSS token audit, updated app theme tokens, contrast/layout evidence, and representative route screenshots or browser assertions. | `make test-ui` and `make test-release` | Closed |
| `DOC091-G07` | Documentation search defaults to a compact one-line control, expands deliberately, keeps deterministic ranking stable, and localizes every visible filter label. | Project maintainer - documentation search and localization | Search UI contract, locale catalog changes, search quality fixture rerun, filter-label parity, and empty-result recovery evidence. | `make test-docs`, `make test-docs-contract`, and `make test-docs-ui` | Closed |
| `DOC091-G08` | Documentation navigation uses a single hierarchical tree for documentation home, guide/document nodes, and topic nodes, with reliable return to parent and root. | Project maintainer - documentation information architecture | Tree-navigation contract, manifest/map evidence, keyboard semantics, direct URL/back-forward/root return evidence, and no duplicated guide titles in page headers. | `make test-docs-contract`, `make test-docs-ui`, and `make test-docs-browser` | Closed |
| `DOC091-G09` | Documentation sufficiency review proves users and administrators can complete documented tasks and obtain the stated result. | Project maintainer - documentation accuracy | User Guide, Firefox Policy, CIS, Administrator/DevOps review records; expected-result and recovery-path evidence; drift checks for missing procedure fields. | `make test-docs-contract` and `make docs-release-check` | Closed |
| `DOC091-G10` | Linux source-install documentation covers exact commands for the five selected worldwide-popular distributions, chosen by a dated recorded decision. | Project maintainer - Administrator/DevOps documentation | Distribution-selection note, command topics, static command checks, retained clean-image live transcripts, health/readiness probes, and unsupported-production boundary review. | `./.venv/bin/pytest -q -m docs_contract documentation/tests/contract/test_live_source_install_evidence_closure.py` and `make docs-release-check` | Closed |
| `DOC091-G11` | Non-English localized UI and documentation remove non-allowlisted English and use established locale terms guided by Mozilla Pontoon and SUMO terminology. | Project maintainer - localization and terminology | Visible-English inventory, updated glossary/allowlists, replacement record, screenshot text review, and human-oriented locale QA evidence. | `make test-locale-contract`, `make test-docs-contract`, and `make test-docs-ui` | Closed |
| `DOC091-G12` | All Settings rows expose manifest-backed circled-info documentation links for every policy or setting with a valid Firefox documentation target. | Project maintainer - All Settings and contextual documentation links | Target-map audit, per-setting target validation, row rendering changes, localized labels/tooltips, missing-target disposition, keyboard evidence, and new-tab behavior. | `./.venv/bin/pytest -q -m docs_contract documentation/tests/contract/test_all_settings_help_target_map.py documentation/tests/contract/test_all_settings_row_help_link_contract.py` and `make test-ui` | Closed |
| `DOC091-G13` | Maintained docs, runbooks, docs index, and drift gates reflect the finished 0.9.1 documentation UX and prevent future drift. | Project maintainer - maintained documentation | Updated product documentation, screenshot/localization runbooks, schema/CIS/locale/Admin/DevOps/update/release drift gates, docs index, and sufficiency record. | `make test-docs-contract` and `pytest -q tests/contract/docs/general/test_docs_index.py` | Closed |
| `DOC091-G14` | Final product quality, documentation validation, coverage, browser smoke, changelog finalization, commit, and maintainer-run push handoff are complete. | Project maintainer - BPM release | Passing full suites, 100% covered code surface, final 0.9.1 changelog entry, no README version anchor, clean commit, and printed push command. | `make typecheck`, `make lint`, `pytest -q`, `make coverage`, `make docs-release-check`, `make test-ui`, and `make test-release` | Open |

## M13-07 Maintained Milestone Handoff

This release-evidence map confirms that the implementation and maintained-documentation milestones
needed before final changelog and repository handoff are complete. It does not close `DOC091-G14`;
M13-10 and M13-11 remain required.

| Milestone | Verified scope | Maintained completion evidence | State |
| --- | --- | --- | --- |
| `M10` | Navigation and locale completion, four-guide/API consolidation, interface-name authority, visible-prose review, and shared sidebar/search generation. | [Navigation/locale completion audit](../../documentation/config/documentation-navigation-locale-completion-audit-0.9.1.json), [API re-home audit](api-integration-rehome-audit-0.9.0.json), and [documentation sufficiency closure](documentation-sufficiency-closure-0.9.1.json). | Closed |
| `M11` | Five-distribution live Linux evidence, explicit conditional Windows 10/11 WSL non-claims, and retained Docker/container/image/network inventory. | [Five-distribution validation](linux-source-install-validation-0.9.1.json), [M11 evidence closure](../../documentation/evidence/live-source-install/0.9.1/m11-14-evidence-closure-20260715/closure.json), [retained environment inventory](../../documentation/evidence/live-source-install/0.9.1/m11-13-validation-environment-handoff-20260715/retained-inventory.json), [Windows 10 WSL outcome](../../documentation/evidence/live-source-install/0.9.1/m11-11-windows10-wsl-20260715/run-manifest.json), and [Windows 11 WSL outcome](../../documentation/evidence/live-source-install/0.9.1/m11-12-windows11-wsl-20260715/run-manifest.json). | Closed within recorded Linux-userspace and conditional-WSL boundaries |
| `M12` | Durable README product facts, product documentation, maintained runbooks, documentation index, final sufficiency record, and fail-closed drift gates. | [README](../../README.md), [documentation runbooks](../../documentation/runbooks/README.md), [documentation index](../docs-index.md), and [documentation sufficiency closure](documentation-sufficiency-closure-0.9.1.json). | Closed |

## Gate Closing Rules

1. A gate closes only after its implementation is complete and every listed command exists and
   passes against a clean generated-output state.
2. Evidence must identify the BPM version, documentation build version, locale set, Firefox schema
   channels, CIS source versions, screenshot matrix revision, and browser/driver versions relevant
   to that gate.
3. All six locales are required for localized documentation, search labels, captions, alt text,
   screenshots, contextual help labels, and terminology checks.
4. Falling below 100% coverage for owned executable code is not accepted as known debt.
5. Browser, Selenium, and screenshot commands require immediate sandbox escalation; do not attempt
   them in the filesystem sandbox first.
6. Search remains deterministic and offline. LLMs, embeddings, vector databases, RAG, generative
   answers, runtime hosted search, and telemetry are prohibited for this release.
7. README must remain current-state product documentation only. A release gate cannot be closed by
   adding README target-version copy.
8. A backlog checkbox, manually opened page, or ad hoc command does not replace the named release
   command and its reproducible evidence.
9. Any product, API, Firefox schema, CIS mapping, locale, route, theme, screenshot, search,
   navigation, packaging, or documentation-link change reopens every gate whose evidence may have
   become stale.
10. Any source-install command, prerequisite, runtime probe, update step, or integration contract
    change reopens `DOC091-G09`, `DOC091-G10`, and affected packaging/navigation gates. Linux
    evidence must be rerun from the retained clean image into a new immutable attempt; accepted
    transcripts are never edited. Docker Engine, clean images, stopped validation containers, and
    the dedicated network remain retained unless a separate cleanup task is approved.
11. Windows 10/11 WSL remains `unverified-no-actual-host-supplied` until the maintained PowerShell
    runner succeeds on each corresponding actual Windows host. Docker, Linux containers, and ISO
    inspection do not close a WSL gate.
12. Schema/CIS/locale/API/route changes also revalidate same-locale `navigation.json`, deterministic
    search, compact filters, light/dark/system theme behavior, direct-topic reveal/root return,
    Administrator API ownership, and policy/preference help-target dispositions where applicable.

## Explicitly Deferred Outcomes

The following outcomes do not block 0.9.1 because they are outside the approved epic scope:

- full screenshot coverage for every guide family beyond the minimal User Guide matrix;
- packaged installers, official service units, supported HA clustering, production hardening,
  managed secrets, official reverse-proxy recipes, rolling upgrades, and automatic restore
  automation;
- distribution package support or source-install variants beyond the five selected Linux
  distributions;
- AI-assisted documentation search or question answering;
- extraction into a separate repository, service, or standalone product;
- new API endpoints or product-specific connectors created only for documentation examples.

Adding any deferred outcome requires a separately approved backlog task or epic; it must not be
silently folded into a release gate above.
