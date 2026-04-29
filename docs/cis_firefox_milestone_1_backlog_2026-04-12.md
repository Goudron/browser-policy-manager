# CIS Firefox Milestone 1 Backlog

Date: 2026-04-12

Milestone 1 goal: store the CIS Firefox Benchmark in the repository as a versioned, validated source artifact that can later generate our CIS policy layers and be overlaid on base profiles.

This milestone does not need to change the wizard or export behavior yet. It should create the foundation: data shape, source metadata, mapping statuses, first-pass validation, and a coverage report.

## Scope

Included in Milestone 1:

- folder structure for CIS Firefox artifacts;
- YAML format for the source benchmark file;
- YAML format for the mapping file;
- YAML format for source metadata;
- recommendation coverage statuses;
- first-pass validators;
- coverage report;
- data integrity tests.

Excluded from Milestone 1:

- wizard UI;
- merge engine;
- final L1/L2 policy layer generation;
- database migrations;
- audit trail for saved profiles;
- full PDF import automation.

## Proposed Files

```text
app/
  compliance/
    __init__.py
    firefox/
      __init__.py
      cis/
        README.md
        sources.yaml
        firefox_esr_gpo_1_0_0.yaml
        mappings.yaml
        schema.yaml
tools/
  cis_firefox/
    validate_sources.py
    coverage_report.py
tests/
  compliance/
    test_cis_firefox_sources.py
    test_cis_firefox_mappings.py
```

`schema.yaml` is optional for the first implementation, but recommended. It can document the expected shape even before we add full JSON Schema validation.

## Source Policy

The authoritative source for the initial benchmark data should be an official CIS PDF downloaded from the CIS website, CIS Portal, or CIS WorkBench. Unofficial mirrors may be useful for discovery, but they should not be treated as authoritative source material.

The baseline target is:

- `CIS Mozilla Firefox ESR GPO Benchmark`
- version `1.0.0`
- release date `2024-07-19`

The exact release date is confirmed from the official CIS PDF provided for curation. The public CIS August 2024 update independently establishes that this benchmark was released in July 2024.

## Source Metadata Format

File: `app/compliance/firefox/cis/sources.yaml`

Purpose: track upstream benchmark identity and update history.

Draft:

```yaml
benchmarks:
  - id: cis-firefox-esr-gpo
    upstream_name: CIS Mozilla Firefox ESR GPO Benchmark
    upstream_version: 1.0.0
    product: Mozilla Firefox
    product_family: Desktop Software
    benchmark_page_url: https://www.cisecurity.org/benchmark/mozilla_firefox
    public_versions_page_url: https://www.cisecurity.org/cis-benchmarks
    release_window: 2024-07
    exact_release_date: 2024-07-19
    exact_release_date_status: confirmed_from_official_pdf
    official_update_article_url: https://portal.cisecurity.org/insights/articles/cis-benchmarks-august-2024-update
    official_source_required: true
    official_source_status: imported
    official_source_pdf: source_materials/CIS_Mozilla_Firefox_ESR_GPO_Benchmark_v1.0.0.pdf
    imported_at: 2026-04-12
    source_file: firefox_esr_gpo_1_0_0.yaml
    mapping_file: mappings.yaml
    notes:
      - Public CIS page lists Mozilla Firefox ESR GPO (1.0.0) as the current enterprise/GPO benchmark line.
      - CIS August 2024 update lists this benchmark as newly released last month, so release window is July 2024.
      - Initial recommendation data should be curated from an official CIS download, not from third-party mirrors.
```

Acceptance criteria:

- Each benchmark id is unique.
- `source_file` exists.
- `mapping_file` exists.
- `upstream_version` is present.
- `release_window` is present when exact date is unknown.
- URL fields are syntactically valid enough for documentation.
- Official source status is explicit.

## Benchmark Recommendation Format

File: `app/compliance/firefox/cis/firefox_esr_gpo_1_0_0.yaml`

Purpose: store CIS recommendations in a stable internal shape.

Draft:

```yaml
benchmark:
  id: cis-firefox-esr-gpo
  upstream_name: CIS Mozilla Firefox ESR GPO Benchmark
  upstream_version: 1.0.0
  source_url: https://www.cisecurity.org/benchmark/mozilla_firefox

recommendations:
  - id: "1.1.1"
    title: "Ensure 'Example setting' is set to 'Enabled'"
    level: 1
    assessment: automated
    scored: true
    category: browser_security
    subcategory: tls
    rationale_summary: "Concise internal summary."
    remediation_summary: "Concise internal summary."
    expected_state:
      kind: gpo
      value: enabled
      raw_value: "Enabled"
    mapping_status: mapped
    tags:
      - tls
      - enterprise_policy
```

Field notes:

- `id`: CIS recommendation id as a string. Keep original numbering.
- `title`: CIS recommendation title. Avoid embedding long prose until licensing is reviewed.
- `level`: integer `1` or `2`.
- `assessment`: `automated`, `manual`, or `unknown`.
- `scored`: boolean or `unknown`.
- `category` and `subcategory`: our internal grouping for UI/reporting.
- `rationale_summary` and `remediation_summary`: short internal summaries, not copied CIS text.
- `expected_state`: upstream control intent before mapping to Firefox policy format.
- `mapping_status`: high-level state mirrored by `mappings.yaml`.

Allowed `mapping_status` values:

- `mapped`: can map to Firefox Enterprise Policy.
- `preference_mapped`: can map to Firefox preference, not first-class policy.
- `manual`: recommendation is valid but cannot be safely automated.
- `not_applicable`: recommendation does not apply to our product/export model.
- `needs_research`: not yet analyzed.
- `deprecated_or_removed`: target appears obsolete in modern Firefox.

Acceptance criteria:

- Every recommendation has `id`, `title`, `level`, `assessment`, `category`, and `mapping_status`.
- `level` is only `1` or `2`.
- Recommendation ids are unique.
- No recommendation uses a mapping status outside the allowed set.
- No long CIS prose is stored without explicit licensing decision.

## Mapping Format

File: `app/compliance/firefox/cis/mappings.yaml`

Purpose: map CIS recommendation ids to app-understandable Firefox policy/preference targets.

Draft:

```yaml
benchmark_id: cis-firefox-esr-gpo
upstream_version: 1.0.0

mappings:
  - recommendation_id: "1.1.1"
    status: mapped
    confidence: high
    targets:
      - kind: policy
        path: ["DisableTelemetry"]
        value: true
        merge_rule: boolean_true_is_stricter
        schema_channels:
          release-149: valid
          esr-140.9: valid
    notes:
      mapping_reason: "Firefox Enterprise Policy equivalent."
      review_note: null
```

Target kinds:

- `policy`: Firefox Enterprise Policy path.
- `preference`: Firefox preference path under `Preferences`.
- `manual`: product should show guidance but not auto-apply.
- `unsupported`: known recommendation but cannot be represented.

Allowed mapping `status` values:

- `mapped`
- `preference_mapped`
- `manual`
- `not_applicable`
- `needs_research`
- `deprecated_or_removed`

Allowed `confidence` values:

- `high`
- `medium`
- `low`

Acceptance criteria:

- Every mapping references an existing recommendation id.
- Every non-manual/non-unsupported target has a `kind`, `path`, and `value`.
- `policy` paths have at least one element.
- `preference` paths identify a preference key.
- `schema_channels` keys match supported schema channels where provided.
- Mapping statuses match source recommendation statuses, or the validator explains the mismatch.

## Coverage Report

Tool: `tools/cis_firefox/coverage_report.py`

Purpose: answer "how complete and safe is our CIS import?"

Suggested output, Markdown and JSON:

```text
CIS Firefox ESR GPO v1.0.0 coverage

Total recommendations: 120
Mapped to policies: 82
Mapped to preferences: 18
Manual: 7
Not applicable: 3
Needs research: 10
Deprecated or removed: 0

By level:
L1: ...
L2: ...

Schema compatibility:
release-149 valid: ...
esr-140.9 valid: ...
invalid: ...
unknown: ...
```

Acceptance criteria:

- Report groups by `mapping_status`.
- Report groups by level.
- Report identifies recommendations missing mappings.
- Report identifies mappings without source recommendations.
- Report identifies schema compatibility gaps.
- Report exits non-zero in strict mode when required fields are missing.

## Validator

Tool: `tools/cis_firefox/validate_sources.py`

Purpose: fast local quality gate for CIS source data.

Validation checks:

- source YAML parses;
- metadata files point to existing files;
- recommendation ids are unique;
- recommendation levels are valid;
- statuses are valid;
- mappings point to existing recommendation ids;
- every recommendation has a mapping entry, even if `needs_research`;
- every `policy` target path is structurally valid;
- every `preference` target has a preference key;
- no duplicate targets for the same recommendation unless explicitly allowed;
- no generated output is required at this milestone.

Acceptance criteria:

- `python tools/cis_firefox/validate_sources.py` succeeds on the initial dataset.
- The command prints a compact summary.
- The command can be used by tests without network access.

## Tests

Suggested tests:

- `test_cis_sources_have_unique_recommendation_ids`
- `test_cis_sources_use_known_mapping_statuses`
- `test_cis_mappings_reference_existing_recommendations`
- `test_cis_recommendations_all_have_mapping_entries`
- `test_cis_policy_targets_have_valid_paths`
- `test_cis_coverage_report_counts_statuses`

These tests should not require CIS network access or downloaded PDFs. The source artifact in the repo is the test input.

## Backlog Items

Current status:

- CIS-M1-001: completed.
- CIS-M1-002: completed with `official_source_status: imported`.
- CIS-M1-003: completed for the initial contract.
- CIS-M1-004: completed for the initial recommendation skeleton.
- CIS-M1-005: completed for the initial contract.
- CIS-M1-006: completed.
- CIS-M1-007: completed.
- CIS-M1-008: completed.
- CIS-M1-009: completed as a repository-local boundary statement; CIS PDF Benchmarks are treated as CC-BY-NC-SA-4.0 source material, not MPL-2.0 code.
- CIS-M1-010: completed for Milestone 2 handoff.

### CIS-M1-001: Create Compliance Folder Structure

Create package/data directories for CIS Firefox artifacts.

Done when:

- `app/compliance/firefox/cis/` exists.
- `README.md` explains purpose and update policy.
- Python packages have `__init__.py` where needed.

### CIS-M1-002: Add Source Metadata

Create `sources.yaml` for `cis-firefox-esr-gpo` version `1.0.0`.

Done when:

- metadata includes upstream name, version, release window, source URLs, imported date, and source file references;
- metadata states that official CIS source material is required;
- validator checks referenced files exist.

### CIS-M1-003: Define Recommendation YAML Contract

Document and enforce required recommendation fields.

Done when:

- `schema.yaml` or README documents required/optional fields;
- validator catches missing `id`, `title`, `level`, `assessment`, `category`, `mapping_status`;
- tests cover invalid examples through small fixtures or direct validation functions.

### CIS-M1-004: Enter Initial CIS Recommendation Skeleton

Create initial `firefox_esr_gpo_1_0_0.yaml`.

Done when:

- all recommendations from the official CIS source are represented;
- each has level and mapping status;
- entries that are not yet mapped are marked `needs_research`;
- no long copyrighted CIS prose is included.

### CIS-M1-005: Define Mapping YAML Contract

Create `mappings.yaml` with target kinds, statuses, confidence, and notes.

Done when:

- every recommendation has a mapping row;
- each mapping status is valid;
- `needs_research` is allowed without targets;
- mapped entries require targets.

### CIS-M1-006: Build Source Validator

Implement `tools/cis_firefox/validate_sources.py`.

Done when:

- local command validates source and mapping files;
- command exits non-zero on malformed data;
- command has no network dependency.

### CIS-M1-007: Build Coverage Report

Implement `tools/cis_firefox/coverage_report.py`.

Done when:

- report prints total counts, status counts, level counts, and gaps;
- report can emit JSON for future CI or UI use;
- tests cover count behavior.

### CIS-M1-008: Add Milestone 1 Tests

Add test coverage for source and mapping integrity.

Done when:

- tests fail on duplicate recommendation ids;
- tests fail on mapping to unknown recommendation;
- tests fail when a recommendation has no mapping row;
- tests fail on invalid status or level.

### CIS-M1-009: Decide Licensing Boundary

Document what CIS text can be stored in the repo.

Done when:

- README and NOTICE state whether we store titles only, short summaries, or full text;
- long CIS prose is excluded unless legal/product explicitly approves it;
- source attribution is retained.

### CIS-M1-010: Prepare Milestone 2 Handoff

Document the inputs expected by the generator.

Done when:

- `mappings.yaml` contains enough information for generation;
- open questions for preference mapping and schema validation are listed;
- Milestone 2 can start without changing the Milestone 1 data shape.

## Recommended Execution Order

1. CIS-M1-001
2. CIS-M1-002
3. CIS-M1-003
4. CIS-M1-005
5. CIS-M1-006
6. CIS-M1-008
7. CIS-M1-004
8. CIS-M1-007
9. CIS-M1-009
10. CIS-M1-010

The reason to implement the validator before entering the full recommendation skeleton is practical: it gives immediate feedback while data is being curated.

## Open Questions Before Implementation

- Do we have an official downloaded CIS PDF available locally, or should the initial skeleton wait until one is provided?
- Should exact CIS titles be stored, or should titles be paraphrased too?
- Should `Preferences` be allowed in MVP source mappings, or postponed to Milestone 2?
- Should generated layer files be committed later, or generated on demand?
- Should existing saved profiles eventually pin to the CIS version used at creation?
