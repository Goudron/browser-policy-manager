# BPM 0.9.6 Dependency, Toolchain, Browser, And AMO Currency Decision

Date: 2026-08-20

Status: **`BPM096-M1-03` review accepted; `BPM096-M1-07` completed the nine deferred stable refreshes.**

## Scope and method

This is the bounded currency decision for the direct Python requirements in
`pyproject.toml`, `package.json` and `package-lock.json`, the checked-in
frontend vendor record, the exact documentation lock/toolchain record, and the
four-channel Firefox manifest. It records the worktree state at review time;
it does not edit a requirement, lockfile, vendor asset, checksum, browser
archive, or documentation artifact.

`Installed` means the local `.venv`, `npm ls --depth=0`, an exact documentation
lock (no docs virtual environment is provisioned), or a manifest-provenanced
browser installation as applicable. The browser verification completed all four
channels on Linux x86_64 and checked the cached SHA-256 provenance and binary
versions. Python optional `postgres` packages are not installed locally, so
that fact is not inferred from their declarations. The local runtime was
CPython 3.14.6, Node 22.22.1, and npm 9.2.0.

Version, Python-floor, and package metadata were rechecked against the
authoritative [PyPI JSON API](https://docs.pypi.org/api/json/) and
[npm registry](https://registry.npmjs.org/). Browser status is from Mozilla's
[Firefox version feed](https://product-details.mozilla.org/1.0/firefox_versions.json)
and the official [geckodriver release](https://github.com/mozilla/geckodriver/releases/tag/v0.37.1).
Documentation executables are from the official [DITA-OT 4.4
release](https://github.com/dita-ot/dita-ot/releases/tag/4.4) and the
[Adoptium API](https://api.adoptium.net/). The CPython runtime source is the
[Python downloads page](https://www.python.org/downloads/). Where a registry
response did not provide an SPDX expression, the stated license is the
upstream project's published license, as already captured in the 0.9.5
decision.

Security evidence on the review date is clean for the reviewed package
resolutions:

- `pip-audit` against a third-party-only pinned freeze of `.venv` found no
  known vulnerabilities. The editable BPM distribution is deliberately
  excluded because it is not published on PyPI.
- `pip-audit --requirement documentation/config/requirements.lock --no-deps
  --strict` found no known vulnerabilities.
- `npm audit --package-lock-only --json` reported zero vulnerabilities.

Executable rows need upstream security/release review and official archive
digest verification at the change; package-audit output is not evidence about
Firefox, geckodriver, Temurin, DITA-OT, or CPython. `Retain floor` preserves a
reviewed minimum while the fresh local resolution is newer; it is not approval
for a floating future upgrade. `Defer` means no M1-04 change is authorized.

## Runtime and base Python dependencies

| Component | Declared / installed / current | License and platform constraint | Advisory / disposition | Focused compatibility check if changed |
| --- | --- | --- | --- | --- |
| CPython | `>=3.14` / `3.14.6` / `3.14.6` | PSF-2.0; BPM supports Python 3.14. | Upstream review; retain. | Fresh editable install, API contracts, `pytest -q`, `ruff check .`, `mypy app`. |
| setuptools | `>=68` / not separately installed / `84.0.0` | MIT; Python `>=3.10`. | Clean; retain build floor. | Isolated editable build and package metadata. |
| wheel | `>=0.48.0` / not separately installed / `0.48.0` | MIT; Python `>=3.9`. | Clean; `BPM096-M1-07` updated the build floor from 0.47.0 after [PyPI JSON](https://pypi.org/pypi/wheel/json) confirmed 0.48.0. | Clean sdist/wheel and `make package-smoke`. |
| FastAPI | `>=0.141.1` / `0.141.1` / `0.141.1` | MIT; Python `>=3.10`. | Clean; retain. | API/OpenAPI and lifespan contracts. |
| Uvicorn[standard] | `>=0.52.1` / `0.52.4` / `0.52.4` | BSD-3-Clause; Python `>=3.10`; standard extra has platform wheels. | Clean; retain floor. | SQLite startup, health/readiness, OpenAPI smoke. |
| Jinja2 | `>=3.1.6` / `3.1.6` / `3.1.6` | BSD-3-Clause; Python `>=3.7`. | Clean; retain. | Template-route contracts. |
| python-multipart | `>=0.0.32` / `0.0.32` / `0.0.32` | Apache-2.0; Python `>=3.10`. | Clean; retain. | Multipart API tests. |
| Pydantic | `>=2.13.4` / `2.13.4` / `2.13.4` | MIT; Python `>=3.9`. | Clean; retain. | Schema/API validation. |
| pydantic-settings | `>=2.14.2` / `2.15.0` / `2.15.0` | MIT; Python `>=3.10`. | Clean; retain floor and resolved version. | Bootstrap/config tests. |
| jsonschema | `>=4.26.0` / `4.26.0` / `4.26.0` | MIT; Python `>=3.10`. | Clean; retain. | Schema contract tests. |
| fastjsonschema | `>=2.22.1` / `2.22.2` / `2.22.2` | BSD-3-Clause; Python `>=3.10`. | Clean; retain floor. | Schema validation/performance checks. |
| SQLAlchemy | `>=2.0.51` / `2.0.52` / `2.0.52` | MIT; Python `>=3.7`. | Clean; retain floor. | DB model/service tests. |
| Alembic | `>=1.18.5` / `1.19.1` / `1.19.1` | MIT; Python `>=3.10`. | Clean; retain floor and resolved version. | Migration suite with no migration edits. |
| aiosqlite | `>=0.22.1` / `0.22.1` / `0.22.1` | MIT; Python `>=3.9`; host SQLite library. | Clean; retain. | Async DB tests. |
| PyYAML | `>=6.0.3` / `6.0.3` / `6.0.3` | MIT; Python `>=3.8`; native wheels vary by platform. | Clean; retain. | YAML import/export. |
| HTTPX | `>=0.28.1` / `0.28.1` / `0.28.1` | BSD-3-Clause; Python `>=3.8`. | Clean; retain; this is the existing HTTP dependency available to a future server-side AMO integration. | Mocked HTTP client/API tests; future AMO contract tests must keep fixed-origin/no-credential behavior. |
| Requests | `>=2.34.2` / `2.34.2` / `2.34.2` | Apache-2.0; Python `>=3.10`. | Clean; retain. | Mocked network-client tests. |

## Test, development, PostgreSQL, and optional AI dependencies

| Component | Declared / installed / current | License and platform constraint | Advisory / disposition | Focused compatibility check if changed |
| --- | --- | --- | --- | --- |
| pytest | `>=9.1.1` / `9.1.1` / `9.1.1` | MIT; Python `>=3.10`. | Clean; retain. | `pytest -q`. |
| pytest-cov | `>=7.1.0` / `7.1.0` / `7.1.0` | MIT; Python `>=3.9`. | Clean; retain. | Focused coverage invocation. |
| pytest-asyncio | `>=1.4.0` / `1.4.0` / `1.4.0` | Apache-2.0; Python `>=3.10`. | Clean; retain. | Async collection and DB tests. |
| pytest-xdist | `>=3.8.0` / `3.8.0` / `3.8.0` | MIT; Python `>=3.9`; process isolation. | Clean; retain. | Narrow `-n 2` check. |
| AnyIO | `>=4.14.2` / `4.14.2` / `4.14.2` | MIT; Python `>=3.10`; async backend behavior. | Clean; retain. | API/async suite. |
| Beautiful Soup 4 | `>=4.15.0` / `4.15.0` / `4.15.0` | MIT; Python `>=3.7`. | Clean; retain. | HTML parsing contracts. |
| build | `==1.5.0` / `1.5.0` / `1.5.0` | MIT; Python `>=3.10`. | Clean; retain exact pin. | `make package-smoke`. |
| Selenium | `>=4.46.0` / `4.47.0` / `4.47.0` | Apache-2.0; Python `>=3.10`; Firefox/geckodriver pair. | Clean; retain floor/resolved version. | Four-channel Firefox provisioning and live-policy smoke. |
| Ruff | `>=0.16.3` / `0.16.3` / `0.16.3` | MIT; Python `>=3.7`; lint/format rules evolve. | Clean; `BPM096-M1-07` aligned the floor and hook at 0.16.3 after [PyPI JSON](https://pypi.org/pypi/ruff/json) confirmed stable. | `ruff check .` and `ruff format --check .`. |
| Mypy | `>=2.3.1` / `2.3.1` / `2.3.1` | MIT; Python `>=3.10`. | Clean; `BPM096-M1-07` aligned the floor and hook at 2.3.1 after [PyPI JSON](https://pypi.org/pypi/mypy/json) confirmed stable. | `mypy app`. |
| Import Linter | `>=2.13,<3` / `2.13` / `2.13` | BSD-2-Clause; Python `>=3.10`. | Clean; retain. | `make architecture`. |
| pre-commit | `==4.6.2` / `4.6.2` / `4.6.2` | MIT; Python `>=3.10`. | Clean; `BPM096-M1-07` updated the exact pin after [PyPI JSON](https://pypi.org/pypi/pre-commit/json) confirmed stable. | `make pre-commit-check`. |
| pip-audit | `==2.10.1` / `2.10.1` / `2.10.1` | Apache-2.0; Python `>=3.10`. | Clean; retain exact pin. | `make dependency-audit`. |
| cyclonedx-bom | `==7.3.1` / `7.3.1` / `7.3.1` | Apache-2.0; Python `>=3.9,<4`. | Clean; retain exact pin. | Reproducible Python SBOM. |
| types-PyYAML | `>=6.0.12.20260724` / `6.0.12.20260815` / `6.0.12.20260815` | Apache-2.0; Python `>=3.10`. | Clean; retain floor. | `mypy app`. |
| types-requests | `>=2.33.0.20260712` / `2.33.0.20260712` / `2.33.0.20260712` | Apache-2.0; Python `>=3.10`. | Clean; retain. | `mypy app`. |
| IPython | `>=9.16.1` / `9.16.1` / `9.16.1` | BSD-3-Clause; Python `>=3.11`; development-only. | Clean; retain. | Interactive import/startup. |
| asyncpg (`postgres`) | `>=0.31.0` / not installed / `0.31.0` | Apache-2.0; Python `>=3.9`; native PostgreSQL protocol. | Clean by source/previous isolated audit; retain. | Clean import and disposable PostgreSQL integration. |
| psycopg[binary] (`postgres`) | `>=3.3.4` / not installed / `3.3.4` | LGPL-3.0-only; Python `>=3.10`; binary wheel/ABI. | Clean by source/previous isolated audit; retain. | Clean import and disposable PostgreSQL integration. |
| NumPy (`ai`) | `>=2.5.2` / `2.5.2` / `2.5.2` | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0; Python `>=3.12`, native CPU wheels. | Clean; retain exact reviewed floor. | `make test-ai-incubation` on Linux x86_64 and base-absence proof. |
| ONNX Runtime (`ai`) | `>=1.29.0` / `1.29.0` / `1.29.0` | MIT; Python `>=3.11`, native CPU/platform wheels. | Clean; `BPM096-M1-07` updated the optional-extra floor after [PyPI JSON](https://pypi.org/pypi/onnxruntime/json) confirmed stable. | Exact-extra import, fixed CPU inference, base-absence proof. |
| Tokenizers (`ai`) | `>=0.23.1` / `0.23.1` / `0.23.1` | Apache-2.0; Python `>=3.10`, Rust/native wheels. | Clean; retain. | Deterministic tokenization and base-absence proof. |

## Frontend vendor and AMO integration boundary

| Component | Declared / installed / current | License and platform constraint | Advisory / disposition | Focused compatibility check if changed |
| --- | --- | --- | --- | --- |
| monaco-editor | `0.56.0` / `0.56.0` / `0.56.0` | MIT; browser bundle, Node only for rebuild. | Clean; retain. | `npm ci`, vendor checksum/license verification, JSON-editor browser smoke. |
| esbuild | `0.28.2` / `0.28.2` / `0.28.2` | MIT; Node `>=18`, platform binary; BPM Node floor `>=22.14`. | Clean; retain. | `npm ci`, Monaco rebuild/integrity, frontend tests. |
| @cyclonedx/cyclonedx-npm | `6.0.1` / `6.0.1` / `6.0.1` | Apache-2.0; Node `>=20.18`, npm `>=9`. | Clean; `BPM096-M1-07` refreshed the lock after [npm registry metadata](https://registry.npmjs.org/%40cyclonedx%2Fcyclonedx-npm) confirmed stable. | Reproducible `make dependency-audit` SBOM. |
| DOMPurify override | `3.4.14` / `3.4.14` vendor record / `3.4.14` | MPL-2.0 OR Apache-2.0; bundled Monaco runtime. | Clean; `BPM096-M1-07` rebuilt Monaco, licenses, and checksums after [npm registry metadata](https://registry.npmjs.org/dompurify) confirmed stable. | Rebuild must retain the DOMPurify marker and vendor evidence. |
| marked (checked-in vendor) | `18.0.10` / `18.0.10` vendor record / `18.0.10` | MIT; Node `>=20`, satisfied by BPM's Node floor. | Clean; `BPM096-M1-07` rebuilt checked-in vendor evidence after [npm registry metadata](https://registry.npmjs.org/marked) confirmed stable. | Provenance review, rebuild/checksum/license evidence, rendered-content browser tests. |
| AMO integration dependency | no dedicated package / no installed client / no package required | Future integration is an outbound Mozilla service boundary, not an npm/PyPI dependency. Existing HTTPX and the Firefox/Selenium canary are the relevant reviewed dependencies; AMO's `latest.xpi` endpoint is intentionally external and mutable. | No package advisory. Retain no-new-dependency decision; M2-08 must define fixed origin/path, allowlists, no credentials/cookies, size/time/rate bounds, cache, and manual fallback before implementation. | `make test-firefox-live-amo` remains a separately marked external canary; run after every Firefox/geckodriver update and never make save-time behavior depend on AMO. |

## Exact documentation toolchain and lock

The docs environment is Linux x86_64 only and requires Python `>=3.14,<3.15`.
Its requirements lock is an exact reproducibility contract; update of any
accepted row must regenerate the lock and its evidence together, never loosen
the line.

| Component | Declared / installed / current | License and platform constraint | Advisory / disposition | Focused compatibility check if changed |
| --- | --- | --- | --- | --- |
| DITA-OT | `4.4` / exact archive not locally provisioned / `4.4` | Apache-2.0; locked Linux x86_64 archive. | Upstream review; retain exact archive/checksum. | `make setup-docs-toolchain`, docs validation/reproducibility. |
| Eclipse Temurin JRE | `21.0.12+8` / exact archive not locally provisioned / `21.0.12.1+1` | GPL-2.0-with-classpath-exception; Linux x86_64 HotSpot archive. | Upstream review; **approve only exact 21.0.12.1+1 archive/checksum refresh in M1-04**. | Bootstrap toolchain, `make test-docs`, reproducibility. |
| First-party DITA plugin | reserved `0.9.0` / not installed / not published | MPL-2.0; deliberately no artifact. | N/A; retain uninstalled. | Provenance and full docs release gate before activation. |
| attrs | `26.1.0` / exact lock / `26.1.0` | MIT; Python `>=3.9`. | Clean; retain. | Fresh docs venv. |
| iniconfig | `2.3.0` / exact lock / `2.3.0` | MIT; Python `>=3.10`. | Clean; retain. | Docs collection. |
| jsonschema | `4.26.0` / exact lock / `4.26.0` | MIT; Python `>=3.10`. | Clean; retain. | Docs schema contracts. |
| jsonschema-specifications | `2025.9.1` / exact lock / `2025.9.1` | MIT; Python `>=3.9`. | Clean; retain. | Docs schema contracts. |
| packaging | `26.3` / exact lock / `26.3` | Apache-2.0 OR BSD-2-Clause; Python `>=3.9`. | Clean; retain. | Docs reproducibility. |
| pluggy | `1.6.0` / exact lock / `1.6.0` | MIT; Python `>=3.9`. | Clean; retain. | Docs collection. |
| Pygments | `2.21.0` / `2.21.0` docs venv / `2.21.0` | BSD-2-Clause; Python `>=3.9`. | Clean; `BPM096-M1-07` refreshed the exact lock and notice after [PyPI JSON](https://pypi.org/pypi/Pygments/json) confirmed stable. | Fresh docs venv, `make test-docs`, docs reproducibility. |
| pytest | `9.1.1` / exact lock / `9.1.1` | MIT; Python `>=3.10`. | Clean; retain. | Documentation tests. |
| PyYAML | `6.0.3` / exact lock / `6.0.3` | MIT; Python `>=3.8`; native wheels. | Clean; retain. | Documentation metadata validation. |
| referencing | `0.37.0` / exact lock / `0.37.0` | MIT; Python `>=3.10`. | Clean; retain. | Docs schema contracts. |
| rpds-py | `2026.6.3` / exact lock / `2026.6.3` | MIT; Python `>=3.11`, native wheels. | Clean; retain. | Linux x86_64 docs schema contracts. |

## Firefox binaries and geckodriver

Mozilla's review-date feed reports Release `154.0`, ESR `140.14.0esr`, ESR
115 `115.39.0esr`, and ESR-next `153.1.0esr`. The `153.1.0esr` row is labeled
ESR-next by the feed; it is a reviewed target for BPM's already-declared
ESR-153 channel, not evidence that an unpinned channel may be downloaded.
Every approved update below remains conditional on recording the official
Linux x86_64 archive URL and SHA-256 in the manifest before provisioning.

| Component | Declared / installed / current | License and platform constraint | Advisory / disposition | Focused compatibility check if changed |
| --- | --- | --- | --- | --- |
| Firefox Release | `153.0.3` / verified `153.0.3` / `154.0` | MPL-2.0; Linux x86_64 manifest archive. | Upstream review; **approve exact 154.0 manifest/archive/checksum refresh in M1-04**. | Atomic provision/version probe, Release local live suite, AMO canary. |
| Firefox ESR 153 | `153.0esr` / verified `153.0esr` / `153.1.0esr` ESR-next | MPL-2.0; Linux x86_64 manifest archive. | Upstream review; **approve exact 153.1.0esr manifest/archive/checksum refresh in M1-04**. | Atomic provision/version probe, ESR-153 local live suite, AMO canary. |
| Firefox ESR 140 | `140.13.0esr` / verified `140.13.0esr` / `140.14.0esr` | MPL-2.0; Linux x86_64 manifest archive. | Upstream review; **approve exact 140.14.0esr manifest/archive/checksum refresh in M1-04**. | Atomic provision/version probe, ESR-140 local live suite, AMO canary. |
| Firefox ESR 115 | `115.39.0esr` / verified `115.39.0esr` / `115.39.0esr` | MPL-2.0; Linux x86_64 manifest archive. | Upstream review; retain exact manifest provenance. | Version probe and ESR-115 local live suite; separate AMO canary. |
| geckodriver | `0.37.1` / verified `0.37.1` / `0.37.1` | MPL-2.0; Linux x86_64 and Selenium/Firefox pair; uses `--allow-system-access`. | Upstream review; retain exact archive/checksum. | Four-channel provision/version probe and Selenium policy suite. |

## Result and completed stable-refresh boundary

`BPM096-M1-03` initially approved only the exact Firefox manifest refreshes
and the Temurin 21.0.12.1+1 refresh. `BPM096-M1-07` subsequently completed the
remaining nine stable component changes recorded above: all sources remain
bounded exact pins or reviewed minimums, no range was loosened, and the
checked-in vendor assets, licenses, and SHA-256 lock were regenerated only by
their owner script. The Firefox and Temurin dispositions remain independent.

The refresh used `npm ci`, `make rebuild-frontend-vendor`, a fresh local
`.[dev,ai]` installation with `pip check`, and `make setup-docs-toolchain`.
Focused owner/AI checks, frontend tests, lint, typecheck, pre-commit, the docs
partition, and the 3/3 dependency audit passed. The initial isolated
AI-extra package-smoke attempt used `/tmp` and encountered its user quota;
the host quota was not changed. A verified rerun set `TMPDIR` to a unique
`/var/tmp` workspace on the large root filesystem: clean sdist/wheel, base,
PostgreSQL, AI/ONNX Runtime 1.29.0, and combined-extra `pip check` and runtime
probes all passed. That unique temporary workspace was removed after the run.
AMO remains an external, non-save-time canary rather than a package dependency.
