# All Settings Single-Surface Decision

Date: 2026-06-12

Backlog item: `BPM088-M2-01`

This note records the BPM 0.8.8 product decision for the All settings work.
The release improves the existing `/profiles/{profile_id}/settings` route
instead of adding a new full-settings route, tab, or standalone interface.

## Decision

All settings remains the single product surface for complete visual inspection
and editing of schema-backed Firefox policy and managed-preference settings.
BPM 0.8.8 changes the route architecture and default workflow inside that
surface, but it does not create another destination for "all controls".

The route keeps this boundary:

- Library opens All settings through `/profiles/{profile_id}/settings`.
- Guided editor remains the shorter task-first workflow for common scenarios.
- JSON editor remains the direct `policies.json` document editor.
- All settings owns full visual inventory, technical review, configured-state
  scanning, catalog discovery, search, and detail editing for full control.

## Non-Goal

Creating a separate interface for every setting is explicitly out of scope for
BPM 0.8.8. A second full-control surface would add another navigation decision,
duplicate editing semantics, split search/detail behavior, and make enterprise
profiles harder to reason about when starter presets, CIS layers, manual edits,
raw fallback values, and imported unknown settings coexist.

The problem to solve is not missing route capacity. The problem is that the
current All settings default presents too much of the complete catalog at once.
The fix is to make the existing route triage-first and state-aware.

## Route Modes

BPM 0.8.8 organizes the current All settings route around three modes:

| Mode | Purpose | Default content |
| --- | --- | --- |
| Review | Triage work that needs attention before export or handoff. | Invalid, CIS manual-review, raw fallback, unknown, deprecated, and imported review items. |
| Configured | Inspect what this profile actually applies. | Configured policy and preference entries, grouped by domain/category and source. |
| Catalog | Browse the full available policy and preference inventory. | Available and catalog-only settings, with search and detail editing. |

These modes are route state, not separate product surfaces. They share one
selected-entry model, one search/detail path, one validation mapping, and one
source-attribution model.

## Expected Workflow

For heavy enterprise profiles, All settings should open with review context
before catalog breadth. A profile built from a corporate preset plus a CIS layer
should show what needs review, what was configured, why each setting exists,
and where the setting came from without requiring the user to scroll through
every schema-backed control.

Users can still reach the complete catalog from the same route. The change is
progressive disclosure: Review and Configured make operational work visible
first, while Catalog preserves full coverage on demand.

## Architecture Implications

- All settings route state must be explicit enough to represent mode,
  selected entry, search query, focused target, expanded groups, counts, and
  active filters across rerenders.
- Settings inventory should become a shared model for review, configured,
  catalog, search, and detail rather than being rebuilt independently by list
  and search renderers.
- Source attribution must be first-class so entries can explain baseline, CIS,
  manual, imported, raw, unknown, and catalog-only states.
- Existing schema-shell and preference editors should be reused through detail
  editing instead of exposing duplicate always-visible editing paths.
- Existing route focus and search-result handoff must keep selecting the same
  setting predictably after the UI becomes mode-based.

## Guardrails

- Do not add a second full-settings route.
- Do not remove `/profiles/{profile_id}/settings`.
- Do not move complete visual control into Guided editor or JSON editor.
- Do not hide schema-backed settings permanently; Catalog remains the full
  coverage mode.
- Do not make Review or Configured depend on browser-only state that cannot be
  reconstructed from profile data, schema catalogs, validation, and merge
  metadata.
