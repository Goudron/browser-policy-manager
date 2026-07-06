# BPM 0.9.0 Product Documentation Portal Backlog

Date: 2026-06-20

This backlog turns the archived `documentation_portal_roadmap_2026-05-21.md` into executable BPM
0.9.0 work. The release adds a case-oriented, six-locale product documentation portal built from
DITA topics, complete Firefox policy and CIS guidance, API-based integration guidance, localized
screenshots, deterministic smart search, and an entry point from the Profile Library.

Product source, UI copy, README, changelog, and maintained documentation stay in English.
Maintainer chat may be Russian, but implementation copy must not switch to Russian unless the task
is explicitly a localization task. English is the source locale for product documentation; all six
published locales are release deliverables, not best-effort fallbacks.
When a task authors publishable topics in more than one locale, all locale peers must be
content-equivalent, not compact placeholders or reduced summaries. If full human localization is not
completed in the same task, the task must explicitly record the gap and the follow-up localization
gate that blocks release readiness.

## Scope Summary

- Target BPM version: `0.9.0`.
- Compact epic id: `BPM090`.
- Source roadmap: `docs/archive/2026-q2/documentation_portal_roadmap_2026-05-21.md`.
- Scope boundary: product documentation architecture, DITA authoring and publishing, case-oriented
  user guidance, Firefox policy reference, CIS guidance, current-API integration guidance,
  deterministic smart search, localized screenshots, BPM documentation navigation, isolated
  documentation tests, localization, accessibility, and release metadata.
- Release risk: high, because the epic introduces a new built product surface and toolchain, must
  remain correct across six locales and two Firefox schema channels, and must not drift from BPM's
  UI, API, policy schema, or CIS data.
- Primary outcome: a user can open BPM documentation from the Profile Library, choose the current
  UI locale, find a task or reference topic through navigation or smart search, and complete every
  supported BPM user workflow without relying on maintainer-oriented repository notes.
- Secondary outcome: documentation sources, generated output, search indexes, screenshots, and
  tests have an explicit ownership boundary so documentation failures can be reproduced and fixed
  without loading or running the whole BPM product test surface.

## Current-State Assessment

- BPM has maintainer documentation and historical planning under `docs/`, but no end-user
  documentation portal or DITA source tree.
- The archived documentation roadmap already identifies DITA, stable topic IDs, UI-to-topic
  mappings, localized output, deterministic search, policy/CIS cross-links, and eventual extraction
  into a standalone product as the intended direction.
- BPM currently exposes five user surfaces: Profile Library, Profile Comparison, Guided Editor,
  All Settings, and JSON Editor. Import, export, validation, schemas, starter presets, CIS layers,
  profile lifecycle, locale, and theme behavior cross those surfaces.
- The current API includes profile list/statistics/read/create/update/archive/restore/permanent-delete
  operations, Firefox `policies.json` import and export, schema-channel validation, and liveness and
  readiness probes. FastAPI also owns `/docs` for OpenAPI UI, so the product documentation route
  must not silently replace that contract.
- Firefox policy schemas, stable policy IDs, schema-channel metadata, known preferences, CIS
  recommendation mappings, preset IDs, UI targets, and validation paths already provide structured
  identifiers from which DITA references and documentation anchors can be built.
- The active locale matrix is `en`, `ru`, `de`, `zh-CN`, `fr`, and `es-ES`. Existing locale
  glossary, placeholder, terminology, ownership, and QA runbooks cover UI copy but do not yet define
  a DITA translation and localized-screenshot workflow.
- Documentation tests now have a dedicated `documentation/tests/` root, explicit suite boundaries,
  compact fixture ownership, a local context guide, focused aggregate Make commands, and a
  documentation-only source fast loop, isolated coverage reporting, a compact fixture catalog, and
  ignored failure diagnostics plus a generated subsystem snapshot.
- The roadmap's second smart-search layer proposed retrieval-based question answering. That layer
  is deliberately excluded from BPM 0.9.0.

## Non-Goals And Assumptions

- Do not add an LLM, embeddings, vector database, RAG, generative answers, chat assistant, external
  AI search service, or AI-generated screenshot descriptions as shipped documentation functionality
  in 0.9.0. This non-goal does not prohibit using AI during development, authoring, or localization,
  and it does not exclude product topics that explain existing BPM or Firefox controls.
- Existing Firefox policies for controlling browser AI and smart features are still product
  capabilities and must be documented like other supported policies. This does not authorize AI in
  the documentation implementation.
- Do not create distribution-specific installation guides yet. The 0.9.0 administrator guide covers
  the currently supported source checkout deployment path for Linux and Windows 10/11 through WSL,
  DevOps integration operation, source-based update procedures, and backup/rollback caveats;
  packaged installers, distribution-specific upgrades, high availability, reverse proxies, and
  production operations remain deferred until BPM distribution formats are defined.
- Do not add new BPM API endpoints or change API semantics merely to make the integration guide
  broader. Document the current API honestly, including missing authentication, concurrency,
  idempotency, pagination, and rate-limit guarantees.
- Do not claim certified CIS conformance. Guidance must preserve benchmark provenance, distinguish
  BPM automation from manual review, and avoid reproducing text that BPM is not licensed to ship.
- Do not copy or translate Mozilla or CIS source material without a recorded reuse/provenance
  decision. Policy behavior remains grounded in bundled schemas and allowed upstream references.
- Do not replace the existing maintainer-oriented `docs/` tree. Product documentation gets a
  separate top-level ownership area and generated output remains distinguishable from hand-edited
  source.
- Do not extract documentation into a separate repository or standalone service in 0.9.0. Keep
  boundaries extraction-ready and reassess after release.
- Do not require internet access, telemetry, or a hosted search backend at runtime. The portal and
  search must work for self-hosted and offline BPM deployments.
- English is authored first, but release acceptance requires topic, navigation, search, alt-text,
  and screenshot parity for all six locales. Silent English fallback in a published localized guide
  is not acceptable except for allowlisted technical identifiers and brand names.
- Localized topic peers must preserve the same user intent, prerequisites, decisions, warnings,
  recovery guidance, examples, and product limitations as the English source. Shorter wording is
  acceptable only when it is semantically equivalent, not when it drops steps or caveats.
- Generated HTML and search indexes are build artifacts, not hand-edited sources. Whether release
  packages commit or assemble them is decided explicitly before implementation; local transient
  output must not pollute the maintained documentation index.

## Milestone 1: Version Transition And Release Anchors

Goal: establish 0.9.0 as the target version before documentation implementation begins.

| ID | Task | Essence | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- |
| `BPM090-M1-01` | Update product version surfaces to `0.9.0`. | Move package metadata, application settings, UI-visible version values, tests, and other active release constants to the target version. | medium | Runtime, package, tests, and active metadata agree on `0.9.0`; old versions remain only in history, archives, or explicit migration context. |
| `BPM090-M1-02` | Establish the 0.9.0 README release anchor. | Update current-version and supported-feature framing without prematurely describing unfinished portal behavior. | low | README identifies 0.9.0 as the active target and has an explicit placeholder for the post-implementation product documentation summary. |
| `BPM090-M1-03` | Open the 0.9.0 changelog entry. | Add a target-version section while preserving all prior release history. | low | `CHANGELOG.md` contains a non-final 0.9.0 section and no older entry is overwritten. |
| `BPM090-M1-04` | Audit active release-naming documentation. | Find active architecture, release-readiness, runbook, and docs-index text that incorrectly treats 0.8.8 as the future/current target. | medium | A bounded update list is recorded; historical and archive references are explicitly excluded. |
| `BPM090-M1-05` | Record the documentation epic release contract. | Define which portal, content, locale, search, screenshot, integration, and test deliverables block 0.9.0. | high | A maintained release checklist maps every mandatory outcome in this backlog to an owner and verification command. |

## Milestone 2: Current-State Inventory And Architecture Decisions

Goal: freeze content coverage and technical ownership contracts before bulk authoring.

| ID | Task | Essence | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- |
| `BPM090-M2-01` | Build the BPM user-capability coverage inventory. | Enumerate every user-visible capability, route, mode, action, state, validation path, schema-channel difference, locale behavior, and recovery flow that needs documentation. | high | A machine-readable or tabular inventory maps every current product capability to a planned DITA task, concept, reference, or troubleshooting topic; no README capability is unmapped. |
| `BPM090-M2-02` | Build the API documentation inventory from OpenAPI and route contracts. | Capture every existing endpoint, method, parameter, payload, response, error, and documented limitation. | high | The inventory agrees with `/openapi.json` and focused API contract tests; undocumented or intentionally internal endpoints are identified. |
| `BPM090-M2-03` | Build the Firefox policy coverage inventory. | Derive the union and differences of supported Release and ESR policy IDs, managed-preference behavior, raw fallback, and version metadata. | high | Every supported schema policy has a stable documentation ID and planned topic; channel-only and changed policies are flagged. |
| `BPM090-M2-04` | Build the CIS content coverage inventory. | Map supported benchmark versions, levels, recommendations, generated layers, presets, policy/preference targets, conflicts, exceptions, and manual-review states. | high | Every shipped CIS recommendation and user-visible CIS state maps to a DITA topic or explicit non-publishable provenance record. |
| `BPM090-M2-05` | Decide the product-documentation ownership boundary. | Define the top-level `documentation/` area and the minimal bridge into `app/`, packaging, and release workflows. | extra high | An architecture decision assigns ownership for DITA source, localized assets, generated output, manifest, search index, runtime serving, and tests; unrelated BPM modules stay outside the normal documentation debug context. |
| `BPM090-M2-06` | Select and pin the DITA publishing toolchain. | Evaluate DITA-OT and any required plugins/wrappers for reproducible local and CI builds. | high | The decision records versions, licenses, Java/runtime prerequisites, offline behavior, install/update procedure, and why the selected toolchain meets six-locale and accessibility needs. |
| `BPM090-M2-07` | Define stable topic, anchor, key, and URL conventions. | Prevent UI refactors, translated filenames, and schema bumps from breaking links. | high | Conventions cover immutable IDs, locale-independent keys, redirects/aliases, policy IDs, CIS IDs, API operations, screenshots, and `/help/{locale}/...` URLs. |
| `BPM090-M2-08` | Define the documentation manifest and UI-target mapping schemas. | Specify how BPM discovers guides, topics, locales, versions, anchors, policy/CIS/API targets, and generated assets. | high | Versioned JSON schemas and examples validate required fields, reject duplicate IDs or broken targets, and support all six locales. |
| `BPM090-M2-09` | Complete source reuse and provenance review. | Establish safe rules for Mozilla schema descriptions, examples, CIS references, licenses, attribution, and translations. | extra high | An approved provenance matrix identifies allowed source use, required attribution, forbidden copying, and update ownership for each guide family. |
| `BPM090-M2-10` | Define documentation accessibility and security contracts. | Set requirements for semantic navigation, keyboard use, alt text, CSP, safe code examples, and static asset handling. | high | WCAG-oriented acceptance checks, CSP constraints, HTML sanitization rules, and security headers are documented before templates or generated output are integrated. |

## Milestone 3: DITA Source, Build, And Publishing Foundation

Goal: create a reproducible structured-authoring pipeline before writing the full guides.

| ID | Task | Essence | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- |
| `BPM090-M3-01` | Scaffold the isolated `documentation/` product area. | Add source, maps, shared resources, locale assets, tools, tests, fixtures, and build-output boundaries. | high | The tree has documented ownership; hand-authored sources and generated artifacts cannot be confused; no dependency, cache, or generated directory enters normal repository context scans. |
| `BPM090-M3-02` | Add a local documentation context guide. | Add `documentation/AGENTS.md` with entry points, narrow read rules, focused commands, generated-file rules, and escalation notes. | medium | A future documentation-only task can start from the local guide and compact snapshot without reading unrelated app or general test modules. |
| `BPM090-M3-03` | Add pinned documentation development dependencies. | Provide a repeatable install/bootstrap path separate from normal runtime dependencies where practical. | medium | A clean environment can install exact DITA/build/test dependencies; licenses and cache/offline expectations are recorded. |
| `BPM090-M3-04` | Create DITA maps for the four guide families. | Establish separate maps for User Guide, Firefox Policy Guide, CIS Settings Guide, and API Integration Guide. | high | Each map builds independently and as part of a portal aggregate; all published content originates in DITA topics or DITA-managed reusable resources. |
| `BPM090-M3-05` | Define reusable DITA subject schemes, keys, and conditional attributes. | Standardize locale, BPM version, Firefox channel, policy, CIS level, API operation, audience, and platform metadata. | high | Validation catches unknown metadata; Release/ESR and locale conditions can be applied without copying entire topics. |
| `BPM090-M3-06` | Implement reproducible DITA validation and static publishing. | Add focused commands for schema validation, link validation, HTML generation, and clean rebuilds. | high | Two clean builds from the same sources produce equivalent publishable content; invalid DITA or broken references fail fast with useful file/topic diagnostics. |
| `BPM090-M3-07` | Implement generated-output and packaging policy. | Keep local output ignored while making release artifacts deterministic and available to BPM. | high | The repository and package rules state exactly what is committed, ignored, built in CI, and shipped; stale output cannot be served after a failed build. |
| `BPM090-M3-08` | Build the portal shell and responsive theme. | Create accessible navigation, breadcrumbs, guide switcher, locale switcher, version context, code blocks, tables, notes, and print behavior. | high | Representative topics pass keyboard, narrow-screen, dark/light theme, heading hierarchy, and CSP checks in every locale. |
| `BPM090-M3-09` | Generate and validate the documentation manifest. | Produce the runtime manifest from DITA maps and metadata rather than maintaining duplicate navigation by hand. | high | The manifest deterministically lists guides, locales, topics, anchors, policy/CIS/API mappings, search assets, and source/build versions; schema validation passes. |
| `BPM090-M3-10` | Add documentation authoring and update runbooks. | Document topic creation, reuse, localization, screenshots, policy/CIS refresh, link changes, review, and publishing. | medium | A maintainer can add or update one topic and run only the documented focused checks before the release suite. |

## Milestone 4: Case-Oriented Product User Guide

Goal: document every BPM user capability as a task the user is trying to complete, with concepts
and reference material supporting rather than replacing the task flow.

| ID | Task | Essence | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- |
| `BPM090-M4-01` | Define the case-oriented user-guide map. | Turn the capability inventory into user goals, prerequisites, outcomes, decision points, related tasks, concepts, and troubleshooting paths. | high | Every capability has a primary task path; navigation is organized by user intent rather than UI module or source-code ownership. |
| `BPM090-M4-02` | Author orientation and core-concept topics. | Explain profiles, Firefox schema channels, policies, managed preferences, validation, presets, CIS layers, lifecycle states, and the five BPM surfaces. | medium | A first-time user can choose the right editor and schema channel without administrator/deployment content. |
| `BPM090-M4-03` | Author Profile Library task topics. | Cover create, find, filter, sort, inspect status, duplicate with naming, archive, restore, permanently delete, reset implications where exposed, and open editor modes. | high | Every Library action and state in the capability inventory has prerequisites, steps, expected result, warnings, recovery, and related links. |
| `BPM090-M4-04` | Author import and export task topics. | Cover JSON and multipart import, schema selection, normalization, validation failures, download/pretty export, and deployment-ready `policies.json` shape. | high | Supported UI and API-adjacent import/export workflows have tested examples and distinguish BPM's internal model from Firefox's boundary document. |
| `BPM090-M4-05` | Author Profile Comparison task topics. | Cover selecting/searching two profiles and interpreting missing, equal, changed, policy, and preference rows. | medium | Users can reproduce the complete comparison workflow and understand every displayed comparison state. |
| `BPM090-M4-06` | Author Guided Editor task topics. | Cover drafts, save behavior, scenarios, starter presets, CIS-aware baselines, each guided section, schema-dependent controls, review, and transition to full editors. | high | Every current guided step and control family is mapped; unsupported ESR controls and existing browser AI-policy settings are explained without adding AI to documentation. |
| `BPM090-M4-07` | Author All Settings task topics. | Cover Review, Configured, and Catalog modes; search; category/source/attention filters; bounded lists; detail editing; raw fallback; policies; and preferences. | high | Users can inspect, add, change, remove, reset, and troubleshoot every supported All Settings state and deliberately reach advanced controls. |
| `BPM090-M4-08` | Author JSON Editor task topics. | Cover document structure, Monaco editing, save/validation behavior, raw values, exact review, and safe recovery from invalid documents. | medium | Valid and invalid end-to-end examples match current JSON editor and import/export contracts. |
| `BPM090-M4-09` | Author validation and schema-channel task topics. | Explain Release/ESR choice, supported-version differences, unknown/unsupported/deprecated settings, validation messages, and migration expectations. | high | Examples are contract-tested against supported schemas and link to the relevant policy and troubleshooting topics. |
| `BPM090-M4-10` | Author cross-cutting user task topics. | Cover locale and theme selection, opening multiple editor tabs, unsaved drafts, navigation, source attribution, keyboard behavior, and safe destructive actions. | medium | All cross-surface behaviors from the coverage inventory have a discoverable task or concept topic. |
| `BPM090-M4-11` | Author troubleshooting and recovery topics. | Cover schema mismatch, malformed JSON, unsupported policy, raw fallback, failed import, validation errors, missing profile, stale tab, and browser-testing caveats visible to users. | high | Each known user-facing error family points to a deterministic diagnosis and recovery path without instructing users to edit internal storage. |
| `BPM090-M4-12` | Close the user-guide coverage matrix. | Review the built English guide against routes, templates, locale catalogs, API boundary behavior, README capabilities, and browser smoke flows. | extra high | No shipped BPM user capability remains unmapped; omissions block localization and 0.9.0 release readiness. |

## Milestone 5: Firefox Policy Guide

Goal: provide a complete, version-aware reference and practical usage guide for every Firefox
policy supported by BPM.

| ID | Task | Essence | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- |
| `BPM090-M5-01` | Define the Firefox policy DITA topic model. | Standardize purpose, BPM location, value shape, Release/ESR support, examples, caveats, interactions, CIS links, validation, and upstream provenance. | high | One template/schema supports simple and complex policies without losing nested value or channel information. |
| `BPM090-M5-02` | Generate schema-grounded policy topic skeletons. | Derive stable DITA reference topics from the supported schema union while preserving hand-authored regions. | high | Every supported policy ID has exactly one stable topic; regeneration is deterministic and never overwrites reviewed prose. |
| `BPM090-M5-03` | Author policy selection and deployment concepts. | Explain how Firefox Enterprise policies, BPM profiles, schema channels, managed preferences, starter presets, and exported `policies.json` relate. | medium | Readers can choose a policy or starter preset and understand where BPM validation ends and Firefox runtime behavior begins. |
| `BPM090-M5-04` | Add valid examples for every supported policy shape. | Provide minimal and practical JSON/DITA examples grounded in bundled schemas. | high | Every policy topic has a schema-valid example or an explicit justified no-example marker; examples pass automated validation in each supported channel. |
| `BPM090-M5-05` | Document Release and ESR differences. | Publish support badges, conditional sections, changed values, and channel-specific caveats from the current schema pair. | high | Search, navigation, and topics can filter or display the active channel; no topic falsely claims cross-channel support. |
| `BPM090-M5-06` | Document complex policy families and managed preferences. | Add deeper task/reference coverage for extensions, permissions, updates, certificates, proxies, search, homepage, privacy, AI controls, and preference locking where supported. | high | Nested structures, conflicts, raw fallback, and related BPM controls are understandable and tested with representative configurations. |
| `BPM090-M5-07` | Add policy relationships and contextual targets. | Link policy topics to BPM UI targets, related policies, user tasks, CIS recommendations, validation errors, and API examples. | high | The generated manifest resolves every mapped policy target and rejects orphaned or ambiguous policy links. |
| `BPM090-M5-08` | Integrate policy docs with the Firefox schema update runbook. | Make documentation drift a required part of Release/ESR schema bumps. | high | The runbook checks added/removed/changed policy topics, examples, aliases, search entries, locales, screenshots where relevant, and manifest parity. |
| `BPM090-M5-09` | Verify policy content provenance and accuracy. | Review generated facts and authored guidance against bundled schemas and approved Mozilla sources. | extra high | Each topic carries source/version metadata; unsupported claims, copied prose, and stale channel information fail review. |

## Milestone 6: CIS Settings Guide

Goal: explain how BPM represents, applies, reviews, and maintains CIS Firefox settings without
overstating automated coverage or certified compliance.

| ID | Task | Essence | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- |
| `BPM090-M6-01` | Define the CIS DITA topic model and disclaimer contract. | Standardize benchmark/version, level, recommendation ID, rationale summary, BPM mapping, automated/manual state, conflicts, verification, and provenance. | extra high | Topics clearly separate licensed source references, BPM-authored explanation, automated configuration, and manual review; certification is never implied. |
| `BPM090-M6-02` | Author CIS orientation and selection topics. | Explain benchmark versions, Level 1/Level 2 intent, supported channels, presets, generated layers, and when CIS guidance is appropriate. | high | Users can select a supported baseline and understand its scope, tradeoffs, and prerequisites. |
| `BPM090-M6-03` | Generate recommendation topic skeletons from shipped mappings. | Create stable DITA references for every supported CIS recommendation and mapping target. | high | Every shipped recommendation maps to exactly one topic or an explicit provenance-only record; generation preserves reviewed prose. |
| `BPM090-M6-04` | Document policy and preference mappings. | Explain what BPM changes for each recommendation, including value, lock state, channel differences, and links to Firefox policy topics. | high | Generated examples and mapping tables agree with current CIS layers and pass fixture-based contract checks. |
| `BPM090-M6-05` | Document presets, layers, merge decisions, and source attribution. | Show how starter baselines and CIS layers combine, override, conflict, or surface manual-review decisions. | high | Users can trace each configured value to baseline, CIS, manual, imported, or raw source and understand conflict resolution. |
| `BPM090-M6-06` | Document manual review, exceptions, and verification. | Provide case-oriented steps for recommendations BPM cannot fully automate and for intentional deviations. | high | Every manual-review state has actionable verification and exception-recording guidance without claiming Firefox behavior BPM does not test. |
| `BPM090-M6-07` | Author end-to-end CIS workflows. | Cover create/apply, inspect in Guided and All Settings, resolve attention items, compare, export, and independently verify a hardened profile. | high | Level 1 and Level 2 representative workflows are reproducible against deterministic fixtures and link to all affected policy topics. |
| `BPM090-M6-08` | Integrate CIS docs with the CIS update runbook. | Make content, mappings, provenance, locales, examples, search, and screenshots part of benchmark updates. | high | A CIS refresh cannot pass focused checks while recommendation topics or mappings are stale. |
| `BPM090-M6-09` | Complete CIS accuracy and provenance review. | Cross-check all shipped guidance against registered benchmark sources and BPM implementation. | extra high | Version, level, mapping, manual-review, and source metadata are complete; prohibited benchmark text is absent. |

## Milestone 7: Existing-API Integration Guide

Goal: help external configuration, compliance, orchestration, inventory, and control products use
the API BPM already exposes, without inventing unsupported guarantees.

| ID | Task | Essence | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- |
| `BPM090-M7-01` | Define the integration-guide audience and supported patterns. | Frame integrations around profile synchronization, validation gates, policy import/export, compliance metadata, inventory, and health checks. | high | Supported and unsupported integration boundaries are explicit; no product-specific connector is claimed unless it exists. |
| `BPM090-M7-02` | Author API conventions and limitation topics. | Document base URLs, content types, OpenAPI discovery, identifiers, schemas, pagination/filtering/sorting, errors, lifecycle, and current security constraints. | high | Topics match the generated OpenAPI contract and clearly state absent authentication, rate-limit, idempotency, and optimistic-concurrency guarantees. |
| `BPM090-M7-03` | Author profile lifecycle integration tasks. | Cover list, statistics, read, create, update, archive, restore, permanent delete, and reset with safe sequencing. | high | Each current profile endpoint has request/response/error examples and destructive operations carry prominent warnings. |
| `BPM090-M7-04` | Author Firefox import/export integration tasks. | Cover JSON and multipart import, compliance metadata, schema selection, canonical export, download, pretty output, and normalization boundaries. | high | Examples execute against the API test app and resulting documents pass current schema validation. |
| `BPM090-M7-05` | Author validation-gate integration tasks. | Show how another product validates candidate `policies.json` documents per supported schema channel and handles structured errors. | high | Success, malformed input, unsupported channel, and policy validation failures have tested examples. |
| `BPM090-M7-06` | Author health and operational handshake topics. | Explain liveness/readiness consumption only to the degree needed by an integrating product. | medium | Examples match `/health` and `/health/ready`; the topic links to, but does not duplicate, the source-deployment Administrator Guide. |
| `BPM090-M7-07` | Add end-to-end control-product scenarios. | Document pull/compare/update, validate-before-apply, import-review-export, compliance scan handoff, and failure recovery using only existing APIs. | high | Each scenario is executable, names data ownership, avoids unsafe retry assumptions, and links to endpoint references. |
| `BPM090-M7-08` | Add reusable curl and Python examples. | Provide localized explanation around language-neutral, copyable requests and response assertions. | medium | Examples contain no secrets or environment-specific hosts and pass automated smoke tests against the current app. |
| `BPM090-M7-09` | Add OpenAPI-to-DITA drift checks. | Detect endpoint, model, parameter, status-code, and example changes that invalidate integration topics. | high | Focused documentation tests fail with the affected operation/topic IDs whenever the API contract changes. |

## Milestone 8: Six-Locale Content And Localized Screenshots

Goal: publish equivalent, reviewed guidance and UI illustrations for `en`, `ru`, `de`, `zh-CN`,
`fr`, and `es-ES`.

| ID | Task | Essence | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- |
| `BPM090-M8-01` | Define the DITA localization workflow. | Extend existing locale ownership, glossary, identifier, placeholder, and Mozilla terminology rules to topics, maps, keys, metadata, code, links, and search aliases. | high | The workflow identifies English source ownership, translation states, review gates, allowed technical English, and update propagation for all six locales. |
| `BPM090-M8-02` | Create locale-parallel maps and topic parity checks. | Keep localized maps and topics structurally and semantically equivalent while allowing language-specific phrasing and navigation labels. | high | Every English publishable topic, title, short description, prerequisite, step, warning, recovery note, example, alt text, keyword set, and navigation entry has a reviewed content-equivalent counterpart in all five localized trees. |
| `BPM090-M8-03` | Localize the complete User Guide. | Translate and review all task, concept, reference, and troubleshooting topics to full content parity, including topics previously created as compact locale peers. | high | All six User Guides build without fallback prose, reduced-summary locale topics, broken keys, placeholder drift, or unreviewed status; compact localized peers from earlier authoring tasks are expanded before release readiness. |
| `BPM090-M8-04` | Localize the Firefox Policy Guide. | Translate authored guidance while preserving policy IDs, JSON, version facts, and approved technical terminology. | high | Every policy topic exists in all six locales; schema-derived facts and examples remain byte/semantic equivalent where they must not be translated. |
| `BPM090-M8-05` | Localize the CIS Settings Guide. | Translate BPM-authored guidance without translating protected source text or changing recommendation identifiers and mappings. | high | All publishable CIS topics have six-locale parity, correct disclaimers, provenance, levels, mappings, and manual-review states. |
| `BPM090-M8-06` | Localize the API Integration Guide. | Translate explanations and navigation while preserving endpoint paths, field names, payloads, and executable examples. | high | All API topics have six-locale parity and the same contract-tested requests and response assertions. |
| `BPM090-M8-07` | Define the localized screenshot matrix and fixture state. | Map each illustrated user-guide function to a stable viewport, theme, schema, seed profile, UI state, locale, filename, caption, and DITA image key. | high | Every required illustration has six locale-specific capture rows; visible UI text may not reuse an image from another locale. |
| `BPM090-M8-08` | Automate deterministic screenshot capture. | Add a documentation-only browser harness that seeds data, selects locale/theme, waits for stable rendering, masks nondeterminism, and captures named assets. | extra high | Repeated captures are stable; failures name topic/locale/state; browser execution uses the dedicated escalated documentation UI command. |
| `BPM090-M8-09` | Capture user-guide screenshots for all six locales. | Produce optimized, reviewable images for every feature that the guide illustrates. | high | The complete matrix exists for `en`, `ru`, `de`, `zh-CN`, `fr`, and `es-ES`; each image shows the matching locale and current 0.9.0 UI. |
| `BPM090-M8-10` | Integrate screenshots, captions, and localized alt text into DITA. | Use stable keys so image replacement does not rewrite topics and accessibility text remains translatable. | high | Built pages resolve the correct locale image and reviewed alt text; missing, cross-locale, oversized, or orphaned images fail focused checks. |
| `BPM090-M8-11` | Run six-locale content and visual QA. | Check terminology, overflow, CJK rendering, captions, responsive images, theme contrast, screenshot freshness, and task accuracy. | extra high | Locale-specific audits pass at desktop and narrow widths; every deviation is fixed or explicitly approved before release. |

## Milestone 9: BPM Portal Integration And Contextual Navigation

Goal: serve the built portal safely and make it discoverable from the Profile Library and relevant
product contexts.

| ID | Task | Essence | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- |
| `BPM090-M9-01` | Add the product documentation runtime route. | Serve generated artifacts under `/help/` while preserving FastAPI OpenAPI `/docs` and `/openapi.json`. | high | `/help/{locale}/` serves only packaged documentation assets with correct MIME types, cache behavior, security headers, 404 handling, and no path traversal. |
| `BPM090-M9-02` | Add locale-aware documentation landing and routing. | Select the active BPM locale, preserve explicit locale choices, and route stable topic aliases safely. | high | All six locale roots work directly; unsupported locales follow the documented fallback; topic URLs remain bookmarkable and refresh-safe. |
| `BPM090-M9-03` | Add the Documentation link to the BPM header. | Provide a visible product-header link under the supported Firefox versions that opens the portal in the current locale. | medium | The visible, keyboard-accessible link exists in all six locales, opens documentation in a new tab with safe `noopener` behavior, preserves the active locale, and opens a working documentation landing page. |
| `BPM090-M9-04` | Wire the generated manifest into BPM. | Let the product resolve topics and anchors without embedding documentation prose or translated URLs in templates. | high | Missing/incompatible manifests fail safely; BPM validates manifest version and never emits a known-broken help link. |
| `BPM090-M9-05` | Add contextual help for the five product surfaces. | Link Library, Compare, Guided, All Settings, and JSON Editor to their primary case-oriented topics. | high | Each surface exposes a consistent localized help action whose target is validated in the manifest. |
| `BPM090-M9-06` | Add policy, CIS, validation, and import/export deep links. | Resolve stable UI targets to the most relevant reference or troubleshooting anchor. | high | Representative and generated target-contract tests cover every supported policy, CIS recommendation, and defined error/help target without orphan links. |
| `BPM090-M9-07` | Add portal empty, missing, stale, and build-mismatch states. | Make unavailable documentation diagnosable without breaking core profile workflows. | medium | Users receive localized recovery guidance; BPM remains usable if optional local docs are missing in a development environment; release packages treat missing docs as a build failure. |
| `BPM090-M9-08` | Verify accessibility, responsive behavior, CSP, and themes end to end. | Test navigation between BPM and generated documentation as one product experience. | extra high | Keyboard, focus, landmarks, headings, locale/theme transitions, desktop/narrow layouts, CSP, and security headers pass focused browser checks. |

## Milestone 10: Deterministic Smart Search Without AI

Goal: provide useful local search through deterministic indexing and ranking only.

| ID | Task | Essence | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- |
| `BPM090-M10-01` | Define search corpus and result contracts. | Index DITA-derived titles, short descriptions, headings, body text, keywords, policy IDs, aliases, API operations, CIS IDs, categories, and versions by locale. | high | The schema identifies source topic/anchor, locale, guide, channel, CIS level, and searchable fields; hidden/non-publishable content is excluded. |
| `BPM090-M10-02` | Implement deterministic per-locale index generation. | Build compact static indexes during publishing with no runtime network or external search service. | high | Clean builds produce reproducible indexes for all six locales; indexes contain only the matching locale plus allowlisted technical identifiers. |
| `BPM090-M10-03` | Implement locale-aware normalization and aliases. | Handle case, Unicode, punctuation, diacritics, CJK tokenization, policy IDs, endpoint paths, glossary synonyms, acronyms, and common UI terms. | extra high | A reviewed six-locale query fixture suite resolves equivalent user intents without translating identifiers or using an AI model. |
| `BPM090-M10-04` | Implement deterministic ranking and typo tolerance. | Prioritize exact IDs/titles, then aliases/headings/body; add bounded fuzzy matching with explainable scoring. | extra high | Ranking is stable, fast, testable, resistant to irrelevant fuzzy matches, and returns exact policy/CIS/API identifiers first. |
| `BPM090-M10-05` | Add search facets and filters. | Support guide family, Firefox channel, policy category, CIS level/control state, API area, and current locale. | high | Filters compose predictably, counts match the corpus, URLs can preserve search state, and empty-result recovery is localized. |
| `BPM090-M10-06` | Build the accessible search UI. | Add keyboard operation, highlighted snippets, result metadata, recent query state limited to the browser, and responsive layouts. | high | Search works without a mouse, does not inject indexed HTML, performs within the agreed offline budget, and exposes no telemetry by default. |
| `BPM090-M10-07` | Add search quality and performance fixtures. | Create representative exact, natural-language, typo, synonym, channel, CIS, API, CJK, no-result, and adversarial queries for each locale. | extra high | Quality thresholds, top-result expectations, index-size limits, and latency budgets pass deterministically on CI hardware. |
| `BPM090-M10-08` | Add search-index drift and integrity checks. | Detect missing topics, stale anchors, duplicate IDs, wrong locales, broken snippets, and schema/CIS/API inventory gaps. | high | Publishing and release checks fail with actionable topic/query IDs when the index diverges from manifests or source inventories. |
| `BPM090-M10-09` | Document the non-AI search boundary. | Make architecture and user copy accurately describe deterministic search and its privacy/offline properties. | medium | No UI or maintained documentation claims conversational answers, semantic embeddings, learning, or AI; future AI work remains a separately approved epic. |

## Milestone 11: Isolated Documentation Test And Debug Area

Goal: make documentation work cheap to understand and debug while keeping it a required part of
the full BPM release.

| ID | Task | Essence | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- |
| `BPM090-M11-01` | Create `documentation/tests/` with explicit suite boundaries. | Separate DITA, content, manifest, localization, screenshot, search, link, API-example, and portal integration tests from general `tests/`. | high | The directory has unit, contract, and browser groups plus compact fixtures; documentation-only failures do not require scanning the general BPM test tree. |
| `BPM090-M11-02` | Add focused documentation test commands. | Provide `make test-docs`, `make test-docs-contract`, and `make test-docs-ui` or equivalent stable targets. | medium | Each command selects only its documented area, prints useful progress, and can run from a clean checkout; browser commands are clearly marked for immediate sandbox escalation. |
| `BPM090-M11-03` | Add a documentation-only build-and-test fast loop. | Validate changed DITA/maps/assets and their directly affected locale/search outputs before the full corpus. | high | A one-topic change can be checked without rebuilding or running unrelated BPM code, while a full deterministic docs gate remains available. |
| `BPM090-M11-04` | Add isolated documentation coverage reporting. | Measure authored tooling and runtime bridge code separately from product application coverage. | high | Focused reports name uncovered documentation modules; covered documentation code reaches 100%, and no shortfall is accepted as known debt. |
| `BPM090-M11-05` | Add compact deterministic documentation fixtures. | Seed representative profile, policy, preference, CIS, API, locale, search, and screenshot states without using production databases or large corpora. | high | Fixtures are versioned, small, readable, reusable, and sufficient to reproduce every documentation test failure. |
| `BPM090-M11-06` | Add failure diagnostics and artifact retention. | Emit topic IDs, locale, guide, source line, target URL, query, screenshot state, and focused rerun command. | high | CI and local failures point directly to the smallest rerunnable documentation check; generated debug artifacts live outside maintained source. |
| `BPM090-M11-07` | Add a compact documentation subsystem snapshot. | Generate a bounded map of source, tooling, manifests, tests, and commands for future Codex sessions. | medium | The snapshot excludes generated pages, indexes, screenshot binaries, dependencies, and unrelated app modules and can be refreshed deterministically. |
| `BPM090-M11-08` | Integrate documentation gates into release tests. | Keep fast isolation for development while preventing `make test-release` from omitting the portal. | high | Release tests run full DITA validation, six-locale parity, content/manifest/search/API-example checks, and the required non-browser portal contracts. |
| `BPM090-M11-09` | Add dedicated browser smoke for portal and BPM links. | Cover Library entry, contextual links, locale, search, screenshots/assets, responsive layouts, and OpenAPI `/docs` preservation. | high | The focused docs browser suite passes in all six locales and runs through the immediate-escalation command without first attempting sandboxed Selenium. |
| `BPM090-M11-10` | Document the documentation-only debugging protocol. | Explain when to use focused source validation, contracts, screenshot capture, browser smoke, and full release gates. | low | Maintainers can diagnose documentation failures with bounded context and know exactly what remains unverified after each cheaper check. |

## Milestone 12: Administrator And DevOps Guide For Source Deployment And Integrations

Goal: document the currently supported administrator and DevOps path for deploying, operating,
updating, and integrating BPM from source before manual integrated documentation QA. This milestone
also re-homes API/integration guidance into the Administrator Guide, audits the User Guide for
API-adjacent content, and keeps end-user topics focused on UI workflows. Future packaged installer
and distribution-specific variants remain separate backlog work.

| ID | Task | Essence | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- |
| `BPM090-M12-01` | Redefine the Administrator Guide map, ownership, and migration scope. | Add a fifth guide family for administrator, DevOps, source-deployment, operations, update, and integration guidance; register stable keys/maps in all six locales; explicitly reserve packaged installer/distribution variants for later. | high | The map, keys, metadata, release contract, and guide descriptions distinguish Administrator/DevOps content from User Guide UI workflows, Firefox/CIS policy guidance, and deferred installer/distribution guidance. |
| `BPM090-M12-02` | Audit and re-home API/integration topics from user and API guides. | Inventory User Guide API-adjacent topics, existing API Integration Guide topics, fixtures, tests, and links; plan which content moves into Administrator Guide integration sections and which User Guide references remain as UI-oriented cross-links. | high | The audit names every affected topic/key/test, removes API procedure ownership from User Guide, preserves user-facing troubleshooting where appropriate, and defines redirects/cross-links so no integration procedure is lost. |
| `BPM090-M12-03` | Author Linux source deployment runbook topics. | Provide step-by-step prerequisites, repository checkout, Python environment, dependency setup, configuration, database/runtime choices, local service start, health/readiness verification, log inspection, and first administrative smoke checks for Linux. | high | A Linux administrator can deploy and verify BPM from source using only documented commands and supported repository scripts; unsafe production claims, unsupported daemonization promises, and hidden manual steps are absent. |
| `BPM090-M12-04` | Author Windows 10/11 source deployment through WSL runbook topics. | Provide step-by-step WSL prerequisites, supported Linux distribution assumptions, filesystem placement, repository checkout, Python/toolchain setup, networking/browser access, service start, health/readiness verification, log inspection, and WSL-specific troubleshooting. | high | A Windows 10/11 administrator can deploy BPM from source through WSL without native-Windows installation claims, path ambiguity, hidden networking caveats, or reduced locale coverage. |
| `BPM090-M12-05` | Document DevOps configuration, secrets, storage, and operational boundaries. | Explain environment variables/config files, local database/storage expectations, log locations, backup caveats, runtime user assumptions, network exposure boundaries, CORS/security limits, and what is not production-hardened yet. | extra high | The guide states current behavior accurately, avoids invented authentication/HA/reverse-proxy/secret-management guarantees, and links to health/readiness, API examples, and user-facing docs where appropriate. |
| `BPM090-M12-06` | Document product update-from-source and rollback procedures. | Provide a step-by-step update procedure for moving to a newer BPM source revision/version, including pre-update backup/export evidence, dependency refresh, database migration expectations, smoke checks, documentation portal rebuild checks, and rollback/stop conditions when safe rollback is not guaranteed. | extra high | The update runbook is explicit about what can be updated today, what must be backed up first, which commands/checks prove success, and which failures require stopping rather than inventing automatic rollback. |
| `BPM090-M12-07` | Move API operation reference and conventions into Administrator Guide integration sections. | Re-home existing API audience, conventions, limitations, profile lifecycle, Firefox import/export, validation-gate, and health/readiness content under Administrator Guide integration/DevOps IA while preserving tested examples and endpoint references. | high | Administrator Guide contains the maintained API integration corpus; the old API guide either becomes a thin redirect/landing map or is removed according to the guide-map contract, and all source links/keyrefs remain valid. |
| `BPM090-M12-08` | Author DevOps integration runbooks for external control products. | Provide step-by-step workflows for pull/list/read, compare/update with `expected_revision`, validate-before-apply, import-review-export, compliance metadata handoff, health-gated startup, failure recovery, and audit evidence using only existing BPM APIs. | high | Each workflow is executable against the API test app, names data ownership, records audit/retry decisions, avoids unsafe retry/transaction assumptions, and links to the endpoint/topic references now owned by Administrator Guide. |
| `BPM090-M12-09` | Add reusable DevOps examples and environment templates. | Provide language-neutral curl examples, compact Python examples, environment-variable setup, JSON/multipart samples, health/readiness probes, validation/import/export/profile lifecycle snippets, and response assertions without secrets or environment-specific hosts. | high | Examples run in focused smoke tests, contain no credentials, use placeholders consistently, and remain synchronized with OpenAPI, product API tests, and DITA topics. |
| `BPM090-M12-10` | Add administrator/DevOps troubleshooting and diagnostics topics. | Document step-by-step diagnosis for failed startup, unreachable probes, schema/cache problems, API validation errors, import/export failures, database/storage issues, WSL networking issues, stale dependencies, and documentation portal build/link failures. | high | Troubleshooting topics preserve user data, avoid editing generated artifacts or database rows as routine recovery, point to focused rerun commands, and separate product defects from deployment/operator actions. |
| `BPM090-M12-11` | Document production-readiness, HA, and reverse-proxy boundaries. | Explain what administrators and DevOps can safely do today from source, what checks/configuration decisions they can prepare now, what is planned but not implemented yet, and which production/HA/reverse-proxy capabilities remain unsupported until distribution/runtime decisions exist. | extra high | The guide contains practical step-by-step current-state preparation for single-node source operation, network exposure review, health/readiness checks, backup/export evidence, proxy-readiness questions, monitoring inputs, and update windows, while explicitly marking absent items such as packaged services, TLS/proxy recipes, supported HA clustering, rolling upgrades, managed secrets, production hardening, and official restore automation. |
| `BPM090-M12-12` | Add Administrator Guide validation fixtures and contracts. | Create compact checks for commands, paths, config names, environment variables, health endpoints, update steps, integration examples, migrated API topics, production-readiness boundaries, guide maps, locale peers, WSL caveats, and deferred installer/HA/reverse-proxy warnings. | high | Focused docs contracts fail on stale commands, broken health/API examples, missing migration links, missing locale peers, missing WSL caveats, or accidental claims that packaged installers, supported HA, official reverse-proxy recipes, or production hardening exist. |
| `BPM090-M12-13` | Localize and review the Administrator/DevOps Guide. | Bring all administrator, DevOps, source-deployment, update, troubleshooting, integration, and production-readiness boundary topics to full six-locale parity while preserving command names, paths, environment variables, URLs, API names, and WSL terminology. | high | All six localized Administrator Guides build without fallback prose or reduced summaries; technical identifiers remain stable and reviewed, and moved API/integration/production-boundary content has no shorter localized variants. |

## Milestone 13: Manual Product Documentation QA

Goal: manually verify the integrated documentation product after the BPM header link opens
the portal in a new tab, and correct discovered issues before final automated release gates,
commits, or push handoff.

| ID | Task | Essence | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- |
| `BPM090-M13-01` | Run manual QA through the Library documentation button. | Open documentation from the Profile Library in a new tab and manually exercise the implemented portal, navigation, search, localized content, screenshots, Administrator/DevOps Guide source-deployment, update, integration, and troubleshooting paths, contextual links, and product-to-docs flow before final tests, commit creation, and push handoff. | extra high | A maintainer-readable QA record covers all six locales, the new-tab behavior, key user journeys, search, guide switching, screenshots, source deployment on Linux and Windows 10/11 through WSL, update-from-source, DevOps/API integration paths, policy/CIS references, and OpenAPI `/docs` preservation; every discovered defect is fixed or explicitly approved before the final quality milestone starts. |

## Milestone 14: Final Quality, Release Documentation, And Handoff

Goal: prove the 0.9.0 documentation product is complete, accurate, maintainable, and releasable.

| ID | Task | Essence | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- |
| `BPM090-M14-01` | Run static typing. | Execute `make typecheck` after manual documentation QA and any required corrections are complete. | low | Mypy passes with no new suppressions hiding documentation defects. |
| `BPM090-M14-02` | Run lint. | Execute `make lint` across maintained product and documentation tooling sources. | low | Ruff passes and generated/vendor output is excluded by explicit ownership rules rather than ad hoc cleanup. |
| `BPM090-M14-03` | Run the complete pytest suite. | Execute `pytest -q` after focused documentation suites pass. | medium | The complete non-browser/non-live default suite passes with no unreviewed skips or xfails added for the epic. |
| `BPM090-M14-04` | Run full code-surface coverage. | Execute `make coverage` and inspect application plus documentation-owned code reports. | high | Covered code surface is 100%; falling below 100% is not accepted as known debt—add focused tests, remove dead code, or eliminate unreachable paths. |
| `BPM090-M14-05` | Run full DITA, locale, content, and search release validation. | Execute the complete documentation build and non-browser release gates from a clean output tree. | high | Five guides and six locales build; manifests, links, examples, screenshots, indexes, provenance, accessibility checks, and parity gates pass. |
| `BPM090-M14-06` | Run Chromium/Selenium BPM and documentation smoke. | Execute `make test-ui` and the dedicated documentation browser suite with immediate sandbox escalation. | high | Core BPM product logic, Library documentation entry, contextual help, six-locale portal navigation, search, responsive layout, CSP, and `/docs` OpenAPI coexistence pass; no sandboxed trial run occurs first. |
| `BPM090-M14-07` | Complete the 0.9.0 content coverage audit. | Reconcile final product, Administrator/DevOps source deployment, update, API/integration, production-readiness boundaries, Firefox schema, CIS, locale, screenshot, manifest, and search inventories. | extra high | Every shipped user capability, source-deployment admin path, update procedure, DevOps integration path, production-readiness boundary, API operation, supported policy, CIS recommendation, locale, and required screenshot is covered or blocks release. |
| `BPM090-M14-08` | Refresh README for the implemented 0.9.0 product. | Describe the actual portal, `/help/`, five guides, six locales, deterministic search, Administrator/DevOps source-deployment and integration docs, focused documentation commands, build prerequisites, and non-AI boundary. | medium | README matches the finished product, preserves maintainer copyright and email-topic/message-theme information, and removes stale documentation-roadmap wording. |
| `BPM090-M14-09` | Finalize the 0.9.0 changelog entry. | Record shipped documentation behavior, Administrator/DevOps source deployment, update and integration guidance, localization, search, UI links, testing boundary, and known non-goals. | low | The 0.9.0 entry is complete and all prior release history remains unchanged. |
| `BPM090-M14-10` | Update maintained runbooks and docs index. | Register final architecture/runbook files and add documentation drift gates to schema, CIS, locale, administrator deployment, DevOps integration, update, and release procedures. | medium | `docs/docs-index.md` lists every maintained file exactly once with correct status; generated product docs and local artifacts remain excluded. |
| `BPM090-M14-11` | Verify clean build and package contents. | Build the release from a clean checkout/output state and inspect included docs, manifests, indexes, locales, screenshots, licenses, and exclusions. | extra high | The package works offline, contains no caches/debug artifacts/unlicensed source material, and cannot ship stale or missing documentation. |
| `BPM090-M14-12` | Create the completed epic commit. | Commit only the approved 0.9.0 documentation epic and necessary integration changes after all gates pass. | medium | The commit is reviewable, excludes unrelated dirty-worktree changes and generated local artifacts, and records final verification results. |
| `BPM090-M14-13` | Provide the maintainer-run push command. | Do not push from backlog execution. | low | The final report prints the exact `git push` command for the maintainer to run manually. |

## Suggested Execution Order

1. Transition release anchors and freeze coverage inventories.
2. Decide ownership, DITA toolchain, IDs, manifests, provenance, accessibility, and security.
3. Establish the isolated documentation tree and deterministic DITA publishing foundation.
4. Author and close English coverage for the User, Firefox Policy, CIS Settings, and API
   Integration guides.
5. Localize the initial four user/policy/CIS/API guides and produce the complete locale-specific
   screenshot matrix.
6. Serve the portal under `/help/`, add the BPM header documentation link, then add validated contextual links.
7. Build deterministic locale-aware smart search without AI.
8. Finish the isolated documentation test/debug loop and connect it to release gates.
9. Add and localize the Administrator/DevOps Guide for source deployment on Linux and Windows 10/11
   through WSL, source-based updates, troubleshooting, and API/integration operation.
10. Manually verify the integrated product documentation through the Library new-tab button and
    correct any discovered issues.
11. Run final quality, coverage, browser, package, README, changelog, commit, and handoff tasks.

## Execution Progress

- [x] `BPM090-M1-01` — completed on 2026-06-20. Package metadata, runtime-derived version,
  active README/changelog/index/system-map anchors, and version contract tests now agree on
  `0.9.0`; retained `0.8.8` references are explicit completed-release or historical context.
- [x] `BPM090-M1-02` — completed on 2026-06-20. README identifies 0.9.0 as the active product
  documentation target, labels the portal as not yet shipped, retains the verified 0.8.8 product
  baseline, and reserves the final summary for behavior and commands verified after implementation.
- [x] `BPM090-M1-03` — completed on 2026-06-20. The top changelog entry is explicitly marked
  in progress, records only completed and verified 0.9.0 work, reserves the final portal summary
  for release validation, and preserves the previous release history unchanged.
- [x] `BPM090-M1-04` — completed on 2026-06-20. The bounded active/runbook release-naming audit
  found one required follow-up:
  - `docs/architecture/all-settings-current-contracts.md` is still indexed as `active` even though
    it is a pre-0.8.8 implementation map and still describes the completed refactor in future tense;
    refresh it as a current contract or reclassify/archive it together with its docs-index row.
  - No stale 0.8.8 current-target wording remains in `docs/architecture/current-system-map.md`,
    active runbooks, or `docs/docs-manifest.json`.
  - `docs/architecture/all-settings-single-surface-decision.md`, the 0.8.8 backlog, changelog
    history, and docs-index descriptions of 0.8.8 artifacts are intentional decision/history
    context and are excluded from version replacement; `docs/archive/` and audit-status files were
    excluded from the audit by definition.
- [x] `BPM090-M1-05` — completed on 2026-06-20. The maintained 0.9.0 product documentation release
  contract defines 14 blocking gates with a project-maintainer functional owner, required evidence,
  stable current or planned verification commands, explicit gate state, closure/reopening rules,
  the six-locale and no-AI boundaries, and outcomes deferred from this epic.
- [x] `BPM090-M2-01` — completed on 2026-06-20. The maintained user-capability inventory maps 106
  current user-visible capabilities across the global shell, Library, Compare, Guided, All
  Settings, JSON, Firefox/CIS boundaries, and recovery states to 89 planned locale-independent DITA
  topic IDs; a closure matrix covers every README `Main Capabilities` bullet and all five product
  routes while leaving API, per-policy, and per-CIS detail to their dedicated inventory tasks.
- [x] `BPM090-M2-02` — completed on 2026-06-21. The maintained API documentation inventory maps all
  15 programmatic/service OpenAPI operations to 13 planned DITA topics, classifies all six OpenAPI
  HTML routes outside the integration contract, records query/model/error contracts and current
  limitations, and identifies generated, schema-excluded, compatibility, opaque, and internal
  surfaces; a drift test compares the inventory directly with `create_app().openapi()`.
- [x] `BPM090-M2-03` — completed on 2026-06-21. The maintained Firefox documentation inventory maps
  all 120 supported policy IDs to stable logical doc IDs, per-channel schema/version fingerprints
  and UI support metadata; flags eight Release-only policies and no changed common definitions;
  maps all 62 known managed preferences and raw/fallback boundaries; and includes a deterministic
  builder plus drift test against both active schemas, the UI registry, and preference catalog.
- [x] `BPM090-M2-04` — completed on 2026-06-21. The maintained CIS documentation inventory maps all
  55 shipped recommendations to unique provenance records, 53 supported mappings to planned DITA
  topic IDs and Firefox documentation targets, and the two unsupported/unresolved records to an
  explicit non-publishable provenance disposition; it also inventories source/license boundaries,
  both levels/channels, four generated layers, five starters, merge rules, nine manual-review paths,
  and the absent persisted exception model through a deterministic builder and drift test.
- [x] `BPM090-M2-05` — completed on 2026-06-21. The accepted ownership decision isolates product
  documentation under a future top-level `documentation/` subsystem, defines reviewed DITA/locales/
  screenshots versus generated artifact ownership, enforces one-way build and artifact-only runtime
  dependencies, bounds the future `/help/` bridge and BPM touch points, assigns focused test/debug
  contexts and commands, and preserves offline, provenance, six-locale, non-AI, packaging, and
  extraction-readiness constraints without scaffolding or implementing the subsystem early.
- [x] `BPM090-M2-06` — completed on 2026-06-21. The accepted publishing decision pins DITA-OT 4.4,
  Eclipse Temurin JRE 21.0.11+10, DITA 1.3, bundled HTML5, and a versioned first-party customization;
  excludes floating/system/container-only and third-party plug-in dependencies; and defines the
  checksum lock, offline bootstrap/build, license inventory, deterministic local/CI output, six-
  locale matrix, accessibility responsibilities, and controlled update gates to implement in M3.
- [x] `BPM090-M2-07` — completed on 2026-06-21. The accepted identity decision separates immutable
  locale-independent topic/anchor/key/target/asset IDs from translated titles, case-fold-safe source
  slugs, and explicit lowercase canonical paths; adopts the inventoried user, Firefox policy and
  preference, CIS, API, and capability identities; defines `/help/{locale}/...`, screenshot parity,
  one-hop aliases, anchor compatibility, honest tombstones, and validation/change-review rules.
- [x] `BPM090-M2-08` — completed on 2026-06-21. Draft 2020-12 manifest and UI-target-map v1 schemas,
  valid architecture examples, and semantic contract tests now define artifact/build identity, all
  four guides and six locales, topic/key/anchor/output registries, localized assets and search files,
  aliases/tombstones, all approved BPM target namespaces, strict duplicate-key rejection, inventory
  alignment, cross-document reference integrity, version compatibility, and atomic fail-closed use.
- [x] `BPM090-M2-09` — completed on 2026-06-21. The approved machine-readable provenance matrix and
  review assign source/license/reuse/attribution/forbidden-use/update ownership for every guide;
  prefer BPM-original prose and synthetic examples; retain Mozilla MPL and trademark boundaries;
  keep MDN, unclassified web, and vendor content link-only; block CIS PDF/source expression without
  scoped rights approval while allowing attributed original BPM mapping guidance; and make all six
  human-reviewed, non-AI locales and generated outputs inherit the complete provenance record.
- [x] `BPM090-M2-10` — completed on 2026-06-21. The accepted WCAG 2.2 AA and security contract now
  covers six-locale semantics, keyboard/focus, contrast/reflow/motion, localized images/tables/code,
  navigation/search/errors, DITA and post-build HTML allowlists, safe bounded DOM search, inert
  examples, path/hash/MIME-safe static assets, a strict route-specific `/help/` CSP, response headers,
  deployment-only HSTS, layered automated/manual evidence, and explicit release blockers.
- [x] `BPM090-M3-01` — completed on 2026-06-21. The top-level `documentation/` scaffold now separates
  six hand-authored locale DITA trees, shared metadata, generator-owned source, six localized
  screenshot trees, configuration, compact fixtures, documentation-only tools, and isolated unit/
  contract/browser tests; local build/reports/cache/toolchain/dependency output is ignored from Git
  and normal scans, runtime packaging remains `app*`-only, and later maps/tools/dependencies/routes
  are explicitly deferred to their approved tasks.
- [x] `BPM090-M3-02` — completed on 2026-06-21. `documentation/AGENTS.md` and the maintained compact
  workspace snapshot now provide ordered local entry points, task-to-context routing, strict narrow-
  read and generated/source/provenance rules, actual-versus-planned focused commands, mandatory
  snapshot maintenance, browser/screenshot immediate-escalation guidance, and an explicit current
  state that lets documentation work start without reading unrelated BPM or general test modules.
- [x] `BPM090-M3-03` — completed on 2026-06-22. The documentation-only bootstrap now pins and
  verifies official DITA-OT 4.4 and Eclipse Temurin JRE 21.0.11+10 Linux x86_64 archives by upstream
  SHA-256, installs an exact isolated Python test stack, preserves all state below the ignored local
  cache, rejects unsupported platforms and unsafe archives, verifies tool versions, and runs a DITA
  1.3 HTML5 smoke build; networked clean setup and a fully offline cache replay both pass, with
  dependency licenses and the reserved first-party plug-in boundary recorded.
- [x] `BPM090-M3-04` — completed on 2026-06-22. All six locale trees now contain separate DITA 1.3
  maps for the User, Firefox Policy, CIS Settings, and API Integration guides plus a localized
  stable-order portal aggregate; immutable map IDs and filenames remain locale-independent, every
  aggregate resolves exactly the four local guide maps, structural parity and DITA-only source
  contracts pass, and each guide map plus every locale aggregate builds with the locked offline
  DITA-OT toolchain without introducing topics, keys, or publishing commands ahead of their tasks.
- [x] `BPM090-M3-05` — completed on 2026-06-22. Locale key maps now expose stable `guide.*`
  identities and reuse one DITA 1.3 subject scheme; fixed audience, platform, BPM version, locale,
  Firefox channel, and CIS-level values are enumerated, while grouped policy, CIS recommendation,
  and API-operation identities are validated against the maintained 120/55/15-record inventories.
  Unknown fixed or dynamic metadata fails with source context, all maps load the shared scheme
  without cycles, and real DITAVAL builds prove that Release/ESR and locale branches can be selected
  independently from one source topic without copied content.
- [x] `BPM090-M3-06` — completed on 2026-06-22. Stable offline `docs-validate`, `docs-build`, and
  `docs-reproducibility-check` commands now validate metadata, well-formed and DITA-OT-validated XML,
  keys, local source links/fragments, generated relative links/fragments, six locale entry points,
  and absolute workspace-path absence; all transforms use the locked toolchain with explicit
  locale, encoding, timezone, temporary, and output inputs. Local publication replaces the ignored
  `documentation/build/site` tree atomically after full validation, malformed XML and broken
  references fail with file-level diagnostics, and two clean six-locale builds produced identical
  SHA-256 values for all 18 current publishable files.
- [x] `BPM090-M3-07` — completed on 2026-06-26. `artifact-policy.json`, `docs-package`, and
  `docs-package-verify` now define committed/ignored/built/shipped output rules, keep
  `documentation/dist/` ignored, build a normalized deterministic tar.gz plus checksum, include
  license notices and an artifact-integrity manifest, and delete stale archive/checksum files before
  validation so failed packages cannot be served. Packaging runs DITA-OT against staged source copies
  and rejects maintained-source mutation; two consecutive package builds verified the same SHA-256
  `681e752c0045cdc3cfc036a805fab94bd098238d938c9888d9bf1c66888652f9`. Runtime delivery remains
  blocked with `runtime_ready=false` until `/help/` extraction/activation and final entry-flow
  checks are implemented.
- [x] `BPM090-M3-08` — completed on 2026-06-26. The DITA build now wraps every generated locale page
  in a deterministic accessible portal shell with skip link, `main#main-content`, distinct
  navigation landmarks, breadcrumbs, guide switcher, locale switcher, BPM/documentation version
  context, and exact route-locale `html lang` values. First-party CSS under
  `documentation/assets/theme/` provides responsive 320px reflow, dark/light and forced-colors
  modes, reduced-motion behavior, visible focus, code/table/note styling, and print output without
  JavaScript, inline styles, remote assets, or runtime BPM dependencies; static validation rejects
  active content and shell regressions across all six locales.
- [x] `BPM090-M3-09` — completed on 2026-06-27. The build now generates schema-valid
  `manifest.json` and `ui-target-map.json` from the current guide maps and artifact files rather
  than duplicating navigation by hand: all six locales, four guide landing topics, stable `a-*`
  anchors, `topic:*` UI targets, source revision, deterministic build SHA-256, target-map digest,
  output paths, and initial search-index files are recorded and semantically validated; `BPM090-M10-02`
  later replaced those placeholder files with real per-locale static indexes.
  Package verification now requires the manifest/target-map/search files and checks their hashes;
  `runtime_ready` remains false until `/help/` extraction/activation and final entry-flow checks are
  implemented.
- [x] `BPM090-M3-10` — completed on 2026-06-27. Maintainer runbooks under
  `documentation/runbooks/` now document one-topic authoring, DITA reuse, localization, screenshots,
  Firefox/CIS/API inventory refresh, link/key/anchor/manifest changes, review, and publishing with
  focused commands before broader release suites. The local context guide routes topic, locale,
  inventory, screenshot, manifest, and publishing work to those runbooks so future documentation
  tasks can change one small area without scanning unrelated BPM code or generated artifacts.
- [x] `BPM090-M4-01` — completed on 2026-06-27. `user-guide-map-0.9.0.json` now turns the capability
  inventory into eight case-oriented user-intent sections and maps all 106 inventoried capabilities
  to the 89 planned primary User Guide topic paths without organizing the guide by UI module or
  source ownership. All six localized `user-guide.ditamap` files expose the same intent-section
  structure with localized navigation labels while leaving product topic authoring to the following
  M4 tasks.
- [x] `BPM090-M4-02` — completed on 2026-06-27. The User Guide now has localized DITA core-concept
  topics for profile lifecycle, choosing among Library/Guided Editor/All Settings/JSON
  Editor/Compare, Firefox Release versus ESR schema validation, policies versus managed
  preferences, and starter presets/CIS layers. The topics are keyed and reachable from all six
  localized User Guide maps, avoid administrator/distribution content, and the build now
  normalizes DITA-OT locale-root links created by the first real topic outputs.
- [x] `BPM090-M4-03` — completed on 2026-06-27. The User Guide now has localized DITA Profile
  Library management topics for create/open, Library orientation, search, filtering, sorting,
  refresh/status handling, row-state reference, duplicate naming, archive, restore, permanent
  delete, archived-profile behavior, and Library operation recovery. These topics are keyed and
  reachable in all six localized maps with prerequisites, actions, expected results, warnings,
  recovery notes, and related links; import/export and Compare remain deferred to M4-04/M4-05.
- [x] `BPM090-M4-04` — completed on 2026-06-27. The User Guide now has localized DITA import/export
  task topics for Firefox Enterprise `policies.json`, covering Library UI handoff, JSON and
  multipart API-adjacent import shapes, schema-channel selection, validation/error recovery,
  canonical export output, `download`/`pretty`/`indent` options, archived-profile export boundaries,
  and the difference between BPM's normalized profile model and Firefox boundary documents. Compact
  synthetic fixtures under `documentation/fixtures/import-export/` validate the documented shapes.
- [x] `BPM090-M4-05` — completed on 2026-06-27. The User Guide now has localized DITA Profile
  Comparison topics covering the Library new-tab handoff, read-only comparison workflow,
  independent Profile A/Profile B search and selection, selected-profile summaries, policy versus
  managed-preference row types, and equal/changed/missing comparison states. The topics are keyed
  and reachable from all six localized maps and validated against the comparison capability rows.
- [x] `BPM090-M4-06` — completed on 2026-06-27. The User Guide now has localized DITA Guided
  Editor topics covering profile identity and schema channel, Guided scenarios, starter presets,
  CIS layers, all six Guided steps, Guided search, browser/default/home/search/navigation,
  security/privacy, users/add-ons/sites, existing Firefox browser AI-policy settings, Release/ESR
  schema-dependent availability, fine-tuning, review, save, and download. The topics are keyed and
  reachable from all six localized maps. The Firefox AI/smart-feature product step remains in
  scope and must explain Release-only support and ESR absence where applicable; only AI
  functionality inside the documentation product itself, such as RAG, embeddings, generative search,
  and generative answers, remains out of scope for 0.9.0.
- [x] `BPM090-M8-01` — completed on 2026-06-29. The localization/screenshot runbook now defines
  English source ownership, translation states (`source-draft`, `source-reviewed`,
  `localization-needed`, `localized-draft`, `localized-reviewed`, and `blocked-source`), structure,
  terminology, placeholder, provenance, example, screenshot, and search review gates, allowed
  technical English, and six-locale update propagation for topics, maps, keys, metadata,
  code/examples, links, captions, alt text, and search aliases. The provenance policy now permits
  AI-assisted drafting/localization during development only after human review and blocks
  unreviewed machine output from shipped documentation.
- [x] `BPM090-M8-02` — completed early on 2026-06-27 for the currently authored User Guide corpus.
  A locale-parity contract now requires every existing User Guide topic to have the same locale
  file set, DITA topic type, metadata, task step shape, warning placement, reference/concept section
  anchors, and related-link structure across `en`, `ru`, `de`, `zh-CN`, `fr`, and `es-ES`, while
  rejecting compact Guided stubs and English-source fallback phrasing.
- [x] `BPM090-M8-03` — completed on 2026-06-28 for the full User Guide M4 corpus. All 89 planned
  User Guide topics now exist in full-content parity across `en`, `ru`, `de`, `zh-CN`, `fr`, and
  `es-ES`, including core, Library, import/export, comparison, Guided, All Settings, JSON,
  schema-validation, cross-cutting, troubleshooting, and coverage-closure topics.
- [x] `BPM090-M8-04` — completed on 2026-06-29. The authored Firefox Policy Guide topics now have
  a focused six-locale parity contract proving full localized peers across `en`, `ru`, `de`,
  `zh-CN`, `fr`, and `es-ES`: file sets, DITA metadata, section/step shape, warnings, related
  links, code/JSON/policy identifiers, and localized titles/prose must match the English source
  semantically without compact summaries or English fallback. The generated 120 policy skeletons
  remain language-neutral schema facts with byte-stable policy IDs, JSON examples, version/channel
  facts, Mozilla provenance, and examples that must not be translated.
- [x] `BPM090-M8-05` — completed on 2026-06-29. The authored CIS Settings Guide topics now have a
  focused six-locale parity contract proving full localized peers across `en`, `ru`, `de`,
  `zh-CN`, `fr`, and `es-ES`: file sets, DITA metadata, section/step shape, warning notes,
  related links, technical identifiers, CIS levels/layers, policy/preference targets, workflow IDs,
  and localized titles/prose must match the English source semantically without compact summaries
  or English fallback. The generated 53 CIS recommendation skeletons remain language-neutral
  mapping/provenance facts and must not be replaced by compact localized copies.
- [x] `BPM090-M8-06` — completed on 2026-06-29. The authored API Integration Guide topics now have
  a focused six-locale parity contract proving full localized peers across `en`, `ru`, `de`,
  `zh-CN`, `fr`, and `es-ES`: file sets, DITA metadata, section/step shape, warning notes,
  related links, endpoint paths, HTTP verbs, field names, API IDs, OpenAPI-facing model names,
  payload/code examples, scenario IDs, and reusable curl/Python examples must preserve the same
  contract-tested requests and response assertions without compact summaries or English fallback.
- [x] `BPM090-M9-01` — completed on 2026-06-29. BPM now includes an `app/documentation/` runtime
  bridge that serves an installed static documentation artifact under `/help/` while preserving
  FastAPI `/docs` and `/openapi.json`. Focused app contracts cover `/help/{locale}/`, manifest,
  target-map, and search asset serving; MIME allowlists; cache behavior; route-specific security
  headers; safe 503 missing-artifact responses; 404 missing-locale/asset responses; path traversal
  rejection; and exclusion from OpenAPI.
- [x] `BPM090-M9-02` — completed on 2026-06-29. The `/help/` runtime bridge now selects the active
  documentation locale from explicit query parameters, BPM locale cookies, and `Accept-Language`,
  preserves direct six-locale roots, redirects unsupported locales to the documented fallback, and
  resolves manifest-backed topic and alias URLs to packaged HTML targets without exposing `/help/`
  in OpenAPI.
- [x] `BPM090-M9-03` — completed on 2026-06-29. BPM now exposes a visible localized documentation
  link in the shared product header under the supported Firefox versions. The link targets
  the active-locale documentation landing page, opens in a new tab with `noopener noreferrer`,
  updates when the user switches UI locale, and is styled as a responsive accessible header
  affordance rather than a workflow button.
- [x] `BPM090-M9-04` — completed on 2026-06-29. BPM now validates the packaged documentation
  `manifest.json` and `ui-target-map.json` before activating documentation URLs: schema versions,
  BPM version, exact six-locale matrix, target-map digest, topic outputs, target IDs, and anchors
  must agree. The shared header link is resolved from the manifest-backed `topic:user-guide` target
  for every locale and is omitted instead of emitting a known-broken href when the artifact is
  missing or incompatible.
- [x] `BPM090-M9-05` — completed on 2026-06-29. Library, Compare, Guided Editor, All Settings, and
  JSON Editor now expose a compact localized “Help for this section” action near the surface
  heading. Each action is resolved from the validated manifest/target-map to the relevant
  case-oriented User Guide topic (`ug-task-use-profile-library`, `ug-task-compare-profiles`,
  `ug-task-use-guided-editor`, `ug-task-use-all-settings`, or `ug-task-use-json-editor`), opens in a
  new tab, follows active locale switches, and is omitted if the documentation artifact or target is
  not valid.
- [x] `BPM090-M9-06` — completed on 2026-06-29. BPM now exposes manifest-backed contextual help
  icons as a circled `i` for policy, CIS, validation, import, and export contexts. The icons render
  localized `title`/`aria-label` tooltips, open the resolved help page in a new tab, follow active
  locale switches, and are omitted if the installed documentation artifact cannot resolve the target.
  Current links cover Firefox AI policy controls (`policy:AIControls`), Visual Search
  (`policy:VisualSearchEnabled`), CIS baseline selection via representative CIS target
  `cis:1.1.1.1`, profile validation, Firefox `policies.json` import, and Firefox `policies.json`
  export.
- [x] `BPM090-M9-07` — completed on 2026-06-29. The `/help/` route now distinguishes missing,
  stale version, incompatible manifest/target-map, incomplete locale-root, and not-found page states.
  Human-facing `/help/` and `/help/{locale}/...html` failures return localized HTML recovery pages
  with the same hardened documentation response headers and a link back to the BPM Profile Library,
  while manifest, target-map, search, and other asset requests remain strict machine-readable
  503/404 responses. OpenAPI `/docs` and `/openapi.json` remain unaffected.
- [x] `BPM090-M9-08` — completed on 2026-06-29. Focused integration contracts now verify the served
  `/help/` experience across successful documentation pages, topic pages, localized not-found pages,
  and preserved FastAPI `/docs`: strict route-specific CSP and security headers, viewport metadata,
  locale `lang`, skip links, navigation landmarks, main landmarks, headings, keyboard-focusable
  main regions, status semantics, theme markers, and absence of inline scripts/styles/event handlers.
  Browser/Selenium evidence remains scheduled for the later dedicated documentation browser suite and
  final release gates.
- [x] `BPM090-M10-01` — completed on 2026-06-29. The accepted search corpus/result contract now
  defines deterministic local static search for all six locales without AI, RAG, embeddings,
  generative answers, runtime network search services, telemetry learning, or personalization. The
  contract covers DITA-derived titles, short descriptions, headings, body text, keywords,
  identifiers, aliases, policy IDs, API operations, CIS IDs, guide/channel/category/CIS/API/version
  facets, source topic/anchor fields, result snippets, score-breakdown fields, strict exclusions for
  hidden, wrong-locale, restricted-source, provenance-only, and private runtime content, plus
  integrity requirements. The contract is now consumed by the real per-locale indexes from
  `BPM090-M10-02`.
- [x] `BPM090-M10-02` — completed on 2026-06-29. Publishing now generates ready deterministic
  per-locale static search indexes instead of placeholders. Each locale index contains one document
  per manifest topic, DITA-derived localized title, short description, headings, body, keywords,
  stable source topic/output metadata, guide/topic facets, source revision/version data, and only
  allowlisted language-neutral technical identifiers from the manifest target map for policy, CIS,
  API, capability, topic, guide, and anchor IDs. Manifest and package validation now reject stale
  hashes, count mismatches, non-ready indexes, wrong-locale URLs/outputs, unknown topics, duplicate
  document IDs, incomplete searchable fields, invalid facets, and broken source mappings; clean
  publish trees reproduce byte-identical search JSON.
- [x] `BPM090-M10-03` — completed on 2026-06-29. Search generation now applies a reviewed
  locale-aware normalization and alias contract for all six locales: NFKC Unicode normalization,
  case folding, Latin-diacritic stripping without damaging Cyrillic, deterministic punctuation
  splitting, CJK full-run/unigram/bigram tokenization, endpoint/path and technical-identifier
  preservation, and no identifier translation. The generated indexes include normalized tokens,
  field-level token groups, reviewed alias IDs/terms for Profile Library, Firefox AI controls,
  API validation, CIS baseline selection, and `policies.json` import/export, plus per-locale query
  fixtures. Manifest and package validation now reject wrong normalization contracts, broken
  fixture tokens, unresolved expected aliases, unknown alias groups, and malformed normalized fields.
- [x] `BPM090-M10-04` — completed on 2026-06-29. Search generation now includes a deterministic
  ranking and bounded typo-tolerance contract with explainable score components for exact
  identifiers, titles, aliases, headings, body matches, bounded typo matches, and a zero-weight
  reserved recency field. Exact policy/CIS/API identifiers outrank ordinary text and are validated
  by fixtures; title and alias fixtures verify stable ordering for task/reference topics; bounded
  Levenshtein typo matching is limited by token length, skips endpoint paths and technical
  identifiers, searches only title/alias/heading fields, and records matched tokens/distances.
  Manifest and package validation now reject wrong ranking contracts, broken fixture top results,
  missing required score components, stale ranking fixture output, and malformed score metadata.
- [x] `BPM090-M10-05` — completed on 2026-06-30. Search generation now includes a deterministic
  facets/filters contract without AI, RAG, embeddings, or generative answers. Per-locale indexes
  expose filter facets for current locale, guide family, DITA topic kind, Firefox channel, Firefox
  policy category, CIS level/control state, API area, and BPM version; counts are derived from the
  generated corpus, filters compose as AND across fields and OR within a field, selected filters are
  serialized into stable URL query parameters, and empty-result recovery messages are localized for
  all six locales. Manifest/package validation now rejects undeclared facet values, stale counts,
  broken filter fixture results, missing expected topics, and empty states without localized copy.
- [x] `BPM090-M10-06` — completed on 2026-06-30. The generated documentation portal shell now ships
  an accessible local search UI for every locale: visible localized search labels, explicit keyboard
  submit/clear controls, polite status announcements, generated filter controls from facet counts,
  highlighted snippets, result title/guide/type/facet metadata, responsive/forced-colors/print CSS,
  URL state preservation, and a locale-scoped browser-only recent-query value in `localStorage`.
  Search loads only the same-artifact static locale index, uses a reviewed first-party deferred
  script, avoids inline/remote scripts, telemetry, AI/RAG/embeddings/generative answers, and inserts
  indexed content with safe text-node DOM operations rather than indexed HTML.
- [x] `BPM090-M10-07` — completed on 2026-06-30. Search generation now embeds deterministic
  quality/performance fixtures for all six locales without AI, RAG, embeddings, or generative
  answers. Each locale covers exact, natural-language, typo, synonym, Firefox channel, CIS, API,
  no-result, and adversarial queries; `zh-CN` also covers CJK tokenization. Per-locale search
  indexes record top-result expectations, score-component checks, zero-result expectations,
  visible-result caps, deterministic scan-unit budgets, document-count budgets, and index-size
  budgets. Manifest and package validation now reject stale quality reports, wrong top results,
  missing score components, unexpected no-result hits, oversized indexes, and scan budgets that no
  longer fit the CI-stable offline search envelope.
- [x] `BPM090-M10-08` — completed on 2026-06-30. Search generation now embeds a deterministic
  integrity/drift report for every locale without AI, RAG, embeddings, or generative answers. The
  gate recomputes manifest-topic coverage, duplicate document IDs, wrong locale/URL/output metadata,
  stale target-map anchors, missing target topics, broken snippet sources, control characters, and
  Firefox policy/CIS/API inventory gaps during manifest and package validation. Publishing now fails
  closed with actionable topic, target, anchor, document, and source IDs whenever the generated
  search index diverges from manifests or maintained source inventories.
- [x] `BPM090-M10-09` — completed on 2026-06-30. The accepted accessibility/security architecture
  contract and six-locale User Guide now explicitly describe documentation search as deterministic
  local retrieval over the packaged static index. The user-facing boundary states that the portal
  does not provide conversational answers, semantic embeddings, vector retrieval, RAG, generative
  summaries, automatic recommendations, telemetry learning, personalization, or external AI/search
  service calls, while still documenting Firefox Release AI/smart-feature policies as ordinary BPM
  product settings. A focused contract test keeps the architecture copy, reachable DITA topic, and
  six-locale parity in sync.
- [x] `BPM090-M11-01` — completed on 2026-06-30. `documentation/tests/` now has an explicit
  suite-boundary contract for unit, contract, and browser groups. The boundary maps DITA, content,
  manifest, localization, screenshot, search, link, API-example, portal-integration, suite-boundary,
  and toolchain failures to focused owners, compact fixtures, and smallest rerun commands, while
  preserving repository-root `tests/` only for cross-boundary architecture, runtime bridge, marker
  policy, and release-gate contracts. The README documents when to stay inside documentation tests
  and which generated, licensed, browser, secret, customer, cache, report, and full-site artifacts
  must not enter fixtures.
- [x] `BPM090-M11-02` — completed on 2026-06-30. The root Makefile now exposes focused
  documentation validation entry points: `make test-docs` for documentation unit plus contract
  suites, `make test-docs-contract` for documentation `docs_contract` checks only, and
  `make test-docs-ui` for current non-browser portal/UI contracts. Each target prints the selected
  documentation area before pytest starts; the UI target also prints that real browser-backed docs
  smoke and screenshots arrive in `BPM090-M11-09` and require immediate sandbox escalation.
- [x] `BPM090-M11-03` — completed on 2026-06-30. `make docs-fast-check` now provides the first
  documentation-only source loop. It accepts explicit `DOCS_CHANGED` paths or derives changed
  documentation inputs from git, validates focused DITA/XML links, JSON, and asset inputs without
  invoking DITA-OT or unrelated BPM runtime code, then reports the affected locales, guide roots,
  search indexes, and expected generated outputs that the full deterministic docs gate would touch.
- [x] `BPM090-M11-04` — completed on 2026-06-30. `make docs-coverage` now runs isolated
  documentation-code coverage for the accepted `coverage-policy-0.9.0.json` scope, writes terminal,
  XML, and HTML reports under ignored `documentation/reports/coverage/`, enforces 100% coverage for
  included modules, and keeps currently uncovered documentation-owned tooling/runtime bridge modules
  explicitly named as release-gate risk rather than hidden product-application coverage debt.
- [x] `BPM090-M11-05` — completed on 2026-06-30. `documentation/fixtures/fixture-catalog-0.9.0.json`
  now indexes compact deterministic synthetic fixtures for profile, policy, preference, CIS, API,
  locale, search, and screenshot states. The catalog maps fixtures to documentation failure domains,
  enforces small JSON-only inputs, keeps generated reports/builds/browser downloads/production data
  out of maintained fixtures, and is guarded by a focused `docs_contract` test.
- [x] `BPM090-M11-06` — completed on 2026-06-30. Focused documentation failures now have an
  accepted diagnostics policy and `build_docs.py` can retain compact JSON diagnostics under ignored
  `documentation/reports/diagnostics/`. Failed `docs-fast-check` runs report the artifact path and
  focused rerun command, while the payload records topic ID, locale, guide, source line, target URL,
  query fixture, screenshot state, and retention boundary without committing generated reports.
- [x] `BPM090-M11-07` — completed on 2026-06-30. `make docs-snapshot` now regenerates
  `documentation/PROJECT_SNAPSHOT.generated.md`, a deterministic bounded map of documentation
  sources, configs, fixtures, runbooks, tools, tests, runtime `/help/` bridge, architecture entry
  points, commands, and locale topic counts. The generator excludes generated pages, search indexes,
  screenshot binaries, reports, caches, dependencies, pyc files, and unrelated `app/` modules.
- [x] `BPM090-M11-08` — completed on 2026-06-30. `make docs-release-check` now runs full
  six-locale DITA validation plus documentation `docs_contract` checks, and `make test-release`
  depends on it before running the general non-live BPM release suite. The documentation
  suite-boundary contract and release contract now name this gate so release testing cannot omit the
  portal, locale parity, content, manifest, search, API-example, or non-browser portal contracts.
- [x] `BPM090-M11-09` — completed on 2026-06-30. `make test-docs-browser` now runs a focused
  Chromium/Selenium documentation portal smoke against a compact installed `/help/` artifact and
  real BPM routes. The smoke covers the header documentation link in all six locales, contextual
  help links, deep help icons, new-tab behavior, search/index and asset fetches, responsive width,
  and preservation of FastAPI OpenAPI `/docs`; `make test-docs-ui` now runs both non-browser portal
  contracts and this browser-backed smoke with immediate sandbox escalation.
- [x] `BPM090-M11-10` — completed on 2026-06-30. `documentation/runbooks/debugging-protocol.md`
  now gives maintainers a bounded documentation-only debugging ladder. It names the smallest first
  command for source, contract, build, browser, screenshot, coverage/diagnostics, and release
  concerns; records what each check proves; and explicitly states what remains unverified before
  moving to browser, screenshot, release, manual QA, product coverage/UI, or live Firefox gates.
- [x] `BPM090-M12-01` — completed on 2026-06-30. Administrator/DevOps documentation is now a fifth
  guide family with six-locale `administrator-guide.ditamap` files, `guide.administrator-guide`
  keys, stable `admin/` manifest/search URL root, schema/build registrations, provenance/release
  scope, and a focused contract that keeps source deployment, operations, update, integration, and
  production-readiness boundary ownership separate from User Guide workflows, Firefox/CIS guidance,
  and deferred packaged installer/distribution variants.
- [x] `BPM090-M12-02` — completed on 2026-06-30. `api-integration-rehome-audit-0.9.0.json` and
  `.md` now inventory all 13 current API Integration Guide topics, 7 API-adjacent User Guide
  topics, preserved fixtures, affected tests, future `admin-*` destination IDs, and alias/cross-link
  rules. The audit keeps User Guide ownership limited to UI workflows and user-visible recovery
  while reserving endpoint, request/response, health/readiness, retry, automation, and external
  control-product procedures for the Administrator/DevOps Guide migration.
- [x] `BPM090-M12-03` — completed on 2026-06-30. The Administrator/DevOps Guide now includes
  six-locale Linux source-deployment task topics for host prerequisites, repository checkout,
  `.venv`/dependency setup, migrations, `BPM_*` runtime configuration, `make dev`, health/readiness
  probes, UI/log smoke checks, and explicit deferred production/installer/systemd/HA boundaries.
- [x] `BPM090-M12-04` — completed on 2026-06-30. The Administrator/DevOps Guide now includes
  six-locale Windows 10/11 through WSL source-deployment task topics for WSL prerequisites,
  distribution assumptions, Linux-filesystem placement, repository checkout, Python/toolchain
  setup, runtime/network configuration, Windows browser access, health/readiness probes, logs,
  WSL-specific troubleshooting, and explicit non-native-Windows/install/service boundaries.
- [x] `BPM090-M12-05` — completed on 2026-06-30. The Administrator/DevOps Guide now includes
  six-locale DevOps operations topics for `BPM_*` configuration sources, `.env` boundaries,
  local SQLite/storage/schema/documentation paths, foreground/stdout/stderr logs, manual backup
  evidence, CORS/network/security limits, runtime-user/process handoff, and explicit unsupported
  authentication/secret-management/HA/reverse-proxy/production-hardening claims.
- [x] `BPM090-M12-06` — completed on 2026-06-30. The Administrator/DevOps Guide now includes
  six-locale update-from-source topics covering pre-update source/config/database/export evidence,
  approved revision checkout, dependency refresh, `alembic upgrade head`, source smoke,
  documentation validation/build checks, post-update health/UI/API evidence, rollback via verified
  pre-update backup, and stop/escalation conditions when automatic rollback is not guaranteed.
- [x] `BPM090-M12-07` — completed on 2026-07-01. The former API Integration Guide corpus now lives
  under the Administrator/DevOps Guide as six-locale `admin-*` topics for API audience, supported
  patterns, conventions, limitations, profile lifecycle, Firefox import/export, validation gates,
  health/readiness, control-product scenarios, and reusable examples. The old API guide is a thin
  compatibility landing page, OpenAPI/search/UI target contracts point API operations to admin
  topics, and User Guide API-adjacent topics cross-link to the new admin owners.
- [x] `BPM090-M12-08` — completed on 2026-07-01. The Administrator/DevOps Guide now includes
  six-locale external control-product runbooks for pull/list/read inventory snapshots,
  validate-before-apply profile updates with `expected_revision`, import-review-export and
  compliance metadata handoff, health-gated startup, failure recovery, and audit evidence.
  A focused docs contract executes the core pull/read/validate/patch/conflict/export path against
  the API test app and preserves the no-unsafe-retry/no-transaction-assumption boundary.
- [x] `BPM090-M12-09` — completed on 2026-07-01. The reusable Administrator/DevOps API examples
  topic now includes six-locale environment templates, health/readiness probes, curl snippets for
  profile lifecycle, validation, JSON import, multipart import, and export, plus compact Python
  response assertions. The focused API docs contract executes create/list/read/patch, validation,
  JSON import, multipart import, and export against the API test app and rejects credentials,
  real hosts, and production identifiers in examples.
- [x] `BPM090-M12-10` — completed on 2026-07-01. The Administrator/DevOps Guide now includes
  six-locale troubleshooting topics for failed startup and unreachable probes, schema/cache and API
  validation errors, JSON/multipart import and export failures, database/storage issues, WSL
  networking and stale dependencies, and documentation portal build/link failures. The focused
  contract checks map/key reachability, locale parity, current API diagnostic statuses, focused
  rerun commands, data-preservation warnings, and the boundary against editing generated artifacts
  or database rows as routine recovery.
- [x] `BPM090-M12-11` — completed on 2026-07-01. The Administrator/DevOps Guide now includes
  six-locale production-readiness boundary topics for current single-node source operation,
  network exposure and proxy-readiness questions, monitoring inputs, backup/export evidence,
  update windows, and HA/deferred production boundaries. The focused contract checks map/key
  reachability, locale parity, current health/readiness, backup, export, documentation rebuild
  commands, and explicit absence of packaged services, official TLS/proxy recipes, supported HA
  clustering, rolling upgrades, managed secrets, production hardening, and official restore
  automation.
- [x] `BPM090-M12-12` — completed on 2026-07-01. The Administrator/DevOps validation fixture now
  enumerates admin topic groups, guide-map expectations, commands, paths, config names, environment
  variables, health endpoints, API examples, migrated API IDs, WSL caveats, and deferred
  production/HA/reverse-proxy warning terms. The focused contract checks those fixture expectations
  against six-locale DITA peers, key maps, the API compatibility landing map, Makefile/README,
  app config, health probes, validation/import/export API smoke paths, and forbidden supported
  claims.
- [x] `BPM090-M12-13` — completed on 2026-07-01. The Administrator/DevOps Guide localization
  review found all six locale peers already full enough under the maintained parity contracts:
  no fallback markers, no compact summaries, stable DITA/map/key structure, preserved commands,
  paths, environment variables, API names, WSL terms, and production-boundary warnings. No content
  rewrite was required.
- [x] `BPM090-M13-01` — closed on 2026-07-02. `make docs-install-dev` now
  builds the validated six-locale site and installs an ignored local copy under
  `app/documentation/site`, so maintainers can run `make dev`, open the BPM header documentation
  link in a new tab, and inspect `/help/` without a temporary Codex-launched server. Maintainer
  manual review found many issues, but they are explicitly accepted for 0.9.0 and deferred to the
  next version rather than blocking the final M14 quality milestone.
- [x] `BPM090-M14-01` — completed on 2026-07-02. `make typecheck` passes with mypy over `app`
  after tightening documentation manifest locale validation so JSON locale data is checked as a
  string list before tuple comparison. The focused `/help` runtime and BPM header documentation
  link contract also passes.
- [x] `BPM090-M14-02` — completed on 2026-07-02. `make lint` passes after applying Ruff's import
  ordering fix to `tests/test_dita_publishing_toolchain_decision.py`; no generated/vendor cleanup
  or new lint exclusions were added.
- [x] `BPM090-M14-03` — completed on 2026-07-02. The full default `pytest -q` suite passes after
  updating stale documentation contracts for Administrator/DevOps API topic grouping, current
  documentation test targets, dev-installed `/help` runtime review, release-contract administrator
  guide wording, and RU/ZH contextual-help labels that no longer expose `VisualSearchEnabled` as
  accidental English. No new skips or xfails were added.
- [x] `BPM090-M14-04` — completed on 2026-07-06. `make coverage` now reports 100% statement and
  branch coverage for the full maintained `app` surface (`939 passed, 34 deselected`) after adding
  focused fail-closed `/help` runtime edge coverage for documentation manifest, target-map, locale,
  asset, status-page, alias, and resolver paths. `make docs-coverage` also remains at 100% for the
  isolated documentation metadata validator.
- [x] `BPM090-M14-05` — completed on 2026-07-06. `make docs-release-check` passes from a regenerated
  validation output tree: all six locales publish through the DITA gate, metadata/source/generated
  links are valid, and the release contract suite passes (`452 passed, 3 deselected`) across
  locale parity, content, manifest/target-map, deterministic search, provenance, API examples,
  accessibility/security, and non-browser portal contracts. The stale manifest contract was updated
  so the already generated six-locale search indexes are no longer treated as a runtime blocker.
- [x] `BPM090-M14-06` — completed on 2026-07-06. Browser-backed UI gates pass with immediate
  escalation as required by the documentation debugging protocol: `make test-ui` completed
  (`253 passed, 720 deselected`) and the dedicated documentation browser smoke
  `make test-docs-browser` completed (`2 passed`). This covers core BPM product UI behavior,
  Library/contextual documentation entry points, the installed documentation portal smoke, and
  browser coexistence expectations without adding skips or xfails.
- [x] `BPM090-M14-07` — completed on 2026-07-06. The final content coverage audit is recorded in
  `product-documentation-content-coverage-audit-0.9.0.{json,md}` and is enforced by a focused
  docs_contract test. The audit reconciles user capabilities, Administrator/DevOps source
  deployment, WSL deployment, operations, update, API/integration, control-product runbooks,
  troubleshooting, production-readiness boundaries, Firefox policy/schema, CIS, OpenAPI/API
  operations, locale parity, manifest/target-map, deterministic search, and portal runtime
  evidence. Localized screenshot capture/review remains an explicit release blocker rather than a
  silent coverage claim.
- [x] `BPM090-M14-08` — completed on 2026-07-06 and adjusted after maintainer review. `README.md`
  describes the current product state without product-version release notes or "what changed in
  this version" history: `/help/`, preserved FastAPI `/docs`, header/contextual help behavior, five
  guide families, six locales, deterministic non-AI search, Administrator/DevOps
  source-deployment/update/integration content, focused documentation commands, maintainer dev
  install through `make docs-install-dev`, and the remaining release blockers for package
  extraction, localized screenshot review, and final manual QA disposition. The epic backlog
  creation runbook now requires a dedicated documentation-update milestone before final quality for
  epics that change functionality, and keeps release history in `CHANGELOG.md`. Existing maintainer
  email-topic and copyright wording is preserved.
- [x] `BPM090-M14-09` — completed on 2026-07-06. The 0.9.0 changelog entry now summarizes shipped
  documentation portal behavior, five guide families, six-locale DITA coverage, deterministic
  non-AI search, BPM header/contextual documentation links, Administrator/DevOps source deployment,
  update and API integration guidance, documentation-specific testing boundaries, dependency/vendor
  refresh, final quality gates, and known non-goals/deferred production capabilities while
  preserving prior release history.
- [x] `BPM090-M14-10` — completed on 2026-07-06. The maintained docs index now carries the final
  0.9.0 review date and already lists every maintained `docs/` file exactly once; documentation
  authoring, publishing, Firefox schema, CIS, locale, Administrator/DevOps deployment,
  update-from-source, API/DevOps integration, production-boundary, and backlog-creation runbooks now
  require documentation drift gates before release readiness.
- [x] `BPM090-M14-11` — completed on 2026-07-06. `make docs-package` rebuilt the release candidate
  archive `documentation/dist/bpm-documentation-0.9.0.tar.gz`, and `make docs-package-verify`
  verified its SHA-256 (`b18cfff5a9657307c6010e27fb808a3e397a505c781a13d0325453107ee0bdb3`).
  A targeted archive audit confirmed one clean package root, root manifest/target-map/integrity
  files, all six locale roots, equal per-locale guide counts (44 admin, 90 user, 9 CIS, 7 Firefox,
  1 API), all six deterministic search indexes, BPM/MPL and third-party notices, no cache/debug/
  local-artifact/source DITA/PDF/database entries, and no runtime external asset references.
  Localized screenshot assets remain absent rather than falsely shipped because screenshot capture
  and review are still an explicit release blocker.
- [x] `BPM090-M14-12` — completed on 2026-07-06. Before creating the completed epic commit, the
  GitHub live Firefox workflows were changed from scheduled nightly runs to guarded manual-only
  dispatches requiring `run_live_tests=RUN`; the workflow contract and live-testing runbook now
  prevent accidental cron re-enablement. Final staging excludes ignored local documentation
  installs, build output, reports, and packaged archives while committing the approved 0.9.0
  documentation epic, dependency/vendor refresh, runtime integration, and verification records.
- [x] `BPM090-M4-07` — completed on 2026-06-27. The User Guide now has localized DITA All Settings
  topics covering Review, Configured, and Catalog modes; invalid, CIS manual-review, raw, unknown,
  deprecated, imported, and clean review states; source and state filters; large inventories;
  detail inspection/edit/apply/remove/reset flows; managed preferences; categories; advanced
  schema controls; raw/unknown preservation; setting deep links; source tracing; and CIS
  manual-review decisions. The topics are keyed, reachable, and parity-checked across all six
  locales.
- [x] `BPM090-M4-08` — completed on 2026-06-27. The User Guide now has localized DITA JSON Editor
  topics covering when to choose JSON editing, raw `policies.json` review, local Monaco editing,
  formatting, validation, save behavior, canonical export handoff, and recovery from malformed JSON
  and schema-invalid policy values. Compact fixtures cover valid `policies.json`, syntax-invalid
  JSON, and a policy value with the wrong type; the topics are keyed, reachable, and parity-checked
  across all six locales.
- [x] `BPM090-M4-09` — completed on 2026-06-27. The User Guide now has localized DITA schema-channel
  and validation topics covering Firefox ESR 140.12 versus Release 152 selection, validation
  messages, supported/unavailable/deprecated/unknown/imported/raw states, Release-only AIControls
  and VisualSearchEnabled boundaries, wrong value types, migration expectations, and revalidation
  before save/export. Fixtures are contract-tested against the current supported schemas.
- [x] `BPM090-M4-10` — completed on 2026-06-27. The User Guide now has localized DITA cross-cutting
  topics covering interface language and locale fallback, system/light/dark theme, accessible
  keyboard/focus/status behavior, editor tabs, save/validate/switch-mode/review-context workflows,
  source attribution context, safe destructive confirmations, and unsaved-change recovery.
- [x] `BPM090-M4-11` — completed on 2026-06-27. The User Guide now has localized DITA troubleshooting
  topics covering save conflicts, malformed JSON, failed import, structured policy validation
  errors, schema mismatch, profile-name validation, missing profile routes, product/API connection
  failures, stale tabs, raw fallback, unsupported policies, and visible browser-testing caveats.
- [x] `BPM090-M4-12` — completed on 2026-06-28. The User Guide coverage matrix is closed by a
  release-gate artifact and contract that reconcile all 106 capability IDs and 89 localized topic
  IDs against README capabilities, profile routes, templates, locale catalogs, API boundary
  behavior, and browser-smoke evidence.
- [x] `BPM090-M5-01` — completed on 2026-06-28. The Firefox Policy Guide now has a DITA reference
  topic model and shared template covering purpose, BPM location, value shape, Release/ESR support,
  examples, validation, caveats, interactions, CIS links, provenance, managed-preference references,
  and regeneration boundaries for the upcoming schema-grounded skeleton task.
- [x] `BPM090-M5-02` — completed on 2026-06-28. The Firefox Policy Guide now has committed
  generator-owned DITA reference skeletons for all 120 supported policy IDs, a generated policy map,
  a skeleton index with source hashes, metadata/source-link validation coverage, and a regeneration
  contract that preserves reviewed regions; publishing/localizing authored policy topics remains
  gated by later M5/M8 tasks.
- [x] `BPM090-M5-03` — completed on 2026-06-28. The Firefox Policy Guide now has six-locale DITA
  concepts for choosing policies, understanding the BPM profile versus Firefox runtime boundary,
  and choosing starter presets for basic corporate, classroom/kiosk, and protected-station/SOC-style
  baselines before detailed validation and export.
- [x] `BPM090-M5-04` — completed on 2026-06-28. The generated Firefox policy reference skeletons
  now embed schema-valid synthetic Firefox boundary-document examples for every supported
  policy/channel pair, with 232 examples recorded in the skeleton index and validated against the
  bundled Release 152 and ESR 140.12 schemas.
- [x] `BPM090-M5-05` — completed on 2026-06-28. The Firefox Policy Guide now records Release 152
  versus ESR 140.12 differences through generated channel-support badges, filter-ready index
  metadata, a channel-differences artifact, and six-locale guidance; the current matrix has 112
  both-channel policies, eight Release-only policies, no ESR-only policies, and no changed common
  definitions.
- [x] `BPM090-M5-06` — completed on 2026-06-28. The Firefox Policy Guide now has six-locale
  concept/task/reference coverage for complex policy families and managed-preference locking, plus
  a representative fixture validated against declared Release/ESR channels.
- [x] `BPM090-M5-07` — completed on 2026-06-28. The generated manifest now registers the current
  publishable topic set and the UI target map resolves 120 Firefox policy targets plus topic,
  capability, CIS, and API-operation targets, with contracts rejecting orphaned or ambiguous policy
  context assignments.
- [x] `BPM090-M5-08` — completed on 2026-06-28. The Firefox inventory refresh runbook now treats
  Release/ESR schema bumps as documentation drift gates covering added, removed, and changed policy
  topics, schema-valid examples, aliases/tombstones, manifest/search parity, locales, and
  screenshot review; generated Firefox artifacts carry the runbook marker and focused contracts.
- [x] `BPM090-M5-09` — completed on 2026-06-28. Generated Firefox policy topics now carry
  source-family, license, reuse-mode, Mozilla tag, retrieval-date, schema-fingerprint, and
  no-affiliation metadata, with a provenance-review artifact and contracts that reject stale channel
  facts, unsupported claims, and unmarked Mozilla prose reuse.
- [x] `BPM090-M6-01` — completed on 2026-06-28. The CIS Settings Guide now has a DITA reference
  topic model and shared template that separate benchmark identity, recommendation identity,
  BPM-authored mapping, automation/manual state, conflicts, verification, provenance, source
  boundary, and mandatory non-certification disclaimers.
- [x] `BPM090-M6-02` — completed on 2026-06-28. The CIS Settings Guide now has equivalent
  six-locale orientation and baseline-selection DITA topics covering benchmark version, Level 1 and
  Level 2 intent, ESR/Release channels, generated layers, manual-review scope, starter presets, and
  non-certification/source-boundary disclaimers.
- [x] `BPM090-M6-03` — completed on 2026-06-28. CIS recommendation skeleton generation now creates
  53 publishable DITA reference skeletons plus a generated map/index from shipped mappings, while
  preserving reviewed hand regions and keeping two unresolved recommendations as explicit
  provenance-only records without publishing restricted CIS source expression.
- [x] `BPM090-M6-04` — completed on 2026-06-28. Generated CIS recommendation topics now include
  mapping tables, Firefox topic keys, UI targets, values, value types, lock states, channel
  validity, merge rules, minimal BPM-owned JSON fragments, and layer checks that verify each row
  against the current shipped CIS layer files.
- [x] `BPM090-M6-05` — completed on 2026-06-28. The CIS Settings Guide now has equivalent
  six-locale topics for starter presets, CIS layers, merge decision types, manual-review conflicts,
  and source attribution from baseline, CIS, manual, imported, and raw sources.
- [x] `BPM090-M6-06` — completed on 2026-06-28. The CIS Settings Guide now has equivalent
  six-locale topics for manual-review paths, deviation boundaries, external exception recording,
  verification evidence, and warnings that BPM does not prove Firefox runtime compliance.
- [x] `BPM090-M6-07` — completed on 2026-06-28. The CIS Settings Guide now has equivalent
  six-locale Level 1 and Level 2 end-to-end workflow topics plus deterministic fixtures covering
  Library, Guided Editor, All Settings, comparison, export, and external verification routes.
- [x] `BPM090-M6-08` — completed on 2026-06-28. The inventory-refresh runbook now gates CIS
  benchmark/mapping drift across inventory, generated recommendation topics, mapping tables,
  provenance, locale parity, examples, search/manifest/UI targets, screenshots, and package
  readiness; the generated CIS index records the refresh runbook marker.
- [x] `BPM090-M6-09` — completed on 2026-06-28. Generated CIS artifacts now include an
  accuracy/provenance review that cross-checks benchmark version, level, mappings, manual-review
  paths, source metadata, provenance-only records, source-boundary flags, and forbidden claims
  against the inventory, topic model, provenance matrix, generated topics, and shipped layer JSON.
- [x] `BPM090-M7-01` — completed on 2026-06-28. The API Integration Guide now has equivalent
  six-locale audience and supported-pattern topics covering generic integration roles, profile
  synchronization, validation gates, policy import/export, compliance metadata, inventory, health
  checks, and explicit unsupported connector/guarantee boundaries.
- [x] `BPM090-M7-02` — completed on 2026-06-28. The API Integration Guide now has equivalent
  six-locale convention and limitation topics covering base URLs, OpenAPI discovery, content types,
  identifiers, normalized/canonical schemas, lifecycle, query semantics, errors, security constraints,
  versioning, concurrency, idempotency, bulk/transaction boundaries, excluded surfaces, and health limits.
- [x] `BPM090-M7-03` — completed on 2026-06-29. The API Integration Guide now has equivalent
  six-locale profile lifecycle task topics covering list, stats, read, create, update, archive,
  restore, permanent delete, and reset endpoints with request/response/error examples, optimistic
  concurrency notes, external audit records, and prominent warnings for destructive operations.
- [x] `BPM090-M7-04` — completed on 2026-06-29. The API Integration Guide now has equivalent
  six-locale Firefox import/export task topics covering JSON and multipart import, compliance
  metadata storage, schema-channel selection, canonical export, download/pretty output, validation
  handoff, and BPM-normalized versus Firefox-deployment shape boundaries, with examples executed
  against the API test app.
- [x] `BPM090-M7-05` — completed on 2026-06-29. The API Integration Guide now has an equivalent
  six-locale validation-gate task topic covering candidate Firefox `policies.json` validation by
  schema channel, `ok=false` body handling, malformed canonical documents, unsupported channels,
  structured policy-validation issues, and external validation-decision evidence, with success and
  failure examples executed against the API test app.
- [x] `BPM090-M7-06` — completed on 2026-06-29. The API Integration Guide now has an equivalent
  six-locale health/readiness handshake task topic covering `/health` and `/health/ready` response
  contracts, readiness boundaries, polling/retry ownership, source-deployment Administrator Guide
  handoff, and non-goals such as dependency diagnostics, deployment troubleshooting, authentication,
  and runtime enforcement guarantees, with examples executed against the API test app.
- [x] `BPM090-M7-07` — completed on 2026-06-29. The API Integration Guide now has equivalent
  six-locale end-to-end control-product scenario task topics covering pull/compare/update,
  validate-before-apply, import-review-export, compliance metadata handoff, health-gated startup,
  failure recovery records, data ownership, and warnings against unsafe retry assumptions, with
  executable API examples linked back to endpoint-reference tasks.
- [x] `BPM090-M7-08` — completed on 2026-06-29. The API Integration Guide now has an equivalent
  six-locale reusable curl/Python example task topic covering `$BPM_BASE_URL` setup, health and
  readiness gates, synthetic profile creation, validation, export, response assertions, timeout
  handling, and evidence boundaries without hardcoded hosts, credentials, tenant names, or
  production identifiers; the example flow is smoke-tested against the current API test app.
- [x] `BPM090-M7-09` — completed on 2026-06-29. Focused documentation contract tests now compare
  generated `/openapi.json` with the API inventory and DITA coverage for programmatic and web
  operation route sets, operation IDs, tags, parameters, request content, response status/schema
  references, model fields, application-status documentation, and copyable examples; failures name
  the affected API or web operation ID, path, and DITA/inventory topic IDs.

## Execution Protocol

When executing this backlog interactively:

1. Show exactly one next task with its ID, essence, acceptance, and minimal reasoning.
2. Wait for explicit maintainer approval.
3. Execute only that approved task.
4. Report what changed and which checks passed.
5. Show the next task for approval.

Browser/Selenium tests and localized screenshot capture in this backlog must run with immediate
sandbox escalation. Do not first try `make test-ui`, `make test-docs-ui`, Selenium, Chromium, or a
screenshot-capture command inside the sandbox.

Documentation-focused commands are the first validation layer during implementation. Passing them
does not replace `pytest -q`, `make coverage`, `make test-ui`, or `make test-release` at the final
quality milestone.

Do not start executing a backlog task just because this backlog exists.

## Backlog Creation Acceptance Checklist

- Target BPM version is present and normalized as `0.9.0`.
- Epic id and task IDs use stable `BPM090-*` identifiers.
- Milestones are grouped by product meaning and every task has a minimal reasoning level.
- First milestone includes the version transition across product surfaces.
- Scope includes a case-oriented User Guide covering every BPM capability, a complete Firefox
  Policy Guide, a CIS Settings Guide, and a guide for integrations built on the existing API.
- All product documentation is authored and published from DITA topics and supports `en`, `ru`,
  `de`, `zh-CN`, `fr`, and `es-ES`.
- User-guide screenshots cover the illustrated functions separately in every locale.
- The Profile Library receives a first-class Documentation button.
- Smart search is deterministic, locale-aware, offline-capable, and explicitly excludes AI, RAG,
  embeddings, and generative answers.
- Distribution-specific administrator installation variants remain deferred until BPM distribution
  formats exist; the Administrator/DevOps Guide for source deployment, source-based updates, and
  API/integration operation is now scheduled before manual QA.
- Documentation sources, tools, fixtures, tests, and debug context have a separate ownership area
  with focused commands, while full release gates still include the documentation product.
- A separate manual QA milestone verifies the integrated documentation product through the Profile
  Library new-tab button before final automated tests, commits, or push handoff.
- Final milestone includes mypy via `make typecheck`, Ruff via `make lint`, `pytest -q`,
  `make coverage`, coverage-to-100%, Selenium smoke via `make test-ui` and the documentation browser
  suite, README refresh, changelog finalization, docs-index refresh, clean package verification,
  commit, and maintainer-run push command.
- Selenium/browser and screenshot verification requires immediate sandbox escalation without a
  sandboxed trial run.
- README instructions preserve maintainer copyright and email-topic/message-theme information.
- Changelog instructions preserve previous version history.
- Product language is English while maintainer chat may be Russian.
- `docs/docs-index.md` includes this active backlog.
- Assumptions, provenance constraints, and non-goals are explicit.
- Execution protocol requires separate user approval for each task.
