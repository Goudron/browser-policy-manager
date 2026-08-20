# Firefox Four-Channel Provenance Matrix (BPM 0.9.5.1)

Status: active architecture evidence
Scope: `BPM095-M8-04`, verified 2026-08-20. This is the reviewed
source/provenance evidence for the active runtime catalog. Lifecycle roles,
transitions, migrations, UI copy, generated schemas, cached inputs, and browser
provisioning remain owned by their respective contracts and runbooks.

## Decision and boundary

BPM publishes four independently evidenced schema rows: Release 153, ESR
153, ESR 140, and the legacy-OS ESR 115 line. The Firefox 115 browser patch
and its schema source are intentionally separate facts:

- Mozilla's product-details version feed reports `FIREFOX_ESR115` as
  `115.39.0esr` on the verification date.
- Mozilla's policy-template release metadata explicitly identifies `v5.12` as
  "Policy templates for Firefox 127 and Firefox ESR 115.12." Its later
  releases explicitly direct an administrator who needs to manage Firefox ESR
  115 to `v5.12`.

Therefore `115.39.0esr` is the pinned browser-version evidence, while
`mozilla-policy-templates-v5.12` is the independently reviewed schema-input
baseline. The latter must not be relabelled as a Firefox `115.38` template
release, and a browser patch must never be inferred from a template tag.

## Mozilla support evidence

Mozilla Support says Firefox 115 is the last supported Firefox version for
Windows 7, Windows 8, Windows 8.1, and macOS 10.12--10.14. Its current
legacy-OS notice says Mozilla will provide Firefox 115 ESR security updates
until March 2027. It also says that support had previously been announced to
end after August 2026, is extended another six months so users can continue to
browse the web, and Mozilla will then re-evaluate. If it is not extended after
that, users need to upgrade their operating system to continue receiving
Firefox security and feature updates.

This is a limited legacy-OS support commitment, not a claim that ESR 115 is
Mozilla's current general ESR. The product-details feed separately reports
`FIREFOX_ESR=140.13.0esr` and `FIREFOX_ESR_NEXT=153.0esr`.

Source consistency note: the opened Windows article also retains one later
older sentence that says security updates run to the end of ESR 115 in August
2026 and that Mozilla would then announce an extension or end of support. It
conflicts with the repeated, more recently updated March-2027 statement above
and with the current macOS article. This matrix records the repeated current
March-2027 extension/re-evaluation wording and retains the inconsistency as a
recheck requirement rather than silently treating the August sentence as a
second support commitment.

## Reviewed matrix

The BPM identifiers and labels below follow the existing catalog convention:
lowercase stable family/line identifiers, with the exact selected browser
patch in ESR identifiers and labels. "BPM evidence role" deliberately records
only the support/provenance classification required here; M2-03 owns durable
catalog lifecycle roles, ordering, defaults, successors, serialization, and
migration meaning.

| BPM channel ID (planned) | User label (planned) | Browser-version evidence | Support state and BPM evidence role | Independent policy-template source | Planned output filename |
| --- | --- | --- | --- | --- | --- |
| `release-153` | Release 153 | `LATEST_FIREFOX_VERSION=153.0.3`; BPM preserves the 153.0 schema surface | Mozilla Release line; supported Release provenance row | `mozilla-policy-templates-master-a892b621f7f98ee91c8ed84290641f2703e88490` (immutable master commit) | `app/schemas/policies/firefox-release-153.json` |
| `esr-153.0` | ESR 153.0 | `FIREFOX_ESR_NEXT=153.0esr` | Mozilla next-ESR transition line; supported selectable ESR provenance row | `mozilla-policy-templates-master-a892b621f7f98ee91c8ed84290641f2703e88490` (immutable master commit) | `app/schemas/policies/firefox-esr-153.0.json` |
| `esr-140.13` | ESR 140.13 | `FIREFOX_ESR=140.13.0esr` | Mozilla current general ESR; existing BPM supported ESR provenance row | `mozilla-policy-templates-v7.12` (`v7.12`, release title explicitly covers Firefox ESR 140.12; `v8.0` metadata directs ESR 140 management to `v7.12`) | `app/schemas/policies/firefox-esr-140.13.json` |
| `esr-115.39` | ESR 115.39 | `FIREFOX_ESR115=115.39.0esr` | Mozilla limited legacy-OS critical-security support through March 2027, then re-evaluation | `mozilla-policy-templates-v5.12` (`v5.12`, release title explicitly covers Firefox ESR 115.12; later Mozilla release metadata directs ESR 115 management to `v5.12`) | `app/schemas/policies/firefox-esr-115.39.json` |

All four rows are selectable runtime artifacts. A same-line ESR 115 refresh
changes its exact artifact ID from `esr-115.38` to `esr-115.39` without
changing its stable `esr-115` lifecycle line.

## Source inputs and byte-level evidence

Every input below was fetched directly from Mozilla's `mozilla/policy-templates`
repository at the named immutable tag or commit on 2026-08-20. Byte count and SHA-256
are of the fetched raw file, not a ZIP asset, generated BPM schema, browser
binary, or documentation page.

| BPM source tag | Upstream tag and release evidence | Documentation input | Bytes / SHA-256 | Linux policies input | Bytes / SHA-256 |
| --- | --- | --- | --- | --- | --- |
| `mozilla-policy-templates-master-a892b621f7f98ee91c8ed84290641f2703e88490` | [`master` commit `a892b621`](https://github.com/mozilla/policy-templates/commit/a892b621f7f98ee91c8ed84290641f2703e88490) | [`docs/index.md`](https://raw.githubusercontent.com/mozilla/policy-templates/a892b621f7f98ee91c8ed84290641f2703e88490/docs/index.md) | 228223 / `2e00f3bf14ce2e90b96d9697700c493cc3688fb95aed2af49a000a5b62ef0bc1` | [`linux/policies.json`](https://raw.githubusercontent.com/mozilla/policy-templates/a892b621f7f98ee91c8ed84290641f2703e88490/linux/policies.json) | 14648 / `d5a8076b9dc7d4332e757af5cf2702e4cf0acf125a9bc4483aaf6780cee833cc` |
| `mozilla-policy-templates-v7.12` | [`v7.12` release](https://github.com/mozilla/policy-templates/releases/tag/v7.12): “Policy templates for Firefox 152 and Firefox ESR 140.12” | [`docs/index.md`](https://raw.githubusercontent.com/mozilla/policy-templates/v7.12/docs/index.md) | 228056 / `cebeacfdff92699c53d1fa7ab3b9db76fb2dae4362e3dd929165be1da79e265b` | [`linux/policies.json`](https://raw.githubusercontent.com/mozilla/policy-templates/v7.12/linux/policies.json) | 14038 / `5a180e55c6838e6d359ce2223e8e41294ab5ebde439347cf4c08bab459f39e5c` |
| `mozilla-policy-templates-v5.12` | [`v5.12` release](https://github.com/mozilla/policy-templates/releases/tag/v5.12): “Policy templates for Firefox 127 and Firefox ESR 115.12” | [`docs/index.md`](https://raw.githubusercontent.com/mozilla/policy-templates/v5.12/docs/index.md) | 180619 / `ce84a587dabc8e995e93206866e8d8ab3c9cf8423bb7dfbe74f20b9b28aaac42` | [`linux/policies.json`](https://raw.githubusercontent.com/mozilla/policy-templates/v5.12/linux/policies.json) | 11922 / `da9caaefe75f7f5e54694bccda8a044e62f034dbd5889bcf1595bb08d6a04347` |

The re-fetched master, v7.12, and v5.12 checksums exactly match the maintained
`tools/firefox_schema_inputs_manifest_0_9_4.json` and
`tools/firefox_schema_targets.json`. The active ESR 115 local cache is:

```text
data/upstream/policy-templates/v5.12/policy-templates.md
data/upstream/policy-templates/v5.12/linux-policies.json
```

Those paths feed the active `firefox-esr-115.39.json` artifact.

## Primary sources and verification method

- [Mozilla product-details Firefox version feed](https://product-details.mozilla.org/1.0/firefox_versions.json)
  was fetched and inspected on 2026-08-20 for `LATEST_FIREFOX_VERSION`,
  `FIREFOX_ESR`, `FIREFOX_ESR_NEXT`, and `FIREFOX_ESR115`.
- [Mozilla Support: Firefox support for Windows 7, 8 and 8.1](https://support.mozilla.org/en-US/kb/firefox-users-windows-7-8-and-81-moving-extended-support)
  and [Mozilla Support: legacy macOS ESR](https://support.mozilla.org/en-US/kb/firefox-users-macos-1012-1013-1014-moving-to-extended-support)
  were opened on 2026-08-20. The Windows article supplies the exact
  March-2027 extension/re-evaluation wording; the macOS article independently
  states the same end-of-ESR-115 security-update boundary.
- Mozilla's official GitHub [`master` commit `a892b621`](https://github.com/mozilla/policy-templates/commit/a892b621f7f98ee91c8ed84290641f2703e88490), [v5.12](https://github.com/mozilla/policy-templates/releases/tag/v5.12),
  [v6.11](https://github.com/mozilla/policy-templates/releases/tag/v6.11),
  [v7.12](https://github.com/mozilla/policy-templates/releases/tag/v7.12), and
  [v8.0](https://github.com/mozilla/policy-templates/releases/tag/v8.0)
  release metadata were fetched and inspected. `v6.11` is corroborating
  evidence only: it says templates may contain policies absent from ESR 115 and
  explicitly says to use `v5.12` when managing ESR 115.

No support-page body, GitHub ZIP asset, product runtime, browser binary, or
generated policy schema is cached as an upstream source. If the source tag,
raw-file checksums, or commit/release metadata can no longer be independently
verified when an update provisions inputs, generation must fail closed rather
than copying or relabelling another schema.

## Focused follow-up verification

Each schema update must re-fetch the raw inputs, compare their SHA-256 values
to the maintained manifest, run the converter, and pass the lifecycle dry-run
and release gates. No tuple order, default, automatic migration, or successor
is inferred from this matrix.
