# Dependency Refresh Backlog

Date: `2026-04-29`

## Goal

Capture the dependency-refresh follow-up that was intentionally deferred from the current `0.7.0`
cycle.

This note records the current stack snapshot, which packages already look stale, which ones appear safe
to update in a low-risk batch, and which ones should wait for a dedicated compatibility pass.

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
- Monaco updates require rebuilding vendored assets and rechecking the advanced editor;
- the likely gain from a patch-only Monaco bump is smaller than the regression risk.

For now, Monaco should only be refreshed together with:

- rebuilt vendor bundles;
- a manual advanced-editor smoke pass;
- the local Chromium UI audit.

## Recommended follow-up plan

### Phase 1: low-risk maintenance batch

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

The repository currently relies on open-ended lower bounds such as `>=`.

Follow-up work should decide whether to:

- add a lock file for reproducible local and CI installs; or
- tighten version constraints for framework-sensitive packages.

This is important because a clean environment created later may not match the currently tested local
stack.

## Definition of done for the later task

- dependency refresh scope is explicitly chosen before implementation;
- low-risk and framework-risk upgrades are not mixed accidentally;
- the project remains green on `mypy` and the main non-live suite after the upgrade pass;
- any frontend vendor bump is validated with the Chromium UI audit;
- reproducibility strategy is clarified instead of continuing to rely only on lower bounds.
