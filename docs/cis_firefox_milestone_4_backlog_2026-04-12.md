# CIS Firefox Milestone 4 Backlog

Date: 2026-04-12

Milestone 4 goal: expose CIS Firefox hardening as an optional wizard layer over the existing starter baselines, using the backend merge engine as the source of truth.

## Current Status

- CIS-M4-001: completed.
- CIS-M4-002: completed.
- CIS-M4-003: completed.
- CIS-M4-004: completed.
- CIS-M4-005: completed for review and handoff surfaces.
- CIS-M4-006: completed.
- CIS-M4-007: completed as a Milestone 5 handoff contract.

## Implemented Slice

The wizard starter catalog now exposes:

- available CIS overlay choices: no CIS, CIS Level 1, CIS Level 2;
- precomputed merged policy documents for each starter baseline, CIS choice, and supported Firefox schema channel;
- merge summary counters for the UI;
- compact merge decision rows for source labels and manual-review details;
- a managed-key union that allows switching CIS on or off without leaving stale CIS-only top-level policy keys in the editor.

The first wizard step now lets the user choose:

- operational scenario and starter baseline;
- CIS overlay level;
- no CIS overlay.

`CIS Level 2` is generated and applied as `Level 1 + Level 2`.

## Business Rules Preserved

- Base-only policies remain in the effective document.
- CIS-only policies are added when an overlay is selected.
- Equal base and CIS values are treated as already satisfied.
- Known strictness rules choose the stricter value.
- Manual-review conflicts keep the base value until the user changes it explicitly.
- The final editor document remains a normal Firefox policies document and can be edited in later wizard steps.

## Backlog Items

### CIS-M4-001: Extend Starter Catalog Contract

Add compliance layer metadata and precomputed merged presets to the existing wizard starter catalog.

Done when:

- catalog includes `compliance_layers`;
- catalog includes `compliance_merged_presets`;
- generated merged documents are schema-channel aware;
- tests cover a representative CIS L2 merge.

### CIS-M4-002: Add Step 1 CIS Selector

Add a user-facing selector for no CIS, CIS Level 1, and CIS Level 2.

Done when:

- selector is visible in Step 1;
- Level 2 copy clearly says it includes Level 1;
- English and Russian UI strings are present;
- page smoke tests assert the selector is rendered.

### CIS-M4-003: Apply Merged Presets In The Wizard

Use backend-computed merged documents instead of duplicating CIS strictness rules in JavaScript.

Done when:

- selecting a starter applies the selected CIS overlay;
- changing the CIS overlay reapplies the current starter;
- switching CIS off removes CIS-only managed keys;
- `keep_current` remains a no-reset path and does not apply CIS automatically.

### CIS-M4-004: Add Wizard And Export Summary

Surface the selected CIS overlay and high-level merge effects in summary areas.

Done when:

- Step 1 summary includes CIS overlay effects;
- preview copy includes CIS when selected;
- Review & export shows the selected CIS overlay.

### CIS-M4-005: Add Source Badges In Guided Settings

Show source context for CIS decisions in the wizard review and handoff surfaces.

Done when:

- settings raised by CIS are labelled in the technical drilldown;
- settings already stricter in the base can be represented from merge decisions;
- manual-review values are labelled;
- labels are derived from merge decisions, not hardcoded per screen.

### CIS-M4-006: Add Manual Review Details

Expose manual-review conflicts clearly before export.

Done when:

- review step lists manual-review paths;
- each item explains why the base value was kept;
- users can jump to the relevant guided section or advanced document location.

### CIS-M4-007: Prepare Persistence Handoff

Prepare the data contract for saved compliance metadata.

Done when:

- selected CIS overlay, benchmark version, summary counts, and compact merge decisions have a proposed storage shape;
- API and migration work are deferred to Milestone 5.

Suggested Milestone 5 metadata shape:

```json
{
  "compliance": {
    "framework": "cis",
    "benchmark_id": "cis-firefox-esr-gpo",
    "benchmark_version": "1.0.0",
    "layer": "cis_l2",
    "summary": {
      "added_from_cis": 20,
      "already_satisfied": 15,
      "manual_review_kept_base": 4,
      "review_required": 4
    },
    "decisions": [
      {
        "path": ["Proxy", "Mode"],
        "decision": "manual_review_kept_base",
        "recommendation_ids": ["1.1.18"],
        "review_required": true,
        "reason": "Proxy governance may be environment-specific."
      }
    ],
    "user_exceptions": []
  }
}
```

## Residual Risks

- The current wizard slice applies CIS at baseline-selection time. If a user later returns to Step 1 and changes the starter or CIS level, the baseline is reapplied and can overwrite later edits in managed CIS/base areas.
- `keep_current` intentionally stays a preservation path. Applying CIS over arbitrary current editor state should be handled by a later explicit "overlay current draft" flow if the product needs it.
- Detailed CIS provenance is not persisted yet. That belongs to Milestone 5.

## Next Handoff

Milestone 5 should add persistence and audit metadata:

- selected CIS level;
- upstream benchmark id and version;
- merge summary and decisions;
- user override notes or exception reasons.
