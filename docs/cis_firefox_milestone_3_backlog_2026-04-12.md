# CIS Firefox Milestone 3 Backlog

Date: 2026-04-12

Milestone 3 goal: merge a selected base profile scenario with a generated CIS Firefox layer while preserving stricter or operationally important base choices and producing an explainable merge report.

## Current Status

- CIS-M3-001: completed.
- CIS-M3-002: completed.
- CIS-M3-003: completed.
- CIS-M3-004: completed.
- CIS-M3-005: completed.
- CIS-M3-006: completed by the Milestone 4 starter-catalog contract.

## Merge Semantics

Inputs:

- base scenario policy document;
- generated CIS layer;
- CIS mapping metadata;
- manual-review merge rules.

Outputs:

- effective policy document;
- per-path merge decisions;
- summary counts.

Decision types:

- `added_from_cis`: CIS defines the setting and the base scenario does not.
- `kept_base_only`: base scenario defines the setting and CIS does not.
- `already_satisfied`: base scenario already matches CIS.
- `cis_replaced_base`: CIS value is stricter by a known rule.
- `kept_base_stricter`: base value is stricter by a known rule.
- `manual_review_kept_base`: automatic strictness comparison is unsafe, so the base value is preserved and review is required.

## Manual Review Families

These policy areas are intentionally not resolved by simple boolean strictness:

- update governance: `AppAutoUpdate`, `BackgroundAppUpdate`, `DisableAppUpdate`, `DisableSystemAddonUpdate`;
- proxy governance: `Proxy.Mode`, `Proxy.Locked`;
- forensic-preservation versus cleanup: `SanitizeOnShutdown.Sessions`, `SanitizeOnShutdown.History`, `SanitizeOnShutdown.FormData`.

For these conflicts, the merge engine keeps the base scenario and asks the UI/review step to surface the decision.

## Current Basic Corporate + CIS L2 Shape

For `basic_corporate` overlaid with CIS Level 2 on `release-149`, the current merge summary is:

```text
added_from_cis: 20
already_satisfied: 15
kept_base_only: 20
manual_review_kept_base: 4
review_required: 4
```

Manual-review paths:

- `AppAutoUpdate`
- `DisableAppUpdate`
- `DisableSystemAddonUpdate`
- `Proxy.Mode`

## Backlog Items

### CIS-M3-001: Add Merge Rule Metadata

Add a rules file for policy paths that require manual review or policy-specific comparison.

Done when:

- update-governance paths are explicitly listed;
- proxy-governance paths are explicitly listed;
- sanitize-on-shutdown forensic conflicts are explicitly listed.

### CIS-M3-002: Add Pure Merge Engine

Implement backend merge logic independent from the wizard UI.

Done when:

- base-only settings are preserved;
- CIS-only settings are added;
- equal values are reported as already satisfied;
- known strictness rules can choose CIS or base;
- unknown conflicts keep base and require review.

### CIS-M3-003: Add CIS Target Metadata

Attach recommendation ids and merge rules to decisions.

Done when:

- decisions include recommendation ids where available;
- decisions include merge rule names where available;
- preference targets map to effective `Preferences.<key>` paths.

### CIS-M3-004: Validate Effective Documents

Validate merged output against supported Firefox schemas.

Done when:

- representative base presets merged with CIS validate against `release-149`;
- tests cover at least basic corporate, blank, and SOC hardening.

### CIS-M3-005: Add Scenario Tests

Add tests for expected business behavior.

Done when:

- CIS L2 includes L1 plus L2 after merge;
- basic corporate keeps update/proxy governance for review;
- classroom kiosk keeps website filtering, global extension blocking, allowed classroom permissions, and homepage settings;
- base-only settings such as homepage and extension blocking survive;
- CIS hardening such as developer tools and TLS settings are added;
- SOC sanitize conflicts are surfaced for review.

### CIS-M3-006: Prepare UI Handoff

Prepare the wizard integration contract.

Done when:

- merge result can be serialized to JSON;
- UI can read summary counts and decision rows;
- decision labels are mapped to user-facing copy.

## Next Handoff

Milestone 4 should integrate this into the wizard:

- Step 1 CIS selector: none, Level 1, Level 2;
- apply base preset first, CIS layer second, user edits last;
- show source labels and manual-review items in relevant steps;
- show merge summary on Review & export.
