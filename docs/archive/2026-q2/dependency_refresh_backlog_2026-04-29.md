# Dependency Refresh Backlog

Date: `2026-04-29`
Status: `completed`

## Goal

Capture the dependency-refresh follow-up that was intentionally deferred from the `0.7.0`
cycle, then record the outcome once the maintenance pass is complete.

This note now records both the original analysis and the implemented refresh results.

## Final outcome

Completed in this maintenance cycle:

- low-risk dependency refresh batch
- framework/test-stack refresh batch
- Python runtime uplift from `3.13` to `3.14`
- `pyproject.toml`, README, and GitHub Actions workflow alignment with the new runtime baseline

Validated successfully on the refreshed stack:

- `./.venv/bin/ruff check .`
- `./.venv/bin/mypy app`
- `./.venv/bin/pytest -m 'not firefox_live and not firefox_live_amo'`
- full `app/` coverage pass at `100%`
- local Chromium UI audit on the rebuilt Python `3.14` environment

Environment note:

- deterministic Firefox live tests still require an unrestricted environment because the suite binds local
  sockets for `geckodriver` and temporary HTTP fixtures; a sandboxed rerun on Python `3.14` failed with
  socket-permission errors rather than product regressions.

## Current state

The repository currently relies on lower-bound dependency declarations in `pyproject.toml`, while the
active local `.venv` already contains newer versions for many packages.

This means the project is functioning on one tested dependency set locally, but a fresh install can
resolve to a meaningfully different environment later.

## Observed local versions

Python/runtime stack observed during the analysis:

- `fastapi` `0.118.0`
- `uvicorn` `0.37.0`
- `pydantic` `2.11.10`
- `pydantic-settings` `2.11.0`
- `SQLAlchemy` `2.0.43`
- `alembic` `1.17.0`
- `httpx` `0.28.1`
- `selenium` `4.41.0`
- `pytest` `8.4.2`
- `pytest-cov` `7.0.0`
- `pytest-asyncio` `1.2.0`
- `ruff` `0.14.0`
- `mypy` `1.18.2`
- `aiosqlite` `0.21.0`
- `Jinja2` `3.1.6`
- frontend vendor pins in `package.json`:
- `esbuild` `0.25.3`
- `js-yaml` `4.1.0`
- `monaco-editor` `0.52.0`

## Analysis summary

### Safe or relatively low-risk upgrade candidates

These look like reasonable follow-up updates that should be possible in one bounded maintenance pass:

- `uvicorn` `0.37.0 -> 0.43.0`
- `SQLAlchemy` `2.0.43 -> 2.0.49`
- `alembic` `1.17.0 -> 1.18.4`
- `selenium` `4.41.0 -> 4.43.0`
- `pytest-cov` `7.0.0 -> 7.1.0`
- `pytest-asyncio` `1.2.0 -> 1.3.0`
- `ruff` `0.14.0 -> 0.15.x`
- `mypy` `1.18.2 -> 1.20.1`
- `aiosqlite` `0.21.0 -> 0.22.1`

Reasoning:

- these remain within the same major release lines;
- the repository already has strong non-live regression coverage;
- most risk here is maintenance churn, not product-contract churn.

### Upgrade candidates that should be isolated in a separate pass

These should not be mixed into an ordinary maintenance patch unless we explicitly want a framework
upgrade cycle:

- `fastapi` `0.118.0 -> 0.135.x`
- `pydantic` `2.11.10 -> 2.13.x`
- `pydantic-settings` `2.11.0 -> 2.13.x`
- `pytest` `8.4.2 -> 9.x`

Reasoning:

- these packages sit on top of route handling, OpenAPI generation, request validation, settings
  loading, or the primary test runner behavior;
- the repository now contains substantial route-contract, import/export, and workspace coverage, so
  even "minor" upstream changes can surface real compatibility issues;
- these should be treated as a compatibility-focused maintenance cycle with full validation.

### Components that do not need immediate work

- `httpx` is already on the current stable line used in the local environment.
- `Jinja2` is already on the current stable line used in the local environment.
- `js-yaml` `4.1.0` does not currently present an obvious refresh target from the package metadata
  reviewed during this pass.

### Frontend vendor caution

`monaco-editor` appears to have a newer patch release than the pinned `0.52.0`, but this is not a
clear "update now" recommendation.

Reasoning:

- the project already had subtle Monaco/CSP/runtime behavior during the current cycle;
- Monaco updates require rebuilding vendored assets and rechecking the JSON editor;
- the likely gain from a patch-only Monaco bump is smaller than the regression risk.

For now, Monaco should only be refreshed together with:

- rebuilt vendor bundles;
- a manual JSON-editor smoke pass;
- the local Chromium UI audit.

## Recommended follow-up plan

### Phase 1: low-risk maintenance batch

Status: completed

Perform one dependency refresh pass for:

- `uvicorn`
- `SQLAlchemy`
- `alembic`
- `selenium`
- `pytest-cov`
- `pytest-asyncio`
- `ruff`
- `mypy`
- `aiosqlite`

Validation:

- `./.venv/bin/mypy app`
- `./.venv/bin/pytest -m 'not firefox_live and not firefox_live_amo'`
- targeted live Firefox sanity check if Selenium changes require it

### Phase 2: framework and typing stack refresh

Status: completed

Run a dedicated compatibility pass for:

- `fastapi`
- `pydantic`
- `pydantic-settings`
- `pytest`

Validation:

- full non-live suite
- full `app/` coverage pass
- OpenAPI and import/export contract review
- local Chromium UI audit
- live Firefox sanity check

### Phase 3: reproducibility hardening

Status: still open as a separate follow-up

The repository currently relies on open-ended lower bounds such as `>=`.

Follow-up work should decide whether to:

- add a lock file for reproducible local and CI installs; or
- tighten version constraints for framework-sensitive packages.

This is important because a clean environment created later may not match the currently tested local
stack.

## Separate task: Python runtime upgrade

This should stay separate from the ordinary dependency-refresh batches above.

### Why it is a separate task

Updating the Python interpreter is not just "one more package bump":

- it changes the runtime for the FastAPI app itself;
- it can affect SQLite and DB-adjacent behavior;
- it changes the toolchain used by `mypy`, `ruff`, `pytest`, and packaging;
- it can affect Selenium/live-browser helpers and local build steps;
- it usually requires CI and local environment alignment.

At the time of the initial analysis:

- the local machine has `Python 3.13.7`;
- the newest stable Python release is `3.14.4`;
- Python `3.15` exists only as an alpha/development line and should not be used for this task.

### Goal

Upgrade the project runtime baseline from Python `3.13` to Python `3.14`, after a dedicated validation
pass.

### Proposed scope

1. Install Python `3.14.x` on the target development machine and any CI runners used by the project.
2. Recreate the project virtual environment on Python `3.14`.
3. Reinstall project dependencies from the refreshed dependency set.
4. Update project metadata if needed:
   - `pyproject.toml`
   - CI workflow Python versions
   - any setup or contributor docs that mention the supported local runtime
5. Re-run the main validation stack on Python `3.14`.

### Required validation

Minimum expected validation for the Python runtime upgrade:

- `./.venv/bin/ruff check .`
- `./.venv/bin/mypy app`
- `./.venv/bin/pytest -m 'not firefox_live and not firefox_live_amo'`
- full coverage pass for `app/`
- local Chromium UI audit
- deterministic live Firefox sanity check

If CI pins a Python version explicitly, CI should also be updated and verified in the same task.

### Things to check carefully

- `sqlalchemy` / `alembic` / `aiosqlite` behavior on the new interpreter
- schema-loading and validation flows
- import/export contract behavior for Firefox `policies.json`
- local Selenium helpers and browser-driver startup
- tooling behavior for `mypy`, `ruff`, and `pytest-asyncio`
- any packaging or editable-install differences under Python `3.14`

### Definition of done

- the project installs cleanly in a fresh Python `3.14` virtual environment
- the main non-live test suite passes on Python `3.14`
- static checks pass on Python `3.14`
- local browser-based sanity checks pass on Python `3.14`
- repository docs and CI reflect the new runtime baseline

Completion note:

- completed with local Python `3.14.4` installed under `~/.local/python-3.14.4`
- project `.venv` rebuilt on `Python 3.14.4`
- repository metadata and GitHub Actions updated to `3.14`
- Chromium browser-level sanity passed on the rebuilt environment
- deterministic Firefox live rerun remains environment-sensitive because sandboxed socket binding is blocked

## Definition of done for the later task

- dependency refresh scope is explicitly chosen before implementation;
- low-risk and framework-risk upgrades are not mixed accidentally;
- the project remains green on `mypy` and the main non-live suite after the upgrade pass;
- any frontend vendor bump is validated with the Chromium UI audit;
- reproducibility strategy is clarified instead of continuing to rely only on lower bounds.
