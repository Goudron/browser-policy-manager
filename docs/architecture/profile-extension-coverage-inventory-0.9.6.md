# BPM 0.9.6 Extensions coverage inventory

Date: 2026-08-21

Backlog item: `BPM096-M7-01`

Status: completed implementation evidence for `BPM096-M7-05`.  The inventory remains the
ownership ledger for the Extensions step while M7-06 through M7-08 add their bounded work.

## Decision

The one Guided owner for extension governance is **step 6, Extensions**.  A policy is not moved to
All settings merely because its value is nested or schema-dependent.  All typed Firefox extension
settings below therefore receive one Extensions-step control in `BPM096-M7-05`; its editor must
preserve the exact schema value and may expose a raw-preserving fallback for imported values it
cannot safely structure.  `3rdparty.Extensions.*.adminSettings` is the single explicit
All-settings-only exception: it is an add-on-defined opaque payload, rather than a Firefox
extension-governance shape, and BPM must not invent fields or normalize it.

M7-05 removed the old block from `_page_wizard_step_sync.html`; it was not copied.  The three
curated cards are legacy examples, not a BPM extension catalog or a recommendation.  M7-04
provides explicit AMO search results and M7-05 provides generic GUID rules.  No M7 task may
silently reintroduce a curated default.

## Normative coverage fixture

<!-- bpm096-profile-extension-coverage-inventory-v1 -->
```json
{
  "inventory_id": "bpm096-profile-extension-coverage",
  "inventory_version": 1,
  "backlog_item": "BPM096-M7-01",
  "guided_owner": {"step": 6, "id": "extensions"},
  "supported_schema_channels": ["release-153", "esr-153.0", "esr-140.13", "esr-115.39"],
  "policy_coverage": {
    "ExtensionSettings": {
      "disposition": "extensions-step-control",
      "delivery": "BPM096-M7-05",
      "paths": [
        "<guid-or-*>.installation_mode",
        "<guid-or-*>.blocked_install_message",
        "<guid-or-*>.install_sources",
        "<guid-or-*>.allowed_types",
        "<guid-or-*>.install_url",
        "<guid-or-*>.updates_disabled",
        "<guid-or-*>.update_url",
        "<guid-or-*>.default_area",
        "<guid-or-*>.private_browsing",
        "<guid-or-*>.restricted_domains",
        "<guid-or-*>.temporarily_allow_weak_signatures",
        "<guid-or-*>.allowed_permissions [153 only]",
        "<guid-or-*>.blocked_permissions [153 only]",
        "<guid-or-*>.runtime_allowed_hosts [153 only]",
        "<guid-or-*>.runtime_blocked_hosts [153 only]"
      ]
    },
    "Extensions": {
      "disposition": "extensions-step-control",
      "delivery": "BPM096-M7-05",
      "paths": ["Install[]", "Uninstall[]", "Locked[]"]
    },
    "ExtensionUpdate": {
      "disposition": "extensions-step-control",
      "delivery": "BPM096-M7-05",
      "paths": ["<boolean>"]
    },
    "InstallAddonsPermission": {
      "disposition": "extensions-step-control",
      "delivery": "BPM096-M7-05",
      "paths": ["Allow[]", "Default"]
    },
    "3rdparty": {
      "disposition": "all-settings-only",
      "reason": "opaque add-on-defined Extensions.<guid>.adminSettings payload; Firefox supplies no stable field contract",
      "paths": ["Extensions.<guid>.adminSettings"]
    }
  },
  "raw_fallback": {
    "typed_extension_policy_values": {"owner": "extensions", "step": 6, "delivery": "BPM096-M7-05", "rule": "preserve and expose a raw fallback when a typed value cannot be structured"},
    "thirdparty_admin_settings": {"owner": "all-settings-only", "rule": "preserve without interpretation; report from Review only"},
    "unknown_policy": {"owner": "all-settings-only", "rule": "never infer extension ownership from a name or URL"}
  },
  "schema_fields": {
    "baseline": ["allowed_types", "blocked_install_message", "default_area", "install_sources", "install_url", "installation_mode", "private_browsing", "restricted_domains", "temporarily_allow_weak_signatures", "update_url", "updates_disabled"],
    "153_extra": ["allowed_permissions", "blocked_permissions", "runtime_allowed_hosts", "runtime_blocked_hosts"]
  },
  "starter_presets": {
    "blank": [],
    "keep_current": [],
    "basic_corporate": ["ExtensionSettings.*.installation_mode=blocked"],
    "classroom_kiosk": ["ExtensionSettings.*.installation_mode=blocked", "ExtensionSettings.uBlock0@raymondhill.net.force_installed", "InstallAddonsPermission.Default=false"],
    "soc_hard": ["ExtensionSettings.*.installation_mode=blocked", "InstallAddonsPermission.Default=false"]
  },
  "cis": {
    "all_layers_all_channels": ["ExtensionUpdate=true", "InstallAddonsPermission.Default=false"],
    "rule": "M7-07 displays attribution and conflicts without changing baseline provenance"
  },
  "legacy_control_dispositions": {
    "wizard-extension-default-mode": {"previous_host_step": 5, "disposition": "removed-in-M7-05"},
    "wizard-extension-install": {"previous_host_step": 5, "current_host_step": 6, "disposition": "rehome-once-to-step-6-in-M7-05"},
    "wizard-extension-locked": {"previous_host_step": 5, "current_host_step": 6, "disposition": "rehome-once-to-step-6-in-M7-05"},
    "wizard-extension-uninstall": {"previous_host_step": 5, "current_host_step": 6, "disposition": "rehome-once-to-step-6-in-M7-05"},
    "policy:InstallAddonsPermission": {"previous_host_step": 5, "current_host_step": 6, "disposition": "rehome-once-to-step-6-in-M7-05"},
    "policy:ExtensionSettings": {"previous_host_step": 5, "current_host_step": 6, "disposition": "rehome-once-to-step-6-in-M7-05"}
  },
  "obsolete_curated_assumptions": {
    "uBlock0@raymondhill.net": "removed-static-card-in-M7-05",
    "adguardadblocker@adguard.com": "removed-static-card-in-M7-05",
    "https-everywhere@eff.org": "removed-static-card-in-M7-05"
  },
  "next_task_boundaries": {
    "BPM096-M7-02": "bounded AMO adapter only",
    "BPM096-M7-03": "same-origin AMO API only",
    "BPM096-M7-04": "explicit AMO search and generic selection; no curated catalog",
    "BPM096-M7-05": "all typed rule controls and single rehome to step 6",
    "BPM096-M7-06": "manual fallback",
    "BPM096-M7-07": "preset/CIS/conversion/review attribution"
  }
}
```

## Schema and provenance notes

All four supported artifacts contain the five policy IDs.  `Extensions`, `ExtensionUpdate`,
`InstallAddonsPermission`, and `3rdparty` have the same schema shape in every artifact.
`ExtensionSettings` has the eleven baseline fields on ESR 115 and ESR 140, and the four additional
permission/runtime-host fields on ESR 153 and Release 153.  M7 must gate those fields from the
active schema rather than from an ESR label.

Starter preset values are source inputs, not a new extension recommendation surface.  CIS L1 and
L2 currently constrain updates and add-on-install default in every artifact; the inventory does
not reinterpret those benchmark values.  Converted or imported values retain their existing
provenance and use the typed Extensions control or its raw-preserving fallback according to the
fixture.

## Verification boundary

The contract test reopens each schema and the starter/CIS sources, checks every policy/path has an
Extensions owner or the recorded All-settings-only reason, and checks the temporary controls and
hard-coded curated GUIDs have a removal disposition.  It deliberately does not exercise network,
AMO, rule editing, or a browser UI: those belong to M7-02 through M7-08.
