# BPM 0.9.4 Dependency, Toolchain, And Browser Currency Decision

Date: 2026-08-03

Status: **Accepted for `BPM094-M1-03`; amended and fully executed by `BPM094-M1-04`.**

## Decision

This is a point-in-time review and execution record for every direct component declared by BPM:
the Python build and application requirements, PostgreSQL extra, development/test extra,
frontend pins, documentation toolchain, and the Firefox/geckodriver live-test pair. `Retain`
means the declared version was already current. `Applied` means the exact version in the row was
installed only after its focused compatibility and provenance checks passed. No row authorizes a
floating or unrecorded transitive upgrade.

The original `BPM094-M1-03` evidence deferred the larger updates because their required focused
checks had not yet been run: framework/OpenAPI compatibility for FastAPI and Uvicorn;
static-analysis diagnostic review for Ruff and Mypy; a rebuilt editor bundle and real browser
smoke for Monaco; immutable archive checksums and reproducible output for Temurin; and a tested,
exact Firefox/geckodriver pair. `BPM094-M1-04` supplied that evidence and applied every approved
update, including those larger changes. CPython is the sole explicit exception and remains at the
existing Python 3.14 declaration and local 3.14.4 runtime.

The date applies to the external lookups below. The project minimum is Python `>=3.14`; a package's
published Python floor is a compatibility floor, not proof of behaviour on BPM's target runtime.

## Evidence And Method

| Evidence | Result and use |
| --- | --- |
| Project declarations | `pyproject.toml`, `package.json`, `package-lock.json`, `documentation/config/requirements.lock`, `documentation/config/toolchain-lock.json`, and `tools/setup_firefox_live_browsers.sh` are the declaration owners. `app/static/vendor/vendor-lock.json` is the owner of checked-in vendor output checksums. |
| Local resolution | `.venv/bin/python -m pip show ...`, `npm ls --depth=0 --json`, local Firefox/geckodriver version probes, and the documentation-toolchain cache probe were run on 2026-08-03 after installation. |
| Python registry and licenses | [PyPI JSON API](https://docs.pypi.org/api/json/) was queried per project for the latest release, `Requires-Python`, and published license expression. Where that field is absent, the named upstream LICENSE is the authority. |
| Python/npm advisories | An [OSV](https://osv.dev/) `querybatch` against each resolved direct PyPI/npm version returned no advisories; `npm audit --omit=dev --json` and full `npm audit --json` each reported zero vulnerabilities. OSV is an advisory index, so an empty response is recorded as a point-in-time result, not a permanent security guarantee. |
| Frontend registry | The official [npm registry](https://registry.npmjs.org/) was queried for `js-yaml`, `monaco-editor`, and `esbuild`; package-lock integrity fields remain the immutable tarball provenance. |
| Browser and tools | Mozilla's [Firefox channel metadata](https://product-details.mozilla.org/1.0/firefox_versions.json), the official [geckodriver releases](https://github.com/mozilla/geckodriver/releases), [DITA-OT releases](https://github.com/dita-ot/dita-ot/releases), and [Eclipse Temurin 21 releases](https://github.com/adoptium/temurin21-binaries/releases) were queried. |

`None` in the advisory column means the preceding OSV query returned no record for that exact
version. `N/A` means an executable or reserved component is not represented by that package query;
it must instead be reviewed against its upstream security release notes before an update.

## Python Build, Base Runtime, And Optional AI Runtime

The local operating runtime remains Python `3.14.4`; local installed versions match the declared
lower bounds, including `wheel` `0.47.0`. As of `BPM094-M3-01`, NumPy, ONNX Runtime, and
Tokenizers belong only to the explicit `ai` optional extra. The base wheel retains the incubation
Python modules because Python extras select dependencies rather than alternate wheel contents, but
it contains no model, tokenizer, ONNX, RAG generation, or other `data/ai` artifact. Base startup
does not import those modules or native dependencies.

| Component | Declared / installed / latest | Primary source and license | Advisory | Platform constraints | Disposition | Focused verification before a change |
| --- | --- | --- | --- | --- | --- | --- |
| CPython runtime | `>=3.14` / `3.14.4` / stable `3.14.6`; `3.15` is pre-release, planned 2026-10-01 | [Python downloads](https://www.python.org/downloads/) and [lifecycle](https://devguide.python.org/versions/); Python Software Foundation License | N/A package query; review Python release-security notes | BPM's floor and supported operating runtime are Python 3.14; verify all supported OS/Python 3.14 combinations | Approve retain `>=3.14`; defer 3.15 adoption until stable | Fresh 3.14.6 environment: editable install, version/API contracts, `pytest -q`, `ruff check .`, `mypy app`, and documentation release checks; repeat full compatibility/release evidence after 3.15 stabilizes |
| setuptools | `>=68` / `83.0.0` / `83.0.0` | PyPI; MIT | None | PyPI: Python `>=3.10`; BPM `>=3.14` | Approve retain | Isolated editable build and version-surface test |
| wheel | `>=0.47.0` / `0.47.0` / `0.47.0` | PyPI; MIT | None | PyPI: Python `>=3.9`; build-isolation only | Applied `0.47.0` | Non-isolated wheel build and package metadata verification passed |
| FastAPI | `>=0.141.1` / `0.141.1` / `0.141.1` | PyPI; MIT | None | PyPI: Python `>=3.10` | Applied `0.141.1` | 52 API/OpenAPI/health/lifespan tests passed |
| Uvicorn | `>=0.52.1` / `0.52.1` / `0.52.1` | PyPI; BSD-3-Clause | None | PyPI: Python `>=3.10`; `standard` extra has platform wheels | Applied `0.52.1` | Real isolated-SQLite startup, health/readiness, and OpenAPI smoke passed |
| Jinja2 | `>=3.1.6` / `3.1.6` / `3.1.6` | PyPI/upstream LICENSE; BSD-3-Clause | None | PyPI: Python `>=3.7` | Approve retain | Template-route contracts |
| python-multipart | `>=0.0.32` / `0.0.32` / `0.0.32` | PyPI; Apache-2.0 | None | PyPI: Python `>=3.10` | Approve retain | Multipart API tests |
| Pydantic | `>=2.13.4` / `2.13.4` / `2.13.4` | PyPI; MIT | None | PyPI: Python `>=3.9` | Approve retain | Schema/API validation tests |
| pydantic-settings | `>=2.14.2` / `2.14.2` / `2.14.2` | PyPI; MIT | None | PyPI: Python `>=3.10` | Approve retain | Bootstrap/config tests |
| jsonschema | `>=4.26.0` / `4.26.0` / `4.26.0` | PyPI; MIT | None | PyPI: Python `>=3.10` | Approve retain | Schema validation tests |
| fastjsonschema | `>=2.22.1` / `2.22.1` / `2.22.1` | PyPI; BSD-3-Clause | None | PyPI: Python `>=3.10` | Approve upgrade to `2.22.1` | Schema-validation and performance checks |
| SQLAlchemy | `>=2.0.51` / `2.0.51` / `2.0.51` | PyPI; MIT | None | PyPI: Python `>=3.7` | Approve retain | DB model/service tests |
| Alembic | `>=1.18.5` / `1.18.5` / `1.18.5` | PyPI; MIT | None | PyPI: Python `>=3.10` | Approve retain | Migration test suite (no migration edits) |
| aiosqlite | `>=0.22.1` / `0.22.1` / `0.22.1` | PyPI/upstream LICENSE; MIT | None | PyPI: Python `>=3.9`; SQLite platform library | Approve retain | Async DB tests |
| PyYAML | `>=6.0.3` / `6.0.3` / `6.0.3` | PyPI; MIT | None | PyPI: Python `>=3.8`; C extension wheels vary by platform | Approve retain | YAML import/export tests |
| HTTPX | `>=0.28.1` / `0.28.1` / `0.28.1` | PyPI; BSD-3-Clause | None | PyPI: Python `>=3.8` | Approve retain | HTTP client/API tests |
| Requests | `>=2.34.2` / `2.34.2` / `2.34.2` | PyPI; Apache-2.0 | None | PyPI: Python `>=3.10` | Approve retain | Network-client unit tests with mocked transport |
| NumPy (`ai` extra) | `>=2.5.1` / `2.5.1` / `2.5.1` | PyPI; BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 | None | PyPI: Python `>=3.12`; native CPU wheels | Retain only in optional AI incubation | `make test-ai-incubation` on Linux x86_64; base-wheel startup proves it is absent |
| ONNX Runtime (`ai` extra) | `>=1.28.0` / `1.28.0` / `1.28.0` | PyPI; MIT | None | PyPI: Python `>=3.11`; native CPU/platform wheels | Retain only in optional AI incubation; feature activation remains separate | Explicit extra import plus fixed CPU inference tests; base-wheel startup proves it is absent |
| Tokenizers (`ai` extra) | `>=0.23.1` / `0.23.1` / `0.23.1` | PyPI/upstream LICENSE; Apache-2.0 | None | PyPI: Python `>=3.10`; Rust/native wheels | Retain only in optional AI incubation; feature activation remains separate | Explicit extra import and deterministic tokenization tests; base-wheel startup proves it is absent |

The `BPM094-M1-03` snapshot found that the shared `.venv` lacked `flatbuffers` and `protobuf` for
`onnxruntime` and `huggingface-hub` for `tokenizers`, alongside unrelated incomplete NLP packages.
`BPM094-M1-04` installed only the exact direct-AI transitives and their required hub dependencies,
then removed the unowned `argostranslate`, `minisbd`, `stanza`, and `sacremoses` roots from this
project `.venv`; its final `pip check` is clean. This repair does not activate AI features: any
activation task still needs a clean reproducible environment and retained artifact provenance.
Install the maintained development and incubation contours together only when needed with
`python -m pip install -e ".[dev,ai]"`; `make ai-extra-check` reports the exact installed native
versions before any AI development command runs.

## Development, Test, And PostgreSQL Extras

| Component | Declared / installed / latest | Primary source and license | Advisory | Platform constraints | Disposition | Focused verification before a change |
| --- | --- | --- | --- | --- | --- | --- |
| pytest | `>=9.1.1` / `9.1.1` / `9.1.1` | PyPI; MIT | None | Python `>=3.10` | Approve retain | `pytest -q` |
| pytest-cov | `>=7.1.0` / `7.1.0` / `7.1.0` | PyPI; MIT | None | Python `>=3.9` | Approve retain | Focused coverage invocation |
| pytest-asyncio | `>=1.4.0` / `1.4.0` / `1.4.0` | PyPI; Apache-2.0 | None | Python `>=3.10` | Approve retain | Async test collection and DB tests |
| pytest-xdist | `>=3.8.0` / `3.8.0` / `3.8.0` | PyPI; MIT | None | Python `>=3.9`; process isolation | Approve retain | Narrow `-n 2` isolation check |
| AnyIO | `>=4.14.2` / `4.14.2` / `4.14.2` | PyPI; MIT | None | Python `>=3.10`; async backend behaviour | Approve upgrade to `4.14.2` | API/async test suite |
| beautifulsoup4 (Beautiful Soup 4) | `>=4.15.0` / `4.15.0` / `4.15.0` | PyPI; MIT | None | Python `>=3.7` | Approve retain | HTML parsing contract tests |
| Selenium | `>=4.46.0` / `4.46.0` / `4.46.0` | PyPI; Apache-2.0 | None | Python `>=3.10`; browser/driver pair | Applied `4.46.0` | Chromium UI suite passed; exact Release and ESR Firefox pairs passed their live suites |
| Ruff | `>=0.16.1` / `0.16.1` / `0.16.1` | PyPI; MIT | None | Python `>=3.7`; rule set and formatter changes | Applied `0.16.1` as the sole formatter and import-sorter authority | `ruff check .` and `ruff format --check .` |
| Mypy | `>=2.3.0` / `2.3.0` / `2.3.0` | PyPI; MIT | None | Python `>=3.10`; Python 3.14 analysis | Applied `2.3.0` | `mypy app` passed |
| Import Linter | `>=2.13,<3` / `2.13` / `2.13` | PyPI; BSD-2-Clause | None; OSV query on 2026-08-04 returned no record | Python `>=3.10`; parses BPM, documentation and tooling import graphs | Added for `BPM094-M2-05` | `make architecture`, focused direct/indirect forbidden-import proof, and mandatory CI gate passed |
| types-PyYAML | `>=6.0.12.20260724` / `6.0.12.20260724` / `6.0.12.20260724` | PyPI; Apache-2.0 | None | Python `>=3.10`; couples to Mypy | Approve upgrade to `6.0.12.20260724` | `mypy app` |
| types-requests | `>=2.33.0.20260712` / `2.33.0.20260712` / `2.33.0.20260712` | PyPI; Apache-2.0 | None | Python `>=3.10`; couples to Mypy | Approve upgrade to `2.33.0.20260712` | `mypy app` |
| IPython | `>=9.16.1` / `9.16.1` / `9.16.1` | PyPI; BSD-3-Clause | None | Python `>=3.11`; development-only | Approve upgrade to `9.16.1` | Interactive startup/import only |
| asyncpg (PostgreSQL) | `>=0.31.0` / `0.31.0` / `0.31.0` | PyPI; Apache-2.0 | None | Python `>=3.9`; libpq-free native protocol | Approve retain | Clean import plus disposable PostgreSQL integration |
| psycopg[binary] (PostgreSQL) | `>=3.3.4` / `3.3.4` / `3.3.4` | PyPI; LGPL-3.0-only | None | Python `>=3.10`; binary wheels/platform ABI | Approve retain | Clean import plus disposable PostgreSQL integration |

## Frontend Vendor Components

| Component | Declared / installed / latest | Primary source and license | Advisory | Platform constraints | Disposition | Focused verification before a change |
| --- | --- | --- | --- | --- | --- | --- |
| js-yaml | `5.2.3` / `5.2.3` / `5.2.3` | npm registry and package-lock integrity; MIT | None; npm prod/full audit clean | Browser bundle; Node/npm only for rebuild | Approve upgrade to `5.2.3` | Intentional lock review, vendor rebuild, license/checksum verification, affected browser smoke |
| monaco-editor | `0.56.0` / `0.56.0` / `0.56.0` | npm registry and package-lock integrity; MIT | None; npm prod/full audit clean | Browser bundle; Node/npm only for rebuild | Applied `0.56.0` | Vendor rebuild/checksum/license gates and real Chromium JSON-editor smoke passed |
| DOMPurify (Monaco runtime transitive) | override/locked/bundled `3.4.13` / `3.4.13` | npm registry and package-lock integrity; Apache-2.0 OR MPL-2.0 | GHSA-55q2-fjhq-7xh7 affects `<=3.4.12`; fresh npm audit passed after remediation | Bundled into Monaco output during rebuild | Applied security override `3.4.13` | Build overlays the resolved module into Monaco before bundling; bundle marker and vendor contract verify `3.4.13` |
| esbuild | `0.28.1` / `0.28.1` / `0.28.1` | npm registry and package-lock integrity; MIT | None; npm prod/full audit clean | Official package requires Node `>=18`; host Node is `22.22.1`; platform binary package | Approve retain | `npm run build:monaco` and vendor verification in a deliberate rebuild task |

`vendor-lock.json`, `package-lock.json`, checked-in output checksums, and the technical vendor
README now agree on Monaco `0.56.0`. The rebuild also records Monaco's third-party notices and the
DOMPurify and marked license files. Monaco `0.56.0` changed the YAML registration module path, so
the first-party entry point now imports the supported `languages/definitions/yaml/register.js`.

## Documentation Toolchain And Exact Documentation-Test Lock

The documentation toolchain is installed in the local cache. The lock is intentionally Linux
`x86_64` only and remains checksum-pinned; its `target_bpm_version` is ownership metadata, not a
toolchain update signal.

| Component | Declared / installed / latest | Primary source and license | Advisory | Platform constraints | Disposition | Focused verification before a change |
| --- | --- | --- | --- | --- | --- | --- |
| DITA-OT | `4.4` exact / `4.4` / `4.4` | Official release + locked SHA-256; Apache-2.0 | N/A executable | Lock supports `linux-x86_64` | Retain exact `4.4` | Installed toolchain, DITA validation, and reproducibility checks passed |
| Eclipse Temurin JRE | `21.0.12+8` exact / `21.0.12+8` / `21.0.12+8` | Official release + locked SHA-256; GPL-2.0-with-classpath-exception | N/A executable | Linux x86_64 HotSpot archive | Applied `21.0.12+8` | SHA-256 `8a379a67c91a3ae61ffb33d46e0a40c7ba35e70713c4db31cfca30492f792eff`; DITA validation and 1,088-file reproducibility check passed |
| First-party DITA plugin | `0.9.0`, reserved / not installed / N/A | `toolchain-lock.json`; MPL-2.0 | N/A; not shipped | Reserved, no artifact | Reject activation in this task | Plugin provenance and full docs release gate before installation |
| attrs | `26.1.0` exact / `26.1.0` / `26.1.0` | PyPI; MIT | None | Python `>=3.9`; docs env Python `>=3.14,<3.15` | Retain | Fresh docs venv validation passed |
| iniconfig | `2.3.0` exact / `2.3.0` / `2.3.0` | PyPI; MIT | None | Python `>=3.10` | Retain | Fresh docs venv validation passed |
| jsonschema | `4.26.0` exact / `4.26.0` / `4.26.0` | PyPI; MIT | None | Python `>=3.10` | Retain | Docs contract validation passed |
| jsonschema-specifications | `2025.9.1` exact / `2025.9.1` / `2025.9.1` | PyPI; MIT | None | Python `>=3.9` | Retain | Docs contract validation passed |
| packaging | `26.2` exact / `26.2` / `26.2` | PyPI; Apache-2.0 OR BSD-2-Clause | None | Python `>=3.8` | Retain | Docs test collection passed |
| pluggy | `1.6.0` exact / `1.6.0` / `1.6.0` | PyPI; MIT | None | Python `>=3.9` | Retain | Docs test collection passed |
| Pygments | `2.20.0` exact / `2.20.0` / `2.20.0` | PyPI; BSD-2-Clause | None | Python `>=3.9` | Retain | Documentation validation passed |
| pytest | `9.1.1` exact / `9.1.1` / `9.1.1` | PyPI; MIT | None | Python `>=3.10` | Retain | Documentation tests passed |
| PyYAML | `6.0.3` exact / `6.0.3` / `6.0.3` | PyPI; MIT | None | Python `>=3.8`; native wheels | Retain | Documentation metadata validation passed |
| referencing | `0.37.0` exact / `0.37.0` / `0.37.0` | PyPI; MIT | None | Python `>=3.10` | Retain | Docs schema contracts passed |
| rpds-py | `2026.6.3` exact / `2026.6.3` / `2026.6.3` | PyPI; MIT | None | Python `>=3.11`; native wheels | Retain | Docs schema contracts passed on Linux x86_64 |

## Firefox And Geckodriver

| Component | Declared / installed / latest | Primary source and license | Advisory | Platform constraints | Disposition | Focused verification before a change |
| --- | --- | --- | --- | --- | --- | --- |
| Firefox Release | exact `153.0.1` / `153.0.1` / `153.0.1` | Immutable Mozilla archive; MPL-2.0 | Mozilla security advisories/release notes reviewed | Setup script supports Linux x86_64 | Applied `153.0.1` | SHA-256 `05fb58905a90ce717c36a2ba5af0bbdc4d0e8b0eed6f50469030774c8c85b8eb`; 20 live tests and 2 AMO-canary tests passed |
| Firefox ESR | exact `140.13.0esr` / tested `140.13.0esr` / `140.13.0esr` | Immutable Mozilla archive; MPL-2.0 | Mozilla ESR security advisories/release notes reviewed | Setup script supports Linux x86_64 | Applied `140.13.0esr` channel pin | SHA-256 `866d7e5f94abe93132e02a0db72da32b6e133905fcbea6afa417a96d496021da`; 20 live tests and 2 AMO-canary tests passed |
| geckodriver | exact `0.37.1` / `0.37.1` / `0.37.1` | Official Mozilla release; MPL-2.0 | Upstream release notes reviewed | Setup script supports Linux x86_64; paired with Firefox and Selenium | Applied `0.37.1` | SHA-256 `e815130ea95983e162ae91843b48d3a3ce991735635fce83a647afde21e09f7e`; WebDriver service uses required `--allow-system-access` |

The setup script no longer uses floating channel URLs. It downloads exact Release or ESR and
geckodriver archives into a sibling staging directory, checks the recorded SHA-256 values, extracts
and probes both executable versions, and only then promotes the verified directory. The previous
working pair is retained until promotion succeeds. The local final state is the default Release
pair: Firefox `153.0.1` with geckodriver `0.37.1`.

## Result And Follow-Up Boundaries

- `BPM094-M1-04` applied all approved current versions, including the formerly deferred framework,
  analysis, frontend, documentation-JRE, and paired-browser updates. CPython was explicitly
  excluded and was not changed.
- Compatibility evidence includes 52 focused API tests, a real Uvicorn startup smoke, Ruff and
  Mypy gates, a non-isolated wheel build, the Chromium UI/editor smokes, frontend checksum/license
  verification, DITA validation, a reproducibility comparison of 1,088 files, 20 Firefox live
  tests on each of Release and ESR, 2 external AMO-canary tests on each channel, and the final
  standard suite with 1,362 passing tests.
- PyPI/OSV results were clean for the queried direct Python and npm records; npm's production and
  full dependency audits were also clean. These dated outcomes do not cover future advisories.
- No dependency update remains deferred other than the explicitly excluded CPython runtime.
  First-party DITA plugin activation and AI feature/model activation remain separate feature and
  provenance decisions; they are not outstanding package-version updates.
