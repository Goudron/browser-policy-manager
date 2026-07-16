# BPM 0.9.1 Dependency Currency Check

Date: 2026-07-06

Status: **Accepted for BPM 0.9.1 M1-03.**

This note records the bounded dependency-currency review for the BPM 0.9.1 documentation
completion epic. It is an inventory and decision record only: no package, browser, driver,
documentation toolchain, or frontend vendor dependency is upgraded by this task.

## Scope

The review covers dependencies that can affect the 0.9.1 work:

- Python runtime and application dependencies in `pyproject.toml`.
- Python test, lint, type-check, browser, and development dependencies in the `dev` optional group.
- Frontend vendor dependencies in `package.json` and `package-lock.json`.
- Documentation publishing toolchain pins in `documentation/config/toolchain-lock.json`.
- Documentation-only Python test pins in `documentation/config/requirements.lock`.
- Local browser and driver binaries used by Chromium/Selenium smoke tests.

Generated documentation output, cached toolchain archives, dependency directories, and local test
artifacts are not part of this review.

## Decision

Keep all existing dependency and toolchain pins for 0.9.1 until a separately approved update task
changes them. The 0.9.1 epic is documentation completion, theme/search/navigation polish,
localized screenshots, terminology cleanup, and All Settings help-link wiring. It should not hide a
runtime framework, documentation toolchain, frontend vendor, browser-driver, or test-platform
upgrade inside feature implementation.

Any future dependency update must be explicit and reviewed, with lockfile or checksum changes,
license review where applicable, focused compatibility tests, and the relevant documentation drift
checks.

## Review Matrix

| Area | Current pin or local version | Source checked | 0.9.1 decision |
| --- | --- | --- | --- |
| Python runtime | `requires-python = ">=3.14"`; tooling targets `py314` | `pyproject.toml` | Keep. No Python support matrix change belongs in this epic. |
| FastAPI runtime | `fastapi>=0.139.0`; local install `0.139.0`; PyPI latest page shows `fastapi 0.139.0`, released 2026-07-01 | `pyproject.toml`; `.venv/bin/pip show fastapi`; `https://pypi.org/project/fastapi/` | Keep. The current minimum already matches the checked latest release. |
| Core runtime stack | `uvicorn>=0.50.0`, `pydantic>=2.13.4`, `jsonschema>=4.26.0`, SQLAlchemy/Alembic/aiosqlite/httpx/requests/PyYAML minimums | `pyproject.toml`; representative `.venv/bin/pip show` probes | Keep. No runtime compatibility issue was identified during this bounded check. |
| Python test stack | `pytest>=9.1.1`; local install `9.1.1`; PyPI latest page shows `pytest 9.1.1`, released 2026-06-19 | `pyproject.toml`; `.venv/bin/pip show pytest`; `https://pypi.org/project/pytest/` | Keep. The current minimum already matches the checked latest release. |
| Lint and type-check stack | `ruff>=0.15.20`, `mypy>=2.1.0`; local installs match; PyPI latest pages show `ruff 0.15.20` and `mypy 2.1.0` | `pyproject.toml`; `.venv/bin/pip show ruff mypy`; `https://pypi.org/project/ruff/`; `https://pypi.org/project/mypy/` | Keep. Current checked versions are current enough for 0.9.1 and no rule/mypy migration is approved here. |
| Browser automation library | `selenium>=4.45.0`; local install `4.45.0`; PyPI latest page shows `selenium 4.45.0`, released 2026-06-16 | `pyproject.toml`; `.venv/bin/pip show selenium`; `https://pypi.org/project/selenium/` | Keep. Screenshot and browser smoke work should use the existing Selenium contract. |
| Local Chromium browser | `/snap/bin/chromium --version` reports `Chromium 150.0.7871.46 snap` | Local probe | Keep local browser for 0.9.1 validation unless a browser smoke task exposes a blocker. |
| Local ChromeDriver | `/snap/bin/chromium.chromedriver --version` reports `ChromeDriver 150.0.7871.46` | Local probe | Keep. Browser and driver major versions match. |
| Frontend vendor stack | `js-yaml 5.2.1`, `monaco-editor 0.53.0`, `esbuild 0.28.1` | `package.json`; `package-lock.json` | Keep. No frontend vendor rebuild or lockfile update is approved by M1-03. If later theme/search work requires a vendor change, open a separate task. |
| Documentation publishing toolchain | DITA-OT `4.4`, Eclipse Temurin JRE `21.0.11+10`, reserved first-party plug-in `0.9.0` | `documentation/config/toolchain-lock.json`; `https://github.com/adoptium/temurin21-binaries/releases/latest` | Keep. The Java pin matches the checked latest Temurin 21 release. DITA-OT remains governed by the accepted 0.9.0 toolchain decision and checksum lock. |
| Documentation-only Python test pins | Exact pins such as `pytest==9.1.1`, `jsonschema==4.26.0`, `PyYAML==6.0.3` | `documentation/config/requirements.lock` | Keep. The lock remains exact and separate from runtime dependencies. |

## Follow-Up Gates

- A dependency update must not be bundled with documentation UX, screenshot, localization, or
  All Settings implementation tasks.
- A Python runtime or runtime-framework update must include focused unit/API tests, default
  `pytest -q`, type-check, lint, and coverage evidence.
- A frontend vendor update must include `package-lock.json` review, vendor rebuild evidence, license
  review, UI contract tests, and browser smoke for affected routes.
- A documentation toolchain update must update `documentation/config/toolchain-lock.json`,
  checksums, third-party notices, reproducible-build evidence, DITA validation, and documentation
  browser smoke.
- A browser or driver update must record matching browser/driver versions and rerun the relevant
  Chromium/Selenium smoke command with immediate sandbox escalation.

## Result

`BPM091-M1-03` does not approve any dependency upgrade. The checked dependencies are either already
current in the areas verified from official project pages or are intentionally kept pinned behind
their existing lock/update procedures. There is no hidden floating upgrade in the 0.9.1 feature work.
