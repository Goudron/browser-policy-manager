# CIS Benchmark for Firefox: preliminary product analysis

Date: 2026-04-12

## Context

Browser Policy Manager already has scenario presets for Firefox, including basic corporate, classroom kiosk, and SOC hardening. The new requirement is to let a user apply CIS Benchmark recommendations as an optional layer over any base scenario, while preserving the operational intent of the selected scenario.

The product should support at least two CIS choices:

- CIS Level 1: baseline hardening with low expected operational impact.
- CIS Level 2: defense-in-depth hardening for higher-risk environments, with higher chance of reduced usability or compatibility.

According to the current CIS public benchmark pages, Mozilla Firefox benchmark artifacts are available for Mozilla Firefox ESR GPO, Mozilla Firefox 102 ESR, and older Firefox 38 ESR. The current app schema targets modern Firefox channels such as release 149 and ESR 140.9, so importing CIS cannot be treated as a blind one-to-one copy. It needs a maintained mapping layer from CIS recommendations to current Firefox Enterprise policies and preferences.

Sources checked:

- https://www.cisecurity.org/benchmark/mozilla_firefox
- https://www.cisecurity.org/cis-benchmarks
- https://www.cisecurity.org/cis-benchmarks/cis-benchmarks-faq

## Business Goal

The feature should help an administrator start from a meaningful operational profile and then opt into a recognized hardening baseline without losing the scenario-specific behavior that made the profile useful.

In plain terms:

- A kiosk profile should remain a kiosk profile.
- A SOC profile should remain strongly restricted.
- CIS should raise the security floor where it is stronger.
- CIS should not weaken an already stricter base scenario.
- The user must still be able to review and tune individual settings before export.

## Primary Users

- IT administrator: wants a fast starting point and a valid policies.json export.
- Security engineer: wants CIS traceability and an explanation of which controls were applied.
- Compliance/audit stakeholder: wants evidence that a selected CIS level was considered, and wants to see exceptions.
- Product/operator: wants versioned, maintainable benchmark data rather than hard-coded one-off settings.

## Product Behavior

The recommended UX model is:

1. The user selects a base scenario preset: blank, current, basic corporate, kiosk, SOC, or future presets.
2. The user optionally enables CIS hardening.
3. If CIS is enabled, the user selects CIS Level 1 or CIS Level 2.
4. The product computes an effective policy document by merging:
   - the base scenario layer;
   - the selected CIS layer;
   - later user edits from the wizard.
5. The wizard shows CIS-originated settings and conflicts as reviewable decisions.
6. The final export contains the effective Firefox policy document, not separate layers.

The product should also keep enough metadata internally to explain the result:

- source: base preset, CIS Level 1, CIS Level 2, or user override;
- CIS recommendation id, when applicable;
- merge decision: added, kept base because stricter, replaced base because CIS stricter, unresolved/manual decision;
- exception reason, if the user overrides or disables a CIS recommendation.

## Merge Rules

The business rule is a security-preferential union:

- If a setting exists only in the base scenario, keep it.
- If a setting exists only in CIS, add it.
- If both layers set the same value, keep one value and mark both sources.
- If both layers set different values and CIS is stricter, use CIS.
- If both layers set different values and the base scenario is stricter, keep the base scenario.
- If strictness cannot be compared reliably, do not guess silently. Keep the scenario value by default and surface the conflict for review, unless the specific policy has a known comparator.

This requires policy-aware comparison. A generic boolean merge will be wrong for several Firefox settings.

Examples:

- `DisableTelemetry: true` is stricter than `false`.
- `DisablePrivateBrowsing: true` is stricter than `false`.
- Permission `BlockNewRequests: true` is stricter than allowing new requests.
- Blocklists usually merge by union because blocking more is stricter.
- Allowlists usually merge by intersection because allowing less is stricter, but this can break kiosk and classroom use cases, so the UI should flag the reduction.
- Extension installation mode needs a hierarchy. For example, `blocked` is stricter than `allowed`, but `force_installed` for a required security extension is not simply weaker or stronger than global blocking.
- Proxy, homepage, certificate roots, and DNS-over-HTTPS can be security-relevant but also environment-specific. These should have explicit comparators or be marked as operational conflicts.

## Data Model Proposal

Add benchmark layer data separate from scenario presets.

Suggested files:

- `app/compliance/firefox/cis/benchmark.yaml`
- `app/compliance/firefox/cis/mappings.yaml`
- `app/compliance/firefox/cis/merge_rules.yaml`

Suggested conceptual structure:

```yaml
benchmark:
  id: cis-firefox
  version: "Mozilla Firefox ESR GPO 1.0.0"
  imported_at: "2026-04-12"
  source_url: "https://www.cisecurity.org/benchmark/mozilla_firefox"

recommendations:
  - id: "cis-firefox-1.1"
    title: "..."
    level: 1
    scored: true
    target:
      type: policy
      path: ["DisableTelemetry"]
      value: true
    rationale_summary: "Short internal summary, not full CIS text."
    status: mapped
```

The app should avoid embedding large CIS text verbatim unless licensing is explicitly cleared. Store concise internal summaries, recommendation ids, mapping metadata, and policy values. Keep source attribution and benchmark version.

## Strictness Comparator Proposal

Create a merge engine with policy path rules, not ad hoc conditionals in the wizard.

Rule examples:

```yaml
rules:
  DisableTelemetry:
    type: boolean_true_is_stricter
  DisablePrivateBrowsing:
    type: boolean_true_is_stricter
  Permissions.*.BlockNewRequests:
    type: boolean_true_is_stricter
  WebsiteFilter.Block:
    type: list_union_is_stricter
  WebsiteFilter.Exceptions:
    type: list_intersection_is_stricter
    conflict_label: "CIS reduces site exceptions"
  ExtensionSettings.*.installation_mode:
    type: enum_rank
    order:
      allowed: 0
      normal_installed: 1
      force_installed: 2
      blocked: 3
    require_manual_when:
      - force_installed_vs_blocked
  Proxy:
    type: operational_manual
  DNSOverHTTPS:
    type: policy_specific
```

Comparator output should be structured:

- selected value;
- selected source;
- decision type;
- confidence;
- user-facing explanation;
- whether review is required.

## Wizard UX Proposal

Step 1 should gain a compliance layer choice:

- "No CIS layer"
- "CIS Level 1"
- "CIS Level 2"

Level 2 should imply Level 1 unless the imported benchmark says otherwise for a specific recommendation. The UI text should warn that Level 2 may reduce usability.

Throughout the wizard:

- CIS-applied settings should be marked with a small source label.
- Settings where base won over CIS should say "Base scenario is already stricter."
- Settings where CIS changed the base should say "Raised by CIS Level N."
- Unresolved conflicts should be shown in the relevant step and again on Review & export.
- User edits after the merge should become the top layer and should be recorded as an intentional override.

Review & export should include a CIS summary:

- selected CIS level;
- number of CIS recommendations mapped;
- number applied;
- number already satisfied by base scenario;
- number overridden by user;
- number unmapped or requiring manual review.

## API And Persistence Proposal

Profile records should store the selected compliance layer metadata, not only the resulting policy JSON.

Possible fields:

- `base_preset_key`
- `compliance_profile`: null, `cis_firefox_l1`, `cis_firefox_l2`
- `compliance_benchmark_version`
- `layer_decisions`: structured merge report
- `user_overrides`: paths explicitly changed after layer calculation

Exports can remain plain Firefox policy documents, but API responses and saved profile metadata should retain explainability.

## Implementation Plan

Phase 1: Foundation

- Add internal CIS benchmark/mapping files.
- Add a pure merge engine with policy-aware strictness rules.
- Add unit tests for union, stricter-wins, base-only, CIS-only, nested policies, and manual conflicts.
- Validate generated policies against existing Firefox schemas.

Phase 2: Product Integration

- Add CIS selection to the first wizard step.
- Extend starter catalog payload with available compliance layers.
- Apply CIS layer after base preset selection and before user edits.
- Add source badges and review summary.

Phase 3: Traceability

- Persist selected CIS level and merge decisions.
- Include compliance summary in profile details and review/export screen.
- Add an exception workflow for user overrides.

Phase 4: Maintenance

- Add a documented import/update process for future CIS benchmark versions.
- Add tests to detect mappings pointing to removed Firefox policies.
- Add a compatibility report for release and ESR channels.

## Key Risks

- CIS Firefox benchmark versions lag current Firefox releases. Mappings must be validated against current Enterprise Policy schemas.
- Some CIS recommendations may target GPO registry settings or preferences rather than Firefox `policies.json`.
- "Stricter" is not always total-order comparable. Some settings are environment-specific, especially proxy, certificate roots, search, extension exceptions, homepage, and DNS-over-HTTPS.
- Licensing needs review before embedding detailed CIS recommendation text.
- Level 2 can break user workflows; the product must make this visible before export.

## Recommended MVP Scope

For the first version, implement CIS as an optional layer over existing starter presets with:

- CIS Level 1 and Level 2 selectors;
- a curated mapping for recommendations that cleanly map to Firefox Enterprise policies or known preferences;
- strictness rules for high-confidence controls;
- manual conflict surfacing for ambiguous controls;
- review summary and export validation.

Do not promise full CIS certification in the UI at MVP stage. Use wording such as "CIS-aligned Firefox hardening" until mapping coverage, benchmark licensing, and audit evidence are mature enough to support stronger claims.

