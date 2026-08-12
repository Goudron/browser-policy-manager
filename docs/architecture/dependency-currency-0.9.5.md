# BPM 0.9.5 Dependency, Toolchain, And Browser Currency Decision

Date: 2026-08-10

Status: **Accepted review for `BPM095-M1-03`; changes require `BPM095-M1-04`.**

## Decision

This is the bounded, maintained currency decision for the direct BPM components
declared in `pyproject.toml`, `package.json`,
`documentation/config/requirements.lock`, `documentation/config/toolchain-lock.json`,
and `tools/firefox_live_browsers_manifest_0_9_4.json`. It supersedes the
0.9.4 matrix for the 0.9.5 release anchor; it does **not** change a dependency,
lock, vendor bundle, checksum, browser archive, or the reserved documentation plugin.

`Approve update` is permission only for the exact target and focused evidence
listed in the row. It is not a floating upgrade permission. `Retain` means the
installed resolution and the latest source result agree, or that the declared
minimum deliberately remains the supported compatibility floor. `Defer` keeps
an unpinned/new channel outside M1-04. No row permits an unrecorded transitive
change.

## Method And Evidence

Local installed versions were read on 2026-08-10 from `.venv`, the repository
documentation virtual environment, `npm ls --depth=0 --json`, and the browser
manifest. There is no repository-local installed Firefox cache, so browser rows
truthfully record **not installed** rather than treating a URL as an installed
binary. The checked local runtime is CPython 3.14.6, Node 22.22.1, and npm 9.2.0.

The latest/version, Python-floor, and license metadata below came from the
authoritative [PyPI JSON API](https://docs.pypi.org/api/json/) for each named
Python project; the authoritative [npm registry](https://registry.npmjs.org/)
for each named npm project; Mozilla's
[Firefox version feed](https://product-details.mozilla.org/1.0/firefox_versions.json);
the official [geckodriver releases](https://github.com/mozilla/geckodriver/releases),
[DITA-OT releases](https://github.com/dita-ot/dita-ot/releases), and
[Temurin 21 releases](https://github.com/adoptium/temurin21-binaries/releases);
and the [Python downloads page](https://www.python.org/downloads/). Where PyPI
does not publish an SPDX expression, the named upstream project's LICENSE is
the license evidence.

Security evidence is point-in-time only:

- `npm audit --omit=dev --json` and full `npm audit --json` both returned zero
  vulnerabilities against `package-lock.json`.
- `pip-audit --requirement documentation/config/requirements.lock --no-deps --strict`
  returned “No known vulnerabilities found.”
- `make dependency-audit` creates clean base and `[dev,postgres,ai]` environments,
  runs `pip check`, `pip-audit`, CycloneDX SBOM generation, and the lockfile npm
  audit. Its outputs are ignored transient evidence under `artifacts/dependency-audit/`;
  M1-04 must rerun it after any approved change.
- Firefox, geckodriver, DITA-OT, Temurin, and CPython are executables rather than
  PyPI/npm packages. Their rows require upstream security-release review and
  archive/checksum verification before an update.

In the tables, **Clean** means the applicable audit above returned no known
advisory for the reviewed resolved version. **Upstream review** means an
executable's upstream security notes/release evidence must be reviewed at the
change. “M1-04” in the final column is the focused verification required before
the disposition may be applied.

## Base Python Runtime And Build

| Component | Declared / installed / current on 2026-08-10 | Primary source, license, and constraints | Security | Disposition and M1-04 verification |
| --- | --- | --- | --- | --- |
| CPython | `>=3.14` / `3.14.6` / `3.14.6` stable | [Python](https://www.python.org/downloads/); PSF-2.0. BPM supports Python 3.14; 3.15 is not adopted before stable release evidence. | Upstream review | Retain 3.14.6; defer 3.15. Fresh 3.14.6 editable install, package/API contracts, `pytest -q`, `ruff check .`, `mypy app`, docs release checks. |
| setuptools | `>=68` / `84.0.0` / `84.0.0` | [PyPI](https://pypi.org/project/setuptools/); MIT; Python `>=3.10`. | Clean | Retain. Isolated editable build and package metadata check. |
| wheel | `>=0.47.0` / `0.47.0` / `0.47.0` | [PyPI](https://pypi.org/project/wheel/); MIT; Python `>=3.9`. | Clean | Retain. Non-isolated wheel/sdist build and package-smoke check. |
| FastAPI | `>=0.141.1` / `0.141.1` / `0.141.1` | [PyPI](https://pypi.org/project/fastapi/); MIT; Python `>=3.10`. | Clean | Retain. API/OpenAPI, health, lifespan contracts. |
| Uvicorn[standard] | `>=0.52.1` / `0.52.1` / `0.52.1` | [PyPI](https://pypi.org/project/uvicorn/); BSD-3-Clause; Python `>=3.10`; standard extra has platform wheels. | Clean | Retain. Isolated SQLite startup, health/readiness, OpenAPI smoke. |
| Jinja2 | `>=3.1.6` / `3.1.6` / `3.1.6` | [PyPI](https://pypi.org/project/Jinja2/); BSD-3-Clause; Python `>=3.7`. | Clean | Retain. Template-route contracts. |
| python-multipart | `>=0.0.32` / `0.0.32` / `0.0.32` | [PyPI](https://pypi.org/project/python-multipart/); Apache-2.0; Python `>=3.10`. | Clean | Retain. Multipart API tests. |
| Pydantic | `>=2.13.4` / `2.13.4` / `2.13.4` | [PyPI](https://pypi.org/project/pydantic/); MIT; Python `>=3.9`. | Clean | Retain. Schema/API validation tests. |
| pydantic-settings | `>=2.14.2` / `2.15.0` / `2.15.0` | [PyPI](https://pypi.org/project/pydantic-settings/); MIT; Python `>=3.10`. | Clean | Retain resolved 2.15.0; do not alter the lower-bound policy here. Bootstrap/config tests. |
| jsonschema | `>=4.26.0` / `4.26.0` / `4.26.0` | [PyPI](https://pypi.org/project/jsonschema/); MIT; Python `>=3.10`. | Clean | Retain. Schema validation contracts. |
| fastjsonschema | `>=2.22.1` / `2.22.1` / `2.22.1` | [PyPI](https://pypi.org/project/fastjsonschema/); BSD-3-Clause; Python `>=3.10`. | Clean | Retain. Schema validation and performance checks. |
| SQLAlchemy | `>=2.0.51` / `2.0.51` / `2.0.51` | [PyPI](https://pypi.org/project/SQLAlchemy/); MIT; Python `>=3.7`. | Clean | Retain. DB model/service tests. |
| Alembic | `>=1.18.5` / `1.19.1` / `1.19.1` | [PyPI](https://pypi.org/project/alembic/); MIT; Python `>=3.10`. | Clean | Retain resolved 1.19.1; do not alter the lower-bound policy here. Migration suite with no migration edits. |
| aiosqlite | `>=0.22.1` / `0.22.1` / `0.22.1` | [PyPI](https://pypi.org/project/aiosqlite/); MIT; Python `>=3.9`; platform SQLite library. | Clean | Retain. Async DB tests. |
| PyYAML | `>=6.0.3` / `6.0.3` / `6.0.3` | [PyPI](https://pypi.org/project/PyYAML/); MIT; Python `>=3.8`; C wheels vary by platform. | Clean | Retain. YAML import/export tests. |
| HTTPX | `>=0.28.1` / `0.28.1` / `0.28.1` | [PyPI](https://pypi.org/project/httpx/); BSD-3-Clause; Python `>=3.8`. | Clean | Retain. HTTP client/API tests. |
| Requests | `>=2.34.2` / `2.34.2` / `2.34.2` | [PyPI](https://pypi.org/project/requests/); Apache-2.0; Python `>=3.10`. | Clean | Retain. Mocked network-client unit tests. |

## Development, Test, PostgreSQL, And Optional AI Extras

| Component | Declared / installed / current on 2026-08-10 | Primary source, license, and constraints | Security | Disposition and M1-04 verification |
| --- | --- | --- | --- | --- |
| pytest | `>=9.1.1` / `9.1.1` / `9.1.1` | [PyPI](https://pypi.org/project/pytest/); MIT; Python `>=3.10`. | Clean | Retain. `pytest -q`. |
| pytest-cov | `>=7.1.0` / `7.1.0` / `7.1.0` | [PyPI](https://pypi.org/project/pytest-cov/); MIT; Python `>=3.9`. | Clean | Retain. Focused coverage invocation. |
| pytest-asyncio | `>=1.4.0` / `1.4.0` / `1.4.0` | [PyPI](https://pypi.org/project/pytest-asyncio/); Apache-2.0; Python `>=3.10`. | Clean | Retain. Async collection and DB tests. |
| pytest-xdist | `>=3.8.0` / `3.8.0` / `3.8.0` | [PyPI](https://pypi.org/project/pytest-xdist/); MIT; Python `>=3.9`; process isolation. | Clean | Retain. Narrow `-n 2` isolation check. |
| AnyIO | `>=4.14.2` / `4.14.2` / `4.14.2` | [PyPI](https://pypi.org/project/anyio/); MIT; Python `>=3.10`; async backend behavior. | Clean | Retain. API/async suite. |
| Beautiful Soup 4 | `>=4.15.0` / `4.15.0` / `4.15.0` | [PyPI](https://pypi.org/project/beautifulsoup4/); MIT; Python `>=3.7`. | Clean | Retain. HTML parsing contracts. |
| build | `==1.3.0` / `1.3.0` / `1.5.0` | [PyPI](https://pypi.org/project/build/); MIT; Python `>=3.10`. | Clean | **Approve update to 1.5.0.** Update exact dev pin only after clean sdist/wheel delivery and `make package-smoke`. |
| Selenium | `>=4.46.0` / `4.46.0` / `4.46.0` | [PyPI](https://pypi.org/project/selenium/); Apache-2.0; Python `>=3.10`; browser/driver pair. | Clean | Retain. Chromium and pinned Firefox smoke. |
| Ruff | `>=0.16.1` / `0.16.2` / `0.16.2` | [PyPI](https://pypi.org/project/ruff/); MIT; Python `>=3.7`; rules/formatter can change. | Clean | Retain resolved 0.16.2. `ruff check .` and `ruff format --check .`. |
| Mypy | `>=2.3.0` / `2.3.0` / `2.3.0` | [PyPI](https://pypi.org/project/mypy/); MIT; Python `>=3.10`. | Clean | Retain. `mypy app`. |
| Import Linter | `>=2.13,<3` / `2.13` / `2.13` | [PyPI](https://pypi.org/project/import-linter/); BSD-2-Clause; Python `>=3.10`. | Clean | Retain. `make architecture`. |
| pre-commit | `==4.6.1` / `4.6.1` / `4.6.1` | [PyPI](https://pypi.org/project/pre-commit/); MIT; Python `>=3.10`. | Clean | Retain. `make pre-commit-check`. |
| pip-audit | `==2.10.1` / `2.10.1` / `2.10.1` | [PyPI](https://pypi.org/project/pip-audit/); Apache-2.0; Python `>=3.10`. | Clean | Retain. `make dependency-audit`. |
| cyclonedx-bom | `==7.3.1` / `7.3.1` / `7.3.1` | [PyPI](https://pypi.org/project/cyclonedx-bom/); Apache-2.0; Python `>=3.9,<4`. | Clean | Retain. Reproducible SBOM portion of dependency audit. |
| types-PyYAML | `>=6.0.12.20260724` / `6.0.12.20260724` / `6.0.12.20260724` | [PyPI](https://pypi.org/project/types-PyYAML/); Apache-2.0; Python `>=3.10`. | Clean | Retain. `mypy app`. |
| types-requests | `>=2.33.0.20260712` / `2.33.0.20260712` / `2.33.0.20260712` | [PyPI](https://pypi.org/project/types-requests/); Apache-2.0; Python `>=3.10`. | Clean | Retain. `mypy app`. |
| IPython | `>=9.16.1` / `9.16.1` / `9.16.1` | [PyPI](https://pypi.org/project/ipython/); BSD-3-Clause; Python `>=3.11`; development-only. | Clean | Retain. Interactive startup/import. |
| asyncpg (PostgreSQL) | `>=0.31.0` / `0.31.0` / `0.31.0` | [PyPI](https://pypi.org/project/asyncpg/); Apache-2.0; Python `>=3.9`; native protocol. | Clean | Retain. Clean import and disposable PostgreSQL integration. |
| psycopg[binary] (PostgreSQL) | `>=3.3.4` / `3.3.4` / `3.3.4` | [PyPI](https://pypi.org/project/psycopg/); LGPL-3.0-only; Python `>=3.10`; binary wheel/ABI. | Clean | Retain. Clean import and disposable PostgreSQL integration. |
| NumPy (`ai`) | `>=2.5.1` / `2.5.1` / `2.5.2` | [PyPI](https://pypi.org/project/numpy/); BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0; Python `>=3.12`, native CPU wheels. | Clean | **Approve update to 2.5.2**, optional AI only. `make test-ai-incubation` on Linux x86_64 and base startup absence proof. |
| ONNX Runtime (`ai`) | `>=1.28.0` / `1.28.0` / `1.28.0` | [PyPI](https://pypi.org/project/onnxruntime/); MIT; Python `>=3.11`, native CPU/platform wheels. | Clean | Retain optional AI-only state. Exact-extra import and fixed CPU inference; base absence proof. |
| Tokenizers (`ai`) | `>=0.23.1` / `0.23.1` / `0.23.1` | [PyPI](https://pypi.org/project/tokenizers/); Apache-2.0; Python `>=3.10`, Rust/native wheels. | Clean | Retain optional AI-only state. Exact-extra import/deterministic tokenization; base absence proof. |

## Frontend Vendor Components

| Component | Declared / installed / current on 2026-08-10 | Primary source, license, and constraints | Security | Disposition and M1-04 verification |
| --- | --- | --- | --- | --- |
| monaco-editor | `0.56.0` / `0.56.0` / `0.56.0` | [npm](https://www.npmjs.com/package/monaco-editor/v/0.56.0); MIT; browser bundle, Node/npm only for rebuild. | Clean, prod/full npm audit | Retain. Intentional lock review, vendor checksum/license verification, JSON-editor browser smoke. |
| esbuild | `0.28.1` / `0.28.1` / `0.28.2` | [npm](https://www.npmjs.com/package/esbuild/v/0.28.2); MIT; Node `>=18`, platform binary; BPM Node floor `>=22.14`. | Clean, prod/full npm audit | **Approve update to 0.28.2.** Exact lock review, `npm ci`, Monaco rebuild, vendor integrity, affected frontend tests. |
| @cyclonedx/cyclonedx-npm | `6.0.0` / `6.0.0` / `6.0.0` | [npm](https://www.npmjs.com/package/@cyclonedx/cyclonedx-npm/v/6.0.0); Apache-2.0; Node `>=20.18`, npm `>=9`. | Clean, full npm audit | Retain. Reproducible `make dependency-audit` SBOM. |
| DOMPurify override | `3.4.13` / `3.4.13` / `3.4.13` | [npm](https://www.npmjs.com/package/dompurify/v/3.4.13); MPL-2.0 OR Apache-2.0; bundled Monaco runtime. | Clean; previous `GHSA-55q2-fjhq-7xh7` is fixed above 3.4.12 | Retain exact override. Rebuild must retain the 3.4.13 bundle marker and vendor-license/checksum evidence. |
| marked (checked-in vendor) | `14.0.0` / `14.0.0` / `18.0.9` | [npm](https://www.npmjs.com/package/marked/v/18.0.9); MIT; latest requires Node `>=20`, while BPM's floor is `>=22.14`. | Clean, full npm audit | **Defer major 14 → 18 update.** No advisory requires it; a future deliberate vendor update needs source/provenance review, `npm ci`, rebuild/checksum/license evidence, and affected rendered-content browser tests. |

## Documentation Toolchain And Exact Documentation-Test Lock

The documentation lock is Linux `x86_64` only and requires Python `>=3.14,<3.15`.
It is an exact reproducibility contract: any accepted change must update its owning
lock/checksum/third-party evidence together, never loosen the line.

| Component | Declared / installed / current on 2026-08-10 | Primary source, license, and constraints | Security | Disposition and M1-04 verification |
| --- | --- | --- | --- | --- |
| DITA-OT | `4.4` / `4.4` / `4.4` | [official release](https://github.com/dita-ot/dita-ot/releases/tag/4.4); Apache-2.0; locked Linux x86_64 archive. | Upstream review | Retain exact archive/checksum. `make setup-docs-toolchain`, docs validation and reproducibility. |
| Eclipse Temurin JRE | `21.0.12+8` / `21.0.12+8` / `21.0.12+8` | [official release](https://github.com/adoptium/temurin21-binaries/releases/tag/jdk-21.0.12%2B8); GPL-2.0-with-classpath-exception; Linux x86_64 HotSpot archive. | Upstream review | Retain exact archive/checksum. Toolchain bootstrap, docs validation/reproducibility. |
| First-party DITA plugin | reserved `0.9.0` / not installed / not published | `toolchain-lock.json`; MPL-2.0; deliberately reserved, no artifact. | N/A | Retain uninstalled; do not activate. Provenance and full docs release gate before a future activation. |
| attrs | `26.1.0` / `26.1.0` / `26.1.0` | [PyPI](https://pypi.org/project/attrs/); MIT; Python `>=3.9`. | Clean | Retain. Fresh docs venv validation. |
| iniconfig | `2.3.0` / `2.3.0` / `2.3.0` | [PyPI](https://pypi.org/project/iniconfig/); MIT; Python `>=3.10`. | Clean | Retain. Docs test collection. |
| jsonschema | `4.26.0` / `4.26.0` / `4.26.0` | [PyPI](https://pypi.org/project/jsonschema/); MIT; Python `>=3.10`. | Clean | Retain. Docs schema contracts. |
| jsonschema-specifications | `2025.9.1` / `2025.9.1` / `2025.9.1` | [PyPI](https://pypi.org/project/jsonschema-specifications/); MIT; Python `>=3.9`. | Clean | Retain. Docs schema contracts. |
| packaging | `26.2` / `26.2` / `26.3` | [PyPI](https://pypi.org/project/packaging/); Apache-2.0 OR BSD-2-Clause; Python `>=3.9`. | Clean | **Approve update to 26.3.** Regenerate exact docs lock, clean docs venv, `make test-docs`, docs reproducibility. |
| pluggy | `1.6.0` / `1.6.0` / `1.6.0` | [PyPI](https://pypi.org/project/pluggy/); MIT; Python `>=3.9`. | Clean | Retain. Docs test collection. |
| Pygments | `2.20.0` / `2.20.0` / `2.20.0` | [PyPI](https://pypi.org/project/Pygments/); BSD-2-Clause; Python `>=3.9`. | Clean | Retain. Documentation validation. |
| pytest | `9.1.1` / `9.1.1` / `9.1.1` | [PyPI](https://pypi.org/project/pytest/); MIT; Python `>=3.10`. | Clean | Retain. Documentation tests. |
| PyYAML | `6.0.3` / `6.0.3` / `6.0.3` | [PyPI](https://pypi.org/project/PyYAML/); MIT; Python `>=3.8`; native wheels. | Clean | Retain. Documentation metadata validation. |
| referencing | `0.37.0` / `0.37.0` / `0.37.0` | [PyPI](https://pypi.org/project/referencing/); MIT; Python `>=3.10`. | Clean | Retain. Docs schema contracts. |
| rpds-py | `2026.6.3` / `2026.6.3` / `2026.6.3` | [PyPI](https://pypi.org/project/rpds-py/); MIT; Python `>=3.11`, native wheels. | Clean | Retain. Docs schema contracts on Linux x86_64. |

## Pinned Firefox Artifacts And Geckodriver

The product-details feed reports Release `153.0.3`, ESR 140 `140.13.0esr`,
ESR 153 `153.0esr`, and ESR 115 `115.38.0esr` on the review date. ESR 115 is
not a current live-browser manifest entry: its independent provenance and
checksum are owned by BPM095-M2-02/M3-01/M7-04, so M1-04 must not invent or
download it. Browser checksums below remain the exact manifest provenance.

| Component | Declared / installed / current on 2026-08-10 | Primary source, license, and constraints | Security | Disposition and M1-04 verification |
| --- | --- | --- | --- | --- |
| Firefox Release | `153.0.1` / not installed / `153.0.3` | [Mozilla feed](https://product-details.mozilla.org/1.0/firefox_versions.json) and [pinned archive](https://archive.mozilla.org/pub/firefox/releases/153.0.1/linux-x86_64/en-US/firefox-153.0.1.tar.xz); MPL-2.0; Linux x86_64 only. | Upstream review | **Approve update to 153.0.3.** Record official archive URL/SHA-256, provision atomically, exact-version probe, Release live and AMO-canary suites. |
| Firefox ESR 153 | `153.0esr` / not installed / `153.0esr` | [Mozilla feed](https://product-details.mozilla.org/1.0/firefox_versions.json) and [pinned archive](https://archive.mozilla.org/pub/firefox/releases/153.0esr/linux-x86_64/en-US/firefox-153.0esr.tar.xz); MPL-2.0; Linux x86_64 only. | Upstream review | Retain exact pin/checksum. Atomic provision, version probe, ESR 153 live and AMO-canary suites. |
| Firefox ESR 140 | `140.13.0esr` / not installed / `140.13.0esr` | [Mozilla feed](https://product-details.mozilla.org/1.0/firefox_versions.json) and [pinned archive](https://archive.mozilla.org/pub/firefox/releases/140.13.0esr/linux-x86_64/en-US/firefox-140.13.0esr.tar.xz); MPL-2.0; Linux x86_64 only. | Upstream review | Retain exact pin/checksum. Atomic provision, version probe, ESR 140 live and AMO-canary suites. |
| Firefox ESR 115 channel | not declared / not installed / `115.38.0esr` | [Mozilla feed](https://product-details.mozilla.org/1.0/firefox_versions.json); MPL-2.0; future Linux x86_64 artifact must be independently pinned. | Upstream review | **Defer to M2-02/M3-01/M7-04.** Verify support statement, source tag/archive/SHA-256 and then run separate ESR 115 live evidence; no M1-04 download/change. |
| geckodriver | `0.37.1` / not installed / `0.37.1` | [official release](https://github.com/mozilla/geckodriver/releases/tag/v0.37.1); MPL-2.0; Linux x86_64 and Selenium/Firefox pairing, `--allow-system-access`. | Upstream review | Retain exact pin/checksum. Pair with every retained/updated Firefox channel and run WebDriver/live suites. |

## Approved, Deferred, And Security Result

M1-04 may apply only these exact candidate groups after their row-level checks:

1. `build==1.5.0` with a clean wheel/sdist and package-smoke proof.
2. `numpy>=2.5.2` only in the optional AI contour, with native Linux inference
   and base-wheel absence proof.
3. `esbuild==0.28.2`, including `package-lock.json`, a deliberate vendor
   rebuild, licenses/checksums, `npm ci`, and frontend evidence.
4. Documentation `packaging==26.3`, regenerated only through the documentation
   lock's owning procedure with clean-toolchain/docs/reproducibility evidence.
5. Firefox Release `153.0.3`, only after authoritative archive/SHA-256,
   atomic provision, version probe, and Release live/AMO-canary proof.

Every other direct component is retained. ESR 115 browser provisioning is
explicitly deferred to its schema/lifecycle tasks; the reserved first-party DITA
plugin remains uninstalled. There is no current advisory blocker: both npm
audits and the documentation-lock `pip-audit` are clean, while the project
clean-environment dependency audit is the final release gate after M1-04
changes. An audit outcome is not a promise about advisories published later.

## Focused M1-04 Closure Checklist

For the approved groups only: update exact source/lock/vendor/browser manifest
owners; retain or refresh third-party notices and SHA-256 evidence; run `npm ci`,
`npm audit`, `pip check`, and `make dependency-audit`; then execute each focused
row-level test. Do not modify the schema catalog, Firefox schema sources, product
channels, changelog, or release documentation as part of the dependency refresh.
