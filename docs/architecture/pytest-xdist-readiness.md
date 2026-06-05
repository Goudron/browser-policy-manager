# Pytest Xdist Readiness

Updated: 2026-06-04

## Decision

Do not enable `pytest-xdist` in mandatory CI for BPM 0.8.5.

Status: final BPM 0.8.5 decision from `BPM085-M8-05`.

The test suite is now split into marker-based layers, and that gives the project
faster feedback without introducing parallel execution risks. A narrow
pure-unit xdist pilot is available only through an explicit local target and a
manual workflow.

## Current Evidence

- `pytest-xdist` is part of the `dev` dependency set for the opt-in pilot.
- `make test-fast`, `make test-contract`, `make test-ui`, `make test-live`, and
  `make test-release` provide explicit test layers.
- CI runs mandatory fast checks separately from coverage/contract checks.
- Browser UI checks are manual, and Firefox live checks are scheduled/manual.
- `docs/architecture/pytest-xdist-isolation-audit.md` records the current
  blocker map for DB/session state, FastAPI overrides, caches, ports, browser
  profiles, and artifacts.
- `tests/db_harness.py` and `tests/conftest.py` now configure a unique temporary
  SQLite database URL before application imports for `main` or each
  `PYTEST_XDIST_WORKER`, and clean the worker root after the session.
- `tests/app_harness.py` and the pytest app fixtures now use fresh FastAPI app
  instances, restore complete dependency override snapshots, and guard the
  module-global app override map between tests.
- `tests/cache_harness.py` provides a named reset registry for mutable
  settings/schema/validator/locale cache inputs while immutable worker-local
  caches can stay warm.
- `make test-unit-pilot` provides the serial baseline for the approved marker
  scope, and `make test-unit-xdist` runs the same scope with xdist.
- `.github/workflows/xdist-pilot.yml` is manual-only and uses two workers.
- The initial local pilot selected 221 tests: the serial baseline completed in
  68.01s, and two repeated two-worker xdist runs completed in 49.71s and
  42.74s with no failures.

## Parallelism Risks

- FastAPI tests share the imported `app` object and mutate
  `app.dependency_overrides`.
- `tests/conftest.py` disposes the global SQLAlchemy engine after each test.
- Some tests intentionally exercise default SQLite configuration and local DB
  setup behavior.
- Several modules use process-local `@cache` or `lru_cache` helpers. These are
  safe inside one process but need explicit cache-clear contracts before worker
  isolation can be trusted.
- Browser UI and live Firefox suites depend on ports, browser profiles,
  downloaded runtimes, screenshots, and local artifacts. They should not share
  worker processes without dedicated per-worker sandboxes.

## Opt-In Pilot

The approved pilot is limited to pure unit/tool tests:

```bash
make test-unit-pilot
make test-unit-xdist
```

The xdist target excludes `api`, `contract`, `docs_contract`, `ui_contract`,
`slow`, `browser_ui`, `firefox_live`, and `firefox_live_amo`. M8-05 concluded
that this target should remain opt-in throughout BPM 0.8.5.

Initial local measurements on 2026-06-04:

| Command | Result | Runtime |
| --- | --- | --- |
| `make test-unit-pilot` | 221 passed, 528 deselected | 68.01s |
| `make test-unit-xdist XDIST_WORKERS=2` | 221 passed | 49.71s |
| `make test-unit-xdist XDIST_WORKERS=2` | 221 passed | 42.74s |

The two-worker pilot was approximately 27% to 37% faster than the serial
baseline.

## M8-05 Decision Rationale

Keep the xdist pilot opt-in for BPM 0.8.5. Do not add a mandatory xdist job and
do not make `-n auto` part of the default pytest configuration.

- The measured saving is 18.30s to 25.27s for a 221-test subset.
- `make test-fast` already runs that subset inside a larger mandatory serial
  layer, so an additional job would duplicate checks without shortening the
  existing job.
- The coverage job also reruns the non-browser suite. The current pure-unit
  pilot does not reduce that coverage path.
- No repeated GitHub-hosted runner evidence exists yet for the manual workflow.
- Replacing part of `test-fast` or combining xdist with coverage would be a new
  test-layer design and needs its own non-overlap, stability, and timing proof.

The manual workflow and local targets remain useful for continued evidence
collection and for diagnosing order-dependent tests.

## Required Gates Before CI Adoption

- TestClient fixtures must continue isolating `app.dependency_overrides`.
- Database tests must continue using per-test or per-worker database URLs and
  must never target `./data/bpm.db`.
- Browser UI and live Firefox jobs must keep separate profiles, ports, artifacts,
  and browser runtime directories per worker, or remain non-xdist.
- Cache-heavy modules must continue documenting whether cache state is
  immutable, reset by tests, or worker-local by design.
- A workflow contract test must prove that mandatory CI does not run `pytest -n`
  outside the approved marker scope.

## Recommendation

Keep BPM 0.8.5 mandatory CI on layered serial pytest. Use xdist only as the
approved opt-in pure-unit pilot. Revisit mandatory adoption after BPM 0.8.5 only
if hosted-runner measurements show a meaningful critical-path improvement and a
non-overlapping CI layer preserves coverage and test selection.
