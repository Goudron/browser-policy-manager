# Firefox 153 Dual-ESR Schema Contract (BPM 0.9.2)

Status: historical architecture evidence. Its current lifecycle interpretation
is preserved or superseded only as listed by
[`firefox-schema-lifecycle-catalog-contract-0.9.5.md`](firefox-schema-lifecycle-catalog-contract-0.9.5.md).

## Purpose

BPM 0.9.2 supports three independent Firefox schema channels during the Firefox 153 ESR
transition. This contract makes channel provenance, defaults, and profile migration destinations
explicit. It prevents the old single-ESR abstraction from silently migrating an ESR 140 profile to
ESR 153.

## Official Source Evidence

The evidence below was verified on 2026-07-21:

- Mozilla's [policy-templates v8.0 release](https://github.com/mozilla/policy-templates/releases/tag/v8.0)
  is named “Policy templates for Firefox 153 and Firefox ESR 153”.
- Mozilla's [Firefox version feed](https://product-details.mozilla.org/1.0/firefox_versions.json)
  identifies `153.0` as the latest Firefox version, `140.13.0esr` as the current ESR, and
  `153.0esr` as the next ESR.
- Mozilla's [Firefox Enterprise 153 release notes](https://support.mozilla.org/en-US/kb/firefox-enterprise-153-release-notes)
  state that 153 is the new ESR and that enterprise changes will not be backported to Firefox 140
  ESR.
- Mozilla's [Firefox administrator reference](https://firefox-admin-docs.mozilla.org/)
  records Firefox-153 policy capabilities. The generated schema diff in BPM, rather than a prose
  inventory in this contract, is the authoritative complete policy-difference record.

`mozilla-policy-templates-v7.12` remains the latest policy-template baseline for the Firefox 140
ESR policy surface. BPM must regenerate `esr-140.13` from that verified input with the explicit
Firefox version `140.13`; it must not relabel an existing bundled JSON file or claim that v8.0 is
the source of the Firefox 140 policy surface.

## M12-02 Generation Evidence

The independently generated inputs and outputs are recorded here so the build can be reproduced
without mistaking a version-label change for schema generation:

| Target channels | Source inputs | SHA-256 | Generated policy count |
| --- | --- | --- | --- |
| `release-153`, `esr-153.0` | v8.0 `docs/index.md` | `2e00f3bf14ce2e90b96d9697700c493cc3688fb95aed2af49a000a5b62ef0bc1` | 121 each |
| `release-153`, `esr-153.0` | v8.0 `linux/policies.json` | `cadcd2052e4c449d68be760234c1eebc2916cb89319d9a4f1b71788504747fac` | 121 each |
| `esr-140.13` | v7.12 `docs/index.md` | `cebeacfdff92699c53d1fa7ab3b9db76fb2dae4362e3dd929165be1da79e265b` | 112 |
| `esr-140.13` | v7.12 `linux/policies.json` | `5a180e55c6838e6d359ce2223e8e41294ab5ebde439347cf4c08bab459f39e5c` | 112 |

The 121-policy Firefox 153 surface differs from the 112-policy Firefox 140.13 surface by
`AIControls`, `BrowserDataBackup`, `DisableRemoteImprovements`,
`DisableRemoteSettingsAndAcceptSecurityConsequences`, `GenerativeAI`,
`IPProtectionAvailable`, `LocalNetworkAccess`, `VisualSearchEnabled`, and `XSLTEnabled`.
`release-153` and `esr-153.0` have the same policy set but remain different BPM channels.

Mozilla's v8.0 package warns that its policy-syntax Markdown is not current. The converter therefore
has a deliberately version-gated bridge for the Firefox-153 `ExtensionSettings` fields documented
by Firefox Administrator Reference: `allowed_permissions`, `blocked_permissions`,
`runtime_allowed_hosts`, and `runtime_blocked_hosts`, plus the established `ExtensionSettings`
enum/field definitions omitted by
the retired Markdown. The bridge does not apply to `esr-140.13`; its tested policy set remains the
v7.12 Firefox 140 baseline.

## Support Matrix

| BPM channel | User-visible label | Firefox version | Policy-template provenance | Default role |
| --- | --- | --- | --- | --- |
| `release-153` | Release 153 | `153.0` | `mozilla-policy-templates-v8.0` | Default Release channel |
| `esr-153.0` | ESR 153.0 | `153.0` | `mozilla-policy-templates-v8.0` | Selectable current ESR; never an automatic migration target |
| `esr-140.13` | ESR 140.13 | `140.13` | `mozilla-policy-templates-v7.12`, validated as the frozen Firefox 140 policy baseline | Default schema channel during the dual-ESR transition |

All three rows are first-class supported schemas. An ESR label is not an alias, and both ESR rows
must be visible in the selector, validation, policy availability, documentation, and export/import
paths.

## Automatic Migration Matrix

| Persisted source channel | Automatic destination | Rule |
| --- | --- | --- |
| `release-149`, `release-150`, `release-151`, `release-152`, `release-153` | `release-153` | Release profiles continue on the Release line. |
| `esr-140.9`, `esr-140.10`, `esr-140.11`, `esr-140.12`, `esr-140.13` | `esr-140.13` | Firefox 140 ESR profiles continue on the Firefox 140 ESR line. |
| `esr-153.0` | `esr-153.0` | Already supported; do not rewrite. |
| `esr-140.13` | `esr-140.13` | Already supported; do not rewrite. |

There is no automatic migration from any Firefox 140 ESR channel to `esr-153.0`, nor from
`esr-153.0` to `esr-140.13`. Moving a profile between supported ESR lines is an explicit user
choice followed by validation against the selected schema.

The singular `CURRENT_ESR_SCHEMA_CHANNEL` must not determine any persistence migration while two
ESRs are supported. The implementation uses the explicit mapping above; the UI default is a
separate, intentional product choice.

## Required Implementation Evidence

Milestone 12 must provide all of the following before final quality:

1. Independent generated JSON files and metadata for all three support-matrix rows.
2. A reproducible policy fingerprint/diff showing the Firefox 140.13 policy surface is generated
   from its v7.12 baseline and that Firefox 153 additions are not attributed to that ESR.
3. Alembic and runtime-normalization tests covering every migration-matrix row and proving no
   cross-ESR automatic migration.
4. Product, locale, documentation, contextual-help, manifest/search, and screenshot evidence for
   three visible channels.
5. A successful `make docs-install-dev` after the final documentation change, so the maintainer's
   next `make dev` uses current documentation.
