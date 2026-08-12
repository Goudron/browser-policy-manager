# ESR 115 Policy Placement, Preset, And CIS Audit

Date: 2026-08-11

Status: **Active evidence and runtime guard for `BPM095-M3-05`.**

The machine-readable [audit contract](firefox-esr-115-policy-disposition-audit-0.9.5.json)
is authoritative. It compares the independently generated ESR 115.38 bundle with
ESR 140.13, ESR 153.0, and Release 153 at validation-relevant policy and nested
schema-path level. It intentionally excludes descriptions and generator metadata.

## Results

| Pair | ESR115 policies | Target policies | Target-only policies | Changed nested paths |
| --- | ---: | ---: | ---: | ---: |
| ESR115 → ESR140 | 97 | 112 | 15 | 11 |
| ESR115 → ESR153 | 97 | 121 | 24 | 18 |
| ESR115 → Release153 | 97 | 121 | 24 | 18 |

There are no ESR115-only policies in any comparison. ESR153 and Release153 have
the same validation-relevant shape. The contract records every difference as a
stable identity constructed from its pair prefix and JSON pointer; the checked-in
bundle SHA-256 values are evidence for both ends of each comparison.

## Product disposition

All settings exposes each exact bundle policy once: ESR115 is 43 reviewed Guided
items plus 54 raw-fallback items, or 97/97. The other exact counts are Release
121 (51/70), ESR153 (51/70), and ESR140 (45/67). A policy is promoted to Guided
only by reviewed UI metadata. The manual quick-control catalog remains curated
and filters each control against the selected schema. The JSON editor/import/
export boundary remains the lossless raw fallback for any schema-valid ESR115
value, including values not represented by a quick control.

The audit found specific newer nested fields in the source-independent starter
defaults. ESR115 now removes only the recorded policy IDs and nested pointers;
all starter documents are validated against the exact ESR115 bundle. It does not
guess equivalent values or silently coerce user documents.

## CIS four-channel compatibility

The unchanged CIS Firefox ESR GPO Benchmark 1.0.0 source registry records that
CIS tested the benchmark against Mozilla Firefox 115.10 ESR on Windows 11 23H2.
The ESR115 evidence was therefore present in the pinned authoritative source and
must not be treated as an unavailable later-channel relabel.

All 53 mapped policy and preference targets now declare all four exact schema
artifacts. Each target validates independently against ESR115, ESR140, ESR153,
and Release153; the complete L1 and L2 documents also validate against every
bundle. Two deterministic layers are generated for every channel, and the Guided
selector exposes both levels everywhere.

The benchmark id, version, recommendation ids, source-PDF identity, license, and
attribution remain unchanged. The per-artifact mapping matrix records BPM's schema
validation evidence and does not claim separate CIS certification or endorsement.

This is an availability guard, not a conversion or retirement decision. M4/M6
continue to own conversion-time compliance disposition.

## Verification

The contract test recomputes the complete semantic diff from the four bundles,
requires every emitted difference to be represented exactly once, and mutates an
in-memory audit copy to prove an omitted disposition fails. Focused tests also
prove exact All-settings coverage, reviewed/raw disjointness, ESR115 starter
validation, four-channel CIS layer generation, and ESR115 policy import/export
round trips.
