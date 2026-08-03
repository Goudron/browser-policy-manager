# BPM 0.9.3 Dependency And Model Currency Check

Date: 2026-07-28

Status: **Accepted for `BPM093-M1-03`.**

This bounded review establishes the dependency, browser, search, and local-RAG starting point for
the BPM 0.9.3 documentation completion epic. It records one security update and explicitly
defers every compatibility-affecting upgrade, model download, and service introduction to a later,
approved backlog task.

## Scope And Evidence Sources

The review covers direct application and development requirements in `pyproject.toml`, frontend
pins and the self-hosted vendor bundle, documentation publishing and test locks, the local browser
and driver pair, and the prospective search/RAG components from the BPM093 backlog. Sources were
checked on 2026-07-28 through the [PyPI index](https://pypi.org/), the
[npm registry](https://registry.npmjs.org/), [npm advisories](https://github.com/advisories),
[DITA-OT releases](https://github.com/dita-ot/dita-ot/releases),
[Eclipse Temurin 21 releases](https://github.com/adoptium/temurin21-binaries/releases), and the
official repositories/model cards linked below. Local versions came from the project virtual
environment, Node/npm, Chromium, ChromeDriver, Firefox, and geckodriver probes.

Generated documentation, dependency directories, caches, corpora, and downloaded model artifacts
are outside this review. No model or search service is installed by this task.

## Security Decision

`npm audit --omit=dev` identified a high-severity parsing denial-of-service advisory,
[`GHSA-pm4m-ph32-ghv5`](https://github.com/advisories/GHSA-pm4m-ph32-ghv5), in direct dependency
`js-yaml` `5.2.1`. Update it to `5.2.2`, the patched MIT-licensed release. Its provenance is the
[npm registry tarball](https://registry.npmjs.org/js-yaml/-/js-yaml-5.2.2.tgz), with recorded
integrity `sha512-dayzUzKkJ1MkuUtZglSebU43utNXH0OWQByK9rKOOuYIO8M5TV1y+n8ALMdG0rdzBnfNkOmZEqrURepb0ejqBw==`.
The project vendor rebuild regenerates `app/static/vendor/js-yaml.js` and the corresponding
checksum in `vendor-lock.json`; the license and vendor checks remain required.

This is the only dependency update in `BPM093-M1-03`. The release owner owns the package lock and
vendor lock; the task record owns the advisory disposition and provenance evidence.

## Review Matrix

| Area | Checked version or candidate | Provenance, license, platform | Decision |
| --- | --- | --- | --- |
| Python application runtime | FastAPI `0.139.0` → `0.140.13`; Uvicorn `0.50.0` → `0.51.0`; FastJSONSchema `2.21.2` → `2.22.1`; remaining direct runtime minimums were not listed as outdated by the PyPI query. | PyPI; project supports Python `>=3.14`. | Keep current declared minimums. A framework/runtime update needs dedicated API and full-suite compatibility evidence. |
| Test, browser, and development stack | AnyIO `4.14.1` → `4.14.2`; Selenium `4.45.0` → `4.46.0`; Ruff `0.15.20` → `0.16.0`; Mypy `2.1.0` → `2.3.0`; updated stub releases are available. | PyPI; browser behavior and static-analysis rules can change. | Defer. Upgrade only in a dedicated task with browser, lint, type, and full-suite evidence. |
| Optional PostgreSQL stack | asyncpg `0.31.0`, psycopg `3.3.4`. | PyPI; optional database platform. | Keep; no update was indicated by the query. |
| Frontend vendor stack | js-yaml `5.2.1` → `5.2.2`; Monaco Editor `0.53.0` → `0.56.0`; esbuild `0.28.1` is current. | npm registry; js-yaml is MIT and self-hosted. | Apply only js-yaml security update. Defer Monaco because it needs a focused vendor and browser-regression task. |
| Documentation publishing toolchain | DITA-OT `4.4`, archive SHA-256 recorded in `documentation/config/toolchain-lock.json`; Temurin JRE `21.0.11+10`, archive SHA-256 recorded there. | DITA-OT Apache-2.0; Temurin GPL-2.0-with-classpath-exception; pinned cross-platform publishing runtime. | Keep exact lock. Its `target_bpm_version` labels are release-metadata ownership, not an implicit toolchain upgrade. |
| Documentation-only test lock | Exact `documentation/config/requirements.lock` pins, including pytest `9.1.1`, jsonschema `4.26.0`, and PyYAML `6.0.3`. | Hashed, exact documentation-test environment. | Keep unchanged; update only with reproducible documentation-test evidence. |
| Browser pair | Chromium `150.0.7871.128`; ChromeDriver `150.0.7871.128`; Firefox `150.0.1`; geckodriver `0.36.0`; Selenium `4.45.0`. | Local Linux test artifacts; Chromium and ChromeDriver exactly match. | Keep. Any browser, driver, or Selenium update requires immediate-escalation browser smoke and an exact version record. |
| Static documentation search | [Pagefind](https://pagefind.app/) `1.5.2` (candidate); [Meilisearch](https://www.meilisearch.com/) (candidate). | Pagefind MIT; Meilisearch MIT. Pagefind is static and cross-platform; Meilisearch requires a managed local service. | Do not install. M3 must benchmark six-locale recall, CJK segmentation, index size, and offline delivery before selecting an engine. |
| Local inference runtime | [llama.cpp](https://github.com/ggml-org/llama.cpp) release `b9637` (candidate). | MIT; signed upstream release includes Linux x64 CPU artifacts. | Do not install. M6 must establish reproducible binary checksum/provenance and CPU/RAM measurements on the target laptop class. |
| Chat model | [Qwen3-0.6B-GGUF](https://huggingface.co/Qwen/Qwen3-0.6B-GGUF) (candidate; Q8 artifact about 639 MB). | Apache-2.0; upstream Hugging Face model card; CPU quantized artifact. | Do not download or fine-tune. M5/M6 must evaluate six locales, product grounding, off-topic rejection, model file checksum, and laptop memory/latency. |
| Embedding model | [multilingual-e5-small](https://huggingface.co/intfloat/multilingual-e5-small) (candidate; 384 dimensions, 100 languages, 512-token input). | MIT; upstream model card; local CPU inference candidate. | Do not download. M4/M5 must test all six locales, chunking, index footprint, retrieval quality, and update/reindex path. |

## Declared-Package Manifest

`pyproject.toml` is the owner of BPM's Python minimum-version declarations; PyPI distribution
metadata is the provenance source and the project requires Python `>=3.14` on every supported
platform. None of these requirements is hash-pinned: the deliberate reproducibility boundary is
the approved virtual-environment build, rather than a hidden lockfile. The checked installed
versions and license expressions were taken from the installed distribution metadata; a missing
expression below is resolved from that distribution's published license notice.

| Group | Declared minimums (checked installed version) | License | Advisory and update decision |
| --- | --- | --- | --- |
| Web and application | FastAPI `>=0.139.0` (`0.139.0`); Uvicorn `>=0.50.0` (`0.50.0`); Jinja2 `>=3.1.6` (`3.1.6`); python-multipart `>=0.0.32` (`0.0.32`) | MIT; BSD-3-Clause; BSD-3-Clause; Apache-2.0 | No advisory returned for the declared set. FastAPI and Uvicorn updates deferred; otherwise keep. |
| Configuration and validation | Pydantic `>=2.13.4` (`2.13.4`); Pydantic Settings `>=2.14.2` (`2.14.2`); jsonschema `>=4.26.0` (`4.26.0`); FastJSONSchema `>=2.21.2` (`2.21.2`) | MIT; MIT; MIT; BSD-3-Clause | No advisory returned. FastJSONSchema update deferred; otherwise keep. |
| Database and utility | SQLAlchemy `>=2.0.51` (`2.0.51`); Alembic `>=1.18.5` (`1.18.5`); aiosqlite `>=0.22.1` (`0.22.1`); PyYAML `>=6.0.3` (`6.0.3`); HTTPX `>=0.28.1` (`0.28.1`); Requests `>=2.34.2` (`2.34.2`) | MIT; MIT; MIT; MIT; BSD-3-Clause; Apache-2.0 | No advisory returned; keep. |
| Tests and browser | pytest `>=9.1.1` (`9.1.1`); pytest-cov `>=7.1.0` (`7.1.0`); pytest-asyncio `>=1.4.0` (`1.4.0`); pytest-xdist `>=3.8.0` (`3.8.0`); AnyIO `>=4.14.1` (`4.14.1`); Beautiful Soup `>=4.15.0` (`4.15.0`); Selenium `>=4.45.0` (`4.45.0`) | MIT; MIT; Apache-2.0; MIT; MIT; MIT; Apache-2.0 | No advisory returned. AnyIO and Selenium updates deferred; otherwise keep. |
| Lint, type, and local development | Ruff `>=0.15.20` (`0.15.20`); Black `>=26.5.1` (`26.5.1`); isort `>=8.0.1` (`8.0.1`); Mypy `>=2.1.0` (`2.1.0`); types-PyYAML `>=6.0.12.20260518` (`6.0.12.20260518`); types-requests `>=2.33.0.20260518` (`2.33.0.20260518`); IPython `>=9.15.0` (`9.15.0`) | MIT; MIT; MIT; MIT; Apache-2.0; Apache-2.0; BSD-3-Clause | No advisory returned. Available Ruff, Mypy, and stub updates deferred; otherwise keep. |
| Optional PostgreSQL | asyncpg `>=0.31.0` (`0.31.0`); psycopg with binary extra `>=3.3.4` (`3.3.4`) | Apache-2.0; LGPL-3.0-only | No advisory returned; keep. |

The frontend owner is `package.json` plus `package-lock.json`; the latter records immutable npm
tarball URLs and Subresource Integrity values. It declares js-yaml `5.2.2` (MIT; patched integrity
recorded above), Monaco Editor `0.53.0` (MIT), and esbuild `0.28.1` (MIT). The self-hosted asset
owner is `app/static/vendor/vendor-lock.json`, which records SHA-256 and byte size for every
checked-in asset. `npm audit --omit=dev` is clean after the js-yaml update; Monaco remains deferred.

The documentation-test owner is `documentation/config/requirements.lock`: attrs `26.1.0`
(MIT), iniconfig `2.3.0` (MIT), jsonschema `4.26.0` (MIT), jsonschema-specifications `2025.9.1`
(MIT), packaging `26.2` (Apache-2.0 OR BSD-2-Clause), pluggy `1.6.0` (MIT), Pygments `2.20.0`
(BSD-2-Clause), pytest `9.1.1` (MIT), PyYAML `6.0.3` (MIT), referencing `0.37.0` (MIT), and
rpds-py `2026.6.3` (MIT).
This exact-name/version file intentionally has no artifact hashes; the documentation-toolchain
owner must add hashes before a future lock refresh, rather than silently loosening it here.

No prospective Pagefind, Meilisearch, llama.cpp, chat-model, embedding-model, or index artifact has
been downloaded, so none has a product checksum yet. The relevant owners are respectively M3
(search selection), M4 (retrieval corpus/index), M5 (model safety and quality), and M6 (local
runtime); each must record the selected immutable source, checksum, license, supported platform,
and update/revocation decision before introducing an artifact.

## Environment Boundary

`pip check` reports missing transitive dependencies for `minisbd`, `argostranslate`, `stanza`,
`sacremoses`, and `ctranslate2`. They are not declared by BPM and have no repository references;
they are incomplete, unrelated packages in the shared local virtual environment. This task neither
adopts nor repairs them. BPM's own declared direct dependency set remains installed.

The future model entries are evaluation candidates, not product commitments. Every downloaded
binary, model, or index must have an owner, immutable source URL or release identifier, license,
checksum, supported platform record, and update/revocation procedure before it can enter a BPM
release artifact.

## Follow-Up Gates

- Python, test, or browser-stack updates require focused tests plus lint, type, and full-suite
  evidence; browser changes also require the exact browser/driver record and browser smoke.
- A frontend update requires package-lock review, vendor rebuild, license review, asset contracts,
  and affected browser smoke.
- A documentation-toolchain update requires lock/checksum and third-party-notice review,
  reproducible build evidence, DITA validation, and documentation browser smoke.
- Search and RAG work must not introduce a floating package/model update. M3--M6 own the six-locale
  benchmark, offline and resource budgets, artifact provenance, retrieval quality, safety boundary,
  and reindex/update validation.

## Result

`BPM093-M1-03` updates only `js-yaml` to the patched `5.2.2` release and regenerates the verified
self-hosted vendor artifacts. All other package updates and all search/RAG candidates are recorded
with their provenance, license, platform, owner boundary, and explicit deferred decision.
