# BPM 0.9.6 Certificates and trust coverage inventory

Date: 2026-08-21

Backlog item: `BPM096-M9-01`

Status: active implementation ledger for M9. This record is inventory and ownership metadata
only; it does not move a Guided control, modify a policy/preference value, inspect a certificate,
or make a trust decision.

## Decision

The one Guided owner for the supported certificate and enterprise-authentication family is
**step 4, Certificates and trust**. A certificate file path is a reference, not a file BPM reads,
uploads, parses, hashes, or validates. `Authentication` contains Firefox authentication host and
browser behavior rules; it is not evidence that a client-certificate-selection policy exists.
No current supported schema exposes such a selection policy. An unregistered/manual client-
certificate preference therefore remains All settings only and must not be inferred from its name.

`DisableSecurityBypass.InvalidCertificate` is the only reviewed neighbouring policy. M9-02 owns
that exact certificate-error posture in step 4; `SafeBrowsing`, its sibling property, remains
Security and privacy and is not certificate/trust work. M9-02 also owns the distinct
`privacy:security.enterprise_roots.enabled` preference as the system-trust choice and
`Certificates.ImportEnterpriseRoots` as the enterprise-roots choice. They are never merged or
shown as aliases. These controls express Firefox policy only: BPM does not read certificates or
validate an organisation's trust configuration.

The historic inner group id `wizard-step-2-trust` is rendered inside the outer step-1 Browser,
network, and search panel. Its old inner number is not an owner. M9-02/03 remove that entire
group and its network presets/status/review jumps exactly once while retaining DNS/DoH in step 1.
The authoritative common owner map remains the
[Guided ownership matrix](profile-guided-ownership-matrix-contract-0.9.6.md); this ledger
expands only its M9 family.

## Normative coverage fixture

<!-- bpm096-profile-certificate-trust-coverage-inventory-v1 -->
```json
{
  "inventory_id": "bpm096-profile-certificate-trust-coverage",
  "inventory_version": 1,
  "backlog_item": "BPM096-M9-01",
  "guided_owner": {"step": 4, "id": "certificates-trust"},
  "supported_schema_channels": ["release-153", "esr-153.0", "esr-140.13", "esr-115.39"],
  "policy_coverage": {
    "Certificates": {"disposition": "certificates-step-control", "delivery": ["BPM096-M9-02", "BPM096-M9-03"], "paths": ["Install[]", "ImportEnterpriseRoots"]},
    "Authentication": {"disposition": "certificates-step-control", "delivery": "BPM096-M9-03", "paths": ["SPNEGO[]", "Delegated[]", "NTLM[]", "AllowNonFQDN.<host>=true", "AllowProxies.<host>=true", "Locked", "PrivateBrowsing"]},
    "SecurityDevices": {"disposition": "certificates-step-raw-preserving-control", "delivery": "BPM096-M9-03", "paths": ["Add.<device-name>=<library-or-module-path>", "Delete[]"]},
    "WindowsSSO": {"disposition": "certificates-step-control", "delivery": "BPM096-M9-02", "paths": ["<boolean>"]},
    "MicrosoftEntraSSO": {"disposition": "certificates-step-control", "delivery": "BPM096-M9-02", "channels": ["release-153", "esr-153.0", "esr-140.13"], "paths": ["<boolean>"]},
    "DisableSecurityBypass": {"disposition": "certificates-step-control", "delivery": "BPM096-M9-02", "paths": ["InvalidCertificate"], "excluded_paths": ["SafeBrowsing"]}
  },
  "preference_coverage": {
    "privacy:security.enterprise_roots.enabled": {"disposition": "certificates-step-control", "delivery": "BPM096-M9-02", "paths": ["<boolean>"], "relationship": "distinct-from-Certificates.ImportEnterpriseRoots; do not merge or duplicate"},
    "unregistered-client-certificate-selection": {"disposition": "all-settings-only", "reason": "no supported Firefox policy or registered Guided preference exposes client-certificate selection"}
  },
  "raw_fallback": {
    "typed_certificate_or_authentication_value": {"owner": "certificates-trust", "step": 4, "rule": "preserve exact imported schema value and expose a raw fallback when it cannot be safely structured"},
    "security_devices": {"owner": "certificates-trust", "step": 4, "rule": "preserve Add and Delete shapes, device names, and platform paths without reading certificate or module contents"},
    "unknown_policy_or_unregistered_preference": {"owner": "all-settings-only", "rule": "preserve without inferred certificate, trust, host, or path ownership; report from Review only"}
  },
  "schema_fields": {
    "all_channels": {"Certificates": ["Install", "ImportEnterpriseRoots"], "Authentication": ["SPNEGO", "Delegated", "NTLM", "AllowNonFQDN", "AllowProxies", "Locked", "PrivateBrowsing"], "SecurityDevices": ["Add", "Delete"], "WindowsSSO": []},
    "153_only": {"MicrosoftEntraSSO": []}
  },
  "starter_presets": {"blank": [], "keep_current": [], "basic_corporate": ["Certificates.ImportEnterpriseRoots=true"], "classroom_kiosk": [], "soc_hard": ["Certificates.ImportEnterpriseRoots=true"]},
  "cis": {"all_layers_all_channels": ["Authentication.NTLM=[]"], "unconstrained": ["Certificates", "SecurityDevices", "WindowsSSO", "MicrosoftEntraSSO", "DisableSecurityBypass"], "rule": "M9 displays attribution and conflicts without changing benchmark provenance"},
  "legacy_control_dispositions": {
    "wizard-step-2-trust": {"historical_outer_host_step": 1, "required_owner_step": 4, "disposition": "removed-in-M9-02"},
    "wizard-network-enterprise-presets": {"historical_outer_host_step": 1, "required_owner_step": 4, "disposition": "replaced-by-schema-aware-trust-posture-in-M9-02"},
    "wizard-windows-sso-card": {"historical_outer_host_step": 1, "required_owner_step": 4, "disposition": "replaced-by-step-4-windows-sso-choice-in-M9-02"},
    "wizard-authentication-card": {"historical_outer_host_step": 1, "required_owner_step": 4, "disposition": "removed-in-M9-02; detailed-list-editor-is-M9-03"},
    "wizard-certificates-card": {"historical_outer_host_step": 1, "required_owner_step": 4, "disposition": "removed-in-M9-02; detailed-reference-editor-is-M9-03"},
    "wizard-network-enterprise-fine-tuning-panel": {"historical_outer_host_step": 1, "required_owner_step": 4, "disposition": "removed-in-M9-02"},
    "wizard-network-summary-authentication": {"historical_outer_host_step": 1, "required_owner_step": 4, "disposition": "removed-and-replaced-by-step-4-attribution-and-final-review-jump-in-M9-04"},
    "wizard-network-summary-certificates": {"historical_outer_host_step": 1, "required_owner_step": 4, "disposition": "removed-and-replaced-by-step-4-attribution-and-final-review-jump-in-M9-04"},
    "wizard-network-summary-windows-sso": {"historical_outer_host_step": 1, "required_owner_step": 4, "disposition": "removed-and-replaced-by-step-4-attribution-and-final-review-jump-in-M9-04"}
  },
  "next_task_boundaries": {"BPM096-M9-02": "compact trust posture and explicit reviewed-neighbour decisions only", "BPM096-M9-03": "certificate references, security devices, and authentication lists without reading certificate contents", "BPM096-M9-04": "CIS, conversion, provenance, review, and final step-4 jump", "BPM096-M9-05": "end-to-end quality proof"}
}
```

## Verification boundary

The focused contract opens all four policy artifacts, the registered privacy preference catalog,
starter catalog, and generated CIS layers. It proves the exact policy fields, the 153-only Entra
availability, the raw-preserving device disposition, and the explicit All-settings boundary. It
also records each legacy trust control that M9-02 removed or deferred to a later task. It does not
inspect certificate contents, make a trust decision, or validate organisational trust; detailed
certificate, device, and authentication editors remain M9-03.
