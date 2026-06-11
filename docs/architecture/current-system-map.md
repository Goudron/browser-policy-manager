# Browser Policy Manager Current System Map

Date: 2026-06-01

This map is the first orientation point for BPM 0.8.7 work. It names the main runtime surfaces, ownership boundaries, generated/vendor zones, and test layers so future changes can start from a smaller shared context.

Refactoring acceptance rules live in `docs/architecture/refactoring-acceptance-rules.md`.

## Application Shell

- ASGI app factory: `app/main.py:create_app`.
- Settings: `app/core/config.py`, with app metadata loaded from `pyproject.toml`.
- Middleware: `app/middleware/security.py`, FastAPI CORS middleware.
- Static assets: mounted at `/static` from `app/static`.
- Runtime locale catalogs: served by `GET /i18n/{locale}.json`.
- Favicon: served by `GET /favicon.ico`.
- Root JSON endpoint: `GET /`.
- Startup side effect: database initialization plus legacy profile schema normalization currently runs in app lifespan.

## Web Routes

Web routes live in `app/web/profiles.py` and render Jinja templates from `app/templates`.
Shared `/profiles` locale, asset-version, footer, wizard catalog, schema shell, all-settings, and manual-control context assembly lives in `app/web/profiles_context.py`.

| Route | Template | Purpose |
|---|---|---|
| `GET /profiles` | `profiles_library.html` | Profile library and lifecycle workspace. |
| `GET /profiles/new` | `profiles_editor.html` | Guided editor for a new unsaved draft. |
| `GET /profiles/{profile_id}/edit` | `profiles_editor.html` | Guided editor for an existing profile. |
| `GET /profiles/{profile_id}/settings` | `profiles_settings.html` | All settings visual policy catalog. |
| `GET /profiles/{profile_id}/json` | `profiles_json.html` | Direct Firefox `policies.json` editor. |

The shared page wrapper is `app/templates/profiles/_page_document.html`. It selects route-specific shells through `profiles_template_kind` and includes the current static script chain.

## API Surface

API routers are included from `app/main.py`.

| Router | Prefix | Main endpoints |
|---|---|---|
| `app/api/health.py` | none | `GET /health`, `GET /health/ready`. |
| `app/api/profiles.py` | `/api/profiles` | List, stats, create, import, get, update, archive, restore, hard-delete, reset. |
| `app/api/export.py` | `/api/export` | `GET /api/export/profiles/{profile_id}/firefox/policies.json`. |
| `app/api/validation.py` | `/api/validate` | `POST /api/validate/{profile}`. |

The product import/export boundary is Firefox Enterprise `policies.json`; internal profile storage stays normalized around `Profile.flags`.

## Data And Services

- Database/session setup: `app/db.py`.
- ORM model: `app/models/profile.py`.
- Pydantic profile schema: `app/schemas/profile.py`.
- Profile CRUD and lifecycle logic: `app/services/profile_service.py`; `ProfileQuery` centralizes list/count filters before command methods mutate rows.
- Firefox `policies.json` import/export adapters: `app/services/firefox_policy_import.py`, `app/services/firefox_policy_export.py`.
- Policy schema service and validation: `app/services/policy_schema_service.py`, `app/core/policy_validation.py`.
- Legacy schema channel normalization: `app/services/profile_schema_normalization.py`; explicit backfill command: `make backfill-profile-schema-versions`.

## Firefox Schemas

Supported schema channels are centralized in `app/core/schema_channels.py`. Update the
single `SCHEMA_CHANNELS` inventory first; labels, filenames, raw schema directories,
Mozilla versions, defaults, and the UI catalog are derived from it.

| Channel | File |
|---|---|
| `esr-140.11` | `app/schemas/policies/firefox-esr-140.11.json` |
| `release-151` | `app/schemas/policies/firefox-release-151.json` |

Schema loading helpers live in `app/core/schemas_loader.py` and `app/schemas/schema_manager.py`. Schema updates are supported by `tools/update_schemas.py` and the Firefox schema update runbook.

## Frontend Runtime

The frontend is currently self-hosted, route-rendered Jinja plus static browser scripts.

| Area | Main files |
|---|---|
| Shared wrapper and route shells | `app/templates/profiles/_page_document.html`, `_library_shell.html`, `_guided_shell.html`, `_settings_shell.html`, `_json_shell.html`. |
| Server-side profile navigation | `app/web/profile_navigation.py` builds profile route URLs and resolves `return`, `focus`, and `include_deleted` semantics. |
| Bootstrap and shared helpers | `profiles_head_bootstrap.js`, `profiles_page_bootstrap.js`, `profiles_bootstrap*.js`, `profiles_shared.js`, `profiles_utils.js`, `profiles_platform.js`, `profiles_data.js`. |
| Profile library | `profiles_library_bootstrap.js`, `profiles_library.js`, `_page_library_workspace.html`. |
| Guided editor | `profiles_guided.js`, `profiles_wizard_flow.js`, `_page_wizard*.html`, `app/web/firefox_wizard_steps.py`. |
| All settings | `profiles_settings.js`, `profiles_schema_shell*.js`, `profiles_all_settings_*.js`, `profiles_settings_search.js`. |
| JSON editor | `profiles_json.js`, `profiles_runtime.js`, vendored Monaco assets. |
| Policy-specific controls | `profiles_preferences*.js`, `profiles_search_engines.js`, `profiles_network.js`, `profiles_extensions.js`, `profiles_review.js`, `profiles_workspace.js`. |
| Styling | Generated bundle `app/static/profiles.css`, source layers in `app/static/profiles_css/`, `app/static/vendor/profiles_tailwind.css`, `app/static/vendor/profiles_monaco.css`. |

Current refactoring risk: scripts are split across files, but most modules communicate through `window.BPMProfiles*` globals and depend on load order in `_page_document.html`.

The profile workspace has four product surfaces only: Library, Guided editor,
All settings, and JSON editor. There is no compatibility route for retired
editor modes.

## Vendor And Generated Assets

- Vendored frontend assets live under `app/static/vendor`.
- `/profiles` CSS source layers live under `app/static/profiles_css`; rebuild the checked-in bundle with `make build-profiles-css`.
- Monaco build input: `app/static_src/profiles_monaco_entry.js`.
- Monaco build script: `tools/build_monaco_bundle.sh`.
- Pinned frontend packages: `package.json`.
- Generated CIS layers live under `app/compliance/firefox/cis/generated`.
- Bundled Firefox policy schemas live under `app/schemas/policies`.

Treat vendor/generated outputs as reproducible artifacts: update them through scripts and verify license/checksum/size drift where possible.

## Localization

- Locale matrix and browser-language fallback rules: `app/core/locales.py`.
- Locale source segments: `app/i18n_src/{locale}/{common,library,wizard,settings,json}.json`.
- Generated locale segments: `app/i18n_src/generated/{locale}/policy-labels.json`, with overrides in `app/i18n_src/overrides/{locale}/policy-labels.json`.
- Runtime catalogs: generated `app/i18n/en.json`, `ru.json`, `de.json`, `zh-CN.json`, `fr.json`, `es-ES.json`.
- Source language: English.
- Catalog contract: all active catalogs keep key and placeholder parity with `en`.
- Locale inventory report: `make locale-inventory`.
- Runtime catalog rebuild: `make build-locale-catalogs`; drift check: `make check-locale-catalogs`.
- Current pressure point: every runtime catalog has 2,620 keys, so copy and generated policy labels are expensive to review as one file.

## CIS And Compliance

CIS Firefox hardening assets live under `app/compliance/firefox/cis`.

| File or module | Purpose |
|---|---|
| `schema.yaml` | Source-data shape contract. |
| `sources.yaml` | Source references. |
| `firefox_esr_gpo_1_0_0.yaml` | Curated benchmark input. |
| `mappings.yaml` | Recommendation-to-policy/preference mapping targets. |
| `merge_rules.yaml` | Layer merge behavior. |
| `validation.py` | Source validation. |
| `generation.py` | Generated layer creation. |
| `merge.py` | Compliance layer merge logic. |
| `generated/*.json` | Generated L1/L2 ESR/Release layers. |

Related tools live under `tools/cis_firefox`.

## Test Layers

The current default pytest config excludes `firefox_live`, `firefox_live_amo`, and `browser_ui`.
Routine development should use the marker-aware Makefile targets documented for the current project shape.

| Layer | Main files or markers |
|---|---|
| Unit/API/service | `tests/test_*unit*.py`, `tests/api`, `tests/core`, profile service/API tests. |
| Route/static contract | `tests/web_profiles_page/`, `tests/test_web_profiles_page.py`, `tests/test_ui_smoke_profile_workflow.py`. |
| Locale/docs contract | `tests/test_locale_*.py`, `tests/test_ui_locale_glossary.py`, docs-specific contract tests. |
| Compliance | `tests/compliance`. |
| Browser UI | marker `browser_ui`, smoke file `tests/test_ui_browser_tabs.py`; covers import, primary routes, route handoff, and RU/ZH-CN rendering. |
| Live Firefox | markers `firefox_live`, `firefox_live_amo`, files under `tests/live_firefox`. |
| Tooling | `tests/tools`. |

Current baseline from `tools/repo_health_report.py`: the historical full default timing was 803.15s test time. BPM now favors layered targets over one default catch-all run.

## CI And Local Commands

- Main CI: `.github/workflows/ci.yml` splits lint/type checks, mandatory fast tests, coverage/contract checks, and manual browser UI checks.
- Scheduled/manual live Firefox policy tests: `.github/workflows/firefox-live.yml`.
- Scheduled/manual AMO canary: `.github/workflows/firefox-live-amo.yml`.
- Gist snapshot publishing: `.github/workflows/gist-snapshot.yml`.
- Layered local tests: `make test-fast`, `make test-contract`, `make test-ui`, `make test-live`, `make test-release`.
- Local health report: `make repo-health`.
- Locale inventory report: `make locale-inventory`.
- Locale rebuild/check: `make build-locale-catalogs`, `make check-locale-catalogs`.
- Default local tests: `make test`.
- Live Firefox setup: `make setup-firefox-live-browsers`.
- `pytest-xdist` status: final BPM 0.8.5 decision is opt-in pure-unit pilot only, not enabled for mandatory CI; see `docs/architecture/pytest-xdist-readiness.md`.

## High-Risk Couplings To Keep In Mind

- `app/web/profiles.py` currently combines web route handling, route URL/focus semantics, catalog context building, locale bootstrapping, and legacy normalization entry points.
- `_page_document.html` centralizes script order for most profile routes.
- Python URL/focus helpers and JavaScript route/focus helpers must stay behaviorally aligned.
- Locale files, docs contracts, and UI static-source tests are tightly coupled; docs or copy cleanup can break tests even when runtime behavior is unchanged.
- CIS generated layers depend on curated YAML inputs plus merge/generation rules; optimize tests with schema/validator caching before changing data shape.
