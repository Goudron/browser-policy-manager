# BPM 0.9.0 Firefox Policy Documentation Inventory

Date: 2026-06-21

Backlog item: `BPM090-M2-03`

Machine-readable inventory:
`docs/architecture/firefox-policy-documentation-inventory-0.9.0.json`

Regeneration command:

```bash
./.venv/bin/python tools/build_firefox_policy_documentation_inventory.py
```

Drift-check command:

```bash
./.venv/bin/python tools/build_firefox_policy_documentation_inventory.py --check
```

## Scope And Sources

The inventory derives only from the two bundled active schemas registered in
`app/core/schema_channels.py`, their normalized `PolicyDefinition` objects and UI registry
metadata, and the known managed-preference catalog returned by
`app.web.firefox_preferences.get_wizard_preferences_catalog()`.

It does not scan downloaded upstream corpora or claim support for policy keys absent from the
selected bundled schema. Schema source metadata for both channels is
`mozilla-policy-templates-v7.12`.

## Channel Coverage

| Channel | Mozilla version | Policies | Value shapes | UI support |
| --- | --- | ---: | --- | --- |
| `esr-140.12` | `140.12` | 112 | 55 boolean, 33 object, 14 string, 8 array, 2 integer | 45 mapped, 67 fallback |
| `release-152` | `152.0` | 120 | 59 boolean, 37 object, 14 string, 8 array, 2 integer | 51 mapped, 69 fallback |

The union contains 120 stable policy IDs. All 112 ESR policies also exist in Release and have
identical raw schema definitions in the current pair. Eight policies are Release-only:

- `AIControls`;
- `BrowserDataBackup`;
- `DisableRemoteImprovements`;
- `GenerativeAI`;
- `IPProtectionAvailable`;
- `LocalNetworkAccess`;
- `VisualSearchEnabled`;
- `XSLTEnabled`.

There are no ESR-only policies and no changed definitions among the 112 common policies. The JSON
inventory nevertheless stores a SHA-256 fingerprint and
`definition_changed_across_channels` for every policy so later channel updates cannot hide a
changed common definition.

## Stable Documentation Contract

Each policy entry records:

- exact case-sensitive `policy_id`;
- stable `doc_id` in the form `fx-policy-{policy_id}`;
- stable BPM target `policy:{policy_id}`;
- `both`, `release-only`, `esr-only`, or `partial` channel scope;
- per-channel value shape, description key, minimum/maximum version, deprecation state, categories,
  schema fingerprint, and source version inherited from channel metadata;
- per-channel UI section, subsection, widget, complexity, `mapped`/`fallback` support level, and
  unknown-field preservation contract.

Mixed case is deliberately retained in policy documentation IDs during inventory. Filename/URL
slug conventions are a later `BPM090-M2-07` architecture decision; they must map from these stable
logical IDs without changing policy identity.

## Managed Preferences

BPM currently recognizes 62 managed preferences across five sections:

| Section | Known preferences |
| --- | ---: |
| `general` | 11 |
| `home` | 8 |
| `search` | 11 |
| `privacy` | 24 |
| `sync` | 8 |

Each preference entry records its exact preference name, a stable normalized `fx-pref-*` document
ID, the live `known-preference:{name}` UI target, section, label/description keys, known type and
status, preset relationships, value-control hint, and whether the catalog can autofill one
unambiguous value.

Known managed preferences support User Guide and Firefox reference cross-links but remain distinct
from Firefox Enterprise policy IDs. Preferences not present in this catalog remain raw
imported/unknown settings and do not acquire a generated supported-reference topic merely because a
user imported them.

## Fallback And Raw Behavior

`ui.support_level=fallback` means BPM uses inferred schema-backed presentation rather than an
explicit policy UI registry mapping. It does not mean the policy is unsupported: the policy remains
schema-valid and reachable through All Settings, but examples and complex nested behavior require
explicit documentation review.

The inventory separately records `preserve_unknown_fields` because complex policies must not lose
nested fields the current UI does not understand. Keys absent from the selected schema and unknown
managed preferences stay visible as imported/raw attention items; they must not be described as
supported policy or known-preference topics.

## Audit Result

- All 120 supported policy IDs have unique stable documentation IDs and channel records.
- Release-only policies are explicit; ESR-only and changed-common counts are both zero.
- Schema value shapes, version metadata, fingerprints, UI support level, and unknown-field behavior
  are recorded per available channel.
- All 62 known managed preferences have unique documentation IDs and UI targets.
- The deterministic builder and contract test fail when schemas, channels, policy definitions, UI
  registry metadata, or the managed-preference catalog drift from the maintained JSON inventory.
- Policy prose, examples, localization, and topic generation are later milestones; this inventory
  records coverage and ownership only.
