# BPM 0.9.6 Profile Editor Chrome Baseline Presentation Contract

Date: 2026-08-20

Backlog item: `BPM096-M2-06`

Status: active planning contract; it deliberately adds no template, browser module, API, locale
catalog, CSS, generated asset, or rendered UI behavior.

## Purpose and authority

This contract freezes the future saved-profile baseline presentation shared by the Guided, All
settings, and JSON editors. It is the presentation consumer of M2-04's server-owned
`baseline_display` projection: it never infers a starter or CIS fact from flags, raw compliance,
the current catalog, a route, or browser-local state. `schema_version` remains the saved-profile
schema authority; only the server resolves its exact saved identity for presentation.

Today all three editors include
[`_page_editor_chrome.html`](../../app/templates/profiles/_page_editor_chrome.html), which still
contains the draft/saved `#profile-type` selector. That is current characterization, not an
authorization to alter it here. M5-02 through M5-05 implement this contract and M5-06 proves the
runtime, DOM, payload, locale, responsive, and browser evidence. M4 preparation and M5 UI work
remain unimplemented by this record.

## Shared authoritative presentation

For one saved profile revision, each editor consumes the same server response/context and displays
one compact fact set. A surface may use localized labels, but it cannot substitute a newer catalog
entry, resolve a separate client catalog, or present a different identity, availability, status, or
claim. The profile name is a saved identity, not a baseline choice.

<!-- bpm096-editor-chrome-baseline-presentation-contract-v1 -->
```json
{
  "contract_id": "bpm096-profile-editor-chrome-baseline-presentation",
  "contract_version": 1,
  "status": "planning-only-no-runtime-change",
  "surfaces": ["guided", "all-settings", "json"],
  "shared_chrome": {
    "future_template_owner": "app/templates/profiles/_page_editor_chrome.html",
    "one_authoritative_fact_set_per_surface": true,
    "saved_profile_only": true,
    "facts": ["profile-name", "schema", "starter-preset", "cis-baseline"]
  },
  "authoritative_inputs": {
    "profile_name": {"source": "ProfileRead.name", "client_inference": "forbidden"},
    "schema": {"source": "ProfileRead.schema_version", "presentation": "server-resolved-exact-saved-schema-identity", "client_catalog_reconstruction": "forbidden"},
    "starter_preset": {"source": "ProfileRead.baseline_display.starter", "fields": ["identity_state", "catalog_id", "catalog_version", "availability"], "flags_or_catalog_inference": "forbidden"},
    "cis_baseline": {"source": "ProfileRead.baseline_display.cis", "fields": ["identity_state", "display_status", "baseline_id", "benchmark_id", "benchmark_version", "current_claim", "reason_code"], "flags_or_compliance_inference": "forbidden"},
    "cross_editor_parity": "same-saved-profile-revision-means-identical-locale-neutral-identities-availability-status-and-current-claim"
  },
  "read_only_boundary": {
    "schema_preset_cis_mutation_surfaces": ["preparation-create", "preparation-duplicate", "explicit-schema-conversion"],
    "forbidden_editor_controls": ["select", "radio", "checkbox", "text-input", "hidden-input", "contenteditable", "writable-shadow-state"],
    "forbidden_editor_payload_fields": ["schema_version", "target_schema_id", "starter_id", "cis_baseline_id", "baseline_provenance", "baseline_display"],
    "disabled_selector_is_not_read_only_presentation": true,
    "saved_profile_schema_change_path": "explicit-schema-conversion-only"
  },
  "starter_truth": {
    "catalog_available": "exact-saved-catalog-id-and-version",
    "custom_imported": "Custom/imported",
    "unavailable": "saved-identity-unavailable-with-reason",
    "replacement_or_flag_match": "forbidden"
  },
  "cis_truth": {
    "none": {"identity_state": "none", "display_status": "none", "current_claim": false, "display": "None"},
    "verified": {"identity_state": "catalog", "display_status": "verified", "current_claim": true, "display": "exact-baseline-identity-with-verified-evidence"},
    "manual_review": {"display_status": "manual-review", "current_claim": false, "display": "identity-or-Custom/imported-plus-manual-review-and-reason"},
    "invalidated": {"identity_state": "catalog", "display_status": "invalidated", "current_claim": false, "display": "historical-identity-plus-invalidated-and-reason"},
    "unavailable": {"display_status": "unavailable", "current_claim": false, "display": "saved-identity-unavailable-and-reason"},
    "prohibited_current_claim_statuses": ["none", "manual-review", "invalidated", "unavailable"],
    "prohibited_claims": ["current-benchmark", "replacement-baseline", "browser-deployment-or-organization-compliance"]
  },
  "accessibility": {
    "structure": "named-profile-heading-plus-semantic-read-only-fact-list",
    "each_fact": ["localized-label", "localized-value", "programmatic-value-association"],
    "noncurrent_cis": ["localized-status", "localized-reason", "local-recovery-or-next-action-when-required"],
    "status_updates": "announced-without-repeating-unrelated-header-content",
    "conversion_entry_accessible_name": "localized-explicit-schema-conversion-review-action"
  },
  "locale": {
    "source_catalog_roots": ["app/i18n_src/en", "app/i18n_src/ru", "app/i18n_src/de", "app/i18n_src/es-ES", "app/i18n_src/fr", "app/i18n_src/zh-CN"],
    "required_families": ["common", "wizard", "settings", "json"],
    "localized_categories": ["fact-label", "state", "reason", "recovery", "conversion-entry-accessible-name"],
    "generated_runtime_catalog_edit": "forbidden"
  },
  "responsive": {
    "authored_css_owners": ["app/static/profiles_css/23-workspace-editor.css", "app/static/profiles_css/30-responsive.css"],
    "generated_css_edit": "forbidden",
    "supported_narrow_viewport_px": 320,
    "requirements": ["facts-wrap-without-horizontal-page-overflow", "long-localized-labels-and-values-wrap", "labels-remain-associated-with-values", "no-fact-or-noncurrent-reason-is-hidden", "conversion-entry-remains-keyboard-reachable"]
  },
  "conversion_entry": {
    "owner": "existing-explicit-schema-conversion-flow",
    "shared_entry": "one-localized-review-action-in-shared-chrome-when-the-saved-profile-is-eligible",
    "entry_is_not": ["schema-selector", "schema-save-payload", "automatic-conversion", "baseline-reapply-control"],
    "unavailable_or_blocked": "truthful-localized-state-and-recovery-in-the-conversion-flow"
  },
  "future_owners": {
    "render_schema": "BPM096-M5-02",
    "render_starter": "BPM096-M5-03",
    "render_cis": "BPM096-M5-04",
    "remove_guided_baseline_controls": "BPM096-M5-05",
    "runtime_parity_proof": "BPM096-M5-06"
  }
}
```

## Truth and interaction rules

`verified` is evidence about the saved policy document against its pinned CIS baseline. It is not a
claim that a browser, deployment, or organization is compliant. `None` similarly says that no
server-composed CIS layer is recorded; it does not say the profile was reviewed. Manual-review,
invalidated, and unavailable are durable non-current states. Invalidated retains its historical
identity and reason; unavailable retains the saved identity when known and never silently selects a
replacement. A malformed or missing M2-04 projection fails closed to an unavailable/manual-review
fact with recovery, never to `verified` or `None`.

The fact list is read-only presentation, not a disabled form. Therefore a disabled `<select>`, a
hidden input used for synchronization, a shadow value copied into a save payload, or a client-side
starter/CIS reconstruction all violate this contract. Editor saves continue to modify only the
policy document fields they own; they cannot submit a schema or baseline mutation. Schema changes
remain possible only through the existing explicit review/confirmation flow, reached through its
one shared, localized action when eligible.

The implementation uses a named heading and a semantic list of label/value pairs. Each non-current
CIS fact exposes its status and reason to assistive technology and its required local recovery; a
visual chip or color alone is insufficient. Status updates are concise and do not repeatedly
announce the whole header. The conversion entry retains an explicit localized accessible name;
removing ordinary explanatory chrome never removes conversion consequences, blocker state,
confirmation, or recovery owned by the conversion surface.

## Ownership and verification boundary

Future locale source is authored only in the six roots named in the fixture. The relevant source
CSS owners are `23-workspace-editor.css` and `30-responsive.css`; `app/static/profiles.css` and
`app/i18n/` are generated outputs. Long labels, localized state/reasons, and the conversion action
wrap and remain reachable at the supported narrow viewport without hiding a fact or relying on
locale-specific CSS.

M5-06 exercises all three routes for the same saved profile/revision and asserts the exact
locale-neutral schema/preset/CIS identities, availability, status, and `current_claim`, the absence
of every prohibited control/payload path, every CIS truth state, six-locale accessibility, and
narrow/long-label layout. Existing owner tests include
`tests/contract/ui/profiles/test_wizard_shell_contracts.py`,
`tests/contract/ui/profiles/test_static_responsive_contracts.py`,
`tests/contract/ui/localization/test_web_profiles_page.py`, and
`tests/contract/ui/localization/test_responsive_long_label_css_contract.py`; later browser route
coverage is runtime proof, not this planning guard.
