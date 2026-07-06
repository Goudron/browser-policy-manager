# BPM 0.9.0 Product Documentation Ownership Boundary

Date: 2026-06-21

Status: **Accepted for BPM 0.9.0**

Backlog item: `BPM090-M2-05`

## Decision

BPM product documentation will be implemented as an isolated top-level `documentation/` subsystem.
It owns DITA source, localized content, screenshots, build tools, generated documentation metadata,
search indexes, fixtures, focused tests, and debug guidance.

The existing top-level `docs/` directory remains maintainer-facing project documentation: backlogs,
architecture decisions, inventories, audits, and runbooks. End-user guide topics must not be added
to `docs/`, and maintainer notes must not be published into the product portal by default.

The BPM application will not parse DITA or import documentation build tooling at runtime. A small
future `app/documentation/` bridge will validate and serve a versioned, prebuilt artifact containing
static pages, assets, a documentation manifest, and deterministic per-locale search indexes. Product
documentation will be reachable under `/help/`; FastAPI `/docs`, `/redoc`, and `/openapi.json` remain
the API discovery surfaces.

This decision defines ownership and dependency direction only. It does not scaffold the subsystem,
select the DITA implementation, decide whether generated output is committed, or add runtime routes.
Those changes remain separately approved backlog tasks.

## Target Directory Boundary

The planned logical tree is:

```text
documentation/
├── AGENTS.md
├── README.md
├── config/
├── src/
│   ├── dita/
│   │   ├── en/
│   │   ├── ru/
│   │   ├── de/
│   │   ├── zh-CN/
│   │   ├── fr/
│   │   └── es-ES/
│   ├── generated/
│   └── shared/
├── assets/
│   └── screenshots/{locale}/
├── fixtures/
├── tools/
├── tests/
│   ├── unit/
│   ├── contract/
│   └── browser/
├── build/
├── reports/
└── .cache/
```

Directory meaning:

- `src/dita/{locale}/` contains reviewed DITA maps, task topics, concepts, references, and
  troubleshooting topics for one locale. Each locale contains User, Firefox Policy, CIS Settings,
  and API Integration guide maps.
- `src/generated/` contains reproducible DITA fragments or topic skeletons generated from approved
  product inventories. Files declare their generator and must never be hand-edited.
- `src/shared/` contains DITA keys, subject schemes, DITAVAL conditions, and language-neutral
  reusable resources. It must not become a hidden English fallback for localized prose.
- `assets/screenshots/{locale}/` contains reviewed, publishable source screenshots. Screenshots are
  source assets, not transient browser-test output.
- `fixtures/` contains compact versioned inputs for build, search, localization, and screenshot
  tests. It must not contain production databases, full external corpora, or licensed source PDFs.
- `tools/` contains documentation-only build/index/validation/capture adapters.
- `tests/` is the documentation subsystem test root. Its unit, contract, and browser groups run
  independently of the general `tests/` tree during focused work.
- `build/`, `reports/`, and `.cache/` are reproducible local/CI artifacts and must be ignored. They
  are never hand-edited or listed in `docs/docs-index.md`.

The exact generated-source commit policy and release staging path remain the decision of
`BPM090-M3-07`. The ownership boundary above is unchanged regardless of that later choice.

## Artifact Boundary

The documentation publisher produces one versioned artifact root with this logical contract:

```text
artifact-root/
├── manifest.json
├── en/
├── ru/
├── de/
├── zh-CN/
├── fr/
├── es-ES/
├── search/
├── assets/
└── licenses/
```

The artifact is immutable for one BPM build. `manifest.json` identifies the manifest schema, BPM
version, documentation build version, six locales, five guide families, topic/anchor mappings,
policy/CIS/API targets, search indexes, asset paths, and content fingerprints.

Only this artifact crosses into runtime ownership. DITA source, DITA-OT, Java, build caches,
translation work files, browser capture tooling, test fixtures, and source inventories do not become
runtime dependencies. Release packaging must fail on a missing, stale, incompatible, or partially
built artifact; local development may expose a clear unavailable state without breaking core profile
workflows.

## Allowed Dependency Flow

```text
BPM contract sources ──build time──> documentation/tools
                                         │
reviewed DITA + locale assets ───────────┤
                                         ▼
                              versioned static artifact
                                         │
                                         ▼
                              app/documentation bridge
                                         │
                                         ▼
                       /help/ + Library/contextual links
```

The arrows are one-way and enforce these rules:

1. `app/` runtime code must not import from `documentation/`, DITA libraries, Java wrappers, search
   builders, screenshot tooling, or documentation tests.
2. Documentation build adapters may read approved stable inputs: `pyproject.toml`, OpenAPI,
   `app/core/schema_channels.py`, bundled policy schemas, CIS registries/mappings/generated layers,
   active locale terminology contracts, and maintained machine-readable documentation inventories.
3. Documentation tools must not read BPM databases, mutate profiles, or depend on unrelated service
   internals merely to publish content. Browser screenshot fixtures may use public UI/API behavior in
   an isolated test database.
4. The future `app/documentation/` bridge reads only the artifact manifest and files. It never reads
   DITA source or invokes the publisher.
5. BPM templates and frontend code use stable manifest topic/target IDs. They must not hard-code
   translated filenames, generated directory layouts, topic prose, or search-index internals.
6. Generated pages and browser search make no runtime database/API calls. Search is deterministic,
   static, local, and offline-capable.
7. Changes to product behavior flow into documentation through versioned inventories and contract
   tests rather than unrestricted imports across the entire repository.

## Ownership Matrix

| Area | Path or artifact | Accountable owner | Mutation rule | Primary verification |
| --- | --- | --- | --- | --- |
| Maintainer architecture and runbooks | `docs/` | Project maintainer — repository documentation | Hand-edited and indexed by `docs/docs-index.md`. | Existing `docs_contract` tests. |
| English product content | `documentation/src/dita/en/` | Project maintainer — source documentation | Hand-edited DITA; English is source locale. | Planned `make test-docs-contract`. |
| Localized product content | Five non-English `documentation/src/dita/{locale}/` trees | Project maintainer — localization | Human-reviewed DITA; no silent generated prose fallback. | Planned `make test-docs-contract`. |
| Generated DITA facts/skeletons | `documentation/src/generated/` | Project maintainer — documentation platform | Generator-owned; never hand-edited. | Planned clean generation and `make test-docs-contract`. |
| Shared DITA metadata | `documentation/src/shared/`, `documentation/config/` | Project maintainer — information architecture | Hand-edited schemas/keys/conditions with compatibility tests. | Planned `make docs-build`. |
| Localized screenshots | `documentation/assets/screenshots/{locale}/` | Project maintainer — localized visual content | Capture-tool output promoted only after review. | Planned `make docs-screenshots-check`. |
| Build and search tooling | `documentation/tools/` | Project maintainer — documentation platform/search | Hand-edited executable source; no runtime import. | Planned `make test-docs`. |
| Documentation fixtures | `documentation/fixtures/` | Project maintainer — documentation test platform | Small deterministic maintained data only. | Planned `make test-docs`. |
| Focused documentation tests | `documentation/tests/` | Project maintainer — documentation test platform | Unit/contract/browser ownership stays local. | Planned `make test-docs`, `make test-docs-contract`, `make test-docs-ui`. |
| Local build/debug output | `documentation/build/`, `reports/`, `.cache/` | Build process | Generated and ignored; never hand-edited. | Clean rebuild and artifact drift checks. |
| Release documentation artifact | Versioned `artifact-root/` | Project maintainer — release engineering | Produced atomically; immutable after build. | Planned `make docs-build` and `make test-release`. |
| Runtime manifest/router | Future `app/documentation/` | Project maintainer — BPM integration | Small typed adapter over artifact only. | Focused app contract tests and planned `make test-docs-ui`. |
| BPM entry/deep links | Library template/static code and six UI locale catalogs | Project maintainer — BPM integration/localization | Only labels, stable target IDs, and navigation behavior live in BPM. | Locale/UI contracts and planned docs browser smoke. |

There is one project maintainer today. Functional ownership labels prevent a content edit, build
change, runtime change, or release mutation from being reviewed as though it belonged to the same
failure domain.

## Minimal BPM Runtime Bridge

Only the following BPM areas may be touched for normal portal integration:

- `app/core/config.py`: configured artifact root and supported manifest version;
- future `app/documentation/`: manifest validation, locale/topic resolution, safe static responses,
  and `/help/` router ownership;
- `app/main.py`: include the dedicated documentation router;
- `app/middleware/security.py`: route-aware CSP only if the strict default cannot serve the
  generated self-hosted artifact;
- Profile Library/shared help templates and their focused frontend module: visible Documentation
  button and stable contextual targets;
- `app/i18n_src/` and generated runtime locale catalogs: portal/navigation/error labels only;
- packaging configuration: include exactly the validated release artifact and licenses;
- focused app contract/browser tests for serving and navigation.

Normal documentation implementation must not modify profile persistence, Alembic migrations,
Firefox import/export semantics, schema validation, CIS merge behavior, profile service logic,
Guided/All Settings editing semantics, or general frontend runtime architecture. A real product
contract change requires its own approved task and then updates documentation inventories.

The route is `/help/`, not `/docs`, because `/docs` is already FastAPI's OpenAPI UI. The bridge must
reject path traversal, validate manifest compatibility before exposing links, return correct content
types and security headers, and fail safely when local development artifacts are absent.

## Focused Test And Debug Contexts

| Work type | Default context to read | Context excluded unless a failing contract points to it |
| --- | --- | --- |
| Edit one topic | Local `documentation/AGENTS.md`, one DITA topic/map, matching locale peers, direct assets, focused contract test | `app/`, general `tests/`, databases, schemas, CIS implementation, unrelated guides, built site |
| Fix DITA build | Failing source/map, `documentation/config/`, one build adapter, focused fixture/test, tool log | BPM routes/services, all product tests, screenshots, unrelated locale trees |
| Fix localization parity | English topic, one target-locale topic, shared keys/glossary, locale parity test | Other locales, app runtime catalogs unless a shared UI term changed, general UI tests |
| Fix deterministic search | Search builder, compact corpus/query fixtures, manifest sample, focused unit/contract test | Full built site, BPM backend, Selenium, unrelated DITA maps |
| Fix screenshot capture | Screenshot matrix row, one locale/topic, capture fixture/harness, directly rendered BPM route | Entire guide corpus, unrelated routes, general browser suite |
| Fix `/help/` serving | Future `app/documentation/`, manifest fixture, security/config bridge, focused app contract | DITA authoring tools, translation files, profile services/database logic |
| Fix Library/help navigation | One template/frontend module, relevant six locale labels, manifest target fixture, focused UI contract | Documentation publisher internals, unrelated editor behavior |
| Final release validation | Full documentation gates followed by BPM release gates | Nothing required by the release contract is excluded. |

Documentation-only work starts with planned `make test-docs`, then
`make test-docs-contract`. Browser/screenshot work uses `make test-docs-ui` with immediate sandbox
escalation. The general `pytest -q`, `make coverage`, `make test-ui`, and `make test-release` remain
final release gates, not the default first debugging loop.

`documentation/AGENTS.md` will make these context rules executable for future sessions. It must
point to a compact subsystem snapshot and prohibit recursive reads of generated pages, indexes,
screenshots, dependencies, caches, external corpora, secrets, and unrelated BPM modules.

## Localization And Content Ownership

- Published locales are exactly `en`, `ru`, `de`, `zh-CN`, `fr`, and `es-ES`.
- English is authored first; each other locale is a first-class reviewed release deliverable.
- Locale-independent identifiers, JSON, API paths, Firefox policy IDs, preference names, CIS IDs,
  code, and product IDs are reused through DITA keys rather than translated.
- Product guide prose, navigation, keywords, captions, and alt text may not silently fall back to
  English in a localized artifact.
- Visible UI screenshots are locale-specific source assets. Cross-locale reuse is allowed only when
  the image contains no localized UI text and the screenshot matrix explicitly approves it.
- Application locale catalogs own only BPM shell/link/error labels. They do not become storage for
  product guide paragraphs.

## Security, Provenance, And Offline Constraints

- Generated content and search snippets are escaped/sanitized at build time and rendered without
  inline executable content where practical.
- The default self-hosted CSP is the target. Any exception must be narrow, route-specific,
  documented, and tested; remote script/font/search dependencies are not allowed.
- Search indexes contain published documentation only, not profile/database content or external
  source corpora, and send no telemetry by default.
- Mozilla/CIS provenance and license metadata travel with the release artifact. Licensed source PDFs
  and unapproved copied prose never enter fixtures, generated pages, search indexes, or packages.
- The artifact works without internet access and does not require a backend search service.
- No LLM, embedding model, vector database, RAG, generative answer, AI translation, or AI-generated
  alt text belongs inside this boundary for 0.9.0.

## Extraction Readiness

Keeping the subsystem top-level is intentional: a future repository split can move
`documentation/` and its artifact protocol without moving BPM profile code. Extraction readiness
requires:

- a versioned manifest/artifact schema rather than Python object sharing;
- stable input inventories/OpenAPI rather than imports of private app services;
- configurable base paths and no repository-absolute URLs in published output;
- documentation tests and fixtures that run without the full BPM test tree;
- BPM runtime integration limited to the small artifact consumer and stable target IDs.

Extraction is not part of 0.9.0 and must not weaken current offline/self-hosted integration.

## Alternatives Rejected For 0.9.0

- Put product topics under `docs/`: rejected because maintainer planning and publishable localized
  content have different ownership, dependencies, indexes, and debug contexts.
- Hard-code guide prose in Jinja, JavaScript, or UI locale catalogs: rejected because it bypasses
  DITA reuse, structured localization, independent builds, and extraction readiness.
- Parse DITA or build search indexes at application startup: rejected because authoring dependencies
  and failures would enter the BPM runtime path.
- Create a separate documentation repository immediately: rejected because build/manifest/runtime
  contracts are not stable yet.
- Add a backend or hosted search service: rejected because the portal must remain deterministic,
  private, self-hosted, and offline-capable.
- Keep documentation tests in the undifferentiated general test tree: rejected because focused
  authoring/debug work needs bounded fixtures, commands, context, and artifacts.

## Consequences And Follow-Up

- `BPM090-M3-01` scaffolds the accepted tree; this decision alone creates no `documentation/`
  directory.
- `BPM090-M3-02` adds the local context guide.
- `BPM090-M2-06` selects the DITA toolchain within this boundary.
- `BPM090-M2-08` defines the versioned manifest and UI-target schemas consumed by the bridge.
- `BPM090-M3-07` decides generated-output commit and package staging policy.
- `BPM090-M9-*` implements `/help/`, Library/context links, and runtime failure states.
- `BPM090-M11-*` implements focused tests, fixtures, coverage, diagnostics, and release integration.

Any implementation that makes BPM runtime import the documentation authoring toolchain, publishes
hand-edited output outside DITA, mixes generated output with source, silently omits a locale, or
requires broad application context for ordinary documentation debugging violates this decision.
