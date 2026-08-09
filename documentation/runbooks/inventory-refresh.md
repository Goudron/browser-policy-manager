# Runbook: Firefox, CIS, And API Inventory Refresh

Use this when documentation facts need to follow a maintained product inventory rather than a single
hand-authored topic edit.

## Firefox policy refresh

1. Start from `docs/architecture/firefox-policy-documentation-inventory-0.9.0.json` and the exact
   existing builder/test named by the failing contract.
2. Use targeted schema lookups only. Do not load full Firefox schemas, upstream trees, or web
   sources unless the approved task explicitly requires a schema refresh.
3. Preserve Mozilla MPL attribution and trademark boundaries.
4. Generated policy facts must declare generator, source version/revision, and provenance. Reviewed
   human prose remains in DITA topics.

### Firefox Release/ESR schema bump drift gate

When the Release or ESR Firefox policy schema changes, treat documentation drift as part of the
schema bump rather than a follow-up cleanup.

1. Rebuild the maintained inventory with the existing inventory builder and verify
   `tests/contract/docs/general/test_firefox_policy_documentation_inventory.py`.
2. Regenerate schema-grounded policy skeletons with
   `./.venv/bin/python documentation/tools/generate_firefox_policy_skeletons.py`.
3. Review added policies, removed policies, and changed common definitions:
   - added policies must create exactly one stable `fx-policy-{PolicyID}` topic, DITA key, generated
     map entry, `policy:{PolicyID}` UI target, schema-valid examples, search/manifest entry when
     publishable, and Release/ESR channel badge;
   - removed policies must delete stale generated skeletons during regeneration and require an
     explicit alias or tombstone decision before any released public topic/path is retired;
   - changed common definitions must appear in
     `firefox-policy-channel-differences-0.9.0.json` and be reviewed for value-shape, validation,
     caveat, CIS-link, and related-policy impact.
4. Review examples for every supported channel. A policy with a supported channel needs one
   schema-valid example for that channel or a documented blocking reason in the generator contract.
5. Review aliases, tombstones, and stable IDs using `links-manifest-and-publishing.md` whenever a
   topic ID, key, anchor, source slug, canonical path, or contextual target changes.
6. Review manifest and search parity: `manifest.json`, `ui-target-map.json`, and each locale search
   file must include the changed publishable topics, anchors, policy targets, hashes, and output
   paths after `make docs-build`.
7. Review locales and screenshots where relevant. Authored Firefox Policy Guide topics must remain
   content-equivalent in `en`, `ru`, `de`, `zh-CN`, `fr`, and `es-ES`; any UI-visible schema change
   that changes documented screens must queue localized screenshot review before release readiness.
8. Do not add, reconfigure, or claim AI/RAG/embeddings/generative search behavior as part of a
   schema bump. The 0.9.3 assistant remains a localized training notice, and
   Firefox product policies about AI remain valid documentation subject matter.
9. When the schema bump changes compact UI copy or documentation shell behavior, cite the exact
   UI-copy classification disposition. Preserve labels, state, validation, consequences,
   unavailable reasons, accessible names, and recovery at the action; do not restore routine
   explanation. Every affected circled-info target needs a localized manifest-backed owner or an
   explicit reviewed no-link disposition. Recheck audience/style review, normalized BPM header
   parity, and one derived BPM product version. Search, URL/history hydration, result updates, and
   clear must not reopen a collapsed advanced-filter panel.

## CIS refresh

1. Start from `docs/architecture/cis-documentation-inventory-0.9.0.json` and the provenance matrix.
2. Do not read ignored CIS PDFs or copy CIS source expression without scoped rights approval.
3. BPM may document its own mappings, UI behavior, merge layers, warnings, and unsupported states in
   original attributed prose.
4. Do not claim CIS certification, endorsement, or conformance.

### CIS benchmark and mapping drift gate

When the CIS benchmark source record, shipped CIS mappings, generated layer files, starter presets,
manual-review paths, or exception boundary changes, treat documentation drift as part of the same
change. Do not leave recommendation topics, mappings, provenance, locales, examples, search, or
screenshots as follow-up work.

1. Rebuild or check the maintained CIS inventory first with `tests/contract/docs/general/test_cis_documentation_inventory.py`.
   The inventory must still close recommendation count, planned-topic count, provenance-only records,
   generated layers, starter presets, merge decisions, manual-review paths, and exception-contract
   facts before DITA source is edited.
2. Regenerate recommendation skeletons with
   `./.venv/bin/python documentation/tools/generate_cis_recommendation_skeletons.py` and run
   `documentation/tests/contract/test_cis_recommendation_skeleton_generation.py`. Regeneration must
   remove stale topics, preserve reviewed hand regions, update mapping tables, update layer-checked
   JSON examples, and keep provenance-only records non-publishable.
3. Review content and mappings together:
   - every publishable recommendation needs exactly one stable `cis-rec-*` topic, DITA key, generated
     map entry, recommendation ID, level, generated layer list, UI target, Firefox policy/preference
     topic route, mapping table row, example fragment, and source hash;
   - changed values, lock state, channel support, merge rule, source attribution, or manual-review
     path must update both the generated row and any authored orientation/workflow topic that refers
     to the behavior;
   - unresolved, unsupported, deprecated, or rights-blocked records must remain provenance-only with
     an explicit non-publishable reason.
4. Review provenance and source boundaries. Confirm the run still records
   `bpm-cis-mapping-implementation` as the publishable source family, `cis-benchmark-pdf` as the
   restricted source family, no copied or indexed CIS source expression, and no certification,
   endorsement, conformance, or compliance guarantee.
5. Review authored CIS topics in every locale. The `en`, `ru`, `de`, `zh-CN`, `fr`, and `es-ES`
   topics must remain content-equivalent for orientation, baseline selection, presets/layers/source
   attribution, manual review, verification, and Level 1/Level 2 workflows. Localized topics may not
   fall back to compact summaries.
6. Review search, manifest, and UI targets after `make docs-build`. `manifest.json`,
   `ui-target-map.json`, and every locale search index must include changed publishable CIS topics,
   anchors, capability targets, recommendation targets, hashes, output paths, and generated
   recommendation routes. Keep search deterministic and static; do not add AI/RAG/embeddings or
   generative answers to this CIS refresh. Any future assistant may consume only the
   resulting reviewed, published locale content through its own contracts.
7. Review screenshots when a refresh changes documented UI state, source labels, review states,
   CIS layer labels, Guided Editor summaries, All Settings rows, comparison output, validation
   screens, or export screens. Queue locale-specific screenshots under
   `documentation/assets/screenshots/{locale}/` before release readiness.
8. Run the focused CIS checks first, then metadata/link/build checks. If generated artifacts,
   manifest data, search data, or package inputs changed, also run reproducibility and package
   verification before release readiness.
9. If the refresh affects compact UI copy or documentation shell/search, apply the exact UI-copy
   disposition and retain essential or safety/accessibility meaning at the action. Every changed
   circled-info target has a localized manifest-backed owner or a reviewed no-link disposition;
   review audience/style, normalized BPM header parity, and one derived BPM product version. Search,
   URL/history hydration, results, and clear must not reopen a collapsed advanced-filter panel.

## API, Administrator/DevOps, and operations refresh

1. Start from `docs/architecture/api-documentation-inventory-0.9.0.md` and the focused OpenAPI or
   route/model contract test.
2. Document current BPM API behavior and limitations honestly. Do not invent authentication,
   idempotency, rate-limit, or compatibility guarantees.
3. Examples use `$BPM_BASE_URL`, `https://example.invalid`, disposable fixture IDs, and non-secret
   placeholders such as `<TOKEN>`.

### Administrator/DevOps source deployment, update, integration, and production-boundary drift gate

When BPM startup, configuration, environment variables, database/storage behavior, source checkout
steps, dependency setup, health/readiness probes, update-from-source steps, API operation contracts,
external-control-product workflows, troubleshooting paths, or production-readiness boundaries
change, treat Administrator/DevOps documentation drift as part of the same product change.

1. Reconcile the change against
   `docs/architecture/product-documentation-content-coverage-audit-0.9.0.{json,md}` and the
   affected Administrator/DevOps contract tests before editing prose.
2. Update the relevant DITA tasks in all six locales for Linux source deployment, Windows 10/11 WSL
   deployment, runtime configuration, storage/logs/backups, source-update evidence, dependency
   refresh, migrations/docs rebuild, rollback-stop decisions, DevOps integration runbooks, reusable
   API examples, troubleshooting diagnostics, and production-readiness boundaries.
3. Preserve current-state boundaries. Do not add packaged installer, native Windows service,
   systemd service, reverse-proxy recipe, TLS termination, HA clustering, rolling upgrade, managed
   secret, production hardening, or official restore guarantees unless the product implements and
   verifies them in the same change.
4. Re-run the narrow Administrator/DevOps contracts that match the changed area:
   - `documentation/tests/contract/test_administrator_guide_scope.py`
   - `documentation/tests/contract/test_administrator_linux_deployment_topics.py`
   - `documentation/tests/contract/test_administrator_windows_wsl_deployment_topics.py`
   - `documentation/tests/contract/test_administrator_devops_operational_boundaries.py`
   - `documentation/tests/contract/test_administrator_update_from_source_topics.py`
   - `documentation/tests/contract/test_api_openapi_drift.py`
   - `documentation/tests/contract/test_api_devops_integration_runbooks.py`
   - `documentation/tests/contract/test_administrator_troubleshooting_diagnostics_topics.py`
   - `documentation/tests/contract/test_administrator_production_readiness_boundaries.py`
5. If an API route, schema, example payload, status code, or response model changed, update the
   maintained API inventory and every affected Administrator/DevOps topic in the same review. User
   Guide topics may keep UI-oriented cross-links, but API procedure ownership stays in the
   Administrator/DevOps Guide.
6. Rebuild metadata, manifest, target map, search indexes, and package evidence when topic IDs,
   anchors, examples, guide map entries, target IDs, or output paths changed. Then verify
   `docs/docs-index.md` still lists every maintained `docs/` file exactly once.
7. Treat maintained installation commands as executable contracts. If prerequisites, checkout,
   virtual-environment, migration, documentation publication, startup, health/readiness, or shutdown
   commands change, the accepted live evidence for every affected Linux distribution becomes stale.
   Re-run `documentation/tools/live_source_install_harness.py` from the retained clean target image,
   write a new attempt-isolated transcript and manifest, and update the closure record only after
   command/result reconciliation. Keep Docker Engine, retained clean images, stopped validation
   containers, and the dedicated network unless a separately approved cleanup task changes that
   handoff; never edit an accepted transcript in place.
8. Keep the Windows boundary explicit. Docker, a Linux container, or an installation ISO does not
   prove WSL behavior. Windows 10/11 WSL evidence may become accepted only after the maintained
   PowerShell runner executes on the corresponding actual Windows host and records host/build,
   systemd/filesystem, Windows and WSL localhost/Edge, clean-stop, and restart checks. Otherwise the
   outcome remains `unverified-no-actual-host-supplied` with no Windows/WSL support claim.
9. For deployment, update, or DevOps integration changes, review generated navigation/search and
   contextual targets together with the DITA peers. The independently scrolling hierarchy must
   reveal direct topics and return to Documents, API procedures must remain owned by the
   Administrator Guide, and theme/search/help labels must stay localized from runtime UI catalogs.
10. Run the current-source installation and documentation-polish contracts that match the change;
    do not infer current behavior from a successful older transcript:

```bash
./.venv/bin/pytest -q -m docs_contract \
  documentation/tests/contract/test_linux_source_install_command_topics.py \
  documentation/tests/contract/test_documentation_semantic_contracts_0_9_4.py \
  documentation/tests/contract/test_wsl_source_install_validation_runner.py \
  documentation/tests/contract/test_documentation_polish_regression_gates.py
```

11. When a deployment, update, integration, or API change affects compact UI copy or the
    documentation shell, apply the UI-copy classification rather than restoring explanatory prose.
    Keep essential and safety/accessibility meaning at the action; reconcile each circled-info
    target with a localized manifest-backed owner or a reviewed no-link disposition. Recheck
    audience/style review, normalized BPM header parity, and one derived BPM product version.
    Search, URL/history hydration, results, and clear must not reopen a collapsed advanced-filter
    panel.

## Focused checks

Use the exact inventory builder/test first, then metadata and DITA checks:

```bash
./.venv/bin/pytest -q -m docs_contract tests/contract/docs/general/test_firefox_policy_documentation_inventory.py
./.venv/bin/python documentation/tools/generate_firefox_policy_skeletons.py
./.venv/bin/pytest -q -m docs_contract documentation/tests/contract/test_firefox_policy_skeleton_generation.py
./.venv/bin/pytest -q -m docs_contract documentation/tests/contract/test_manifest_generation.py
./.venv/bin/pytest -q -m docs_contract tests/contract/docs/general/test_cis_documentation_inventory.py
./.venv/bin/pytest -q -m docs_contract tests/contract/docs/general/test_api_documentation_inventory.py
./documentation/.cache/toolchain/python-venv/bin/pytest -q documentation/tests/contract/test_api_openapi_drift.py
./documentation/.cache/toolchain/python-venv/bin/pytest -q documentation/tests/contract/test_administrator_update_from_source_topics.py
./documentation/.cache/toolchain/python-venv/bin/pytest -q documentation/tests/contract/test_api_devops_integration_runbooks.py
./.venv/bin/python documentation/tools/validate_metadata.py
make docs-validate
```

Run only the inventory tests that match the changed source. If the refresh changes generated
artifact contents or manifest mappings, also run `make docs-reproducibility-check` and package
verification.

## Done

- Inventory drift is resolved at the maintained inventory/generator boundary, not patched in built
  HTML or generated output.
- Provenance and license restrictions still match the accepted matrix.
- A future topic author can trace each fact to the maintained inventory and its focused test.
- Changed source-install commands have fresh attempt-isolated evidence from retained clean images;
  unchanged Docker resources remain available for later validation.
- Windows 10/11 WSL claims remain unverified until the maintained runner succeeds on each actual
  Windows host.
- Deployment, update, and integration topics keep locale navigation/search, contextual targets,
  Administrator API ownership, and localized theme/search/help behavior aligned.
