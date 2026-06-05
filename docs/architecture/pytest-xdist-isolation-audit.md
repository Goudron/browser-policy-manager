# Pytest Xdist Isolation Audit

Updated: 2026-06-04

Backlog item: `BPM085-M8-01`

## Scope

This audit maps current blockers and boundaries for the `pytest-xdist` pilot. It covers:

- database and session isolation;
- FastAPI app and dependency override isolation;
- process-local caches and mutable module state;
- temporary files, ports, browser profiles, screenshots, and local artifacts;
- the safest first pilot scope for BPM 0.8.5.

## Current Decision

Do not enable `pytest-xdist` for mandatory BPM 0.8.5 CI.

The project should continue using marker-based serial layers as the default:

- `make test-fast`
- `make test-contract`
- `make test-ui`
- `make test-release`
- scheduled/manual Firefox live workflows

The implemented xdist pilot is opt-in and limited to pure `unit`/tool tests.

## Risk Map

| Area | Current evidence | Risk | Required before pilot |
| --- | --- | --- | --- |
| Dependency availability | `pytest-xdist` is in `pyproject.toml` dev dependencies for the opt-in pilot. | Low | Keep it paired with opt-in targets/workflow, not a mandatory CI behavior change. |
| DB engine lifecycle | `app.db` still creates `engine` and `SessionLocal` at module import, but `tests/conftest.py` now configures a worker-local database URL before importing application modules and disposes the global engine after each test. | Medium | Keep DB/API tests out of the first pure-unit pilot until app/client state isolation is complete. |
| DB URL handling | `tests/db_harness.py` creates a unique temporary SQLite root for `main` or each `PYTEST_XDIST_WORKER`, exports `BPM_DATABASE_URL`, and removes the worker root at session teardown/unconfigure. | Low | Preserve the runtime and source contracts proving workers never target `./data/bpm.db`. |
| FastAPI app state | `tests/app_harness.py` provides fresh app instances for new tests and preserves explicit legacy/custom apps with complete dependency override snapshot/restore. `tests/conftest.py` clears the module-global app override map before and after every test. | Low | Keep the default-app override guard and app harness contracts in the pilot. |
| Async client fixture | `tests/conftest.py` now builds a fixture-scoped fresh app for the async `client` fixture and restores its complete override map after use. | Low | Keep API tests outside the first pure-unit pilot until a later pilot measures their stability separately. |
| Settings and schema caches | `tests/cache_harness.py` records reset callbacks and policies for settings, schemas, validators, locale catalogs, and profile asset versions. Mutating tests can use the `reset_app_caches` fixture while immutable worker-local caches stay warm. | Low | Preserve the registry contract and add new mutable caches when application code introduces them. |
| Mutable module state | The default FastAPI app override map is cleared before and after each test. Other monkeypatched module constants remain process-local and are restored by pytest fixtures. | Low | Keep tests that reload modules or depend on ordered state out of the first pure-unit pilot unless explicitly proven safe. |
| Ordered tests | `tests/test_migrations.py` uses `pytest.mark.order` for two migration smoke tests. | Medium | Keep ordered migration tests out of the first xdist pilot; they are DB-heavy and do not belong in the pure unit pilot. |
| Temporary files | Most file-writing tests use `tmp_path`, which is naturally worker-safe. | Low | Keep using `tmp_path`; avoid repo-root outputs in pilot scope. |
| Local ports | Browser tests and local audit helpers use picked ports and uvicorn threads. | High | Keep `browser_ui` and local Chromium audit out of xdist unless they get per-worker server, port, and artifact roots. |
| Firefox live runtime | Live tests reuse `.bpm-test-browsers/` and write `distribution/policies.json` into the shared Firefox install root. | Extra high | Keep `firefox_live` and `firefox_live_amo` serial. Parallel live tests need per-worker staged Firefox install roots. |
| Artifacts/screenshots | Chromium audit writes to `artifacts/local_chromium_ui_audit`; screenshot docs are ignored but shared path conventions exist. | Medium | Require per-worker artifact roots before any browser/UI xdist pilot. |

## Safe First Pilot Candidate

The first pilot should be local/opt-in only and should exclude:

- `api`
- `contract`
- `docs_contract`
- `ui_contract`
- `slow`
- `browser_ui`
- `firefox_live`
- `firefox_live_amo`
- migration/order tests

Candidate marker expression after M8-02 and M8-03:

```bash
pytest -q -m "unit and not api and not contract and not docs_contract and not ui_contract and not slow and not browser_ui and not firefox_live and not firefox_live_amo" -n auto
```

Do not add this to mandatory CI until repeated local and opt-in CI runs show stable runtime and
no order-dependent failures.

## M8-02 Implementation Result

`BPM085-M8-02` is implemented by:

- `tests/db_harness.py`, which creates a unique temporary SQLite database root per
  `PYTEST_XDIST_WORKER` and exports `BPM_DATABASE_URL` before application imports;
- `tests/conftest.py`, which installs the worker database context before importing `app.db`,
  guards against `./data/bpm.db`, disposes the global engine, and cleans the worker root;
- `tests/test_db_harness_unit.py` and `tests/test_pytest_db_isolation_contract.py`, which prove
  worker path uniqueness, stable-root cleanup, import ordering, and the project DB guard.

This closed the DB URL and worker cleanup prerequisite for the future pure-unit pilot. At that
point, shared FastAPI app objects, dependency overrides, and process-local caches remained
`BPM085-M8-03`.

## M8-03 Implementation Result

`BPM085-M8-03` is implemented by:

- `tests/app_harness.py`, which creates fresh test app instances for new tests and restores full
  dependency override snapshots for explicit legacy/custom apps;
- `tests/conftest.py`, which exposes `app_factory` and `test_app`, uses a fresh app for the async
  client fixture, and clears the default app override map before and after every test;
- `tests/cache_harness.py`, which provides a named reset registry for settings, raw schemas,
  policy schemas, compiled validators, locale catalogs, and profile asset versions;
- `tests/test_app_harness_unit.py`, `tests/test_cache_harness_unit.py`, and
  `tests/test_pytest_app_state_isolation_contract.py`, which lock the app/client/cache contracts.

This closes the app/client/cache prerequisites for the narrow pure-unit/tool pilot in
`BPM085-M8-04`. It does not approve API, contract, docs, UI, browser, or live Firefox tests for
parallel execution.

## M8-04 Implementation Result

`BPM085-M8-04` is implemented by:

- `pytest-xdist` in the `dev` dependency set;
- `TEST_UNIT_PILOT_MARKERS` in `Makefile`, shared by `make test-unit-pilot` and
  `make test-unit-xdist`;
- `XDIST_WORKERS`, which defaults to `auto` locally and is fixed to `2` in the
  manual `.github/workflows/xdist-pilot.yml` workflow;
- Makefile and workflow contract tests that keep mandatory `ci.yml` serial and
  prevent browser/live/contract targets from entering the pilot.

The pilot remains opt-in pending the final M8-05 decision.

Initial local measurements on 2026-06-04 selected the same 221-test scope:

| Command | Result | Runtime |
| --- | --- | --- |
| `make test-unit-pilot` | 221 passed, 528 deselected | 68.01s |
| `make test-unit-xdist XDIST_WORKERS=2` | 221 passed | 49.71s |
| `make test-unit-xdist XDIST_WORKERS=2` | 221 passed | 42.74s |

The repeated xdist runs were approximately 27% to 37% faster than the serial
baseline and left no worker temporary roots behind.

## M8-05 Decision Result

`BPM085-M8-05` keeps the xdist pilot opt-in for BPM 0.8.5. Mandatory CI remains
on the existing layered serial pytest targets. No mandatory xdist job is
introduced. No default `-n auto` configuration is introduced.

The decision is based on:

- a measured saving of 18.30s to 25.27s for the 221-test pure-unit subset;
- `make test-fast` already containing that subset, which means an additional
  mandatory pilot job would duplicate work without shortening the existing job;
- the serial non-browser coverage path remaining unaffected by this pilot;
- no repeated GitHub-hosted runner evidence from the manual workflow yet;
- a split fast-test or xdist coverage design requiring a separate proof that
  test selection, coverage, stability, and CI critical-path time remain sound.

Keep the local Make targets and manual workflow for continued evidence
collection. Revisit mandatory adoption after BPM 0.8.5 only with hosted-runner
measurements and a non-overlapping CI layer design.

## Backlog Corrections

Use this audit to steer the rest of M8:

- `BPM085-M8-02` should focus first on a reusable xdist-safe DB/session harness and safe
  `BPM_DATABASE_URL` handling.
- `BPM085-M8-03` should combine FastAPI app isolation with an explicit cache-reset registry,
  because dependency overrides and caches are the same class of process-local state risk.
- `BPM085-M8-04` introduced `pytest-xdist`, Make targets, and an opt-in workflow only
  for the pure unit/tool pilot scope above.
- `BPM085-M8-05` keeps xdist opt-in for BPM 0.8.5 and defers mandatory CI adoption until a
  non-overlapping layer shows hosted-runner critical-path value.
- Browser UI and Firefox live parallelism should remain outside BPM 0.8.5 unless a separate
  future backlog creates per-worker browser runtimes, profiles, ports, and artifact roots.

## Acceptance Gates For Any Pilot

- `pytest-xdist` exists in dev dependencies only when paired with an opt-in target/workflow.
- No pilot target includes browser, live Firefox, slow, docs, or UI contract markers.
- Pilot tests use fresh app/client factories or proven override cleanup.
- DB-writing pilot tests use per-test or per-worker database URLs and never touch `./data/bpm.db`.
- Cache-clearing behavior is centralized or explicitly documented.
- Mandatory CI still has a contract test proving it does not run `pytest -n`.
