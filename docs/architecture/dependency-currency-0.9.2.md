# BPM 0.9.2 Dependency Currency Check

Date: 2026-07-17

Status: **Accepted for BPM 0.9.2 M1-03.**

This note records the bounded dependency-currency review for the BPM 0.9.2 UI compaction and
documentation coherence epic. It does not approve a hidden dependency upgrade: the release keeps
its declared minimums, exact frontend pins, documentation toolchain lock, and matching local
browser/driver pair unless a separately approved task changes one of them.

## Scope And Sources

The review covers direct application and `dev` dependencies in `pyproject.toml`, frontend pins in
`package.json` and `package-lock.json`, the documentation toolchain lock and exact documentation
test lock, plus the local Chromium/Selenium environment.

Current upstream versions were checked on 2026-07-17 through the [PyPI JSON API](https://pypi.org/),
the [npm registry](https://registry.npmjs.org/), [DITA-OT releases](https://github.com/dita-ot/dita-ot/releases),
and [Eclipse Temurin 21 releases](https://github.com/adoptium/temurin21-binaries/releases). Local
versions came from `.venv/bin/pip show`, Node/npm, Chromium, and ChromeDriver probes.

Generated documentation, dependency directories, caches, and local browser artifacts are excluded.

## Decision

Keep the existing declared dependencies and toolchain pins for 0.9.2. The epic changes UI copy,
layout, documentation shell behavior, search-panel state, and localized prose; it does not need a
runtime-framework, frontend-vendor, documentation-toolchain, browser-driver, or test-platform
upgrade to perform that work safely.

Available updates are recorded below as follow-up candidates, not silently adopted. Any such change
requires a separately approved task with its compatibility, lock/checksum, license, test, and browser
verification evidence. No package pin, lockfile, checksum, or vendor bundle changes in this task.

## Review Matrix

| Area | Declared/local version | Current upstream result | Decision |
| --- | --- | --- | --- |
| Python runtime | `>=3.14`; local Python `3.14.4`; tooling targets `py314` | Supported project baseline. | Keep. No Python support change is required for 0.9.2. |
| Core application runtime | FastAPI `0.139.0`, Uvicorn `0.50.0`, Jinja2 `3.1.6`, Pydantic `2.13.4`, Pydantic Settings `2.14.2`, JSON Schema `4.26.0`, FastJSONSchema `2.21.2`, SQLAlchemy `2.0.51`, Alembic `1.18.5`, aiosqlite `0.22.1`, PyYAML `6.0.3`, HTTPX `0.28.1`, Requests `2.34.2`, python-multipart `0.0.32`. | FastAPI `0.139.2` and Uvicorn `0.51.0` are newer; all other listed direct runtime pins match the checked latest release. | Keep. The two available runtime updates need a dedicated compatibility task. |
| Test and browser stack | pytest `9.1.1`, pytest-cov `7.1.0`, pytest-asyncio `1.4.0`, pytest-xdist `3.8.0`, AnyIO `4.14.1`, Beautiful Soup `4.15.0`, Selenium `4.45.0`. | AnyIO `4.14.2` and Selenium `4.46.0` are newer; the remaining listed pins match the checked latest release. | Keep. Selenium/browser behavior must not change inside UI work. |
| Lint, type, and dev tools | Ruff `0.15.20`, Black `26.5.1`, isort `8.0.1`, Mypy `2.1.0`, types-PyYAML `6.0.12.20260518`, types-requests `2.33.0.20260518`, IPython `9.15.0`. | Ruff `0.15.22`, Mypy `2.3.0`, and types-requests `2.33.0.20260712` are newer; the other pins match the checked latest release. | Keep. Rule/type-check migrations require focused type, lint, and full-suite evidence. |
| PostgreSQL optional dependencies | asyncpg `0.31.0`, psycopg `3.3.4`. | Both match the checked latest release. | Keep. |
| Frontend vendor stack | js-yaml `5.2.1`, Monaco Editor `0.53.0`, esbuild `0.28.1`; `npm audit --omit=dev` reports zero vulnerabilities. | js-yaml and esbuild match the checked latest release; Monaco Editor `0.55.1` is available. | Keep. Monaco rebuild and browser regression evidence belong to a dedicated vendor task. |
| Documentation publishing toolchain | DITA-OT `4.4`, Temurin JRE `21.0.11+10`; first-party plugin remains reserved/not installed. | DITA-OT `4.4` and Temurin `jdk-21.0.11+10` match current official releases. | Keep exact lock and checksums. The stale 0.9.0 labels are version-ownership work, not a dependency update. |
| Documentation-only test lock | attrs `26.1.0`, iniconfig `2.3.0`, jsonschema `4.26.0`, jsonschema-specifications `2025.9.1`, packaging `26.2`, pluggy `1.6.0`, Pygments `2.20.0`, PyYAML `6.0.3`, referencing `0.37.0`, rpds-py `2026.6.3`, pytest `9.1.1`. | Every exact pin matches the checked latest PyPI release. | Keep the exact lock. |
| Browser and driver | Chromium `150.0.7871.114`; ChromeDriver `150.0.7871.114`; Selenium `4.45.0`. | Browser and driver versions match exactly. | Keep. Rerun browser smoke after any browser, driver, or Selenium update with immediate sandbox escalation. |

## Environment Boundary

`pip check` reports missing transitive dependencies for `minisbd`, `argostranslate`, `stanza`,
`sacremoses`, and `ctranslate2`. These packages are absent from BPM's project metadata and have no
repository references; `argostranslate` has no installed dependent. They are unrelated incomplete
packages in the shared local virtual environment, not BPM dependency defects. BPM's declared direct
requirements are installed, and `browser-policy-manager 0.9.2` reports its expected dependency set.

## Follow-Up Gates

- Runtime or test-platform changes require focused unit/API tests, `pytest -q`, type-check, lint, and
  coverage evidence.
- A frontend update requires package-lock review, vendor rebuild, license review, UI contracts, and
  affected browser smoke.
- A documentation-toolchain update requires lock/checksum and third-party-notice review,
  reproducible-build evidence, DITA validation, and documentation browser smoke.
- A browser, driver, or Selenium update requires an exact browser/driver record and immediate-
  escalation Chromium/Selenium smoke.

## Result

`BPM092-M1-03` approves no dependency update. The checked active pins are either current or have a
bounded, explicitly deferred update candidate; no floating upgrade is introduced into 0.9.2 UI and
documentation work.
