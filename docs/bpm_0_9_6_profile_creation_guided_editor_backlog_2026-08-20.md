# BPM 0.9.6 Profile Creation And Guided Domain Workflows Backlog

Date: 2026-08-20

Target BPM version: `0.9.6`

Epic ID: `BPM096`

Release risk: high. This epic replaces the profile creation and duplication lifecycle, persists new
baseline provenance, invokes cross-schema conversion while creating a duplicate, introduces an
explicit outbound AMO integration, and redistributes settings across the Guided editor. A defect
could create a partially initialized profile, mutate or lose source-profile data, misstate CIS or
preset provenance, write a document against the wrong Firefox schema, expose an unsafe outbound
request path, or silently omit a policy from every guided workflow.

This backlog takes BPM from the current `0.9.5.1` implementation to a release-ready `0.9.6`. It
replaces unsaved new-profile drafts and inline clone naming with one minimal preparation surface,
makes schema, starter preset, and CIS baseline creation-time choices, opens only a successfully
persisted profile in the Guided editor, removes schema selection from all editor chrome, and gives
extensions, URL/site management, and certificates complete dedicated Guided steps.

Model assignments use the current
[GPT-5.6 model guidance](https://developers.openai.com/api/docs/guides/latest-model), rechecked on
2026-08-20: Luna for deterministic maintenance, Terra as the normal engineering default, and Sol
only where cross-schema duplication and baseline composition create a material silent-data-loss
risk. Reasoning effort is selected independently.

## Scope Summary

- Move active BPM version, package, editable-install, runtime/UI/generated, documentation, test,
  release, and changelog surfaces from `0.9.5.1` to `0.9.6`; keep README version-neutral.
- Remove the explanatory consequence text below the Library's `Check upgrade to ...` link while
  retaining the link itself, its accessible name, its availability conditions, and the complete
  preview/confirmation/recovery copy on the conversion surface.
- Replace `/profiles/new` as an unsaved Guided-editor draft with one minimal create/duplicate
  preparation surface containing profile name, any supported Firefox schema, one supported starter
  preset, CIS baseline (`None`, Level 1, or Level 2 when available), and one terminal `Create` or
  `Duplicate` action.
- Create or duplicate a profile atomically before navigation. A successful action opens the saved
  profile at `/profiles/{id}/edit`; validation, name conflict, stale source, conversion blocker, or
  unavailable CIS state leaves the preparation form open and creates no partial row.
- For duplication, preserve the source profile, offer every supported target schema, and use the
  existing deterministic no-silent-loss conversion planner when the target differs. Never relabel
  source policy data as another schema or mutate the source profile.
- Persist enough reviewed baseline provenance to display the chosen starter preset and CIS baseline
  truthfully after reload, migration, import, duplication, and schema conversion.
- Remove the schema selector from Guided, All settings, and JSON editor chrome. Show read-only
  schema, starter-preset, and CIS-baseline state instead; schema changes remain available only in
  create, duplicate, and the explicit schema-conversion flow.
- Delete the current Guided `Profile & baseline` step. The Guided editor becomes an eight-step
  workflow beginning with the reorganized content of today's second step; presets are not selected
  or reapplied inside an editor.
- Add complete dedicated Guided steps for extensions, navigation URLs/site access, and
  certificates/trust. Remove their owned controls from every other Guided step so each setting has
  exactly one Guided owner while All settings retains complete catalog coverage.
- Integrate extension discovery with Mozilla Add-ons (AMO) by an explicit user-initiated search by
  name. Normalize only the fields BPM needs to configure a Firefox enterprise extension rule; if
  AMO is unavailable or its response cannot be trusted, say so and keep the complete manual path.
- Update all six product locales, product/API/administrator documentation, contextual help,
  screenshots, search/manifests, README durable current-state copy, and release evidence.

## Current-State Assessment

- `GET /profiles/new` currently renders the complete Guided editor as an unsaved draft. Name and
  schema are editable in both the common editor chrome and Guided step 1; the profile does not exist
  until the editor-level Save/Create action posts a generic `ProfileCreate` document.
- Library duplication currently expands `.library-clone-name-panel` in the profile row, validates
  only a suggested name against loaded rows, and opens
  `/profiles/new?clone_from={id}&clone_name={name}`. The new tab copies the source into an unsaved
  draft and keeps the source schema; it has no target-schema conversion preparation flow.
- `app/templates/profiles/_page_editor_chrome.html` renders `#profile-type` for Guided, All settings,
  and JSON. It is enabled for a new draft and disabled for a saved profile, but remains a schema
  selector presentation in every editor.
- Generic profile PATCH already refuses a saved schema change and directs callers to the explicit
  preview/apply conversion flow. BPM 0.9.6 must preserve that fail-closed API boundary while
  removing the misleading editor selector.
- The profile row stores flags and optional CIS compliance metadata, but it does not store a stable
  starter-preset identity. Reopening a saved profile therefore cannot truthfully display which
  creation-time preset was selected without a new provenance contract and migration rule.
- `app/web/firefox_wizard_steps.py` defines six steps. Step 1 mixes name, schema, scenario, starter
  preset, CIS layer, baseline summaries, and overrides. The maintainer's revised decision removes
  that entire step rather than reducing it to a preset picker.
- Today's step 2 combines browser behavior, proxy/network, authentication, certificates, homepage,
  new-tab/Home, search, and review. Today's step 4 combines accounts, language, extensions,
  bookmarks, website filtering/handlers, `InstallAddonsPermission`, and `ExtensionSettings`.
- Extension controls are substantial but static and manual: governance presets, newline textareas,
  several hard-coded curated extensions, install/lock/uninstall fields, and raw policy controls.
  There is no AMO client, BPM AMO API adapter, availability state, or search-by-name workflow.
- Homepage/startup controls live inside step 2, while website allow/block and handler controls live
  inside step 4. Certificate controls are hidden inside step 2 enterprise-network fine tuning.
  Those three domains therefore lack the single, complete Guided ownership requested for 0.9.6.
- The current conversion planner and preview/apply API already prove source/target schema identity,
  target validation, optimistic revision, CIS disposition, and no-silent-loss behavior for saved
  profiles. Duplication should reuse the pure planner and its evidence rather than invent a second
  converter or applying conversion to the source row.
- Locale source begins in `app/i18n_src/`; runtime catalogs, route bundles, profile CSS, installed
  documentation, search indexes, and PDFs are generated owners and must not be hand-edited.

## External AMO Planning Evidence

Mozilla documents the production external API at `https://addons.mozilla.org/api/v5/` and provides
public add-on search and detail endpoints. Search can filter by `app=firefox` and `type=extension`;
the add-on representation exposes a Firefox extension GUID and public current-version metadata.
The API documentation also warns that v5 response shapes are not frozen, so BPM must parse a small
allowlisted contract and fail to the manual workflow on drift rather than trust arbitrary upstream
fields. See the official Mozilla
[external API overview](https://mozilla.github.io/addons-server/topics/api/index.html),
[add-on endpoints](https://mozilla.github.io/addons-server/topics/api/addons), and
[response/version rules](https://mozilla.github.io/addons-server/topics/api/overview.html).

This is planning evidence, not a permanent upstream guarantee. The AMO contract task must recheck
the production endpoint, fields, availability behavior, terms, and compatibility at execution time.

## Approved Product And Workflow Decisions

1. `/profiles/new` becomes the common preparation surface. It renders create mode without a source
   and duplicate mode when a valid source profile is supplied. It does not embed the Guided editor.
2. The form contains only the controls needed to initialize the saved profile: name, Firefox
   schema, starter preset, CIS baseline, validation/unavailability state, and the terminal action.
   Routine product explanations remain in documentation rather than filling the form.
3. Opening the preparation form never writes a profile. `Create` or `Duplicate` performs exactly
   one atomic server-owned creation. Only a successful response navigates the preparation tab to
   `/profiles/{created_id}/edit`; the Library tab remains unchanged.
4. Every supported schema appears in create and duplicate mode. A duplicate targeting its source
   schema preserves source policy data directly; a different target is created only from an
   applicable, target-valid conversion result derived from the current source revision.
5. The source profile is immutable during duplication. Blocked conversion, stale source revision,
   invalid source data, unavailable target, invalid CIS choice, preset-composition conflict, or
   duplicate name produces no clone and no source mutation.
6. A duplicate defaults to the `Keep source settings` preset. When another starter preset is
   explicitly selected, converted source values remain authoritative, the selected preset may fill
   only schema-valid absent paths, and the selected CIS layer is composed by the existing reviewed
   CIS merge rules. No preset may silently overwrite or remove a source value; every collision has
   a deterministic decision or blocks creation.
7. A new profile uses the selected preset as its starting document and then applies the selected CIS
   layer through the same server-owned composition rules. Client-submitted flags are not trusted as
   proof that the displayed preset/CIS choices were applied.
8. Starter-preset identity is durable profile provenance, not a guess from current flags. Legacy,
   imported, or otherwise unattributable profiles receive a truthful `Custom/imported` baseline;
   migrations do not invent a historical preset choice.
9. Editor chrome shows the saved profile name plus read-only schema, selected starter preset, and
   CIS baseline. `None`, unavailable, invalidated, and manual-review CIS states remain distinguishable;
   the header never presents an invalidated benchmark claim as current.
10. Schema choice exists only on create, duplicate, and explicit conversion surfaces. Starter
    preset and CIS level are creation/duplication baseline choices; they are not mutable selectors
    in Guided, All settings, or JSON editor chrome.
11. The former Guided step 1 is removed. The new eight-step order is:

    1. Browser, network, and search
    2. URLs, sites, and navigation
    3. Security and privacy
    4. Certificates and trust
    5. Users, language, and sync
    6. Extensions
    7. AI and smart features
    8. Review and export

12. The URLs step owns user navigation destinations and site-access behavior, not every technical
    field whose value happens to be a URL. Proxy auto-configuration stays with network, extension
    install URLs stay with extensions, and certificate/trust inputs stay with certificates.
13. The Extensions step owns all common add-on governance: global default, allowed, blocked,
    force-installed, normally installed, uninstall, update control, private-browsing allowance,
    install source, `InstallAddonsPermission`, and `ExtensionSettings` details supported by the
    selected schema. Unsupported controls are omitted or truthfully disabled per schema.
14. AMO lookup is explicit and optional. BPM never calls AMO on startup, page load, profile open,
    save, validation, export, or manual entry. The user can always configure an extension by GUID
    and validated install URL without AMO.
15. The AMO adapter accepts no caller-controlled upstream host or path, sends no BPM credentials,
    cookies, profile policy data, or other profile fields, and returns only normalized allowlisted
    extension metadata. Timeout, DNS/TLS failure, non-success, rate limiting, malformed data, or
    response drift becomes one localized unavailable state with a manual recovery action.
16. The Library upgrade recommendation keeps only its actionable `Check upgrade to ...` link.
    Removing the adjacent routine explanation does not remove preview results, destructive-action
    consequences, blockers, confirmation, unavailable reasons, accessible names, or recovery from
    the conversion review surface.
17. Product source, visible UI copy, changelog, and maintained documentation remain English-first;
    the maintainer-facing execution conversation may remain Russian.

## Non-Goals And Assumptions

- Do not change the supported Firefox schema matrix or CIS benchmark provenance merely to implement
  the new workflow. Availability must derive from the active schema/CIS catalogs.
- Do not mutate the source profile, apply conversion to it, archive it, or rename it during
  duplication.
- Do not create a profile row when preparation validation or composition fails. There is no
  `initializing`, half-converted, or cleanup-later profile lifecycle.
- Do not infer a preset by comparing saved flags with a current preset snapshot; current preset
  definitions can evolve and equality would not prove historical selection.
- Do not permit generic PATCH, Guided, All settings, or JSON save payloads to relabel a saved profile
  with another schema. The existing explicit conversion boundary remains authoritative.
- Do not make AMO a product availability dependency, cache an AMO catalog into release artifacts,
  proxy arbitrary URLs, download XPI contents for search, install an add-on into BPM, or promise
  that an AMO listing is safe for a particular organization.
- Do not send the profile name, policy document, CIS data, schema document, existing extension list,
  or stable user/session identifier to AMO. Search disclosure must state that the typed query and
  requested locale are sent to Mozilla only after the explicit search action.
- Do not duplicate extension, URL/site, or certificate controls across Guided steps. All settings
  remains the complete visual catalog and JSON remains the direct document editor.
- Do not move proxy PAC URLs into the URL/navigation step or extension install URLs out of the
  Extensions step merely because they are syntactically URLs; ownership follows the administrator's
  task.
- Do not redesign comparison, import, export document shape, schema retirement migration, or the
  documentation assistant beyond the focused impacts of baseline provenance and editor navigation.
- README may change only for durable current product facts. It must not contain a `0.9.6` anchor,
  active-target statement, planned work, completion placeholder, or release-history summary.
- Do not hand-edit generated locale catalogs, profile bundles, CSS output, installed documentation,
  site/search data, packages, schemas, reports, or PDFs.

## Milestone 1: Version Transition And Release Anchors

Goal: establish `0.9.6` as the single active BPM product version and refresh release inputs before
feature work without turning README into a version surface.

| ID | Task | Essence | Model | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- | --- |
| `BPM096-M1-01` | Update active product version surfaces to `0.9.6`. | Move package, runtime/OpenAPI/UI/generated version data, active architecture/release surfaces, and current-version assertions from `0.9.5.1` to `0.9.6`. | GPT-5.6 Luna | Light | All nonhistorical version surfaces agree on `0.9.6`; historical evidence and migrations remain unchanged; README receives no target-version marker. |
| `BPM096-M1-02` | Refresh editable-package metadata. | Reinstall the local editable package and remove stale environment metadata after the version transition. | GPT-5.6 Luna | Light | `pip show browser-policy-manager`, `importlib.metadata.version`, and a clean editable reinstall report `0.9.6`; local `*.egg-info` is not committed. |
| `BPM096-M1-03` | Recheck dependency and toolchain currency. | Review Python/base and optional dependencies, frontend vendor packages, documentation tooling, test/dev tools, Firefox binaries, and geckodriver against official sources. | GPT-5.6 Terra | High | A reviewed matrix records declared/installed/current versions, licenses, advisories, platform constraints, dispositions, and focused compatibility checks; AMO integration dependencies are included; materially uncertain audits print flushed phase/component progress. |
| `BPM096-M1-04` | Apply approved dependency and lock refreshes. | Update only M1-03-approved constraints, locks, vendor outputs, pre-commit pins, licenses, and checksums. | GPT-5.6 Terra | High | Lock/vendor integrity, `npm ci`, `pip check`, license/advisory checks, and focused compatibility tests pass; all reviewed component outcomes are applied through a stable follow-up task; long installs/builds print real completed/total unit progress. |
| `BPM096-M1-05` | Open the `0.9.6` changelog entry. | Add an English release landing section for atomic profile preparation, read-only baseline chrome, eight Guided steps, and the three complete domain workflows while preserving history. | GPT-5.6 Luna | Light | The entry contains only approved or completed claims and every older changelog section remains intact. |
| `BPM096-M1-06` | Guard version and package consistency. | Extend focused contracts for project, wheel/sdist, installed/runtime, served documentation, and README version-neutrality. | GPT-5.6 Terra | Medium | Tests fail on active `0.9.5.1` leakage, package/runtime disagreement, stale served documentation version, or README release prose while allowing explicit historical context. |
| `BPM096-M1-07` | Refresh every M1-03-deferred stable component. | Apply the current stable wheel, Ruff, Mypy, pre-commit, ONNX Runtime, CycloneDX npm, DOMPurify, marked, and Pygments releases; regenerate every affected owner-controlled lock, vendor asset, license, provenance, and checksum. | GPT-5.6 Terra | High | Each source is rechecked against the official PyPI JSON API or npm registry; Python, frontend/vendor, docs-lock, AI/type/lint/pre-commit, and audit checks pass with no stale deferred component. |

`BPM096-M1-07` — **completed 2026-08-20.** Official PyPI JSON confirmed wheel `0.48.0`, Ruff
`0.16.3`, Mypy `2.3.1`, pre-commit `4.6.2`, ONNX Runtime `1.29.0`, and Pygments `2.21.0`; the
official npm registry confirmed `@cyclonedx/cyclonedx-npm` `6.0.1`, DOMPurify `3.4.14`, and marked
`18.0.10`. The update raised the declared floors/exact pins, aligned the Ruff/Mypy pre-commit hooks,
regenerated `package-lock.json` and the Monaco vendor assets/licenses/SHA-256 record via
`make rebuild-frontend-vendor`, and rebuilt the exact documentation toolchain environment. Focused
owner/AI checks, vendor integrity, 66 frontend tests, lint, typecheck, pre-commit validation, 1,054
documentation tests, and the 3/3 dependency audit passed. An initial `make package-smoke` AI
isolated-install attempt used `/tmp` and encountered its user quota; no host quota was changed.
The verified rerun set `TMPDIR` to a unique `/var/tmp` workspace on the large root filesystem and
passed clean sdist/wheel, base, PostgreSQL, AI/ONNX Runtime 1.29.0, and combined-extra `pip check`
and runtime probes. The unique workspace was removed after the successful run.

## Milestone 2: Workflow, Provenance, Copy, And External-Service Contracts

Goal: freeze lifecycle, ownership, no-silent-loss, UI-copy, and AMO trust boundaries before database,
API, or rendered-workflow changes.

| ID | Task | Essence | Model | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- | --- |
| `BPM096-M2-01` | Inventory profile initialization and editor ownership. | Map Library entrypoints, `/profiles/new`, clone query state, editor chrome, preset/CIS catalogs, storage/API, conversion, Guided steps, locales, docs, tests, and generated owners. | GPT-5.6 Luna | Medium | Every current create/clone/schema/preset/CIS assumption has one owner, intended disposition, and focused verification route; source and generated files are distinguished. |
| `BPM096-M2-02` | Classify affected visible UI copy. | Apply the active UI-copy classification contract to the removed recommendation text, preparation form, read-only header facts, eight steps, AMO states, validation, consequences, and recovery. | GPT-5.6 Terra | High | Routine explanation is distinguished from labels, state, validation, consequences, unavailable reasons, accessible names, and recovery; only approved routine copy is removed; all six locale owners are named. |
| `BPM096-M2-03` | Define the atomic preparation lifecycle contract. | Specify create/duplicate modes, form state, no-write GET behavior, server validation, atomic creation, navigation, retries, idempotency boundary, name conflict, stale source, and interruption. | GPT-5.6 Terra | Extra High | One contract proves that every failure leaves zero new rows and the source unchanged, while one successful action yields exactly one saved profile and one deterministic Guided-editor destination. |
| `BPM096-M2-04` | Define durable starter and CIS provenance. | Specify stored preset identity/version, `Custom/imported` legacy state, CIS display projection, invalidated/manual-review states, API serialization, conversion disposition, and migration defaults. | GPT-5.6 Terra | Extra High | Reloaded headers never infer preset history from flags or overstate CIS status; import, legacy, duplicate, and conversion cases have explicit truthful values and compatibility rules. |
| `BPM096-M2-05` | Define cross-schema duplicate composition. | Freeze conversion, converted-source precedence, absent-path preset fill, CIS merge, collision/blocker, digest, revision, target-validation, and source-nonmutation rules. Sol is required because an incorrect cross-system rule could silently lose enterprise policy or misstate CIS compliance in the new clone. | GPT-5.6 Sol | Extra High | The contract covers same-schema and all directed cross-schema targets, proves no source overwrite/removal, accounts for every preset/CIS decision, and forbids creation from an invalid or stale plan. |
| `BPM096-M2-06` | Define editor chrome baseline presentation. | Specify the shared read-only schema, preset, CIS, state, accessibility, locale, responsive, and conversion-entry behavior for Guided, All settings, and JSON. | GPT-5.6 Terra | High | The three editors expose identical authoritative facts; no schema/preset/CIS selector or writable shadow control remains; invalidated/unavailable values are not collapsed into a current claim. |
| `BPM096-M2-07` | Freeze the eight-step Guided ownership matrix. | Assign every current Guided field, preset, summary, deep link, search target, raw fallback, and schema-specific control to exactly one of the approved eight steps or to All settings only. | GPT-5.6 Terra | Extra High | Extension, URL/site, and certificate families each have one complete Guided owner; other settings retain logical placement; zero duplicate and zero orphan mappings are machine-checkable. |
| `BPM096-M2-08` | Define the AMO privacy and security contract. | Recheck Mozilla's API and specify fixed origin/path, query/locale allowlists, data minimization, response schema, size/time/rate bounds, caching, CSP, logging, availability, and manual fallback. | GPT-5.6 Terra | Extra High | No SSRF, arbitrary redirect, credential/cookie forwarding, profile-data disclosure, active-content rendering, XPI fetch, or save-time dependency is possible; upstream drift and every failure class fail closed to manual entry. |

### BPM096-M2-01 — Current initialization and editor owner map (2026-08-20)

This is an inventory, not an implementation contract for the later milestones.  “Replace” means
replace only through the named later task; “preserve” means retain the existing boundary until a
later contract explicitly supersedes it.  Historical migrations, retirement stores, and versioned
schema/CIS inputs are evidence, not targets for this work.

| Current assumption | Authored owner(s) | Intended disposition | Focused verification |
| --- | --- | --- | --- |
| Library **New profile** links directly to `/profiles/new`; duplicate expands the inline clone-name panel, checks loaded names optimistically, then opens a new tab at `/profiles/new?clone_from={id}&clone_name={name}`. | `app/templates/profiles/_page_library_workspace.html`; `app/static/profiles_library_bootstrap.js`; `docs/architecture/profile-clone-naming-ux-decision.md` | M4-05 replaces both entrypoints with the shared preparation surface; M4-02/M4-04 replace client-only naming and draft navigation. | `tests/contract/ui/profiles/test_clone_naming_contracts.py`; Library DOM/browser contracts; `make frontend-profile-graph`. |
| `GET /profiles/new` parses optional `clone_from`, `clone_name`, and `include_deleted`, then renders `profiles_editor.html` in `new` mode.  Its context includes the complete Guided catalogs and its document exposes clone state as data attributes. | `app/web/profiles.py`; `app/web/profiles_context.py`; `app/templates/profiles/_page_document.html`; `_page_wizard.html` | M4-01 changes this route to a read-only create/duplicate preparation template/context; M4-03/M4-04 alone navigate on a successful atomic response. | `tests/contract/ui/profiles/test_clone_naming_contracts.py`; `tests/contract/ui/profiles/test_wizard_shell_contracts.py`; rendered-route localization contracts. |
| New and clone drafts are client-composed and remain unsaved until the editor Save/Create path posts generic `ProfileCreate`; a clone keeps its source schema. | Guided route entries and legacy authored route scripts listed by `tools/frontend_profile_graph_0_9_5.json`; `app/api/profiles.py`; `app/services/profile_service.py`; `app/schemas/profile.py` | M3-02–M3-05 introduce server-owned composition and dedicated atomic create/duplicate APIs.  Do not retrofit this behavior into generic create/PATCH. | `tests/integration/api/test_profiles_api.py`; `tests/unit/profiles/test_profiles_core_unit.py`; later M3 lifecycle/concurrency suites. |
| Storage is `Profile.schema_version`, `flags`, and optional `compliance`; `ProfileCreate` accepts those caller values and `ProfileService.create` flushes one row.  There is no durable starter-preset identity. | `app/models/profile.py`; `app/schemas/profile.py`; `app/services/profile_service.py`; Alembic ownership in `alembic/versions/` | M2-04 defines provenance; M3-01 adds an immutable migration and truthful legacy/import defaults.  Existing and archived rows remain historical data. | `tests/integration/db/test_migrations.py`; `tests/integration/db/test_database_integration.py`; M3 provenance/migration tests. |
| Generic `PATCH` rejects a changed saved `schema_version` with `profile_schema_conversion_required`; only explicit preview/apply may persist a converted target. | `app/api/profiles.py`; `app/services/profile_service.py`; `app/core/profile_conversion_planner.py`; `app/core/profile_conversion_recipes.py` | Preserve as the schema-relabeling fail-closed boundary.  M2-05/M3-03/M3-05 reuse the pure planner for a duplicate and never apply it to the source. | `tests/integration/api/test_profile_conversion_preview_api.py`; `tests/integration/api/test_profile_conversion_apply_api.py`; `tests/unit/schema/general/test_profile_conversion_planner.py`; `make verify-firefox-conversion-matrix`. |
| The shared editor chrome shows editable draft name/schema and `#profile-type`; it disables the selector only after save, across Guided, All settings, and JSON. | `app/templates/profiles/_page_editor_chrome.html`; `app/templates/profiles/_page_document.html`; route templates | M4 removes draft editor entry; M5/M2-06 replace schema selection with read-only saved schema/preset/CIS facts on all three editors. | `tests/contract/ui/profiles/test_wizard_shell_contracts.py`; `tests/contract/ui/profiles/test_semantic_characterization.py`; browser editor contracts. |
| The Guided catalog has six steps, including `start` (“Profile & baseline”); templates place baseline, browser/network/home/search, privacy, users/add-ons/sites, AI, and review across those six panels. | `app/web/firefox_wizard_steps.py`; `app/templates/profiles/_page_wizard.html`; `_page_wizard_step_*.html`; Guided route scripts | M2-07 freezes the complete mapping; M6 removes `start` and establishes the approved eight-step sequence.  No field move occurs in this inventory task. | `tests/contract/ui/profiles/test_wizard_shell_contracts.py`; `tests/integration/firefox/test_firefox_wizard_shell.py`; later M6 ownership guard. |
| Schema choices derive from the active lifecycle catalog; starter presets are in-process web catalog definitions resolved per supported schema; `keep_current` is currently a client-facing starter option, not persisted provenance. | `app/core/schema_channels.py`; `app/web/firefox_starter_presets.py`; `app/web/profiles_context.py` | M2-03/M2-04 define catalog identities and durable provenance; M3 rederives valid documents server-side.  Do not infer old selection from `flags`. | `tests/unit/schema/contracts/test_schema_channels.py`; `tests/integration/firefox/test_firefox_wizard_shell.py`; M3 catalog/API contracts. |
| CIS availability and generated layers are schema-bound; the web catalog currently computes starter/CIS merges and serves a constrained guided snapshot route. | Authored: `app/compliance/firefox/cis/{sources.yaml,mappings.yaml,merge_rules.yaml,schema.yaml,generation.py,merge.py,validation.py}` and `app/web/firefox_starter_presets.py`; route: `app/web/profiles.py` | M2-04/M2-05 define durable, truthful CIS disposition and duplicate composition; M3 uses the reviewed merge rules server-side. | `tests/contract/compliance/`; `tests/contract/docs/general/test_cis_documentation_inventory.py`; `make test-firefox-schema-workflow`. |
| Six locale source catalogs supply Library, Guided, Settings, JSON, and common copy; current clone and six-step strings are runtime output. | `app/core/locales.py`; `app/i18n_src/{en,ru,de,es-ES,fr,zh-CN}/`; `app/i18n_src/README.md` | M2-02 classifies visible copy before M4–M7 edit it.  Update source catalogs only, then regenerate/check runtime catalogs. | `make check-locale-catalogs`; `tests/integration/locale/test_locale_catalogs.py`; `tests/contract/ui/localization/test_web_profiles_page.py`. |
| Product/help/API documentation and screenshots still describe the shipped draft, inline-clone, and six-step behavior. | Authored documentation under `documentation/src/` and maintained maps under `documentation/config/`; documentation ownership map: `docs/architecture/current-system-map.md` | M10 owns reader-facing corrections after behavior ships.  This backlog record is the planning source, not product documentation. | `make test-docs-contract`; `documentation/tests/unit/test_build_docs_structure.py`; M10 documentation inventory. |
| Profile ESM sources, CSS layers, locale runtime catalogs, CIS layers, schemas, bundles, documentation artifacts, search, PDFs, and vendor files do not share one edit model. | Authored: `app/static/profiles_modules/`, profile templates, `app/static/profiles_css/`, `app/i18n_src/`, CIS YAML/Python sources, and `app/static_src/profiles_monaco_entry.js`.  Generated/vendored: `app/static/profiles_bundles/`, `app/static/profiles.css`, `app/i18n/`, `app/compliance/firefox/cis/generated/`, `app/schemas/policies/`, `app/static/vendor/`, installed docs/site/search/PDFs. | Edit only authored owners; use each owner command to regenerate outputs.  Preserve `docs/archive/`, `alembic/versions/`, `migration_support/`, and versioned schema/CIS material unless a later task names them. | `make frontend-profile-graph`; `make test-profile-pure-modules`; `make check-profile-frontend-bundles`; `make check-locale-catalogs`; applicable CIS/schema contracts. |

The maintained frontend graph (`tools/frontend_profile_graph_0_9_5.json`) is the authoritative
route/source-versus-bundle ownership record even though its historical filename remains `0_9_5`;
do not treat its generated bundle paths or the old global-route JavaScript names as independent
product contracts.  The source/current-generated distinction above also applies to the dirty
worktree: BPM096-M2-01 changes this backlog only and does not normalize, regenerate, or absorb
unrelated work.

### BPM096-M2-02 — Visible UI-copy classification (2026-08-20)

This is a classification record, not a copy, template, locale, API, AMO, or behavior change.  It
applies the active [UI-copy classification contract](architecture/ui-copy-classification-contract-0.9.2.md)
to the 0.9.6 target surfaces.  The contract's safety rule wins whenever a node combines explanation
with a current state, consequence, unavailable reason, validation, accessibility, or recovery.
Consequently, only the routine prose expressly listed as `remove-explanation` below is eligible for
future removal; an implementation must still cite its exact key and surface before deleting it.

| Target surface / copy family | Classification | Required local meaning and later disposition |
| --- | --- | --- |
| Library upgrade recommendation's actionable `Check upgrade to {target}` / current `profiles.schema_conversion_recommendation_action` | `essential` | Keep the localized action and exact target.  It remains a navigation target, not an automatic conversion or a claim that an update was applied. |
| Adjacent Library-only recommendation narration that repeats the action's purpose without communicating a preview consequence, state, or recovery | `remove-explanation` | Remove only this routine explanation.  It cannot include conversion eligibility, the exact source/target, confirmation, or a failure state. |
| Current `profiles.schema_conversion_recommendation_consequence` and `profiles.schema_conversion_recommendation_accessible_name`, and the conversion-review preview, blocker, confirmation, unavailable, failure, and return/reload text | `safety-accessibility` | Preserve the no-write-before-confirmation consequence, accessible action meaning, exact state, and local recovery.  Future work may relocate the consequence from the compact Library row to its owning conversion-review surface, but may not delete it or replace it with a help link.  The active conversion UI-copy interaction contract remains normative for those states. |
| Preparation page title; create/duplicate mode; source-profile identity; form labels and selected values for name, Firefox schema, starter preset, CIS baseline; option labels; and `Create`/`Duplicate` action | `essential` | These are the compact form's identity, choices, and terminal action.  Duplicate mode must name the source as a separate profile rather than imply a source mutation. |
| Preparation page purpose paragraphs, repeated descriptions of the product, or generic instructions that merely restate the adjacent labels and terminal action | `remove-explanation` | Do not fill the compact form with routine workflow narration.  Product background belongs in documentation, subject to the existing documentation-disposition process. |
| Preparation field requirements; invalid or duplicate name; unsupported schema; unavailable/invalid CIS choice; stale source; conversion blocker; composition conflict; loading/submission state; atomic no-row/no-source-mutation consequence; and the action that corrects or retries each condition | `safety-accessibility` | Keep each condition associated with its field or terminal action, announced as needed, and recoverable without documentation.  A disabled `Create`/`Duplicate` control must retain its blocking reason and enabling action programmatically and visibly where needed. |
| Saved editor header: profile name and read-only labels/values for schema, starter preset, and CIS baseline | `essential` | One compact authoritative header facts presentation appears consistently in Guided, All settings, and JSON.  Values are saved facts, never editable shadow selectors or inferred provenance. |
| Header states `None`, `Custom/imported`, unavailable, invalidated, and manual review | `essential` | Retain the exact truthful state distinction; specifically, an invalidated CIS baseline must never be rendered as a current benchmark claim. |
| Header unavailable/invalidated/manual-review reason, any required next action, accessible description, and live update | `safety-accessibility` | A terse value alone is insufficient when it would conceal why it is unavailable/invalidated or how an operator can recover. |
| Header prose that only explains that the facts are read-only, repeats a displayed value, or restates that schema/preset/CIS are chosen at creation | `remove-explanation` | The labels, values, and absence of selectors convey the routine fact; retain a safety consequence only where changing the fact would otherwise be suggested. |
| Eight Guided step names, ordinal/current-step/progress semantics, navigation labels, selected state, field labels, option names and values, and a shortest choice-card differentiator when labels alone would make choices ambiguous | `essential` | Preserve the approved order: Browser, network, and search; URLs, sites, and navigation; Security and privacy; Certificates and trust; Users, language, and sync; Extensions; AI and smart features; Review and export.  No generic prose authorizes duplicating a setting between steps. |
| Generic eight-step introductions, step-map narration, handoff narration, and helper prose that repeats nearby labels, values, or navigation | `remove-explanation` | This follows the contract's exhaustive `profiles.wizard_*_body`, `*_hint`, and `*_copy` rule unless a protected category below applies. |
| Schema-support/coverage/raw/unknown/deprecated notices; disabled controls and reason; input validation; review/export/import/save/conflict/destructive consequences; status announcements; and recovery actions in any Guided step | `safety-accessibility` | Keep the truthful technical boundary, consequence, accessible association, and next action inline.  Do not move these to documentation while compacting the workflow. |
| AMO search heading, query-field label, explicit Search action, normalized result name/GUID/version labels, result selection, and the manual GUID plus validated-install-URL path | `essential` | Search is optional and user initiated; manual extension configuration remains a complete, named first-class path. |
| AMO disclosure that only the typed query and requested locale go to Mozilla after explicit search; no profile data/cookies/credentials are sent; selection is not an organizational safety endorsement; pending/live result status; malformed/no-result/rate-limit/network/TLS/timeout/drift unavailable reason; accessible status; and manual-entry/retry recovery | `safety-accessibility` | Preserve the privacy/security consequence and the exact localized unavailable state with a local manual recovery action.  AMO cannot become a save-time or editor-availability dependency, and neither a generic error nor documentation-only link is sufficient. |
| AMO marketing/background prose or a repeated explanation of what an add-on search is, when it adds no disclosure, state, consequence, or recovery | `remove-explanation` | Keep the compact explicit action and protected trust/privacy copy; move genuine product background through the documentation process if needed. |

All six locale owners for every eventual new, moved, or retired source key are
`app/i18n_src/en/`, `app/i18n_src/ru/`, `app/i18n_src/de/`, `app/i18n_src/es-ES/`,
`app/i18n_src/fr/`, and `app/i18n_src/zh-CN/` (their `common.json`, `library.json`,
`wizard.json`, `settings.json`, and `json.json` catalogs as the surface requires).  Policy labels
remain under the separately generated/override policy-label ownership and are not an M2-02 edit
target.  `app/i18n/` runtime catalogs, frontend bundles/CSS, schemas, CIS generated layers,
documentation outputs, historical stores, and migrations are generated or historical and remain
untouched.  A later implementation updates all six authored peers together, then regenerates and
checks the relevant owner outputs with `make check-locale-catalogs`, locale/rendered-route tests,
and its surface-specific accessibility/behavior tests.

### BPM096-M2-03 — Atomic preparation lifecycle contract (2026-08-20)

[`profile-atomic-preparation-lifecycle-contract-0.9.6.md`](architecture/profile-atomic-preparation-lifecycle-contract-0.9.6.md)
defines the future create/duplicate form state, no-write GET boundary, server-owned validation and
single transaction, immutable duplicate source, deterministic `/profiles/{id}/edit` handoff,
database-backed name race, idempotency/retry boundary, stale-source rejection, and interruption
reconciliation.  It explicitly reserves dedicated M3 commands and M4 presentation work: generic
`ProfileCreate`/PATCH and the current unsaved Guided route are unchanged by this record.  Its
focused documentation-contract test validates zero profile rows for every terminal failure, one
saved row and one destination for success, exact source nonmutation, and the post-commit
lost-response reconciliation distinction.

### BPM096-M2-04 — Durable starter and CIS provenance contract (2026-08-20)

[`profile-baseline-provenance-contract-0.9.6.md`](architecture/profile-baseline-provenance-contract-0.9.6.md)
defines the future `baseline_provenance` envelope and server-only API/header projection. It pins
starter identity/version and CIS evidence, makes `Custom/imported` the non-inferential import and
legacy state, defines verified/manual-review/invalidated/unavailable CIS display states, and fixes
same-schema duplicate, re-composed duplicate, conversion, generic-create, import, and migration
compatibility. It reserves M3 storage/API/conversion integration and M5 rendering: current profile
fields, catalog, generic CRUD/import, retirement tooling, and editor chrome remain unchanged. Its
focused contract test rejects flag/compliance inference and checks legacy/import defaults, read
projection, duplicate non-promotion, and the target-proof conversion rule.

### BPM096-M2-05 — Cross-schema duplicate composition contract (2026-08-20)

[`profile-cross-schema-duplicate-composition-contract-0.9.6.md`](architecture/profile-cross-schema-duplicate-composition-contract-0.9.6.md)
defines the future duplicate derivation for four same-schema targets and every ordered cross-schema
pair. It reuses the exact pure conversion planner, makes converted source authoritative over
absent-path-only preset fill, applies selected CIS through the reviewed merge rules, accounts every
conversion/preset/CIS decision, binds source revision and all result identities into one composition
digest, and requires final target validation. Invalid, blocked, or stale plans create no row; every
outcome leaves the source byte/value unchanged. The focused contract test guards this planning
fixture only: M3 API/persistence and M4 UI behavior remain deliberately unimplemented.

### BPM096-M2-06 — Editor chrome baseline presentation contract (2026-08-20)

[`profile-editor-chrome-baseline-presentation-contract-0.9.6.md`](architecture/profile-editor-chrome-baseline-presentation-contract-0.9.6.md)
defines the future shared saved-profile chrome for Guided, All settings, and JSON. It requires one
server-authoritative schema/starter/CIS fact set per saved profile revision; forbids schema, preset,
and CIS selectors, writable shadows, and save payloads in every editor; and makes unavailable,
invalidated, and manual-review CIS states explicitly non-current. It also fixes the semantic
read-only fact-list, six authored locale roots, narrow/long-label responsive rule, and the sole
explicit schema-conversion review entry. The focused guard protects planning only: M5 implements
the template, locale, CSS, and browser behavior and M5-06 proves runtime parity.

### BPM096-M2-07 — Guided ownership matrix contract (2026-08-20)

[`profile-guided-ownership-matrix-contract-0.9.6.md`](architecture/profile-guided-ownership-matrix-contract-0.9.6.md)
freezes one executable destination for every current schema-backed Guided policy and preference,
manual control, template field, preset, summary, deep link, search target, raw fallback, and
schema-specific variant. It assigns only the approved eight steps or All settings only, with
explicit no-duplicate complete families for Extensions, URLs/sites/navigation, and
Certificates/trust. The former step-1 name/schema/starter/CIS values are separately recorded as
the M2-03 preparation handoff rather than misrepresented as editor settings. The focused guard
enumerates the current source catalogs and templates; M6 implements the topology and consumes the
matrix, while M7-M9 complete their respective domains. No runtime or UI behavior changes here.

### BPM096-M2-08 — AMO privacy and security contract (2026-08-20)

[`amo-privacy-security-contract-0.9.6.md`](architecture/amo-privacy-security-contract-0.9.6.md)
defines the only future AMO lookup as an explicit, server-mediated `GET` to the fixed production
search origin/path with a small query and six-locale allowlist. It forbids caller URLs, redirects,
proxies, credentials/cookies, profile disclosure, URLs/XPI downloads, active-content rendering, and
save-time use. Only a bounded text `guid`/localized-name/version projection may reach the future
same-origin Extensions surface; cache, rate, CSP, and logging rules retain no sensitive query or
profile data. Every local, transport, response, or upstream-drift failure closes to localized
manual GUID plus validated-install-URL entry, which remains available independently of AMO. M7
implements the adapter/UI and mocked/browser proof; the separately invoked Firefox AMO canary stays
an external policy-install check rather than a lookup or save-time gate.

## Milestone 3: Baseline Persistence And Atomic Profile APIs

Goal: make creation and duplication server-owned domain operations that persist truthful baseline
provenance and reuse conversion safety without changing the source profile.

| ID | Task | Essence | Model | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- | --- |
| `BPM096-M3-01` | Add baseline-provenance storage and migration. | Implement the M2-04 profile fields/envelope and an immutable Alembic revision for SQLite and PostgreSQL, including truthful legacy/import defaults. | GPT-5.6 Terra | Extra High | Upgrade/downgrade, clean install, existing rows, archived rows, backups, constraints, serialization, and two-engine rollback/recovery pass; no legacy preset is invented. |
| `BPM096-M3-02` | Build server-owned initialization composition. | Resolve selected schema, preset, and CIS catalog entries into one target-valid document and provenance result without accepting client-composed flags as authority. | GPT-5.6 Terra | Extra High | Every supported schema/preset/CIS combination is valid or has a stable unavailable/blocker result; preset and CIS decisions are deterministic, source-attributed, and covered by focused tests. |
| `BPM096-M3-03` | Build read-only duplicate planning. | Load a fixed source revision, invoke the pure conversion planner when needed, compose preset/CIS under M2-05, and emit a value-safe plan identity without writing. | GPT-5.6 Terra | Extra High | Same-schema and cross-schema plans prove source revision, source/target artifacts, composition decisions, validation, blockers, and result digest; database state is byte-for-byte unchanged. |
| `BPM096-M3-04` | Implement atomic new-profile preparation API. | Add a dedicated request that accepts name plus catalog identities, rederives flags/compliance/provenance server-side, and creates one profile transactionally. | GPT-5.6 Terra | High | Success returns a complete `ProfileRead` with baseline provenance; invalid name/schema/preset/CIS or generated document returns a stable localized/API error and creates no row. |
| `BPM096-M3-05` | Implement atomic duplicate-profile API. | Revalidate the source revision and duplicate plan inside one transaction, then create a new row without applying conversion to the source. | GPT-5.6 Terra | Extra High | Duplicate creation is exactly-once per accepted request boundary, the result matches the rederived digest and target schema, the source is unchanged, and stale/blocking/conflict failures create nothing. |
| `BPM096-M3-06` | Publish initialization API and error contracts. | Update Pydantic/OpenAPI examples, status codes, value-safe diagnostics, authorization assumptions, API inventory, and focused create/duplicate clients. | GPT-5.6 Terra | High | OpenAPI and runtime agree; public examples use complete envelopes; no response leaks policy values through conversion diagnostics; generic PATCH continues to reject schema relabeling. |
| `BPM096-M3-07` | Prove database and concurrency semantics. | Exercise simultaneous names, repeated submits, stale duplicate sources, archived source rules, interruption, transaction rollback, and SQLite/PostgreSQL behavior. | GPT-5.6 Terra | Extra High | No race creates duplicate names or partial rows, no retry mutates the source, revision errors are deterministic, and both engines retain identical lifecycle semantics. |

## Milestone 4: Minimal Create And Duplicate Preparation Surface

Goal: replace the draft wizard and inline clone-name panel with one compact, accessible form whose
successful terminal action opens the saved profile in Guided editing.

| ID | Task | Essence | Model | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- | --- |
| `BPM096-M4-01` | Render the common preparation route. | Make `/profiles/new` render a dedicated create/duplicate template and context with supported schema, preset, CIS, source identity, and terminal-action mode. | GPT-5.6 Terra | High | GET is read-only; invalid/missing duplicate sources are handled explicitly; the full Guided editor, editor chrome, and policy document are not embedded in the preparation page. |
| `BPM096-M4-02` | Implement the minimal form and validation. | Add only name, schema, preset, CIS, state/error region, and `Create`/`Duplicate`, with old-name context as the duplicate name hint. | GPT-5.6 Terra | High | Required, conflict, unavailable, and blocker states appear at the responsible control; keyboard order, labels, descriptions, focus, and six-locale responsive layout pass; routine help prose is absent. |
| `BPM096-M4-03` | Wire atomic new-profile submission. | Submit catalog identities to M3-04, prevent accidental double activation, preserve user input on failure, and navigate the same preparation tab to the created Guided route on success. | GPT-5.6 Terra | High | One activation creates one row; terminal failure creates none; success lands on `/profiles/{id}/edit` with schema/preset/CIS matching the form and no unsaved-new draft state. |
| `BPM096-M4-04` | Wire duplicate preview and submission. | Refresh duplicate planning as schema/preset/CIS changes, show only necessary blocker/unavailable state, and submit the current source revision to M3-05. | GPT-5.6 Terra | Extra High | Every supported schema is offered; conversion never runs by relabeling; stale/blocked results retain the form for recovery; success opens the clone and source facts remain unchanged. |
| `BPM096-M4-05` | Replace Library create and duplicate entrypoints. | Route New profile and Duplicate actions to the common preparation surface and remove the inline clone-name panel, query-carried name, and unsaved clone-draft bootstrap. | GPT-5.6 Terra | High | The Library keeps filters/selection/scroll in its tab, preparation opens through a real `target="_blank" rel="noopener"` link, archived-source rules remain explicit, and obsolete panel CSS/locale/tests are removed. |
| `BPM096-M4-06` | Guard preparation-route behavior. | Add unit, API, DOM, locale, accessibility, responsive, and Chromium tests for create/duplicate success and every terminal failure class. | GPT-5.6 Terra | Extra High | Tests assert persisted outcomes and navigation rather than source strings; double-submit, reload, back, stale source, name conflict, blocked conversion, unavailable CIS, and narrow/long-label layouts pass. |

## Milestone 5: Read-Only Editor Chrome And Baseline State

Goal: make every editor show authoritative saved schema, starter preset, and CIS state without
offering schema or baseline changes outside their explicit lifecycle flows.

| ID | Task | Essence | Model | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- | --- |
| `BPM096-M5-01` | Remove the Library recommendation explanation. | Delete the rendered consequence paragraph below `Check upgrade to ...` and its recommendation-only locale source while keeping the link and conversion-review behavior. | GPT-5.6 Luna | Medium | Library markup in all six locales contains only the actionable link; accessible link text, eligibility, target, preview, confirmation, blockers, consequences, and recovery tests remain green. |
| `BPM096-M5-02` | Replace schema selectors with read-only facts. | Remove `#profile-type` and all writable/disabled schema-selector synchronization from Guided, All settings, and JSON chrome; render the saved schema label instead. | GPT-5.6 Terra | High | No selector is present in DOM or payload construction; each editor reads the server profile's schema; explicit conversion remains reachable and generic saves cannot submit schema changes. |
| `BPM096-M5-03` | Display starter preset in shared chrome. | Render the persisted preset label and provenance state consistently across all three editors, including `Keep source settings` and `Custom/imported`. | GPT-5.6 Terra | High | Refresh, direct deep link, duplicate, import, and migrated-profile views show the exact server-owned state without inference from flags or locale fallback. |
| `BPM096-M5-04` | Display CIS baseline in shared chrome. | Render None, Level 1, Level 2, unavailable, invalidated, and review-required projections from the persisted compliance envelope. | GPT-5.6 Terra | High | The header never claims current compliance from absent/stale evidence; conversion dispositions and schema-unavailable CIS states have localized, accessible presentation. |
| `BPM096-M5-05` | Remove Guided baseline selection state. | Delete name/schema/scenario/preset/CIS step-1 controls, client initialization branches, summary dependencies, and unsaved draft assumptions now owned by preparation. | GPT-5.6 Terra | Extra High | No editor can choose or reapply schema/preset/CIS; initial policy/compliance state comes from the saved profile; direct opens and reloads do not reset its baseline. |
| `BPM096-M5-06` | Guard the shared chrome contract. | Add server-template, DOM, API payload, locale, responsive, and cross-editor parity tests for read-only schema/preset/CIS facts. | GPT-5.6 Terra | High | Guided, All settings, and JSON show the same identities/status; no hidden selector survives; long schema/preset/locale labels fit supported viewports and themes. |

## Milestone 6: Eight-Step Guided Topology And Exclusive Ownership

Goal: remove the former first step, make today's second step the beginning of the workflow, and
establish stable navigation before completing the three new domain experiences.

| ID | Task | Essence | Model | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- | --- |
| `BPM096-M6-01` | Implement the eight-step definition. | Replace the six-step catalog with the approved Browser/network/search, URLs/sites/navigation, Security/privacy, Certificates/trust, Users/language/sync, Extensions, AI, and Review/export order. | GPT-5.6 Terra | High | Stable semantic IDs, visible numbering, progress copy, Back/Next behavior, completion state, all six locales, and direct-start-at-step-1 behavior agree on eight steps. |
| `BPM096-M6-02` | Migrate step state and navigation. | Update state machines, selectors, focus targets, URL/deep-link mapping, settings-search results, summary jumps, dirty guards, and keyboard behavior from six to eight steps. | GPT-5.6 Terra | Extra High | Old numeric assumptions are removed or intentionally mapped; focus never lands on a deleted step; search/jump targets open the one owning step; reload and history behavior are deterministic. |
| `BPM096-M6-03` | Rehome the non-domain step content. | Move current browser/network/search, privacy, users/language/sync, AI, and export controls to their new numbers while leaving domain-owned controls for M7-M9. | GPT-5.6 Terra | Extra High | Every non-extension/non-URL/non-certificate control retains behavior, schema availability, source attribution, validation, and one Guided owner; current browser tests are remapped rather than discarded. |
| `BPM096-M6-04` | Enforce the Guided ownership matrix. | Generate or validate one machine-readable mapping from supported policy/preference controls and special widgets to Guided owner step or All-settings-only disposition. | GPT-5.6 Terra | Extra High | The guard fails on a duplicate, orphan, stale selector, missing schema variant, or mismatch between step catalog, templates, search index, and final review summary. |
| `BPM096-M6-05` | Rebuild final review and export summaries. | Reorder review groups around the eight domains and source them from the same normalized state used by each owning step. | GPT-5.6 Terra | High | Schema, preset, CIS, domain counts, validation, raw fallback, review-required state, export links, and jump actions are correct without reintroducing baseline selectors. |
| `BPM096-M6-06` | Prove topology accessibility and responsiveness. | Run focused DOM and Chromium scenarios for stepper overflow, long locales, keyboard movement, focus restoration, search-to-step, mobile layout, themes, and reduced motion. | GPT-5.6 Terra | Extra High | All eight steps remain operable and visible at supported viewports; no removed six-step copy/selector or duplicate domain control is present. |

### BPM096-M6-03 — Non-domain Guided content rehomed (2026-08-21)

Browser/network/search is now owned by step 1; the retained privacy, users/language/sync, AI, and
export owners align with steps 3, 5, 7, and 8.  Their existing controls, schema availability,
source attribution, and validation remain intact.  Guided settings search retains its direct
control targets, while All settings continues to use its shell aliases.  The browser regression
checks the five non-domain owners and search-to-control navigation.  Extensions, URLs/sites, and
certificates/trust remain reserved for M7--M9; M6-05 remains responsible for the complete review
rebuild.

### BPM096-M6-04 — Guided ownership matrix enforced (2026-08-21)

The M2-07 JSON fixture is now the single machine-readable ownership map used by a runtime
contract guard.  The guard reconciles every supported schema policy, preference, rendered Guided
target, special mounted widget, search-section host, summary, and step-catalog entry, and fails
on duplicate or orphan ownership, stale selectors, missing schema variants, or divergent hosts.
Its explicitly transitional host ledger preserves the current URL, certificate, and extension
locations only until M8, M9, and M7 respectively; it does not change their Guided owners.
M6-05 review/export reconstruction and all M7--M9 product work remain out of scope.

### BPM096-M6-05 — Final review and export rebuilt by domain (2026-08-21)

The final review now presents the same eight domains as the Guided topology: Browser/network/search,
URLs/sites/navigation, Security/privacy, Certificates/trust, Users/language/sync, Extensions, AI,
and Review/export. Its aggregates are derived from the normalized saved-policy document shared by
the existing domain summaries; certificates, URL/site/bookmark, and extension values are no longer
misrepresented as generic network or features output. The transitional M7--M9 host ledger remains
explicit: review jumps lead to the currently rendered host while retaining the future domain owner.
Validation, raw/deprecated/unknown fallback reporting, CIS review-required state, saved schema,
starter preset, CIS facts, and Firefox export links remain present without reintroducing a baseline
selector. The ownership matrix, DOM/runtime contracts, six locale catalogs, frontend bundle
reproducibility, and a Chromium saved-profile acceptance test provide focused evidence.

### BPM096-M6-06 — Topology accessibility and responsiveness proven (2026-08-21)

The eight-step navigation is now a named navigation landmark whose labels wrap safely and whose
horizontal scroll position follows the active step on constrained desktop widths. Normal and
reduced-motion navigation use the appropriate scroll behavior; repeating the active step does not
steal focus. Guided search resolves shell-policy search entries to their owning Guided policy,
opens that owner, and restores focus in the active panel. The focused Chromium matrix proves the
overflowed 1180px stepper, End/Enter roving navigation, no-op focus retention, search-to-step,
reduced motion, 320px German labels, and light/dark layouts. It also asserts eight visible steps,
the absence of stale six-step copy/selectors, and no page overflow. The existing topology and
machine-readable ownership guard remain green, including the duplicate-domain-control check;
M7--M9 domain implementation remains out of scope.

## Milestone 7: Complete Extensions Step And AMO Integration

Goal: make extension governance a full schema-aware Guided workflow with easy AMO discovery and an
equally complete manual path when Mozilla's service is unavailable.

| ID | Task | Essence | Model | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- | --- |
| `BPM096-M7-01` | Inventory extension policy coverage. | Map `ExtensionSettings`, `InstallAddonsPermission`, update controls, managed install/uninstall fields, private-browsing settings, presets, raw fallback, and schema differences. | GPT-5.6 Terra | High | Every supported extension-related policy/path has one Extensions-step control or explicit All-settings-only reason; old step-4 duplicates and obsolete hard-coded curated assumptions have dispositions. |
| `BPM096-M7-02` | Implement the bounded AMO client adapter. | Add a fixed-origin server client for public Firefox extension search/detail with strict query/locale inputs, time/size/redirect bounds, normalized schema, caching, rate limits, and injected transport. | GPT-5.6 Terra | Extra High | Only allowlisted Mozilla endpoints and fields are accepted; GUID/install metadata is verified; malformed, oversized, redirected, timed-out, rate-limited, and non-success responses produce stable unavailable results; no secrets/profile data leave BPM. |
| `BPM096-M7-03` | Expose the BPM AMO search API. | Add a same-origin, read-only endpoint that accepts a bounded name query and locale and returns normalized value-safe results plus availability state. | GPT-5.6 Terra | High | OpenAPI/runtime, cache headers, input limits, error mapping, CSP, request cancellation, privacy-safe logs, and stubbed tests agree; the endpoint cannot be used as an arbitrary proxy. |
| `BPM096-M7-04` | Build extension search and selection UX. | Add explicit search-by-name, loading/no-result/unavailable states, compact result identity, and selection that creates an editable rule keyed by verified Firefox GUID. | GPT-5.6 Terra | High | Search occurs only after user action; typed query disclosure is localized; keyboard/assistive interaction works; external text/URLs are rendered inert and escaped; selection never installs or executes an XPI. |
| `BPM096-M7-05` | Build complete extension rule editing. | Provide add/edit/remove for allowed, blocked, force-installed, normally installed, uninstall, install URL, update-disabled, private-browsing, and schema-supported detail fields. | GPT-5.6 Terra | Extra High | Multiple GUID rules, global wildcard/default, conflict detection, exact policy serialization, raw imported values, and source attribution round-trip without silent normalization or loss. |
| `BPM096-M7-06` | Complete the manual fallback. | Keep GUID and install-URL entry continuously reachable and surface AMO unavailability with a direct switch/focus to manual controls. | GPT-5.6 Terra | High | Startup/page load/offline/timeout/5xx/rate-limit/malformed AMO cases do not block editing, validation, save, export, or reopen; manual rules are functionally equal to AMO-selected rules. |
| `BPM096-M7-07` | Integrate presets, CIS, conversion, and review. | Reconcile starter extension settings and converted/imported rules with the new editor and final summary without changing benchmark or conversion provenance. | GPT-5.6 Terra | Extra High | Every value is attributed to converted source, preset, CIS, manual, AMO-assisted manual selection, imported, or raw fallback; reopen and cross-schema duplicates preserve supported rules and block unsupported ones. |
| `BPM096-M7-08` | Prove extension workflow quality. | Add unit, adapter, API, DOM, locale, security, CSP, offline, schema-matrix, round-trip, and Chromium tests with deterministic fake AMO responses. | GPT-5.6 Terra | Extra High | Tests cover all four active schema artifacts, every availability state, hostile upstream strings/links, cancellation/races, duplicate GUIDs, manual fallback, save/reopen/export, and zero network use outside explicit search. |

### BPM096-M7-01 — Extension policy coverage inventoried (2026-08-21)

The executable [extension coverage inventory](architecture/profile-extension-coverage-inventory-0.9.6.md)
now maps all five extension policy families across the four supported schema artifacts, including
the ESR-153/Release-153-only `ExtensionSettings` permission and runtime-host fields.  Typed
extension policy values have one future owner — the step-6 Extensions editor — with a
raw-preserving fallback; opaque add-on-defined `3rdparty.Extensions.*.adminSettings` is explicitly
All-settings-only.  Starter and CIS inputs, the prior install/uninstall/locked/default controls,
their temporary step-5 hosts, and the three hard-coded curated GUID cards have explicit removal or
single-rehome dispositions.  This task adds no AMO, editor, or write behavior; those remain owned
by M7-02 through M7-08.

### BPM096-M7-02 — Bounded AMO adapter implemented (2026-08-21)

The server-only `app.services.amo_search` adapter now owns the one permitted AMO request: a
canonical HTTPS `GET` to the fixed public Firefox-extension search endpoint.  It accepts only a
trimmed, NFC-normalized 1--100-character name lookup and one of the six authored locale mappings;
the fixed query filters, `Accept: application/json`, and `Accept-Encoding: identity` headers are
not caller-configurable.  Its injected HTTPX transport verifies TLS, disables redirects and
environment proxies, has a five-second timeout, rejects arbitrary URLs/headers, and bounds the
response before JSON interpretation.

Only verified Firefox extension GUIDs, a requested/default localized name, and a version string
survive the complete-response projection.  URLs, icons, XPI/download metadata, HTML, descriptions,
and all other AMO fields are discarded.  The adapter holds successful results only in an
in-memory, session-secret-HMAC-keyed five-minute cache with ten entries per session; it enforces
the contract's per-session/global request reservations and retains no query, session secret,
profile value, credential, or log record.  Invalid inputs, cancellation, transport/TLS/timeout,
redirect, non-success, encoding/type, size, malformed, and schema-drift responses return a stable
unavailable result for a future manual-entry UI.  No API route, browser request, CSP change,
profile write, policy edit, install URL, XPI fetch, or AMO result provenance is introduced here.

Focused deterministic adapter/security tests cover the fixed outbound request, six-locale boundary,
cache privacy/expiry/bounds, rate limits, cancellation, hostile upstream fields, GUID validation,
duplicate IDs, and every availability class.  Ruff and strict module type checking pass.  The
repository-wide import-linter check remains blocked by pre-existing M3
`ProfileService -> app.compliance.firefox` layer violations, not this isolated adapter.

### BPM096-M7-03 — Same-origin AMO search API implemented (2026-08-21)

`GET /api/profiles/extensions/amo-search` is the only BPM HTTP surface for the bounded adapter.
It accepts exactly one `q` and one authored `locale`, rejects duplicate or unknown parameters before
an AMO attempt, and has no upstream host, path, pagination, header, profile, or write input. A
browser must present `Sec-Fetch-Site: same-origin`; a cross-site request returns a value-free
`403` unavailable state and starts no AMO work. The successful and unavailable response is the
small `AmoSearchApiResponse` projection only: availability, stable reason code, cache-hit fact,
and the adapter's escaped-text GUID/name/version values.

The endpoint creates an opaque HttpOnly, SameSite-Strict browser-session cookie scoped to itself
only when needed for the existing session-private cache/rate boundary. It sends `Cache-Control:
no-store, max-age=0` and `Pragma: no-cache`; it does not log lookup/provider values. The app owns
one process-local adapter and clears its bounded state at controlled shutdown. A pre-dispatch and
in-flight disconnect check produces the adapter's `cancelled` unavailable state without starting a
request where cancellation is already known; no UI, policy edit, manual-rule write, XPI fetch, or
AMO-result provenance was added.

Focused proof passed: Ruff; 67 deterministic adapter/API/OpenAPI/privacy-contract/inventory tests;
strict `mypy` for `app/api/profiles.py`; and `git diff --check`. The complete `make typecheck`
remains blocked by the pre-existing M5 error in `app/web/profiles.py:259` (optional
`preparation_source` indexing), outside this API route.

### BPM096-M7-04 — Extension search and selection UX implemented (2026-08-21)

The real Guided Extensions panel (step 6) now has an explicit, native search form for the bounded
same-origin AMO endpoint.  Typing is entirely local; only form submission starts one cancellable
same-origin request.  The localized interface provides idle, required-query, loading, no-results,
unavailable/manual-continuation, and results states, plus a clear disclosure that only the typed
name is sent to Mozilla after the user chooses Search.

Results retain only the adapter's GUID, name, and version projection.  They are rendered through
DOM text nodes, never as provider HTML or links, and selection cannot fetch, install, execute, or
open an XPI.  A selected verified Firefox GUID creates a small editable `ExtensionSettings` rule
with an allowed/blocked policy handoff.  Complete multi-field rule editing, manual GUID/URL entry,
and AMO-selection provenance remain deliberately owned by M7-05 through M7-07.  The older
extension controls remain temporarily hosted at step 5 only until M7-05 removes/re-homes them; the
new AMO UI exists only at the active step-6 owner.

Focused proof passed: 34 DOM/API/inventory contracts; all six locale/CSS checks; 32 pure frontend
module tests; generated frontend bundle verification and reproducibility; `git diff --check`; and
the Chromium explicit-submit/hostile-result/verified-GUID handoff acceptance test.

### BPM096-M7-05 — Complete schema-aware extension rule editing implemented (2026-08-21)

Step 6 is now the sole Guided owner for Firefox extension governance.  Its rule editor adds,
edits, and removes verified extension GUID rules and the global `*` default.  It serializes all
four installation modes; install and update URLs; update/private-browsing controls; blocked-install
text; install sources, types, and restricted domains; the Release/ESR-153 permission and runtime
host fields; and the shared install, lock, uninstall, default-install-permission, and update-policy
values.  Values remain exact while they are typed (including line-list contents and explicit
`false` booleans); unstructured or target-schema-unsupported imported values are exposed as raw
JSON instead of being silently repaired or lost.

The panel detects the global force-install/default contradiction, install/uninstall overlap,
install URLs paired with allowed/blocked modes, and overlapping allowed/blocked permissions.
Each rendered rule carries its manual, CIS, baseline, or raw attribution from the persisted profile
metadata.  AMO selection still uses the bounded M7-04 handoff only; this task neither changes the
AMO backend nor adds fallback-specific availability UX reserved for M7-06.

The old step-5 extension panel, curated cards, default-mode control, and stale search aliases were
removed.  The ownership matrix, extension inventory ledger, schema-shell materialization, and
settings catalog now record exactly one step-6 owner; the generic schema shell keeps its technical
coverage in the review/All-settings surface.

Focused proof passed: 92 M7 DOM, ownership-matrix, AMO UX, locale/catalog, inventory, and new
rule-editing contracts; syntax checks for the changed frontend modules; `git diff --check`.

### BPM096-M7-06 — AMO-independent manual fallback completed (2026-08-21)

The Extensions step now keeps one continuously rendered manual form for a Firefox extension GUID
and optional install URL. It writes through the same `ExtensionSettings` rule path as an
AMO-assisted selection, so manual editing, policy validation, saving, export, and reopening do not
depend on Mozilla. Every unavailable AMO outcome — including transport/offline/timeout, non-success,
rate-limit, malformed response, and response drift — uses the existing localized unavailable state
and reveals a direct action that scrolls to and focuses the manual GUID control. The browser makes
no AMO request on editor startup, load, validation, save, export, or reopen; only an explicit search
may call the same-origin AMO endpoint. The server adapter and outbound boundary were unchanged.

Focused proof passed: all 16 M7 manual-fallback/AMO/rule/API contracts; 32 pure frontend-module
tests; locale and CSS owner checks; frontend bundle verification and reproducibility; `git diff
--check`; and Chromium 5xx → unavailable/focus → manual GUID+URL → save/API → reopen (1 passed).

### BPM096-M7-07 — Extension provenance integrated with preparation, duplication, conversion, and review (2026-08-21)

`extension_provenance` is now a durable, value-level record separate from the M2/M3
`baseline_provenance` authority.  It records only the current extension-value source — `preset`,
`cis`, `manual`, `amo-assisted-manual`, `raw`, `imported`, or `converted` — and can neither create
nor alter a starter identity, CIS benchmark claim, conversion recipe, or compliance proof.

The server derives prepared-profile sources from the existing starter/CIS composition ledgers,
preserves exact sources through a same-schema duplicate, marks each pairwise-planner-admitted
cross-schema value `converted`, and labels explicit conversion results the same way.  A pairwise
blocker still writes no target.  Existing active and archived rows are migrated uniformly to
`imported` without inspecting policy content to guess historical Guided, AMO, preset, or CIS state.
Editor saves preserve untouched sources, accept AMO-assisted and raw markers only for values
changed in that request, and otherwise derive `manual`; final review/export now summarizes the
persisted source evidence.  The extensions editor does not add an AMO request or new AMO UI path.

Focused proof passed: migration/head/runtime and database-matrix checks, active-and-archived
upgrade/downgrade/re-upgrade provenance round-trip, prepared starter/CIS attribution, API
save/reopen, same- and cross-schema duplicate preservation, supported-rule conversion,
unsupported-rule zero-write blocking, conversion-apply attribution, review/editor contracts, all
six locale catalogs, frontend bundle verification/reproducibility, JavaScript syntax, and focused
frontend tests.  The broad extension workflow/Chromium matrix remains owned by M7-08.

### BPM096-M7-08 — Extension workflow quality proved (2026-08-21)

The final extension-workflow matrix now has deterministic adapter, API, DOM, locale/security, and
Chromium coverage.  It exercises every active schema artifact (`release-153`, `esr-153.0`,
`esr-140.13`, and `esr-115.39`), all adapter unavailable codes plus the initial UI state, hostile
AMO names/descriptions/links, duplicate GUID rejection, offline/manual recovery, and the complete
save → reopen → export path.  The Chromium fake-AMO scenario intercepts only the same-origin
search endpoint and proves that opening, validating, saving, exporting, and reopening perform no
AMO request; a request occurs only after an explicit form submission.  Its selected rule survives
as `amo-assisted-manual` provenance while the exported policy remains provenance-free.

The matrix exposed one narrow workflow defect: a pending search disabled the Search control, so an
explicit newer request could not reach the existing abort/sequence protection.  The control now
remains available while a request is pending.  A newer explicit search cancels/replaces the old
request and the deterministic Chromium race test proves that only the newest result is rendered.
This does not create background AMO traffic.

Focused proof passed: 142 unit/API/conversion/provenance/contract tests; Chromium AMO-selection,
manual-fallback, four-schema round-trip, and cancellation-race regression (4 passed); 32 pure
frontend-module tests; all six locale catalogs; all four offline schema artifacts and their
import/edit/export matrix; and frontend bundle integrity/reproducibility.  `ruff`, JavaScript
syntax, and `git diff --check` were also clean.

## Milestone 8: Complete URLs, Sites, And Navigation Step

Goal: give homepage and site-access administration one complete task-centered step while keeping
technical URL values with their proper domains.

| ID | Task | Essence | Model | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- | --- |
| `BPM096-M8-01` | Inventory navigation and site-access ownership. | Map Homepage/startup/new-tab/Home, `WebsiteFilter`, handlers, managed bookmarks, site access lists, related presets/preferences, and schema-specific/raw values. | GPT-5.6 Terra | High | Every user-navigation destination and site-access rule has one step owner or explicit All-settings-only disposition; proxy, extension, and certificate URLs remain with their domains. |
| `BPM096-M8-02` | Rebuild homepage and startup controls. | Move and refine primary/additional homepages, start-page behavior, lock state, new-tab overrides, and Firefox Home choices in step 2. | GPT-5.6 Terra | High | Common tasks are compact, full schema-backed values remain reachable, presets/source attribution survive, and old browser-step copies are removed rather than hidden. |
| `BPM096-M8-03` | Build allowed and blocked site management. | Provide structured add/edit/remove, ordering, wildcard/pattern guidance, allow-only/block-some posture, conflict detection, and exact `WebsiteFilter` serialization. | GPT-5.6 Terra | Extra High | Valid schema patterns round-trip exactly; duplicates, contradictory rules, unsafe/invalid values, IDN, ports, schemes, and imported raw entries receive deterministic validation or fallback without silent repair. |
| `BPM096-M8-04` | Consolidate handlers and managed navigation. | Move protocol/content handlers and managed bookmark/navigation URL tasks that belong to user destinations into the URL step with focused progressive disclosure. | GPT-5.6 Terra | High | Nested values remain complete and editable; bookmarks/handlers no longer appear in Users/language/sync; search-engine and proxy technical configuration remains in its approved owner. |
| `BPM096-M8-05` | Unify URL validation and safe rendering. | Reuse one domain-aware parser/validator for navigation inputs, escaped display, external-link behavior, errors, and raw fallback without over-normalizing Firefox patterns. | GPT-5.6 Terra | Extra High | No script/data URL injection, markup execution, Unicode-host confusion, accidental credential disclosure, or lossy canonicalization occurs; validation messages identify the exact field/rule. |
| `BPM096-M8-06` | Prove URL workflow quality. | Add catalog, schema-matrix, DOM, locale, accessibility, responsive, round-trip, import/export, conversion, and Chromium tests. | GPT-5.6 Terra | Extra High | Homepage, allowed/blocked sites, handlers, bookmarks, raw fallback, and final-review jumps work across supported schemas with one Guided owner and no stale old-step control. |

### BPM096-M8-01 — Navigation and site-access ownership inventoried (2026-08-21)

The executable [navigation and site-access coverage inventory](architecture/profile-navigation-site-coverage-inventory-0.9.6.md)
now assigns every supported user destination and site-access path to the future step-2 URLs,
sites, and navigation owner: homepage/startup/new-tab/Firefox Home, site filters and lists,
protocol/content handlers, bookmarks, and managed navigation. It records the ESR-115 absence of
`HttpAllowlist`, all related managed preferences, starter and CIS inputs, raw fallback, and the
temporary step-1/step-5 hosts that must be removed once rather than copied. Proxy/PAC, search,
extension and certificate URL-bearing values retain their respective domain owners; unknown and
opaque values are explicitly All-settings-only. This task adds no UI or write behavior; M8-02
through M8-06 own implementation and verification.

### BPM096-M8-02 — Homepage and startup controls moved to URLs (2026-08-21)

The existing complete Homepage, startup, new-tab override, and Firefox Home workflow is now
materialized once in the real step-2 `urls_sites_navigation` panel. Its compact presets, typed
primary/additional homepage fields, startup mode, lock, first-run/post-update overrides, Firefox
Home choices, fine tuning, source/status presentation, and local review jump move together; no
copy remains in Browser, network, and search. Search aliases and step-scoped undo/change state now
resolve the same controls to step 2, while proxy and search remain at step 1. The ownership ledger
records the completed host move, while `WebsiteFilter`, site lists, handlers, and bookmarks remain
explicitly deferred to M8-03/M8-04 rather than being copied into this task. Full schema and raw
coverage remains available through the existing All settings/JSON path.

Evidence: ownership-matrix, runtime-guard, shell, asset/i18n, Firefox preference and starter
catalog contracts pass; the frontend bundle builds, verifies, and reproduces; 32 pure frontend
module tests pass; locale catalog verification and `git diff --check` pass. The M6 topology
Chromium suite was started but exceeded the interactive 30-second collection window without a
terminal result; M8-06 owns the required retained Chromium URL workflow evidence.

### BPM096-M8-03 — Allowed and blocked site management completed (2026-08-21)

`WebsiteFilter` now has one structured, schema-backed owner in the step-2 URLs, sites, and
navigation panel. Its two ordered lists support add, edit, remove, and move operations; the
explicit Firefox-pattern hint covers `<all_urls>`, scheme, host, optional port, wildcard path,
and imported values. The available postures are Firefox defaults, block some sites, allow only
managed destinations, and mixed rules. Their implementation preserves the retained spelling and
relative order of every unaffected value.

The dedicated lossless WebsiteFilter module accepts typed safe patterns without canonicalization,
including IDN, IPv6, wildcard, port, and `file:///…` forms. It rejects newly entered unsafe
schemes, credentials, whitespace, malformed ports, and invalid patterns before they can reach the
policy document; it reports exact duplicates and block/exception contradictions. Imported invalid
string entries remain visible and unchanged until deliberately replaced, while non-object,
non-list, non-string, or extra-field imports take an explicit raw-policy fallback rather than
being coerced or silently repaired. The existing simple schema-backed holders for
`AllowedDomainsForApps`, `HttpAllowlist` (where the selected Firefox schema supports it), and
`LocalFileLinks` move to the same step-2 site-access group. No handlers or managed bookmarks move
in this task; `BPM096-M8-04` remains their sole implementation owner.

Evidence: the focused pure frontend set passes 34/34, including the new exact-pattern, IDN,
IPv6/port, unsafe-input, raw-fallback, duplicate/conflict, and posture-order cases. The strict
frontend coverage gate passes all 69 tests at 100% lines, branches, and functions across every
declared pure module. The focused Wizard shell, ownership-matrix, registry-inference, and catalog
integration set passes 42/42. Locale catalog and CSS sources build and verify; profile frontend
bundles build, verify, and reproduce; the frontend ownership graph, JS syntax, Python compilation,
and `git diff --check` pass. The final Chromium URL workflow quality gate remains owned by
`BPM096-M8-06`.

### BPM096-M8-04 — Handlers and managed navigation consolidated (2026-08-21)

The step-2 URLs, sites, and navigation panel now owns one progressive-disclosure group for
protocol/content handlers and managed navigation. `Handlers`, `AutoLaunchProtocolsFromOrigins`,
`GoToIntranetSiteForSingleWordEntryInAddressBar`, `Bookmarks`, `ManagedBookmarks`, and
`NoDefaultBookmarks` are schema-backed, inline-editable controls across all four supported
Firefox channels. Their nested object and array values retain the existing schema editors; the
previous step-5 bookmarks/handlers handoff and its All-settings detour are removed. Final-review
jumps reveal the same step-2 holders. Proxy/PAC and search-engine configuration remain step 1.

Evidence: four-channel catalog checks prove the six policy editors and their recursive shapes;
focused Guided shell, ownership/navigation, asset/i18n, and pure-module tests pass. Frontend
bundles build, verify, and reproduce, and the ownership matrix records the completed host move.
M8-05 remains the owner of generic URL validation and safe external-link rendering; M8-06 owns
the retained end-to-end browser matrix.

### BPM096-M8-05 — URL validation and safe rendering unified (2026-08-21)

The Guided URL workflow now uses one lossless, domain-aware validation boundary for WebsiteFilter,
home/startup values, site-access lists, handlers, and managed bookmarks.  It preserves the exact
Firefox-facing input instead of serializing a parsed URL: paths, case, ports, placeholders, IDN
spelling, and supported match-pattern syntax are never silently canonicalized.  Imported values
outside the typed grammar remain visibly marked raw fallbacks and are retained until deliberately
replaced; malformed list shapes are display-only, preventing accidental conversion on a later
save.

The boundary rejects active URL schemes, credentials, control/bidirectional Unicode characters,
and invalid origin/template forms with a field-specific rule message.  Generated external links
are restricted to unambiguous ASCII HTTP(S) values, HTML-escaped, and receive `noopener`,
`noreferrer`, and no-referrer behavior.  IDN values, templates, raw imports, and non-web schemes
are never promoted to clickable external links.  The simple schema-backed `AllowedDomainsForApps`,
`HttpAllowlist`, and `LocalFileLinks` controls are typed list editors where the selected Firefox
schema supports them.

Evidence: URL/security pure modules pass 9/9; the no-inline-English-fallback asset contract and
the full Guided shell contract suite pass; Python lint and `git diff --check` pass.  Locale
catalogs, Guided CSS, and frontend bundles build, verify, and reproduce.  Cross-browser,
responsive, full import/export, and end-to-end workflow proof remains explicitly owned by
`BPM096-M8-06`.

### BPM096-M8-06 — URL workflow quality proved (2026-08-21)

The URL workflow is now covered end to end for every supported Firefox channel.  The executable
matrix saves, reopens, exports, imports, and runs a directed conversion cycle for homepage,
allowed and blocked sites, handler rules, bookmarks, managed bookmarks, and the no-default-
bookmarks flag.  It also verifies that each URL policy has one Guided owner and that a policy
cannot remain in a legacy step.

The matrix found and corrected a real catalog drift: `Homepage` and related first-run/update
navigation settings had still been assigned to the former home section.  They now have the
step-2 URL owner, while `UserMessaging` is retained with its step-5 accounts/sync owner.  The
schema shell keeps `home_startup` and `urls_sites_navigation` together only in step 2; the
generic startup preference compatibility entry is documented as non-rendered and cannot create a
second Guided control.

Chromium proof covers the structured homepage and WebsiteFilter UI, allowed and blocked rules,
handlers, managed bookmarks, the review-to-URLs jump, all six shipped locales at a narrow
viewport, and a deliberately unsafe imported WebsiteFilter string.  The latter remains an exact,
visible raw fallback and never executes or silently changes during export.

Evidence: focused registry, ownership, matrix, import/export, conversion, and shell tests pass
34/34; the retained Chromium workflow suite passes 2/2 after the catalog correction.  Locale
catalog validation and `git diff --check` are retained as release checks.

## Milestone 9: Complete Certificates And Trust Step

Goal: make enterprise certificate and trust-store administration a visible, complete Guided task
instead of hidden network fine tuning.

| ID | Task | Essence | Model | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- | --- |
| `BPM096-M9-01` | Inventory certificate and trust coverage. | Map `Certificates`, enterprise roots/preferences, certificate installation, client-certificate/authentication links, security devices, overrides, presets, CIS influence, raw fallback, and schema differences. | GPT-5.6 Terra | High | Every certificate/trust-related supported path has one Certificates-step owner or reviewed neighboring/All-settings-only disposition; current step-2 duplicates are listed for removal. |
| `BPM096-M9-02` | Build the certificate trust posture. | Add compact common choices for system trust, enterprise roots, certificate-error behavior, and other schema-supported trust posture before detailed inputs. | GPT-5.6 Terra | High | Choices map exactly to supported policy/preference values, disclose schema/CIS constraints, preserve imported/custom state, and never imply that BPM validates organizational trust decisions. |
| `BPM096-M9-03` | Build certificate and device list editing. | Provide structured controls for install/remove certificate references, client-certificate selection where supported, security devices, and nested certificate policy fields. | GPT-5.6 Terra | Extra High | Add/edit/remove, ordering, duplicates, platform paths, raw entries, empty states, validation, serialization, reopen, and export preserve exact Firefox semantics without reading certificate contents unexpectedly. |
| `BPM096-M9-04` | Integrate CIS, conversion, and source attribution. | Show baseline/manual/converted/imported ownership and CIS conflicts or review requirements without changing benchmark provenance. | GPT-5.6 Terra | Extra High | Selected CIS status remains truthful, manual exceptions are visible, unsupported target-schema values block duplication/conversion, and final review jumps to the certificate owner. |
| `BPM096-M9-05` | Prove certificate workflow quality. | Add schema/CIS contract, DOM, locale, accessibility, responsive, security, path, round-trip, import/export, conversion, and Chromium/Firefox tests. | GPT-5.6 Terra | Extra High | All supported certificate/trust shapes and failure states pass; no certificate value remains duplicated in Browser/network/search or hidden from the ownership guard. |

### BPM096-M9-01 — Certificate and trust coverage inventoried (2026-08-21)

The executable [certificate and trust coverage inventory](architecture/profile-certificate-trust-coverage-inventory-0.9.6.md)
now maps `Certificates.Install` and `ImportEnterpriseRoots`, all `Authentication` host and lock
fields, raw-preserving `SecurityDevices`, `WindowsSSO`, and the three-channel
`MicrosoftEntraSSO` policy. It records the distinct managed
`privacy:security.enterprise_roots.enabled` preference, the certificate-error neighbour
`DisableSecurityBypass.InvalidCertificate`, the absence of a schema-backed client-certificate
selection policy, starter and CIS inputs, raw fallback, and every current legacy trust control.
The historic `wizard-step-2-trust` group is in outer step 1; all listed changes are one removal
or rehome to Certificates and trust step 4, never a copy. This task adds no trust UI, certificate
I/O, policy write, or provenance behavior; M9-02 through M9-05 retain those responsibilities.

### BPM096-M9-02 — Compact certificate trust posture delivered (2026-08-21)

Step 4, Certificates and trust, now provides compact schema-aware choices for the exact Firefox
values `Preferences.security.enterprise_roots.enabled`, `Certificates.ImportEnterpriseRoots`,
`DisableSecurityBypass.InvalidCertificate`, `WindowsSSO`, and, on supported 153 schemas only,
`MicrosoftEntraSSO`. The old step-1 composite trust group and its duplicate controls are removed;
DNS/DoH remains in step 1. The updater preserves `Certificates.Install`,
`DisableSecurityBypass.SafeBrowsing`, managed preference status, and every imported/custom shape
it cannot safely structure, which remains disabled for manual handling in All settings or JSON.
The UI discloses schema and CIS boundaries and explicitly does not claim that BPM validates an
organisation's trust configuration. Certificate references, security devices, and authentication
list editing remain M9-03 scope.

Focused evidence: 33 relevant Python contract/unit tests and 10 Node integration tests pass; the
profile frontend bundle reproducibility and verification checks pass.

### BPM096-M9-03 — Certificate and device list editing delivered (2026-08-21)

Step 4 now owns the structured Firefox policy shapes `Certificates.Install`,
`Authentication`, and `SecurityDevices.Add`/`Delete`. Certificate references remain literal
references: the UI neither opens, uploads, hashes, nor otherwise reads certificate contents.
It accepts relative, POSIX, Windows, and UNC paths; preserves list order and duplicate install
references; offers add, edit, remove, and move controls; and keeps empty fields out of serialized
policy objects. Authentication provides the schema-supported SPNEGO, Delegated, NTLM,
AllowNonFQDN, AllowProxies, Locked, and PrivateBrowsing controls. Security devices provide
ordered add-path and delete-name controls, refuse an accidental duplicate device name, and retain
unknown/direct legacy shapes as visible raw fallback. Client-certificate selection is explicitly
identified as unavailable because no active Firefox schema supports such a policy; it is never
invented as a preference.

All strings are authored for en, ru, de, es-ES, fr, and zh-CN. The Guided bootstrap now receives
the active schema accessor from its public shared state, so a profile's initial certificate fields
render before interaction. Focused evidence: 37 Node pure-module tests, 86 targeted Python
contracts/integration tests, frontend bundle reproducibility and verification, and the retained
Chromium create/edit/save/reopen/export workflow (`1 passed`, 13.88 s) pass. M9-04 CIS,
conversion, and provenance behavior remains deliberately out of scope.

### BPM096-M9-04 — CIS, conversion, and certificate source attribution delivered (2026-08-21)

`certificate_provenance` is now a separate value-free RFC 6901 ledger for certificate, trust,
authentication, and security-device values. It records only `baseline`, `cis`, `manual`,
`converted`, `imported`, or `raw` ownership; it never rewrites the selected starter/CIS benchmark
envelope. Prepared profiles derive the ledger from the server composition decisions, unchanged
same-schema duplicates preserve the recorded source, successful supported cross-schema duplicate
or conversion values become `converted`, and a true editor change is `manual` or an explicitly
changed `raw` value. The new Alembic head
`20260821_add_profile_certificate_provenance` gives all historical certificate-related values the
non-inferential `imported` source without touching `baseline_provenance`.

Step 4 displays the source counts and its certificate-specific CIS-review state. The final Review
and export certificate action resolves to its step-4 attribution owner; the former step-1
authentication/certificates/Windows-SSO summaries are removed. Cross-schema duplicate and
conversion remain fail-closed when the target does not support a certificate policy such as
`MicrosoftEntraSSO`; neither operation writes a target or mutates the source. The ownership,
duplicate, conversion, recovery, and database-upgrade contracts record the new field and the
preserved benchmark boundary.

Focused evidence: certificate provenance units; preparation/duplicate/conversion API and SQLite
migration matrix/recovery suites (the PostgreSQL cases remain expected skips without an external
test database); 67 UI/ownership/architecture/DB-matrix contracts; 37 Node pure-module tests;
locale and frontend bundle verification/reproducibility; and two focused Chromium scenarios pass.
The new Chromium scenario proves `Starter baseline` and `CIS layer` display, a truthful overall
CIS manual-review status with a certificate-specific clear state, and the final-review jump back
to step 4. M9-05's broad quality proof remains out of scope.

### BPM096-M9-05 — Certificate workflow quality proved (2026-08-21)

The final certificate/trust regression confirms the complete structured step-four surface across
`release-153`, `esr-153.0`, `esr-140.13`, and `esr-115.39`: certificates, enterprise and system
roots, authentication host lists/maps/booleans, security-device add/remove lists, certificate-error
bypass, Windows SSO, the supported-only Entra SSO choice, CIS/source ledger, raw fallback, exact
POSIX/Windows/UNC/relative references, and the schema-unavailable boundary.  It proves creation,
same-schema duplicate, cross-schema duplicate/conversion, reopen, export, import, re-export, and
no client-side certificate-provenance relabelling.  CIS composition keeps benchmark provenance
truthful while the separate certificate ledger records baseline/CIS/imported/converted state.

Final quality found and closed one real ownership escape: the generic technical schema shell mounted
on step 8 could render `MicrosoftEntraSSO` from the `advanced` section in addition to the dedicated
step-four control.  The catalog now excludes the complete structured certificate/trust family
(`Authentication`, `Certificates`, `SecurityDevices`, `DisableSecurityBypass`, `WindowsSSO`, and
`MicrosoftEntraSSO`) from every generic shell bucket.  This makes step 4 the sole Guided owner and
prevents a hidden technical-shell editor from bypassing raw-preservation or provenance safeguards.
No certificate input uploads, opens, hashes, reads, or validates certificate/device file contents;
hostile strings render as text and invalid typed input leaves saved values unchanged.

Focused evidence: 133 Python schema/CIS/provenance/duplicate/conversion/DOM/ownership/locale
checks pass (including 18 new M9-05 API/locale checks); certificate pure-module coverage is 100%
lines, branches, and functions under the project threshold with 73 Node tests; locale/CSS catalog
checks and 9 frontend graph/bundle contracts pass; the new Chromium quality matrix passes 2/2 and
the retained M9-03 Chromium workflow passes 2/2; the provisioned Firefox release scenario for a
strict baseline plus managed CA/trust passes (`1 passed`, 13.73 s). Ruff and the scoped diff check
pass. The broad locale guard has one pre-existing M8 false positive: it treats the legitimate Chinese
word `配置文件` in `profiles.wizard_extensions_amo_query_disclosure` as a machine placeholder; it is
outside certificate scope. The broad all-module frontend coverage gate likewise retains existing
`navigation_url.mjs` coverage debt; the certificate module itself is fully covered.

## Milestone 10: Product Documentation, README, And Maintainer Handoff

Goal: make the six-locale product documentation describe only the delivered 0.9.6 workflows, then
build and install one verified documentation artifact before final release quality work.

| ID | Task | Essence | Model | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- | --- |
| `BPM096-M10-01` | Inventory affected documentation and help ownership. | Map User, Firefox Policy, CIS, Administrator/DevOps, API, privacy/security, troubleshooting, search, contextual help, screenshots, and guide-map impacts. | GPT-5.6 Terra | High | Every delivered behavior and failure/recovery boundary has one reader owner; all four guide maps are reviewed; each untouched guide has a recorded unaffected reason; stale six-step/draft/inline-clone claims have dispositions. |
| `BPM096-M10-02` | Update English product and API source. | Document atomic create/duplicate, schema/preset/CIS choices, no-silent-loss duplicate conversion, read-only chrome, eight steps, extension/URL/certificate workflows, AMO disclosure/fallback, and errors. | GPT-5.6 Terra | High | Procedures match shipped UI/API and exact public envelopes; purpose, prerequisites, outcome, limitations, privacy, recovery, and related tasks are complete; no internal, future, or unsafe workflow is exposed. |
| `BPM096-M10-03` | Localize the delivered documentation scope. | Propagate equivalent content to `ru`, `de`, `zh-CN`, `fr`, and `es-ES` using the BPM catalog, Pontoon for Firefox UI terms, SUMO for support prose, and native heading rules. | GPT-5.6 Terra | Extra High | All six locales cover the same workflow, AMO availability/privacy, conversion blockers, CIS states, and recovery without fallback islands, English-calqued headings, stale step counts, or translated identifiers. |
| `BPM096-M10-04` | Refresh help, search, and screenshot sources. | Update contextual targets, aliases, maps/manifests inputs, screenshot disposition, and localized captures for preparation, editor chrome, and the three new domain steps. | GPT-5.6 Terra | High | Every changed action reveals the correct topic; obsolete step/inline-clone screenshots are removed from source ownership; new captures fit site/PDF layouts with localized captions/alt text; source refreshes report phase/locale and completed/total artifacts. |
| `BPM096-M10-05` | Run the required editorial documentation review. | Follow `documentation-update-for-future-epics.md` across affected guide maps, headings, completeness/exclusions, Microsoft style, locale rules, BPM UI labels, Pontoon/SUMO evidence, and search-versus-assistant separation. | GPT-5.6 Terra | Extra High | The review records guide-map coverage, terminology URLs/decisions, native headings, topic completeness, and removed stale/internal/unsafe/unshipped content; untouched guides are justified before any site/PDF build. |
| `BPM096-M10-06` | Run documentation preflight before heavy builds. | Inventory every changed English topic and localized peer, then validate DITA, examples, links, metadata, locale parity, API inventory, Firefox/CIS inventories, search/help/manifests, screenshot disposition, source-bound version/layout contracts, and snapshot owners. | GPT-5.6 Terra | Extra High | Before a site or PDF candidate exists, `make docs-fast-check DOCS_CHANGED='...'`, `make test-docs-contract`, `make docs-validate`, `make check-locale-catalogs`, `make test-locale-contract`, `make test-firefox-schema-contract`, `make verify-firefox-schema-matrix`, `make verify-firefox-conversion-matrix`, `pytest -q tests/integration/api/test_openapi_surface.py tests/contract/docs/general/test_api_documentation_inventory.py`, `pytest -q tests/contract/docs/general/test_firefox_policy_documentation_inventory.py tests/contract/docs/general/test_cis_documentation_inventory.py tests/contract/compliance`, `make frontend-profile-graph`, `make docs-snapshot`, and `make codex-snapshot` pass; failures are repaired at source, never in generated output. |
| `BPM096-M10-07` | Build and verify one documentation site candidate. | After green preflight, run the owner site build once and verify atomic publication, navigation, manifests, search, aliases, contextual help, security/CSP, locale parity, and screenshots. | GPT-5.6 Terra | Extra High | The site command prints flushed phase/locale/completed-total progress; the candidate is quarantined until every check passes and then promoted atomically; any source fix reruns the smallest preflight and this stage only when site inputs changed. |
| `BPM096-M10-08` | Build and review both PDFs in six locales. | Run one owner PDF build followed by verification, visual review, reproducibility, and atomic delivery for User and Administrator guides. | GPT-5.6 Terra | Extra High | `make docs-pdf-build`, `make docs-pdf-verify`, `make docs-pdf-reproducibility`, `make docs-pdf-deliver`, and `make docs-pdf-delivery-verify` pass with real guide/locale progress; title/contents, CJK glyphs, inline literals, code blocks, links, screenshots, page fit/count/numbering, and hashes are checked. |
| `BPM096-M10-09` | Run the documentation release, package, and dev-install handoff. | Execute one authoritative release gate after current sources/site/PDFs, then package verification and `make docs-install-dev`. | GPT-5.6 Terra | Extra High | `make docs-release-check`, `make docs-package`, `make docs-package-verify`, and `make docs-install-dev` pass with real progress; drift returns to the smallest invalidated owner; installed artifacts derive visible version from BPM `0.9.6`; no task starts the development server. |
| `BPM096-M10-10` | Refresh README durable current-state copy. | Review and update only installer/user/administrator descriptions materially changed by profile preparation, editor topology, AMO fallback, or schema/preset/CIS display; inventory every README-reading test. | GPT-5.6 Terra | Medium | README states durable current facts, retains legal/author/contact material, contains no `0.9.6` release/planning/maintainer/test prose, and every README-reading contract plus `pytest -q` passes after the final edit; if no durable paragraph changes, the task records why. |

### BPM096-M10-01 — Documentation and help ownership inventoried (2026-08-21)

Added `profile-documentation-impact-inventory-0.9.6.md` as the active,
executable M10 ledger. All four published guide maps are affected: the User
Guide owns create/duplicate and the eight-step reader workflow; Firefox Policy
owns policy shape, raw-preservation, AMO, URL/site, and certificate/trust
semantics; CIS owns attribution and non-compliance manual-review truth; and the
Administrator Guide owns public API, Firefox interchange, deployment, and
support boundaries. API Integration remains within Administrator, not a fifth
guide.

The ledger assigns M10-04 the search/contextual-help and screenshot-source
refresh. It requires preparation and three-domain captures, and marks obsolete
six-step, draft-only, and inline clone-panel claims for removal or replacement.
No guide is unaffected; any future `unaffected` review requires a non-empty
reason. Product DITA/locales, target maps, aliases, screenshots, generated
artifacts, and runtime behavior remain untouched for M10-02 through M10-09.

### BPM096-M10-02 — English product and API source updated (2026-08-21)

Updated only authored English DITA sources and one focused source-contract. The
User Guide now describes atomic create and duplicate preparation: name, schema,
preset, and CIS baseline are selected before one saved profile opens in Guided
editor; duplicate conversion is planned before creation, never silently loses
data, and a blocked result creates no target or source mutation. Guided, All
settings, and JSON documentation now present schema, preset, and CIS as
read-only saved-profile facts and list the eight delivered steps, including
URLs/sites/navigation (2), certificates/trust (4), and extensions (6).

Firefox Policy documentation assigns those three domains to their exclusive
Guided owners, documents optional explicit AMO lookup with manual GUID and
validated install-URL fallback, and states that BPM never fetches an XPI or
reads certificate/device contents. CIS documentation records preparation,
converted/imported/manual/raw attribution, the separate certificate/trust
ledger, and manual-review truth without a benchmark-compliance claim.

Administrator/API documentation now gives the public
`/api/profiles/prepare/new`, `/prepare/duplicate`, and read-only
`/prepare/duplicate/preview` contracts, stable value-free
`ProfilePreparationErrorEnvelope` recovery, narrow idempotency behavior, and
the same-origin optional AMO lookup boundary. It does not document caller
policy/compliance/provenance candidates, internal implementation details, or
future API guarantees. Localized source peers, guide maps, aliases, help
targets, screenshot sources, and generated documentation artifacts remain
reserved for later M10 tasks.

Focused contract: `tests/contract/docs/general/test_bpm096_english_profile_api_docs.py`.

Verification evidence: the focused source/API/preparation command completed
`26 passed`; XML parsing completed `27/27` changed English DITA sources; and
Ruff plus `git diff --check` passed. A deliberate broad-boundary observation is
recorded, not repaired here: `make test-docs-contract` reached the API-topic
contract at `271 passed` and then failed
`test_english_api_topics_cover_audience_patterns_and_current_api_boundaries`
because it asserts the obsolete inventory phrase `17 programmatic/service
operations` while the unchanged active
`docs/architecture/api-documentation-inventory-0.9.0.md` truthfully says `21`.
The inventory and locale-wide contract owner are outside this English-only task;
M10-02 made no change to either and must not lower the active API count or edit
localized peers merely to hide the drift. M10-03/M10-05/M10-06 own the
localization/editorial/preflight disposition.

### BPM096-M10-03 — Delivered documentation scope localized (2026-08-21)

Localized the delivered reader workflow in ru, de, zh-CN, fr, and es-ES without
changing English source, guide maps, aliases, contextual-help targets,
screenshots, or generated documentation. Each locale now has native create and
duplicate preparation recovery, source nonmutation, and the eight Guided
owners. The Firefox Policy peers cover the optional explicit AMO lookup,
query/locale-only disclosure, no-XPI boundary, and manual GUID plus validated
install-URL recovery. CIS peers distinguish ordinary source attribution from
the separate certificate/trust path ledger and state that imported, manual,
converted, raw, unavailable, and blocked states require review rather than
prove benchmark compliance. Administrator peers cover the narrow public
preparation endpoints and value-free ProfilePreparationErrorEnvelope with
mutation="none".

docs/bpm096_m10_03_locale_terminology_audit_2026-08-21.md records BPM catalog,
Pontoon, SUMO, native-heading, and identifier decisions. It preserves technical
identifiers (including API paths, policy/schema IDs, CIS, AMO, GUID, URL, XPI,
and policies.json) and does not allow English prose fallback.

Focused proof: tests/contract/docs/general/test_bpm096_localized_profile_docs.py
completed 15 passed, parsing all 135 affected localized DITA peers and checking
atomic preparation, eight-step topology, AMO recovery, CIS attribution, public
API recovery, identifier preservation, and no draft fallback in the localized
primary workflow. Broader map/search/help, screenshots, site, and PDF refresh
remain owned by M10-04 through M10-09.

Observed outside this DITA-only scope: the broader runtime-catalog subset had
two pre-existing failures. Its BPM091 authority fixture expects the former
zh-CN step-five value, while the delivered runtime catalog correctly has the
M6 user/language/sync label; its historical French anti-anglicism fixture also
finds legacy English extension catalog fragments. M10-03 does not change
runtime catalog source or a historical authority fixture to hide either drift.
M10-05/M10-06 must retain and disposition those catalog owners before the
release gate.

### BPM096-M10-04 — Help, search, and screenshot sources refreshed (2026-08-21)

Refreshed source-owned contextual help without constructing documentation URLs:
atomic create and duplicate preparation resolve to their canonical User Guide
topics, while Guided steps 2, 4, and 6 resolve to the exact Homepage,
Certificates, and ExtensionSettings policy targets. The same canonical targets
are recorded in the all-settings help contract and the deterministic,
non-assistant search aliases for every locale. New help labels were authored
in all six product catalogs and the runtime catalogs were regenerated.

The User Guide screenshot source matrix now owns 66 localized rows. It adds
create preparation, duplicate preparation, current eight-step editor chrome,
and the dedicated URLs/sites/navigation, certificates/trust, and extensions
captures. Every new capture has one same-locale PNG, DITA key, localized figure
caption, and localized alt text. The obsolete six-step overview, draft-only
creation flow, and inline clone panel have explicit removed-source
dispositions; no source asset owns any of them. The capture owner now upgrades
its temporary SQLite database through Alembic before starting BPM and prints
flushed migration/seed/capture phase, locale, and completed/total progress.

Focused evidence: the 30 newly required localized PNGs were captured with
Chromium/Selenium (6 locales × 5 scenarios); the matrix/source integration,
help/search contracts, source-only canonical-target contract, Ruff, and
`git diff --check` passed (`20 passed` across the focused contract group).
The site candidate, PDF build/delivery, and editorial visual sign-off remain
reserved for M10-05 through M10-08.

### BPM096-M10-05 — Editorial documentation review completed (2026-08-21)

Reviewed all four affected guide maps and the current English plus five
localized source peers against the M10 impact inventory and the documentation
update runbook. Added the indexed source-review record
`profile-documentation-editorial-review-0.9.6.md`, including guide-map
coverage, topic completeness, exclusions, native headings, BPM UI labels,
Pontoon/SUMO terminology URLs and decisions, stale-content dispositions, and
the deterministic-search versus documentation-assistant boundary.

The review corrected direct source and evidence defects in all applicable
locales: Step 2 now owns URLs/sites/navigation rather than managed search; the
complex-policy reference has one current locale-owned source for Step 4
certificates, Step 6 extensions, and Step 7 AI; CIS selection/Level 2 recovery
no longer claims that BPM has a profile-draft lifecycle; and every displayed
Guided label now comes from the same locale `wizard.json` key as runtime. The
historical zh-CN Step 5 AI authority finding is explicitly superseded by the
current Step 7 `AI` key rather than being asserted against the new topology.

The screenshot evidence now distinguishes the accepted historical BPM091
36-row visual review from M10-04's 30 new localized source PNGs in the current
66-row matrix. The latter is `source-capture-complete`, not a rendered site or
PDF visual acceptance; those remain M10-07/M10-08 work. The review preserves
technical literals, does not expose internal, unsafe, or unshipped workflow,
and does not run the M10-07 site or M10-08 PDF work.

Focused reader-source, locale, UI-authority, terminology, assistant-boundary,
screenshot, historical-evidence, navigation, semantic, and editorial contract
bundle passed. `make docs-fast-check` also passed for 34 source/evidence
inputs across all six locales and User/Firefox/CIS guide roots, checking XML,
direct links, semantic UI/figure markup, and localized structural shape. It
explicitly skipped full DITA/portal/PDF/reproducibility work; M10-06 owns that
preflight and M10-07/M10-08 own site/PDF production and rendered review.

### BPM096-M10-06 — Documentation preflight completed (2026-08-21)

Created the source evidence record
`docs/architecture/profile-documentation-preflight-0.9.6.md`. It inventories
the 31 changed English reader topics, all 155 named authored localized peers,
and the six locale key maps; it separately identifies the help/search,
screenshot, and review inputs. The record keeps M10-07 site work and M10-08
PDF work explicitly out of scope.

The required source gates are green before the final snapshot owners:
`docs-fast-check` (296 exact-set inputs), docs contract (1002), docs validation,
locale-catalog check, locale contract (78), Firefox schema contract (79), the
four-channel schema matrix, the twelve-direction conversion matrix, API
inventory (11), Firefox/CIS/compliance inventory (55), and the frontend graph
(42 JS modules, 9 CSS layers). The final `docs-snapshot`, full docs-contract
confirmation (`1002 passed`), and `codex-snapshot` owner calls also passed.
Preflight repaired its own authored documentation and contract owners, used
owner generators only for runtime and documentation inventories, and recorded
every stale/matrix/locale failure with its focused rerun.

### BPM096-M10-07 — Documentation site candidate built and verified (2026-08-21)

Ran the owner `make docs-build` command. Its first candidate was correctly
quarantined before publication when it found two Firefox inventory categories
that were not yet declared by the deterministic search contract:
`sync_accounts` and `urls_sites_navigation`. The source-only repair added both
declared facets, native visible labels in all six locales, and a focused
regression contract. The focused search set passed (`18 passed`) and the
smallest invalidated `docs-fast-check` passed before the owner-build retry.

The retry completed all six HTML5 locale transforms and atomically published
`documentation/build/site` only after the owner validated the candidate. The
published site then passed owner output and manifest validation for HTML,
links, manifest, navigation, search, aliases, locale parity, and screenshot
references. It has 11 locale-owned PNG screenshots in each of `en`, `ru`,
`de`, `zh-CN`, `fr`, and `es-ES`. `make test-docs-ui-contract` passed (`11
passed`); the focused contextual-help, CSP/runtime-boundary, search,
navigation, and localized-screenshot group passed (`52 passed`).

Evidence: `docs/architecture/profile-documentation-site-candidate-0.9.6.md`.
No generated site artifact was hand edited, and this task did not run PDF,
development-site installation, or a development server. M10-08 remains the
owner of both PDF builds and their visual review.

### BPM096-M10-08 — Six-locale User and Administrator PDFs built and reviewed (2026-08-21)

The first owner PDF build quarantined its candidate after DITA-OT correctly
found an invalid `section`-inside-`taskbody` structure in the M10 localization
fragments. The narrow repair normalized the same 11 task topics across all six
locales (66 authored DITA sources) to valid `example` content before
`postreq`, preserving localized text and all literal IDs. The exact 66-input
`docs-fast-check` and direct XML parsing (`66/66`) passed before the next PDF
stage; no generated output was edited.

`make docs-pdf-build` then completed real sequential progress for all 24
locale-guide render stages and atomically published the 12-PDF candidate.
`make docs-pdf-verify` passed. The full no-cache independent rebuild completed
24/24 and `make docs-pdf-reproducibility` matched all 13 candidate hashes
(twelve PDFs plus manifest). Rendered English and Simplified Chinese title,
contents, certificate screenshot, API-literal, and code-block pages were
visually inspected; CJK glyphs, inline literals, page fit, captions, and
bottom numbering were clean. The owner verifier proves those layout and link
contracts across the complete six-locale matrix.

`make docs-pdf-deliver` staged and atomically promoted only
`distributions/documentation/0.9.6`, preserving earlier delivery versions;
`make docs-pdf-delivery-verify` passed candidate provenance, inventory, and
all delivery checksums. Evidence:
`docs/architecture/profile-documentation-pdf-candidate-0.9.6.md`. This task
did not create a package, install documentation for development, or start a
development server; those remain later M10 ownership.

The focused PDF unit/contract bundle then passed. It updated only stale M10-07
site expectations in `documentation/tests/unit/test_build_docs.py` (current
BPM version, alias and locale-fixture counts, and UI/API target coverage); PDF
inputs did not change. Final `docs-pdf-verify`, `docs-pdf-delivery-verify`,
`git diff --check`, and an independent candidate-to-delivery SHA-256 comparison
passed for all `12/12` PDFs.

### BPM096-M10-09 — Documentation release, package, and development-install handoff completed (2026-08-21)

Ran one authoritative `make docs-release-check` after the current M10-07 site
and M10-08 PDF owners. The DITA candidate validation completed `2/2`, the
editorial release gate accepted all six locales, and the full documentation
contract suite passed: `1002 passed in 42.78s`. No drift required returning to
an earlier source, site, or PDF owner.

`make docs-package` completed its owner workflow `4/4` and atomically
published `documentation/dist/bpm-documentation-0.9.6.tar.gz`.
`make docs-package-verify` verified SHA-256
`2e53f3bc8caf61e476fd99c100105ea82a1331ca8f1fde9a3d100888b16c5fac`.
`make docs-install-dev` completed site publication `3/3` and atomic dev-site
installation `2/2` at `app/documentation/site`.

The installed metadata and manifest derive `0.9.6` from BPM, and every locale
root (`en`, `ru`, `de`, `zh-CN`, `fr`, `es-ES`) visibly renders `v0.9.6`.
No development server was started and no generated artifact was edited by
hand. Evidence: `docs/architecture/profile-documentation-release-handoff-0.9.6.md`.

### BPM096-M10-10 — README durable current-state copy refreshed (2026-08-22)

The root README now records atomic create/duplicate preparation (name, supported schema, starter
preset, CIS baseline), source-preserving duplicate conversion, eight Guided steps, read-only saved
schema/preset/CIS facts, and optional AMO lookup with manual GUID and validated install-URL fallback.
It removes obsolete draft and inline-clone claims while retaining legal, author, and contact copy.

All README-reading contracts were inventoried; the focused set passed `144` tests. The mandatory
final JUnit suite passed `1763` tests with `0` failures, `0` errors, and `22` skips in `549.878s`.
The Codex snapshot was regenerated through its owner after the final source changes.

## Milestone 11: Final Quality, Release Commit, And CI Handoff

Goal: prove release readiness across profile lifecycle, databases, conversion, external-service
fallback, policy output, locales, documentation, and real browsers, then publish only reviewed work.

| ID | Task | Essence | Model | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- | --- |
| `BPM096-M11-01` | Run focused epic verification. | Execute initialization, baseline provenance, migration, duplicate conversion, Guided ownership, AMO security/fallback, extension, URL, certificate, locale, UI-contract, and documentation checks before broad gates. | GPT-5.6 Terra | Extra High | Every owning focused suite passes with no unexplained skip/warning; M10 completion and `make docs-install-dev` are reconfirmed; the gate prints current suite/schema/locale and completed/total suites. |
| `BPM096-M11-02` | Run the final Mypy gate. | Execute maintained type checking over application, Alembic/migration support, tooling, and documentation-owned Python surfaces. | GPT-5.6 Luna | Medium | `make typecheck` passes without broad ignores, untyped initialization/AMO payloads, or excluded new modules. |
| `BPM096-M11-03` | Run the final Ruff and architecture gates. | Execute lint, format, complexity, import-boundary, generated-source, frontend-graph, and ownership checks. | GPT-5.6 Luna | Medium | `make lint`, architecture contracts, frontend graph, and generated-owner checks pass with no temporary suppression, cycle, hand-edited output, stale selector, or duplicate Guided owner. |
| `BPM096-M11-04` | Run the complete test suite. | Execute `pytest -q` and the complete maintained documentation contours after focused checks pass. | GPT-5.6 Terra | Extra High | All tests pass with no unexpected skip/deselection/warning; lifecycle/AMO/domain behavior is not replaced by source-text assertions; long execution exposes real layer/completed-test progress and a terminal result. |
| `BPM096-M11-05` | Prove 100% covered code surface. | Run `make coverage` plus owned JavaScript/documentation coverage and close every new or existing line/branch gap. | GPT-5.6 Terra | Extra High | Every declared maintained surface is exactly 100%; no gap is accepted as known debt; reports remain uncommitted; progress names current and completed/total surfaces. |
| `BPM096-M11-06` | Run final Chromium product/documentation smoke. | Exercise create/duplicate, stale/blocking failures, read-only chrome, eight-step navigation, AMO success/fallback, extension/URL/certificate round trips, locales, themes, keyboard, and docs. | GPT-5.6 Terra | Extra High | `make test-ui` passes with clean logs, real scenario/completed-total progress, and retained failure artifacts; browser execution uses immediate sandbox escalation where applicable. |
| `BPM096-M11-07` | Run pinned Firefox policy evidence. | Validate representative created/duplicated profiles for all active schema artifacts in pinned Firefox, including managed extensions, site restrictions/homepage, and certificates/trust. | GPT-5.6 Terra | Extra High | Each deterministic channel reports versions, hashes, policy installation/runtime observations, explicit unsupported cases, artifacts, and completed/total progress; AMO availability is not required for manual policy evidence. |
| `BPM096-M11-08` | Run migration, package, security, and reproducibility gates. | Prove clean installs, SQLite/PostgreSQL upgrades/recovery, source nonmutation, schema/frontend/docs byte reproducibility, AMO outbound-security tests, dependency audits, and release procedures. | GPT-5.6 Terra | Extra High | All gates pass from clean state with real progress, no stale-cache dependency, no partial profile or migration, no open proxy/data leak, and no unreviewed advisory exception. |
| `BPM096-M11-09` | Finalize changelog, README, docs index, and drift evidence. | Replace provisional changelog text with verified claims; validate README boundaries, documentation completion, schema/CIS/locale/Admin/DevOps/update/release drift gates, indexes/manifests/snapshots, and release-readiness evidence. | GPT-5.6 Luna | Medium | Older changelog history is preserved; README remains version-neutral; maintained docs are indexed once; no active surface calls the release `0.9.5.1`, describes six Guided steps, or retains the old draft/clone/schema-selector workflow. |
| `BPM096-M11-10` | Create the reviewed BPM 0.9.6 epic commit. | Review status/diff/evidence, exclude unrelated/local/generated-report changes, and commit the completed approved epic without tagging or releasing. | GPT-5.6 Terra | High | Only reviewed BPM096 changes are committed; all checks are current; the SHA is reported; no unrelated user work, tag, release, or PR is included. |
| `BPM096-M11-11` | Push normally and monitor required CI. | Push the reviewed commit to the configured branch without force/history rewrite and observe every triggered required workflow to terminal state. | GPT-5.6 Terra | High | Commit SHA, remote branch, workflow URLs, and every job result are reported; direct actionable failures are fixed in normal follow-up commits and the full required-CI set is rerun until green; evidenced remote/credential/protection/external blockers stop for maintainer direction. |

## Suggested Execution Order

1. Complete M1 version, package, dependency, and changelog anchors.
2. Freeze atomic lifecycle, provenance, duplicate composition, editor chrome, Guided ownership, UI
   copy, and AMO trust contracts in M2.
3. Add storage and server-owned create/duplicate domain operations in M3 before building the form.
4. Replace `/profiles/new` and Library entrypoints with the atomic preparation UI in M4.
5. Remove recommendation explanation, editor selectors, and former Guided baseline state in M5.
6. Establish the eight-step topology and exclusive ownership guard in M6.
7. Complete Extensions/AMO, URLs/sites/navigation, and Certificates/trust independently in M7, M8,
   and M9; do not close one story by leaving controls duplicated on an old step.
8. Complete English and six-locale sources, editorial review, preflight, one site build, one PDF
   build, final documentation release/package gates, README review, and `make docs-install-dev` in M10.
9. Execute M11 focused and broad release gates, reviewed commit, regular push, repair loop, and
   terminal required-CI monitoring.

Within a milestone, follow task ID order unless an acceptance condition explicitly depends on a
later fixture. Do not render the preparation workflow before the M3 API is authoritative, do not
remove old Guided owners before the M2 mapping is frozen, do not call real AMO in deterministic
tests, and do not document behavior as shipped before focused implementation checks pass.

## Execution Protocol

- Do not execute a task merely because this backlog exists.
- Before each task, show exactly one next task with its ID, essence, acceptance, minimum model, and
  minimal reasoning; wait for explicit maintainer approval.
- Execute only that approved task through exactly one focused subagent using the task-row model and
  at least the task-row reasoning level. If that exact model is unavailable, report it and obtain
  approval for the nearest replacement before starting.
- Keep the primary agent as maintainer-facing coordinator. Report task start, meaningful phase
  transitions, a material finding/blocker, and terminal verification; raw subagent command streams
  remain opt-in.
- Start from `docs/codex/PROJECT_SNAPSHOT.md`, then read only named owners, adjacent tests, relevant
  runbooks/contracts, and nearby modules. Preserve unrelated user changes and keep diffs reviewable.
- Run the narrowest relevant validation first. Expand to database, conversion, schema, CIS, locale,
  AMO security, documentation, browser, Firefox, or release contours only when the owning task calls
  for them.
- Any command that may exceed one minute or has uncertain duration must print flushed real-work
  progress on stdout: phase/schema/locale/scenario, completed and total units, cache/retry state, and
  a terminal success/failure boundary. Measured elapsed time/ETA is allowed; fabricated percentages,
  decorative spinners, timers, and chat-only progress are not.
- While a long command runs, keep maintainer chat silent. If a third-party command cannot expose
  units, use a task-owned read-only observer. Preserve safe interruption, partial-artifact
  quarantine, and atomic promotion.
- Run Selenium/Chromium/Firefox commands with immediate sandbox escalation where the environment
  requires it; do not first perform a known-failing sandbox trial.
- Recheck Mozilla AMO endpoint/field/version/terms evidence, dependencies, licenses, advisories,
  browser binaries, geckodriver, and GPT-5.6 guidance at the task that consumes them. Backlog-time
  observations are not permanent pins.
- AMO calls are allowed only after an explicit user search. Deterministic tests use injected fake
  transports; product startup, page load, profile open/save/validate/export, documentation build,
  and release gates remain network-independent.
- Duplicate preparation is read-only until the terminal create transaction. Cross-schema duplicate
  creation rederives conversion and composition against the locked current source revision; it
  never applies conversion to the source profile.
- Coverage below 100% is never accepted as known debt. Add focused tests, remove proven dead code,
  or stop for an approved scope decision.
- The final push is regular and non-force. Do not rewrite history, tag, create a release/PR, or
  include unrelated changes. Monitor every required workflow to a terminal result and repair every
  direct actionable failure through normal follow-up commits until the complete required set is green.

## Backlog Creation Acceptance Checklist

- Target version is normalized as `0.9.6`, epic ID `BPM096`, and filename prefix `bpm_0_9_6`.
- Scope, current state, AMO evidence, approved eight-step sequence, assumptions, non-goals, and high
  lifecycle/data/external-service risk are explicit.
- Every task has one stable ID, one minimum GPT-5.6 model, one allowed reasoning level, and a focused
  acceptance condition; the single Sol assignment explains why Terra is unsafe.
- M1 covers version surfaces, editable metadata, external dependency/toolchain checks, changelog,
  package/version tests, and README version-neutrality.
- Create and duplicate use one minimal preparation surface with name, any supported schema, preset,
  CIS, and one terminal action; opening the surface itself never writes.
- Success creates exactly one saved profile and opens Guided editing; every failure creates no row
  and preserves the duplicate source.
- Cross-schema duplication reuses no-silent-loss conversion, revision validation, target validation,
  preset absent-path fill, and CIS merge rather than relabeling or silently overwriting source data.
- Starter-preset provenance is persisted truthfully; legacy/imported profiles receive an explicit
  custom/imported state rather than an inferred historical preset.
- Guided, All settings, and JSON show read-only schema, preset, and CIS facts; schema/preset/CIS
  selectors are absent and generic PATCH still rejects schema changes.
- The former first Guided step is deleted. The eight-step order begins with the reorganized current
  second step and contains dedicated URLs, Certificates, and Extensions steps.
- Every Guided policy/preference/widget has exactly one owner or explicit All-settings-only
  disposition; extension, URL/site, and certificate controls are removed from old steps.
- AMO search is user-initiated, fixed-origin, minimized, bounded, safely normalized, and optional;
  manual entry remains complete for offline, unavailable, rate-limited, or drifting upstream states.
- The Library keeps only `Check upgrade to ...`; conversion review still owns preview, confirmation,
  consequences, blockers, unavailable reasons, accessible state, and recovery.
- M10 follows `documentation-update-for-future-epics.md`, including guide-map/exclusion review,
  Microsoft/Pontoon/SUMO/native-heading authority, full changed-topic/locale preflight before heavy
  builds, one site build, both PDFs in six locales, CJK/code-block/page-fit checks, reproducibility,
  package verification, and successful `make docs-install-dev` handoff.
- README work is limited to durable installer/user/administrator facts, preserves legal and
  author/contact material, inventories all README-reading contracts, and reruns `pytest -q`.
- M11 includes mypy, ruff, `pytest -q`, coverage-to-100%, Chromium, pinned Firefox, documentation,
  changelog, README/index/drift review, git commit, regular push, and the post-push repair loop through
  a fully green required-CI set or an evidenced external blocker.
- Long-running commands have real flushed stdout progress and browser commands require immediate
  escalation where applicable.
- Every backlog task requires separate explicit maintainer approval, one focused subagent, exact
  task-row model/minimum reasoning or an approved replacement, major coordinator updates, and
  opt-in raw command output.
- Docs index includes this backlog with status `backlog`; no creation-time manifest entry or archive
  move is required.

### BPM096-M11-01 — Focused epic verification complete (2026-08-22)

The owner-focused release gate completed all `14/14` suites before the broad M11 gates.  The
initialization, baseline-provenance, SQLite migration, duplicate-conversion, Guided-ownership,
AMO-security/fallback, extension, URL/site, certificate/trust, locale, UI-contract, and
M10-documentation suites passed `645` Python checks.  The profile pure-module owner passed
`38/38` Node checks, including URL, WebsiteFilter, certificate raw-fallback, and conversion
boundaries.  There were no test failures or warning summaries.

The `8` reported skips were audited with `-rs`: five PostgreSQL preparation-concurrency cases
and three PostgreSQL database-integration cases require `BPM_POSTGRES_TEST_URL`.  Their explicit
skip reasons preserve the unavailable live-PostgreSQL proof for M11-08; the SQLite migration and
all applicable focused owners passed here.

M10 completion was reconfirmed by the focused documentation suite (`33` passed).  The final
`make docs-install-dev` owner command printed and completed source validation `1/3`, six DITA
locales `6/6`, candidate promotion `3/3`, and atomic development-site installation `2/2` without
starting a development server.  Final `git diff --check` was clean.

### BPM096-M11-02 — Final maintained Mypy gate complete (2026-08-22)

`make typecheck` completed successfully for all `114` maintained application, Alembic/migration,
release-tooling, and documentation-owned Python source files.  The first gate attempt exposed four
actual type defects: two provenance-ledger reads treated a checked `object` as a mapping, the
certificate ledger could return an unchecked source value, and the duplicate-page title indexed an
optional preparation source.  The fixes retain explicit runtime shape checks, preserve the existing
source vocabulary, and narrow the source only after the unavailable branch; no broad Mypy ignore,
cast, untyped initialization, AMO-payload relaxation, or excluded module was introduced.

The affected three-file Mypy retry passed, together with `20` focused extension/certificate
provenance and duplicate-preparation API tests.  The complete maintained gate then passed with
`Success: no issues found in 114 source files`.

### BPM096-M11-03 — Final Ruff and architecture gates complete (2026-08-22)

The maintained formatting, lint, architecture, generated-source, frontend-graph, and ownership
gates are green.  The first `make lint` pass exposed one unused Alembic graph local and seven
unsorted imports in the new browser and UI-contract owners; all were corrected without a
suppression.  `ruff format` then applied the repository's reviewed formatter mechanically to `51`
changed source and test files; the final check reports all `1019` tracked Python files formatted.

The final `make lint` passed, and Import Linter analysed `403` files and `416` dependencies with
all `7/7` contracts kept: delivery remains downward-only, owned profile layers have no sibling
cycles, schema and policy UI boundaries remain encapsulated, and release assembly cannot reach
incubation or documentation-build runtimes.  `make release-boundary` completed its clean-wheel
and base-startup checks.  The focused architecture/current-artifact/Guided-owner owners passed
`3/3`, `82/82`, `30/30`, and `20/20` checks in their respective retained sets.

Generated owner checks confirm locale catalogs, CSS, native frontend fixtures, and vendor-lock
are current.  The frontend graph remains acyclic at `42` owned JavaScript modules and `9` CSS
layers; profile bundle manifests, checksums, source maps, route boundaries, and pinned-esbuild
byte reproducibility all passed.  `git diff --check` is clean; no hand-edited generated output,
temporary suppression, stale selector, or duplicate Guided owner was introduced.

### BPM096-M11-04 — Complete test and maintained documentation contours complete (2026-08-22)

The full `./.venv/bin/pytest -q` gate passed to `100%` after two narrow reviewed drift repairs:
`make codex-snapshot` refreshed the generated Codex source digest, and the profile-performance
guardrail received the actual SHA-256 of its intentionally updated atomic-preparation UI contract.
No test, collection floor, performance ceiling, or behavioural lifecycle/AMO/domain assertion was
removed or weakened.  The two affected contract owners passed `7/7` before the final full-suite
retry, which completed without failures, errors, or warning summary.

The separate full `pytest -q -rs` audit also passed.  Its `22` skips are all explicit live
PostgreSQL cases guarded by unavailable `BPM_POSTGRES_TEST_URL` (database integration/recovery,
conversion, preparation-concurrency, retirement matrix/materializer); no unexpected skip or
deselection was accepted.  That environment-dependent proof remains owned by M11-08.

The complete maintained non-coverage documentation partition, `make test-docs`, passed
`1055` tests in `289.60s`.  Its `11` deselections are the target's declared coverage witnesses,
reserved for M11-05 rather than an undisclosed test reduction.  The authoritative non-browser
documentation release contour, `make docs-release-check`, passed full DITA validation (`2/2`),
editorial release sign-off for all six locales, and `1002` documentation release contracts in
`36.45s`.  Final snapshot/guardrail focused checks and `git diff --check` are green.

### BPM096-M11-05 — Complete declared coverage surface (2026-08-22)

All three declared deterministic coverage gates are now exactly `100%`, with no accepted
line, branch, or function debt.  `make coverage` passed its release-implementation (`11`)
and optional-incubation (`238`) contours: the combined report covers `3,429` statements and
`1,056` branches at `100%`.  `make test-frontend-coverage` passed all `73` Node tests, with
every one of the `12` extracted profile pure modules at `100%` for lines, branches, and
functions.  `make docs-coverage` passed `112` documentation tests in `337.95s`, covering
`2,564` statements and `1,048` branches at `100%`.

The gate found and closed two real defects instead of recording them as debt.  First,
`navigation_url.mjs` had unexercised typed-input, parser-failure, raw-preservation, IDN, URL
kind, and match-pattern safety branches; the owner tests now prove each result, including the
defensive no-host parser result.  Second, after the generic schema shell correctly removed the
six certificate/trust policies, the All settings inventory had not reintroduced them under the
single Guided step-4 owner.  The channel catalog now supplies the supported certificate/trust
policy IDs, and the inventory contracts prove their presence only on `certificates_trust` step
4 without restoring a generic duplicate.

The native frontend fixture was regenerated through its owner and verified current.  Focused
inventory/catalog contracts (`11`), snapshot contracts (`2`), Ruff, formatter, and `git diff
--check` all passed.  Python, frontend, and documentation HTML/XML/text coverage reports remain
ignored, uncommitted local evidence; no generated report is included in the reviewed source set.

### BPM096-M11-06 — Final Chromium product and documentation smoke (2026-08-22)

The final direct Chromium gate passed: `PYTEST_ADDOPTS=-s make test-ui` selected the complete
`ui or browser_ui` contour and finished with `309 passed, 1506 deselected in 389.64s (0:06:29)`.
The marker expression deliberately includes the deterministic real-browser product and
documentation scenarios; selecting only `ui` had omitted that `browser_ui` contour.

The run reported real scenario progress: `BPM096 M4-06 Chromium 4/4` covered create and duplicate
success/reload/Back, name conflict, stale source, conversion block, unavailable CIS, six locales,
keyboard order, narrow viewport, and a long source label. `BPM095 M5 UX 3/3` covered eligibility and
locale/keyboard/responsive recommendation, blocked/retry and unsaved cancellation, then explicit
apply/reload/stale recovery. The selected gate also exercised the atomic preparation flow, shared
read-only schema/preset/CIS chrome, the eight-step Guided editor, AMO success and manual fallback,
extension/URL/certificate round trips, themes, documentation, and keyboard behavior.

Two defects found during the smoke were repaired before this acceptance: the Make target now selects
`ui or browser_ui`, and an invalid Monaco JSON edit no longer lets a downstream editor-sync parser
throw before workspace state updates. Invalid editor values now skip parse-dependent synchronisation,
show the localized error state, and disable the mutable actions; a focused six-scenario Chromium
retry passed `6/6` in `47.79s`. The bundle owner/Makefile contracts and focused browser lint then
passed `26` tests, with `git diff --check` clean.

Failure evidence was retained under `artifacts/m11-06-chromium-failures/` (18 files),
`artifacts/m11-06-focused-failures-retry/` (3),
`artifacts/m11-06-json-invalid-final/` (3), and
`artifacts/m11-06-json-invalid-pdb/` (3). The accepted final artifact root was not created because
the full gate had no failure; its terminal log has no test failure or warning summary.

### BPM096-M11-07 — Pinned Firefox policy evidence complete (2026-08-22)

The final immutable-browser matrix passed `4/4` channels and `52/52` deterministic scenarios with
zero failures, errors, skips, or AMO calls.  Every channel first reverified its pinned Firefox and
geckodriver provenance, then ran thirteen local-loopback policy/runtime scenarios with flushed
`channel` and `scenario completed/total` progress.  The accepted artifact root is
`artifacts/m11-07-pinned-firefox/matrix-accepted/`; each channel retains `versions.json`, JUnit,
safe pytest log, run summary, failure-artifact location, schema identity, and runtime observation
list.  The matrix terminal summary records all four as passed.

The exact browser/schema pairs were Firefox `154.0` / `release-153`
(`7665cd49ab13417270748325838e565136adbc76d41bbd76fb24d15a0cc7792b` /
`3903bf9c49fa250a04839fdb4d6fd79c0106a5c927a5bb30f0c660151000dc9f`), Firefox
`153.1.0esr` / `esr-153.0`, Firefox `140.14.0esr` / `esr-140.13`, and Firefox
`115.39.0esr` / `esr-115.39`
(`d7fb42d0aaf4bfccec49c5e3918118d55a222a52854a7ad4651e09eaf7b7c685` /
`81056cba8d2f6b3545cc0ed073e30177eb720f7ec8877ba08c009130dae22022`).  All used
geckodriver `0.37.1` with SHA-256
`e815130ea95983e162ae91843b48d3a3ce991735635fce83a647afde21e09f7e`.

The BPM096 lifecycle scenario creates an atomic blank profile for the channel schema, applies
manual M7--M9 policy values through BPM's public API, creates a source-preserving prepared
duplicate, exports both, proves the cloned Firefox installation receives the duplicate's exact
response bytes, and observes active `ExtensionSettings`, `Homepage`, `WebsiteFilter`, and
`Certificates` policies.  Separate created/duplicated pairs prove site blocking and managed-CA
trust without relying on AMO availability or an external XPI.  Existing local-loopback policy
scenarios retain independent homepage, site, preference, proxy, certificate, and persisted-export
runtime evidence.

Two harness defects were found and repaired instead of accepting misleading evidence.  The runner
previously omitted `BPM_FIREFOX_CHANNEL` from its child pytest environment, allowing every matrix
worker to select Release by default; it now passes both the verified browser channel and its mapped
schema artifact, and records the schema bundle hash in every summary.  Firefox ESR 115 hides the
`about:policies` Errors category when clean while retaining static “Policy Errors” tab text; the
live helper now recognizes that explicit hidden category state while preserving a visible-error
failure path.  Focused runner/harness/provisioning and preparation API checks passed `45/45`, Ruff
and format checks passed, and `git diff --check` was clean.

The only explicit unsupported case is `MicrosoftEntraSSO` in `esr-115.39`: the policy is absent
from that target schema, so the runner records it as `not-declared-in-target-schema` and never
silently creates, duplicates, or installs it.  This is a passed supported-schema disposition, not a
skipped browser scenario.

### BPM096-M11-08 — Migration, package, security, and reproducibility gates complete (2026-08-22)

All required gates passed from fresh, disposable environments.  `tools/package_smoke.py` created
independent base, `postgres`, `ai`, and combined `postgres,ai` installations with cache use disabled;
each passed its import/runtime probe and `pip check`.  The complete SQLite/PostgreSQL integration
suite passed with PostgreSQL recovery required, using disposable database
`bpm_m4_05_m11_08`, service `17.10`, client `psycopg 3.3.4`, and the final Alembic revision
`20260821_add_profile_certificate_provenance`.  A post-suite read-only query found no recovery
temporary databases (`bpm_m4_06_*`), so no source, restore, failed, or retry migration state was
left behind.

The source-preserving Firefox conversion matrix passed all `12/12` pairs.  Focused AMO adapter/API
and privacy/security contracts also passed: requests remain bound to the configured AMO origin,
unavailable AMO selects the manual fallback, and arbitrary proxy targets or leaked request data are
rejected.  Dependency checks recreated their Python environments with `PIP_NO_CACHE_DIR=1` and ran
the fresh `npm ci` tree: base Python, all-extras Python, and npm audits all passed with no known
vulnerabilities.  The three CycloneDX SBOMs contain `41`, `143`, and `184` components respectively;
the advisory-suppression lists remain empty.  Transient pip cache-deserialization notices were
explicitly ignored by the tool rather than accepted as cached audit data.

Reproducibility gates passed for the four Firefox schema channels (`4/4`), the frontend profile
bundles and graph (`42` owned JS modules, `9` CSS layers), and two independent six-locale
documentation builds (`1118` identical files).  The verified documentation archive is
`bpm-documentation-0.9.6.tar.gz` with SHA-256
`963def935a46e269ad1fddac77459d548c13d15f458238687d1df12b2b1b474c`.
Release-boundary, native Linux, Windows, and macOS package validations passed.  An active Docker
smoke workflow still referenced `0.9.5`; it was corrected to `0.9.6` together with a regression
guard.  The real fresh image then passed its base-dependency exclusion, explicit SQLite migration,
health/readiness, documentation, and persistent-volume restart checks; its temporary containers and
volume were removed.  The focused Docker tests (`5/5`), Ruff/format checks, and final
`git diff --check` passed.

### BPM096-M11-09 — Changelog, README, index, and drift closeout (2026-08-22)

The provisional `0.9.6` changelog section was replaced with verified delivery and quality claims.
It preserves the `0.9.5.1` and earlier release history and keeps the remaining handoff truthful:
the reviewed commit and required-CI observation are still owned by M11-10 and M11-11. README
remains version-neutral and describes atomic preparation, the eight-step Guided editor, read-only
schema/preset/CIS facts, explicit conversion, AMO fallback, and dedicated URL/site,
certificate/trust, and extension workflows.

The six current Administrator minimum-requirements topics no longer carry an active `0.9.5.1`
claim. The new [BPM 0.9.6 release-readiness evidence](architecture/release-readiness-evidence-0.9.6.md)
links the schema/CIS, locale, Administrator/DevOps, update, release, documentation, package, and
drift gate owners without treating generated artifacts as source authority. The documentation
index lists it once. Focused README/editorial/index/artifact-ownership/drift/release contracts
and the new closeout contract passed (`47` tests). `make docs-fast-check` passed for the ten
changed documentation inputs, and the complete `make docs-validate` rerun passed source validation
and all six DITA HTML5 locales before its portal candidate completed. The stale user-guide browser
witness was corrected to its current read-only editor-chrome locale test.
