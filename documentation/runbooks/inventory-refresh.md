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
   `tests/test_firefox_policy_documentation_inventory.py`.
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
8. Do not add AI/RAG/embeddings/generative search behavior as part of a schema bump. Firefox
   product policies about AI still remain valid documentation subject matter.

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

1. Rebuild or check the maintained CIS inventory first with `tests/test_cis_documentation_inventory.py`.
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
   generative answers.
7. Review screenshots when a refresh changes documented UI state, source labels, review states,
   CIS layer labels, Guided Editor summaries, All Settings rows, comparison output, validation
   screens, or export screens. Queue locale-specific screenshots under
   `documentation/assets/screenshots/{locale}/` before release readiness.
8. Run the focused CIS checks first, then metadata/link/build checks. If generated artifacts,
   manifest data, search data, or package inputs changed, also run reproducibility and package
   verification before release readiness.

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
   - `documentation/tests/contract/test_administrator_linux_deployment.py`
   - `documentation/tests/contract/test_administrator_windows_wsl_deployment.py`
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

## Focused checks

Use the exact inventory builder/test first, then metadata and DITA checks:

```bash
./.venv/bin/pytest -q -m docs_contract tests/test_firefox_policy_documentation_inventory.py
./.venv/bin/python documentation/tools/generate_firefox_policy_skeletons.py
./.venv/bin/pytest -q -m docs_contract documentation/tests/contract/test_firefox_policy_skeleton_generation.py
./.venv/bin/pytest -q -m docs_contract documentation/tests/contract/test_manifest_generation.py
./.venv/bin/pytest -q -m docs_contract tests/test_cis_documentation_inventory.py
./.venv/bin/pytest -q -m docs_contract tests/test_api_documentation_inventory.py
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
