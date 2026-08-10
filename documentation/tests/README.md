# Focused Documentation Tests

Documentation tests remain inside this subsystem so documentation-only debugging does not require
the general BPM test tree.

- `unit/`: pure build/search/validation helper behavior with compact fixtures;
- `contract/`: DITA, IDs, manifests, locales, provenance, accessibility, security, links, assets,
  and deterministic artifact contracts;
- `browser/`: `/help/`, keyboard, responsive theme, search, locale, CSP, and screenshot behavior.

`suite-boundaries-0.9.0.json` is the machine-readable boundary contract for `BPM090-M11-02`. It
maps each documentation failure domain to a primary suite, owned fixtures, focused Make targets, and
the smallest focused rerun command. Keep it updated before adding or moving documentation tests.
`documentation/config/documentation-test-estate-inventory-0.9.4.json` separately resolves every
maintained documentation test to exactly one M11A execution layer, risk owner, cost, and coupling;
use its focused contract before changing a test layer or retiring stale evidence.

## Suite Boundary

| Suite | Owns | Must not require |
| --- | --- | --- |
| `unit/` | Pure documentation tooling helpers, bootstrap behavior, manifest/search helper logic, and compact temporary publish trees. | Browser, network, installed documentation artifact, production DB, full generated site scan. |
| `contract/` | DITA/maps, content parity, manifests, target maps, search contracts, source inventories, links, API examples, provenance, and release-shape rules. | Browser, live Firefox, ignored generated output, customer data, licensed PDFs. |
| `browser/` | Real-browser portal smoke, BPM-to-docs entry flow, keyboard/focus, responsive/theme, locale, search UI, CSP, and screenshots. | Production DB, external search, unreviewed screenshots, sandboxed browser trial before escalation. |

## Failure Domains

| Domain | Primary suite | Typical focused start |
| --- | --- | --- |
| DITA | `contract/` | `test_guide_maps.py`, `test_metadata_contract.py`, then `test_build_docs.py` only if transform/link behavior fails. |
| Content | `contract/` | The one guide/topic contract matching the changed area: User Guide, Firefox, CIS, or API. |
| Manifest | `contract/` + `unit/` | `test_manifest_generation.py` and the manifest generation unit test in `test_build_docs.py`. |
| Localization | `contract/` | The relevant `*_locale_parity.py` contract; do not scan all locale trees before the focused failure points there. |
| Screenshot | `browser/` | Future screenshot/browser checks only; source assets remain under `assets/screenshots/{locale}/`. |
| Search | `contract/` + `unit/` | `test_search_*.py` plus the generated search assertions in `test_build_docs.py`. |
| Links | `contract/` + `unit/` | Manifest/link contracts and generated link validation in `test_build_docs.py`. |
| API examples | `contract/` | `test_api_openapi_drift.py`, `test_api_integration_topics.py`, and compact `fixtures/import-export/` examples. |
| Portal integration | `contract/` now, `browser/` later | `test_portal_shell_theme.py`, `test_manifest_generation.py`, and future browser smoke. |
| Fixtures | `contract/` | `test_documentation_fixture_catalog.py` and `fixtures/fixture-catalog-0.9.0.json` before adding or copying fixture inputs. |
| Diagnostics | `contract/` + `unit/` | `test_documentation_diagnostics_policy.py` and focused `build_docs.py` diagnostics helpers; generated artifacts stay under `reports/diagnostics/`. |

Repository-root `tests/` may keep cross-boundary architecture, runtime bridge, marker policy, and
release-gate contracts. It must not become the normal debug entry point for DITA authoring, locale
parity, search fixture drift, manifest internals, screenshot capture, or API example source issues.

## Fixture Boundary

Fixtures are compact, deterministic, synthetic, and checked in only when they make a focused
documentation failure reproducible. They may live in `documentation/fixtures/`, `documentation/config/`
for reviewed search/config contracts, or directly beside the suite-boundary contract. Do not store
generated sites, search indexes, screenshots captured during a run, browser downloads, ignored
reports, production data, secrets, full external corpora, or licensed PDFs in this tree.

Use the focused documentation test commands before broader repository or release gates:

```bash
make docs-fast-check DOCS_CHANGED="documentation/src/dita/en/user/example.dita"
make docs-snapshot      # regenerated bounded subsystem snapshot
make test-docs          # documentation unit + contract suites, no browser
make test-docs-contract # documentation docs_contract suite only
make test-docs-ui-contract # non-browser portal/UI contracts
make test-docs-browser  # browser-backed portal smoke; immediate sandbox escalation
make test-docs-ui       # non-browser contracts + browser smoke
make docs-coverage      # isolated documentation-code coverage policy
```

`make docs-fast-check` is the first one-topic loop: it validates changed source inputs and reports
the affected locale, guide, search, and build-output area without invoking DITA-OT or unrelated BPM
runtime code. Use `make docs-validate` when generated HTML, manifests, and search indexes must be
proved end to end.
`make docs-coverage` writes isolated terminal, XML, HTML, and coverage-data reports under
`documentation/reports/coverage/` and fails below 100% line and branch coverage for the maintained
build library plus metadata validator. CLI/subprocess adapters and browser checks stay in their
focused execution layers, as declared in `documentation/config/coverage-policy-0.9.4.json`.
Failed `make docs-fast-check` runs write a compact JSON diagnostic artifact under
`documentation/reports/diagnostics/` with topic, locale, guide, source line, target URL, query,
screenshot state, and focused rerun context.

The pinned documentation test environment and bootstrap unit test are available after
`make setup-docs-toolchain`; run the focused test with
`./documentation/.cache/toolchain/python-venv/bin/pytest -q documentation/tests/unit/test_bootstrap_toolchain.py`.
`make test-docs-browser` and the aggregate `make test-docs-ui` launch Selenium/Chromium and require
immediate sandbox escalation under the backlog protocol.
