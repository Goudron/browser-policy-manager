# CIS Firefox implementation roadmap

Date: 2026-04-12

## Current CIS Version Baseline

As of 2026-04-12, the public CIS Mozilla Firefox benchmark page lists these recent benchmark versions:

- Mozilla Firefox ESR GPO (1.0.0)
- Mozilla Firefox 102 ESR (1.0.0)
- Mozilla Firefox 38 ESR (1.0.0)

The same page lists CIS-CAT Pro coverage for Mozilla Firefox ESR GPO (1.0.0), and build kit coverage for Mozilla Firefox 102 ESR (1.0.0) and Mozilla Firefox ESR GPO (1.0.0).

The best implementation baseline for this product should be:

- `cis-firefox-esr-gpo`
- upstream benchmark version `1.0.0`
- upstream product label `Mozilla Firefox ESR GPO`
- release date: `2024-07-19`

Reasoning: CIS published an official "CIS Benchmarks August 2024 Update" article on 2024-08-02. In that article, `CIS Mozilla Firefox ESR GPO Benchmark v1.0.0` is listed under "New CIS Benchmarks Released Last Month", which places the release in July 2024. The official CIS PDF provided for curation confirms the exact title-page date as `2024-07-19`.

Primary public references:

- https://www.cisecurity.org/benchmark/mozilla_firefox
- https://www.cisecurity.org/cis-benchmarks
- https://portal.cisecurity.org/insights/articles/cis-benchmarks-august-2024-update

## Product Direction

CIS should be implemented as a versioned compliance source that can generate a hardening layer for Firefox profiles.

The app should not make CIS one more ordinary starter preset. The user should still choose an operational scenario first, then optionally apply a CIS layer:

- no CIS layer;
- CIS Level 1;
- CIS Level 2.

The generated result should be a normal Firefox policy document, but the app should retain source metadata and merge decisions for explainability.

## Repository Shape

Recommended high-level structure:

```text
app/
  compliance/
    firefox/
      cis/
        README.md
        sources.yaml
        firefox_esr_gpo_1_0_0.yaml
        mappings.yaml
        merge_rules.yaml
        generated/
          cis_l1.release-149.json
          cis_l2.release-149.json
          cis_l1.esr-140.9.json
          cis_l2.esr-140.9.json
tools/
  cis_firefox/
    import_benchmark.py
    validate_mappings.py
    generate_presets.py
    diff_versions.py
tests/
  compliance/
    test_cis_firefox_mapping.py
    test_cis_firefox_merge.py
    test_cis_firefox_generated_presets.py
```

The source CIS file should preserve recommendation-level structure, not just final policy values. The generated files should be disposable build artifacts or deterministic outputs that can be regenerated.

## Source Data Model

The source benchmark file should represent CIS recommendations in our own structured format:

```yaml
benchmark:
  id: cis-firefox-esr-gpo
  upstream_name: CIS Mozilla Firefox ESR GPO Benchmark
  upstream_version: 1.0.0
  release_window: 2024-07
  release_date: 2024-07-19
  imported_at: 2026-04-12
  source_url: https://www.cisecurity.org/benchmark/mozilla_firefox

recommendations:
  - id: "1.1.1"
    level: 1
    assessment: automated
    title: "Ensure 'Allow add-on installs from websites' is set to 'Disabled'"
    category: addons
    source_status: mapped
    target:
      kind: policy
      path: ["InstallAddonsPermission", "Default"]
      value: false
    notes:
      mapping_reason: "Firefox Enterprise policy equivalent."
```

The source data should avoid embedding long CIS prose unless licensing is explicitly reviewed. Recommendation ids, titles, profiles, expected values, and concise internal mapping notes should be enough for product behavior.

## Conversion Pipeline

The pipeline should be deterministic:

1. Curate or import CIS source recommendations into `firefox_esr_gpo_1_0_0.yaml`.
2. Map each recommendation to a Firefox Enterprise Policy path or known preference path.
3. Validate each mapped target against the current app schema channels.
4. Generate CIS Level 1 and Level 2 policy layers.
5. Run merge tests against our starter presets.
6. Produce a coverage report.

Level behavior:

- Level 1 contains all L1 recommendations.
- Level 2 contains L1 plus L2 recommendations, unless a future CIS version explicitly defines otherwise.

## Merge Engine

Implement a pure backend merge module before UI integration.

Inputs:

- base scenario document;
- CIS generated layer;
- strictness rules;
- schema version;
- optional user overrides.

Outputs:

- effective policy document;
- merge report;
- unresolved conflicts;
- source metadata by policy path.

The merge report is as important as the resulting JSON because the UI needs to explain why a value was selected.

## Roadmap

### Milestone 1: Source And Mapping Foundation

Goal: CIS recommendations live in the repository in a versioned, reviewable form.

Deliverables:

- Add `app/compliance/firefox/cis/` package/data folder.
- Add `sources.yaml` with current CIS version metadata.
- Add `firefox_esr_gpo_1_0_0.yaml` with the curated recommendation list.
- Add `mappings.yaml` for policy/preference mapping.
- Add a coverage report command showing mapped, unmapped, manual, deprecated, and schema-invalid recommendations.

Backlog candidates:

- Create source YAML schema.
- Enter initial CIS Firefox ESR GPO v1.0.0 recommendations.
- Add validation for duplicate CIS ids.
- Add validation for missing level/profile fields.
- Add validation for unsupported target kinds.

### Milestone 2: Generation And Validation

Goal: convert CIS source data into our policy-layer format.

Deliverables:

- `tools/cis_firefox/generate_presets.py`
- generated Level 1 and Level 2 layer documents per supported Firefox schema channel;
- tests that generated layers validate against release and ESR policy schemas;
- clear failures for recommendations that cannot be represented in `policies.json`.

Backlog candidates:

- Generate L1 layer.
- Generate L2 layer as L1 plus L2.
- Validate policy targets against `firefox-release-149.json` and `firefox-esr-140.9.json`.
- Support preference targets where no first-class policy exists.
- Produce a Markdown/JSON mapping coverage report.

### Milestone 3: Strictness Merge

Goal: combine base scenario and CIS layer using explicit security semantics.

Deliverables:

- backend merge module;
- `merge_rules.yaml`;
- unit tests for scalar, nested object, list, enum, and manual-conflict rules;
- integration tests for `basic_corporate`, `classroom_kiosk`, and `soc_hard` with CIS L1/L2.

Backlog candidates:

- Add boolean comparator rules.
- Add enum-rank comparator rules.
- Add list union/intersection rules.
- Add policy-specific comparators for `ExtensionSettings`, `Permissions`, `Cookies`, `EnableTrackingProtection`, `DNSOverHTTPS`.
- Mark proxy/homepage/certificates as operational review items unless rules are explicit.

### Milestone 4: Wizard Integration

Goal: make CIS selectable and reviewable in the existing profile wizard.

Deliverables:

- Step 1 compliance selector: none, CIS L1, CIS L2.
- starter catalog payload includes available compliance layers.
- generated CIS layer is applied after base preset and before user edits.
- source badges in settings UI.
- Review & export includes compliance summary and conflicts.

Backlog candidates:

- Add CIS selector UI.
- Add i18n strings.
- Show "raised by CIS", "already stricter in base", "manual review", and "user override" states.
- Add summary counters.
- Ensure every CIS-applied value remains editable before export.

### Milestone 5: Persistence And Audit Trail

Goal: saved profiles keep enough metadata to explain CIS decisions later.

Deliverables:

- profile metadata stores selected compliance layer and benchmark version;
- merge decisions are persisted;
- user overrides can carry exception notes;
- export remains a clean Firefox policies document.

Backlog candidates:

- Add model/API fields for compliance metadata.
- Add migration.
- Add API tests.
- Add profile detail compliance summary.
- Add exception notes for user overrides.

### Milestone 6: Update Workflow

Goal: make future CIS updates repeatable.

Deliverables:

- documented update runbook;
- version diff tool;
- mapping regression tests;
- release checklist for replacing or adding CIS versions.

Backlog candidates:

- Add command to compare old and new CIS recommendation sets.
- Mark added, removed, changed, and unchanged recommendations.
- Detect mappings that reference removed Firefox policies.
- Keep old CIS versions available for existing saved profiles.
- Add documentation for when to migrate default CIS version.

## Definition Of Done For MVP

- CIS Firefox ESR GPO v1.0.0 metadata is stored in the repo.
- L1 and L2 layers can be generated deterministically.
- Generated layers validate against supported Firefox schemas.
- Base presets can be merged with CIS without weakening stricter base values.
- Ambiguous conflicts are surfaced rather than silently resolved.
- The wizard lets users choose CIS level and then edit individual settings.
- Review screen shows applied, already satisfied, overridden, unmapped, and manual-review counts.

## Open Decisions

- Whether to commit generated CIS layer files or generate them at build/test time.
- Whether saved profiles should pin to the CIS version used at creation or automatically follow the latest version.
- Whether the first MVP should include preference-level recommendations or only Enterprise Policy recommendations.
- Whether CIS exact recommendation prose can be stored, or whether we store only concise internal summaries and source identifiers.
- Whether CIS update checks should be manual only or include a small command that checks CIS public pages.
