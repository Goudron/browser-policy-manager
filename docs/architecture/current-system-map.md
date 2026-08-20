# Browser Policy Manager Current System Map

Date: 2026-08-20

This is the first orientation point for BPM 0.9.5.1 work. Read this map before
opening a subsystem. It names owned entrypoints and narrow verification routes;
it is not an inventory of dependencies, generated files, caches, secrets, or
the implementation of every feature. Import direction rules are executable in
`docs/architecture/python-architecture-boundaries-0.9.5.md`.

## Release Application

`app/main.py:create_app` is the ASGI factory and release assembly. Each app owns
an injectable `app/db.py:DatabaseRuntime` with a native async engine and session
factory. Its lifespan initializes that runtime, verifies the exact Alembic head
without writing, and disposes the database and documentation-assistant runtimes.
Alembic, not application startup or a request path, owns every retained schema
and stored-channel upgrade.

| Concern | Owner and minimum reading route | Focused verification |
| --- | --- | --- |
| Configuration and HTTP shell | `app/core/config.py`, `app/main.py`, `app/middleware/security.py` | `tests/unit/app/test_bootstrap_config.py`, `tests/integration/app/test_current_version_surfaces.py` |
| Database lifecycle | `app/db.py`, `app/models/profile.py`, `alembic/env.py`, `alembic/versions/` | `tests/unit/db/test_db_helpers.py`, `tests/integration/db/test_migrations.py`, `tests/integration/db/test_database_integration.py`, `tests/integration/db/test_database_recovery.py` |
| Profile data/API lifecycle | `app/api/profiles.py` -> `app/services/profile_service.py` -> `app/schemas/profile.py`/`app/models/profile.py`; M4-03 preview is read-only, while M4-04 apply rederives a digest-bound preview in one API-owned transaction and conditionally writes the target-valid channel, flags, compliance disposition, revision, and DB-managed timestamp | `tests/integration/api/test_profiles_api.py`, `tests/integration/api/test_profile_conversion_preview_api.py`, `tests/integration/api/test_profile_conversion_apply_api.py`, `tests/integration/db/test_profile_conversion_apply_integration.py`, `tests/unit/profiles/test_profiles_core_unit.py`, `tests/integration/profiles/test_profiles_update_and_pagination.py` |
| Firefox boundary | `app/services/firefox_policy_import.py`, `app/services/firefox_policy_export.py`, `app/api/export.py`, `app/api/validation.py` | `tests/integration/api/test_firefox_policies_import_api.py`, `tests/integration/api/test_openapi_surface.py` |
| Schema-conversion planner | `app/core/profile_conversion_planner.py` plus `app/core/profile_conversion_recipes.py` are the pure M4-01/M4-02 plan/candidate and bounded registry boundary; `app/core/policy_validation.py` reuses immutable normalized validators; M4-03 preview is read-only and M4-04 apply is the API-owned transaction adapter that rederives rather than trusts a preview candidate | `tests/unit/schema/general/test_profile_conversion_planner.py`, `tests/integration/api/test_profile_conversion_preview_api.py`, `tests/integration/api/test_profile_conversion_apply_api.py`, `tests/integration/db/test_profile_conversion_apply_integration.py`, `tests/contract/docs/schema/test_firefox_pairwise_profile_conversion_contract.py` |
| Directed conversion matrix | `tools/verify_firefox_conversion_matrix.py` owns the offline M4-06 12-pair planner/API proof and deterministic value-free report. It uses one disposable in-memory API fixture, records zero production transformations, and proves a separate synthetic registry mechanism only. | `tests/unit/tooling/test_verify_firefox_conversion_matrix.py`, `make verify-firefox-conversion-matrix` |
| Schema-conversion UI | `app/static/profiles_modules/conversion_recommendation.mjs` owns the Library entry recommendation; `app/static/profiles_modules/conversion_review.mjs` owns the route-local preview/apply state machine. Both consume catalog-derived artifact identities and never render policy values, plan digests, or a retirement action. | `tests/javascript/integration/profiles/profile_conversion_review.test.js`, `tests/browser/profiles/test_schema_conversion_ux.py` |
| Lifecycle-transition planning | `app/core/lifecycle_transition_plan.py` performs M6-01's pure, value-free previous/candidate catalog validation and diff. It binds only reviewed catalog snapshots and exact bundle availability; it cannot read or write profiles, execute conversion, or alter runtime channel resolution. | `tests/unit/schema/contracts/test_lifecycle_transition_plan.py`, `tests/contract/docs/schema/test_firefox_schema_lifecycle_catalog_contract.py`, `tests/contract/docs/schema/test_firefox_retired_esr_migration_safety_contract.py` |
| Schema-lifecycle dry run | `tools/schema_lifecycle_dry_run.py` is the M7-02 review command. It requires explicit previous/candidate catalog snapshots, emits flushed deterministic value-free planning evidence, rechecks exact retirement proof/materializer readiness, and opens no database by default. Optional aggregate counts require an explicit disposable or verified-backup read-only target and never write profiles or Alembic state. | `tests/unit/tooling/test_schema_lifecycle_dry_run.py`, `make schema-lifecycle-dry-run` |
| Retirement total-convertibility gate | `app/core/retirement_convertibility_preflight.py` consumes only a valid M6-01 retirement mapping, explicit exact source/target bundle bindings, reviewed schema-containment evidence, and M4's immutable recipe registry. It produces a deterministic, value-free static result before any Alembic or database preflight. The exact ESR 140.13 to ESR 153.0 proof is complete and digest-bound; it does not retire the still-supported runtime catalog row. | `tests/unit/schema/contracts/test_retirement_convertibility_preflight.py`, `tests/unit/schema/contracts/test_lifecycle_transition_plan.py` |
| Retired-ESR migration owner | `migration_support/retirement_owner_v1.py` owns the offline preflight/locked Alembic transaction. `migration_support/retirement_revision_materializer_v1.py` is the exact ESR 140.13 candidate-only materializer: it rejects the current supported catalog and renders an inert Alembic-compatible artifact only from a reviewed retired candidate. Nothing is installed in `alembic/versions`, so the released head remains unchanged. | `tests/integration/db/test_retirement_owner_v1.py`, `tests/integration/db/test_retirement_revision_materializer_v1.py` |
| Rendered profile routes | `app/web/profiles.py`, `app/web/profiles_context.py`, `app/web/profile_navigation.py`, `app/templates/profiles/` | `tests/contract/ui/profiles/`, `tests/contract/ui/localization/test_web_profiles_page.py` |

The public policy exchange format is a complete Firefox `policies.json` object;
database storage is normalized around `Profile.flags`. Schema channels start at
`app/core/schema_channels.py`, whose lifecycle catalog derives public order,
latest/default roles, filenames, and validation views; `app/core/schemas_loader.py`
reads the four pinned bundled policy schemas. CIS YAML source and generated compliance
layers are owned by `app/compliance/firefox/cis/`, with tests in
`tests/contract/compliance/`.

`app/core/profile_conversion_planner.py` and its bounded immutable
`app/core/profile_conversion_recipes.py` registry consume the exact catalog and
normalized validators to make a read-only, deterministic conversion plan. The
production registry is explicitly empty after the four-channel diff audit;
unreviewed transformations remain blocked. The M4-03 profile API adapter binds
the current stored row to that pure planner and exposes a value-free preview;
neither domain module writes profiles. M4-04's profile service adapter reads a
locked current row, rederives that pure plan, and conditionally persists only
the approved target candidate inside the API-owned transaction.

`app/core/lifecycle_transition_plan.py` is separate from that manual conversion
path. It validates explicit previous/candidate lifecycle snapshots and emits a
deterministic, value-free classification of added, retained, refreshed, and
retired stable lines, exact same-line refresh mappings, and exact retirement
successor mappings. It has no database, API, service, or runtime-normalization
dependency. `app/core/retirement_convertibility_preflight.py` consumes that
already-valid plan for a schema-wide proof. It binds raw bundle and normalized
validator identities exactly, accepts only reviewed structural containment or
an exhaustive finite-domain reversible M4 recipe partition, and reports every
uncovered RFC 6901 schema/atom location. It neither scans profiles nor treats
one manual preview or sample as proof. A later immutable Alembic revision
remains the only retirement writer.

M4-06 is owned by `tools/verify_firefox_conversion_matrix.py`. Its catalog
order is the only pair order; it checks all 12 non-self directions without
network access, sends output as `phase=... pair=source->target [n/12]`, and
leaves no profile database behind. The retained report is deterministic and
value-free: pairs, counts, codes, and digests only. Run
`make verify-firefox-conversion-matrix` after planner, recipe, preview, apply,
or schema-channel changes.

## Browser Runtime And Generated Boundaries

The browser application is Jinja-rendered and self-hosted. The wrapper
`app/templates/profiles/_page_document.html` selects the five profile surfaces:
library, comparison, guided editor, all settings, and JSON editor.
`app/templates/profiles/_page_route_assets.html` reads the generated manifest
and loads each route-specific native ESM entry. Route source uses direct imports;
there is no profile-global compatibility bridge or load-order contract.

- CSS source is `app/static/profiles_css/`; rebuild its checked-in output
  `app/static/profiles.css` with `make build-profiles-css`.
- `tools/frontend_profile_graph_0_9_5.json` freezes the owned profile
  frontend: direct-import module sources, route entries, vendor boundary,
  public DOM test owner, and conversion stage. Run
  `make frontend-profile-graph` before moving an owned profile asset.
- `app/static/profiles_modules/` contains side-effect-free ES-module sources.
  Use `make test-profile-pure-modules` for native Node import/parity contracts.
- `app/static/profiles_bundles/` is generated M6-04 output: five route entries,
  shared chunks, external source maps, a canonical metafile, and a checksum
  manifest. Rebuild only with `make build-profile-frontend-bundles`; run
  `make check-profile-frontend-bundles` before review. The template reads that
  manifest, while Monaco remains the separately verified JSON-only vendor
  boundary. The manifest holds generated/JavaScript/per-route byte ceilings,
  so generated output is sized even before it enters Git. Do not hand-edit
  bundle output or use it as general source context.
- Monaco source input is `app/static_src/profiles_monaco_entry.js`; rebuild
  vendor output with `tools/build_monaco_bundle.sh` or
  `make rebuild-frontend-vendor`.
- `app/static/vendor/`, `app/static/profiles.css`,
  `app/compliance/firefox/cis/generated/`, runtime locale catalogs in
  `app/i18n/`, and bundled schemas in `app/schemas/policies/` are generated or
  vendored boundaries. Do not use them for broad context; change their owned
  source and run the relevant rebuild/check command instead.
- Locale ownership starts at `app/core/locales.py` and `app/i18n_src/`.
  Use `make check-locale-catalogs` and locale-contract tests after changes.

## Documentation And Optional AI Are Separate Contours

The installed documentation HTTP surface is assembled by `app/main.py` from
`app/documentation/router.py`. Its release-safe assistant transport is
`app/documentation/assistant_contracts.py` and
`app/documentation/assistant_service.py`; the visible default is a training
notice, not local model/RAG execution.

`app/ai/` and `app/documentation/local_assistant_runtime.py` are optional
incubation/development assembly. They are reached only through explicit
development commands (`make dev`, `make ai-*-dev`) or named offline tooling.
Install `[dev,ai]`, run `make ai-extra-check`, and use
`make test-ai-incubation` for this separate contour;
they must not become a transitive dependency of `app.main`. Documentation
build sources and tools live in `documentation/` and are likewise not release
runtime. Their maintained entrypoint is `documentation/tools/build_docs.py`;
its owned library responsibilities live in `documentation/buildlib/` (source
validation, portal/catalog generation, PDF, and publication). Use
`make docs-validate` or `make test-docs` rather than loading its corpus.

Native Linux packaging is a separate release-assembly contour. Its source of
truth is `distributions/native/targets.json`; `tools/native_distribution.py`
builds one frozen target userspace at a time, while
`distributions/native/build-target.sh` and `distributions/native/smoke-target.sh`
own the private Python payload and clean-install proof. It produces transient
`.deb`, `.rpm`, and `pkg.tar.zst` evidence only after verified documentation
packaging; it never imports application runtime modules or changes BPM
functionality. Start with `make native-package-validate`; the explicit release
gate is `make native-package-release-gate`, with focused contracts in
`tests/unit/tooling/test_native_distribution.py`.

Native Windows packaging is a separate direct-host MSI contour, never a WSL
adapter. `distributions/windows/targets.json` freezes the Windows 10/11 x64
payload inputs; `tools/windows_distribution.py` assembles and smoke-tests the
MSI only on a native Windows x64 host. It retains explicit migration, a manual
least-privilege service, and Authenticode-required release staging. Start with
`make windows-package-validate`; the native-host release gate is
`make windows-package-release-gate`, with focused contracts in
`tests/unit/tooling/test_windows_distribution.py`.

Native macOS packaging is a separate native-DMG distribution contour. Its two frozen
targets are defined by `distributions/macos/targets.json`; the macOS-only
builder, mounted-DMG smoke proof, and explicit migration launcher live beneath
`distributions/macos/`, orchestrated by `tools/macos_distribution.py`. The
manual CI workflow builds Intel and Apple Silicon artifacts separately; release
publication uses the Developer ID signature and Apple notarization boundary.
Start with `make macos-package-validate`; use
`make macos-package-release-gate` only on matching native macOS architectures.
Focused contracts are in `tests/unit/tooling/test_macos_distribution.py`.
For an on-demand future-version run across all native contours, start with
`distributions/NATIVE_DISTRIBUTION_PLAYBOOK.md`; it requires a reviewed,
version-scoped manual workflow rather than adding native packaging to normal CI.

## Test Contours And Fast Commands

| Change area | Start here | Escalate when needed |
| --- | --- | --- |
| Python ownership/imports | `make architecture` | `tests/integration/app/test_python_architecture_contracts.py` |
| Optional AI incubation | `make ai-extra-check` | `make test-ai-incubation` |
| Product unit/API/route contracts | `make test-unit`, `make test-integration`, or a named test file | `make test-contract`, `make test-browser` |
| Firefox schema bundles | `make test-firefox-schema-workflow` | `make test-firefox-schema-contract` |
| Directed Firefox conversion | `make verify-firefox-conversion-matrix` | `tests/unit/tooling/test_verify_firefox_conversion_matrix.py` |
| Firefox policy behavior | `make setup-firefox-live-browsers FIREFOX_CHANNEL=<release|esr153|esr140|esr115>` | `make firefox-live-four-channel-workflow` |
| Documentation tooling/portal | `make test-docs` | `make docs-validate` |
| Native Linux distributions | `make native-package-validate` | `make native-package-release-gate` |
| Native Windows MSI | `make windows-package-validate` | `make windows-package-release-gate` |
| Native macOS DMG distribution | `make macos-package-validate` | `make macos-package-release-gate` |
| Performance/repository health | `make profile-performance-gate` | `make repo-health` |
| Profile frontend graph | `make frontend-profile-graph` | named DOM/browser contracts in `tests/contract/ui/profiles/` |
| Profile route bundles | `make check-profile-frontend-bundles` | `tests/unit/profiles/test_profile_frontend_bundles.py`, route/browser asset contracts |

`browser_ui`, `firefox_live`, and `firefox_live_amo` are deliberately outside
the default pytest selection. Generated artifacts, dependency trees, local
artifacts, and credentials are excluded from this map and from routine context
loading.

## Machine-Checked Drift Contract

The following bounded manifest is verified by
`tests/contract/docs/general/test_current_system_map.py`. When moving an owner, entrypoint, test
contour, or command listed here, update the map in the same change. It only
checks named paths and commands; it does not recursively scan the repository.

```json system-map-contract
{
  "version": "0.9.5.1",
  "paths": [
    "app/main.py",
    "app/core/config.py",
    "app/db.py",
    "app/models/profile.py",
    "app/schemas/profile.py",
    "app/api/profiles.py",
    "app/api/export.py",
    "app/api/validation.py",
    "app/services/profile_service.py",
    "app/services/firefox_policy_import.py",
    "app/services/firefox_policy_export.py",
    "app/web/profiles.py",
    "app/web/profiles_context.py",
    "app/templates/profiles/_page_document.html",
    "app/static_src/profiles_monaco_entry.js",
    "app/static/profiles_modules/",
    "app/static/profiles_bundles/",
    "app/core/schema_channels.py",
    "app/core/schemas_loader.py",
    "app/core/profile_conversion_planner.py",
    "app/core/profile_conversion_recipes.py",
    "app/static/profiles_modules/conversion_recommendation.mjs",
    "app/static/profiles_modules/conversion_review.mjs",
    "app/core/lifecycle_transition_plan.py",
    "app/core/retirement_convertibility_preflight.py",
    "migration_support/retirement_owner_v1.py",
    "migration_support/retirement_revision_materializer_v1.py",
    "app/core/policy_validation.py",
    "tools/verify_firefox_conversion_matrix.py",
    "tools/schema_lifecycle_dry_run.py",
    "app/documentation/router.py",
    "app/documentation/assistant_contracts.py",
    "app/documentation/assistant_service.py",
    "app/documentation/local_assistant_runtime.py",
    "app/ai/",
    "documentation/tools/build_docs.py",
    "documentation/buildlib/",
    "distributions/NATIVE_DISTRIBUTION_PLAYBOOK.md",
    "distributions/native/targets.json",
    "distributions/native/build-target.sh",
    "distributions/native/smoke-target.sh",
    "tools/native_distribution.py",
    "distributions/windows/targets.json",
    "distributions/windows/build-msi.ps1",
    "distributions/windows/smoke-msi.ps1",
    "tools/windows_distribution.py",
    "distributions/macos/targets.json",
    "distributions/macos/build-dmg.sh",
    "distributions/macos/smoke-dmg.sh",
    "distributions/macos/launcher.py",
    "tools/macos_distribution.py",
    "tests/contract/ui/profiles/",
    "tests/live/firefox/",
    "tests/contract/compliance/",
    "tests/unit/tooling/test_verify_firefox_conversion_matrix.py",
    "tests/unit/tooling/test_schema_lifecycle_dry_run.py",
    "tests/javascript/integration/profiles/profile_conversion_review.test.js",
    "tests/browser/profiles/test_schema_conversion_ux.py",
    "tests/unit/schema/contracts/test_lifecycle_transition_plan.py",
    "tests/unit/schema/contracts/test_retirement_convertibility_preflight.py",
    "tests/integration/db/test_retirement_owner_v1.py",
    "tests/integration/db/test_retirement_revision_materializer_v1.py",
    "tests/unit/tooling/test_native_distribution.py",
    "tests/unit/tooling/test_windows_distribution.py",
    "tests/unit/tooling/test_macos_distribution.py"
  ],
  "commands": [
    "make architecture",
    "make ai-extra-check",
    "make test-ai-incubation",
    "make test-fast",
    "make test-unit",
    "make test-integration",
    "make test-contract",
    "make test-browser",
    "make test-firefox-schema-workflow",
    "make test-firefox-schema-contract",
    "make verify-firefox-conversion-matrix",
    "make schema-lifecycle-dry-run",
    "make test-live",
    "make test-docs",
    "make docs-validate",
    "make profile-performance-gate",
    "make repo-health",
    "make test-profile-pure-modules",
    "make check-profile-frontend-bundles",
    "make native-package-validate",
    "make native-package-release-gate",
    "make windows-package-validate",
    "make windows-package-release-gate",
    "make macos-package-validate",
    "make macos-package-release-gate"
  ],
  "excluded_boundaries": [
    "app/static/vendor/",
    "app/static/profiles.css",
    "app/compliance/firefox/cis/generated/",
    "app/i18n/",
    "app/schemas/policies/"
  ]
}
```
