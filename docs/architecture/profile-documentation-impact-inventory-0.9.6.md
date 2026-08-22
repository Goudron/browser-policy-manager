# BPM 0.9.6 Profile documentation and help impact inventory

Date: 2026-08-21

Backlog item: `BPM096-M10-01`

Status: active implementation inventory. This ledger assigns reader and source
owners for the delivered 0.9.6 profile lifecycle. It changes no product
behavior, reader DITA, guide map, runtime help target, search index, screenshot,
API, or generated artifact.

## Decision

All four published guide maps are affected and reviewed. The User Guide owns
the reader workflow; Firefox Policy owns Firefox-policy meaning and schema
support; CIS Settings owns benchmark/source interpretation; Administrator owns
operator, deployment, and public API boundaries. API Integration remains a
section of Administrator, not a fifth guide. A cross-link is allowed, but each
behavior below has one primary reader owner.

M10-02 updates English DITA, M10-03 its localized peers, and M10-04 alone
refreshes contextual-help target inputs, aliases, search/map/manifest inputs,
and approved localized screenshot sources. Generated site, search, manifest,
PDF, package, and installed-site output are rebuilt, never edited.

## Normative impact fixture

<!-- bpm096-profile-documentation-impact-inventory-v1 -->
```json
{
  "inventory_id": "bpm096-profile-documentation-impact",
  "inventory_version": 1,
  "backlog_item": "BPM096-M10-01",
  "target_bpm_version": "0.9.6",
  "source_locale": "en",
  "localized_peer_locales": ["ru", "de", "zh-CN", "fr", "es-ES"],
  "guide_maps": {
    "user-guide": {
      "review": "affected",
      "primary_reader": "profile author",
      "owners": ["atomic-create-duplicate", "eight-step-editor", "troubleshooting"],
      "source_topics": ["ug-task-create-first-profile", "ug-task-duplicate-profile", "ug-task-use-guided-editor", "ug-task-configure-browser-access-defaults", "ug-task-configure-security-privacy", "ug-task-configure-users-addons-sites", "ug-task-use-all-settings", "ug-task-use-json-editor", "ug-troubleshoot-profile-name", "ug-troubleshoot-schema-mismatch", "ug-troubleshoot-policy-validation"],
      "reason": "Creation, duplicate, editor topology, conversion recovery, and the three dedicated Guided domains changed reader-visible behavior."
    },
    "firefox-policy-guide": {
      "review": "affected",
      "primary_reader": "Firefox policy author",
      "owners": ["extension-policy-and-amo-boundary", "url-site-policy-shapes", "certificate-trust-policy-shapes"],
      "source_topics": ["fx-concept-policy-selection", "fx-concept-release-esr-differences", "fx-concept-bpm-firefox-boundary", "fx-concept-starter-presets", "fx-concept-complex-policy-families", "fx-task-review-complex-policy-configuration", "fx-reference-managed-preference-locking"],
      "reason": "The selected schema constrains policy shapes, supported controls, raw preservation, conversion blocks, and AMO's non-policy lookup boundary."
    },
    "cis-settings-guide": {
      "review": "affected",
      "primary_reader": "CIS baseline reviewer",
      "owners": ["preset-cis-selection", "baseline-and-value-attribution", "cis-conflict-and-manual-review"],
      "source_topics": ["cis-concept-orientation", "cis-concept-levels-channels-layers", "cis-task-select-cis-baseline", "cis-concept-presets-layers-merge", "cis-task-trace-cis-source", "cis-concept-manual-review-exceptions", "cis-task-verify-cis-deviation", "cis-task-run-level-1-workflow", "cis-task-run-level-2-hardened-workflow"],
      "reason": "Prepared baseline choices, read-only chrome, certificate attribution, and manual-review states must not be represented as a compliance claim."
    },
    "administrator-guide": {
      "review": "affected",
      "primary_reader": "administrator, DevOps operator, and API integrator",
      "owners": ["public-preparation-and-profile-api", "firefox-interchange", "deployment-and-support-boundary"],
      "source_topics": ["admin-concept-api-conventions", "admin-concept-api-limitations", "admin-task-use-reusable-api-examples", "admin-task-sync-profile-lifecycle", "admin-task-import-firefox-policies-json", "admin-task-export-firefox-policies-json", "admin-task-validate-firefox-policies-json", "admin-troubleshoot-import-export-failures", "admin-troubleshoot-schema-cache-validation"],
      "reason": "Preparation commands, additive profile fields, interchange envelopes, and safe conversion failure/recovery change supported operator and API facts."
    }
  },
  "untouched_guide_rule": "Every guide with review=unaffected must record a non-empty reason. No published guide is unaffected for BPM096-M10-01.",
  "reader_ownership": {
    "atomic-create-duplicate": {"guide": "user-guide", "topics": ["ug-task-create-first-profile", "ug-task-duplicate-profile", "ug-troubleshoot-profile-name"], "boundary": "Create and duplicate collect name, schema, preset, and CIS before one saved profile opens in Guided editor; a blocked conversion creates no target and does not mutate the source."},
    "eight-step-editor": {"guide": "user-guide", "topics": ["ug-task-use-guided-editor", "ug-task-configure-browser-access-defaults", "ug-task-configure-security-privacy", "ug-task-configure-users-addons-sites", "ug-task-use-all-settings", "ug-task-use-json-editor"], "boundary": "Schema, preset, and CIS are read-only facts in editor chrome; only preparation or explicit schema conversion changes them."},
    "extension-policy-and-amo-boundary": {"guide": "firefox-policy-guide", "topics": ["fx-concept-complex-policy-families", "fx-task-review-complex-policy-configuration"], "boundary": "AMO lookup is optional and explicit; no XPI/result URL is fetched, and unavailable AMO leaves manual GUID and validated URL entry available."},
    "url-site-policy-shapes": {"guide": "firefox-policy-guide", "topics": ["fx-concept-complex-policy-families", "fx-task-review-complex-policy-configuration"], "boundary": "Homepage, navigation, site filters, handlers, and managed bookmarks are one URLs/sites domain; unsafe or unsupported imported shapes are preserved or reviewed, never silently normalized."},
    "certificate-trust-policy-shapes": {"guide": "firefox-policy-guide", "topics": ["fx-concept-complex-policy-families", "fx-task-review-complex-policy-configuration"], "boundary": "Certificate references and device settings are literal values; BPM does not upload, open, hash, read, or validate certificate/device contents."},
    "preset-cis-selection": {"guide": "cis-settings-guide", "topics": ["cis-task-select-cis-baseline", "cis-concept-presets-layers-merge"], "boundary": "Preset and CIS choices occur during preparation; displayed identity never infers a benchmark claim from policy flags."},
    "baseline-and-value-attribution": {"guide": "cis-settings-guide", "topics": ["cis-task-trace-cis-source", "cis-concept-manual-review-exceptions"], "boundary": "Baseline provenance and extension/certificate attribution are separate; imported, manual, raw, or converted values do not promote a baseline claim."},
    "cis-conflict-and-manual-review": {"guide": "cis-settings-guide", "topics": ["cis-concept-manual-review-exceptions", "cis-task-verify-cis-deviation"], "boundary": "Manual-review, unavailable, invalidated, raw, and blocked states require recovery and never assert browser, deployment, or organization compliance."},
    "public-preparation-and-profile-api": {"guide": "administrator-guide", "topics": ["admin-concept-api-conventions", "admin-task-sync-profile-lifecycle", "admin-task-use-reusable-api-examples"], "boundary": "Document only public preparation/profile envelopes; clients cannot submit composed policy data, provenance, conversion candidates, or baseline display fields."},
    "firefox-interchange": {"guide": "administrator-guide", "topics": ["admin-task-import-firefox-policies-json", "admin-task-export-firefox-policies-json", "admin-task-validate-firefox-policies-json"], "boundary": "Import/export remains a full Firefox policies.json boundary; unsupported conversion preserves data or blocks, never silently drops policy values."},
    "deployment-and-support-boundary": {"guide": "administrator-guide", "topics": ["admin-troubleshoot-import-export-failures", "admin-troubleshoot-schema-cache-validation"], "boundary": "Recovery uses visible BPM/API errors and supported schema artifacts; it does not prescribe database edits, source-tree work, credentials, or external AMO operations."}
  },
  "search_and_contextual_help": {
    "owner": "BPM096-M10-04",
    "source_inputs": ["documentation/config/search-normalization-aliases-0.9.0.json", "documentation/config/all-settings-help-target-map-0.9.1.json", "app/documentation/manifest.py", "app/documentation/site/ui-target-map.json"],
    "required_action_topics": {"preparation-create": "ug-task-create-first-profile", "preparation-duplicate": "ug-task-duplicate-profile", "guided-editor": "ug-task-use-guided-editor", "extensions": "fx-concept-complex-policy-families", "urls-sites-navigation": "fx-concept-complex-policy-families", "certificates-trust": "fx-concept-complex-policy-families", "cis-review": "cis-concept-manual-review-exceptions", "profile-api": "admin-task-sync-profile-lifecycle"},
    "rule": "Aliases resolve to canonical topic or policy identity; deterministic search remains separate from the documentation assistant; generated target maps are rebuilt, never hand-edited."
  },
  "screenshot_disposition": {
    "owner": "BPM096-M10-04",
    "matrix": "documentation/config/user-guide-screenshot-matrix-0.9.1.json",
    "affected_scenarios": ["library-overview", "guided-editor-overview", "guided-settings-search", "all-settings-review", "json-editor"],
    "new_required_subjects": ["preparation-create", "preparation-duplicate", "guided-step-2-urls-sites-navigation", "guided-step-4-certificates-trust", "guided-step-6-extensions"],
    "remove_or_replace": ["six-step-guided-editor-overview", "draft-only-create-flow", "inline-clone-name-panel"],
    "rule": "Each approved capture has one localized source asset, caption, and alt text; no cross-locale fallback or generated artifact is source evidence."
  },
  "stale_claim_dispositions": {
    "six-guided-steps": {"status": "replace", "locations": ["ug-task-use-guided-editor", "ug-task-configure-browser-access-defaults", "ug-task-configure-security-privacy", "ug-task-configure-users-addons-sites"], "replacement": "eight delivered steps and their one-domain owners"},
    "profile-baseline-guided-step": {"status": "replace", "locations": ["ug-task-use-guided-editor"], "replacement": "preparation owns name/schema/preset/CIS; the editor header displays read-only facts"},
    "new-profile-draft": {"status": "remove", "locations": ["ug-task-create-first-profile", "ug-task-use-all-settings", "ug-task-use-json-editor", "ug-troubleshoot-import-failure"], "replacement": "successful preparation creates one saved profile; a terminal failure creates none"},
    "draft-save-recovery": {"status": "remove", "locations": ["ug-task-create-first-profile", "ug-task-use-all-settings", "ug-task-use-json-editor"], "replacement": "use visible preparation, save, conversion, or validation recovery without draft-only persistence"},
    "inline-clone-name-panel": {"status": "replace", "locations": ["ug-task-duplicate-profile", "ug-troubleshoot-profile-name"], "replacement": "dedicated duplicate preparation form with suggested source name, schema, preset, CIS, conversion review, and one terminal Duplicate action"},
    "schema-selector-in-editor-chrome": {"status": "replace", "locations": ["ug-concept-choose-editor-surface", "ug-concept-schema-aware-behavior", "ug-task-use-guided-editor", "ug-task-use-all-settings", "ug-task-use-json-editor"], "replacement": "read-only selected schema/preset/CIS chrome and explicit schema-conversion entry"},
    "old-domain-ownership": {"status": "replace", "locations": ["ug-task-configure-browser-access-defaults", "ug-task-configure-security-privacy", "ug-task-configure-users-addons-sites"], "replacement": "URLs/sites step 2, certificates/trust step 4, extensions step 6; remove duplicate descriptions from prior hosts"}
  },
  "out_of_scope": ["authoring or translating reader DITA", "changing a guide map", "changing screenshot pixels", "changing search aliases or contextual target maps", "building site/PDF/package artifacts", "changing runtime product behavior"]
}
```

## Verification boundary

The focused contract proves all four maps are reviewed, each behavior/recovery
boundary has one primary guide, every referenced English topic key exists, no
guide is silently unaffected, and stale six-step/draft/inline-clone claims have
an explicit disposition. It does not prove reader prose, localization, help,
search, screenshots, or generated artifacts; those remain M10-02 through
M10-09 work.
