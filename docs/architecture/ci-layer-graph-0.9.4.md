# BPM 0.9.4 Mandatory CI Layer Graph

Updated: 2026-08-05
Backlog item: `BPM094-M10-01`

## Decision

The required pull-request workflow partitions executable tests by their one
primary owner. `tests/test-layer-ownership-0.9.4.json` remains the
fail-closed source of truth for Python and documentation primary layers, and
`tests/javascript/test-layer-ownership-0.9.4.json` does the same for native
JavaScript tests. A coverage job consumes coverage data from the Python owners;
it never invokes pytest and therefore cannot duplicate or hide a layer.

Firefox tests are deliberately not part of this workflow. Deterministic local
policy validation remains scheduled/manual in `firefox-live.yml`; the
network-dependent AMO check remains manual in `firefox-live-amo.yml`.

## Required-job ownership

| CI job | Owns | Command or action | Failure evidence / next owner |
| --- | --- | --- | --- |
| `lint` | no test layer | `make lint`, `make typecheck`, `make architecture` | Static/type/import failure belongs to the changed Python or configuration owner. |
| `base-runtime` | package base-runtime smoke | Base `pip install .`, `pip check`, `make release-boundary` | Delivery-boundary or installed-runtime failure belongs to package/release assembly. |
| `unit-tests` | `unit` product tests | `make test-unit` | A failure belongs to the unit owner. |
| `integration-tests` | `integration` product tests without `db` | `make test-integration` | Database-marked tests are not selected here. |
| `postgres-integration` | all product `db` integration tests | `make test-postgres-integration` against the disposable service | Migration/engine failure belongs to the database contour. |
| `contract-tests` | product `contract` tests | `make test-contract` | A failure belongs to the contract owner. |
| `documentation-coverage` | documentation `unit` and `contract` tests | `make docs-coverage`, then the complementary `make test-docs` partition | Its independent 100% documentation report is retained as `documentation-coverage-artifacts`; the two commands have disjoint test selections. |
| `frontend-tests` | native JavaScript contract/integration tests | `make test-frontend-coverage` | Node coverage output and a failing test identify the JavaScript owner. |
| `chromium-tests` | product and documentation `browser` tests | `make test-browser`, `make test-docs-browser` with one matching Chrome-for-Testing/ChromeDriver pair | Sanitized browser failure artifacts are retained. |
| `coverage` | no tests | download `python-coverage-*`, then `make coverage-report` | Combines the two declared strict-coverage owner artifacts and reports the current app floor. |
| `required-gates` | no tests | waits for the required results | Makes the complete required dependency set visible as one terminal status. |

`live` is intentionally outside the normal PR owner set. It is owned by the
separate Firefox workflows so a network or browser-runtime signal cannot mask a
deterministic required CI result.

## Dependency and artifact flow

```text
lint
 ├── base-runtime ───────────────────────────────────────────────┐
 ├── unit-tests ─────────────────────────────────────────────────┤
 ├── integration-tests ──────────────────────────────────────────┤
 ├── postgres-integration ───────────────────────────────────────┤
 ├── contract-tests ─────────────────────────────────────────────┤
 ├── release-implementation-coverage ─ .coverage.release-implementation ─┐
 ├── ai-incubation-tests ───────────── .coverage.ai-incubation ──────────┼─ coverage
 ├── documentation-coverage ─ documentation report ─────────────┤
 ├── frontend-tests ─ native JS result ──────────────────────────┤
 └── chromium-tests ─ browser failure artifacts ─────────────────┘
                                                        required-gates
```

All producing jobs retain their evidence on failure. The aggregate coverage
job downloads only artifacts named `python-coverage-*`, so unrelated failure
artifacts cannot alter coverage data. Artifact integrity is checked by the
official download action before the report is combined.

## Coverage transition boundary

The graph preserves the accepted current application threshold of 85 percent.
`BPM094-M10-06` is the sole task that may change it to the required 100 percent
after the declared app and JavaScript surfaces are proved complete. Documentation
coverage stays at its already accepted 100 percent boundary and remains separate
from application coverage.

## Maintainer rules

- Put a new Python or documentation test under an existing unique primary-layer
  owner before it can collect; unowned paths stop collection.
- Do not add a second `pytest` invocation for a primary layer to `ci.yml`.
  Extend the owner command or its coverage artifact instead.
- Keep Chromium tests in `chromium-tests`; do not reintroduce Firefox live or
  AMO tests into required pull-request CI.
- A coverage job may consume artifacts and report results, but it must not rerun
  tests. This preserves both failure ownership and the serial test semantics
  recorded in the pytest parallelism decision.

## Local pre-commit boundary

The local hook toolchain is pinned to Python 3.14, Ruff 0.16.1, and Mypy
2.3.0. Ruff is the sole Python formatter and import-sorter authority; this
avoids non-convergent output from independent formatter preview styles. In
addition to file-oriented formatter/linter/type hooks,
`layered-fast-architecture` runs `make pre-commit-check`: import-layer
validation and three tooling/CI configuration contracts only.  It is bounded
for a commit-time feedback loop and explicitly prints that it is **not** the
full test suite.

Run the layer owners explicitly (or let required CI run them): `make test-unit`,
`make test-integration`, `make test-postgres-integration`, `make test-contract`,
`make docs-release-check`, `make test-frontend-coverage`, `make test-browser`,
and `make test-docs-browser`.  Firefox deterministic and AMO workflows remain
scheduled/manual as described above.  Passing pre-commit is therefore never a
release or full-suite success signal.
