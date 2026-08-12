# ESR 140.13 → ESR 153.0 Total-Convertibility Proof

Status: **active M6-02 production exact-artifact proof; the M6-03 candidate-only
materializer and SQLite candidate evidence are complete, while active catalog
retirement/revision installation and PostgreSQL evidence remain pending.**

The machine-readable [proof artifact](firefox-esr-140.13-to-esr-153.0-retirement-total-proof-0.9.5.json)
and its [schema](schemas/firefox-retirement-exact-schema-containment-proof-v1.schema.json)
are authoritative. Its digest is computed over every member except
`proof_artifact_digest`, using `bpm-retired-esr-exact-proof-artifact:v1\n` and
RFC 8785/JCS SHA-256. The artifact binds exact raw bundle SHA-256 values,
normalized validation-schema SHA-256 values, the M4 registry identity, all 112
source policy identifiers, and the two reviewed upstream policy documents.

The M6-02 checker reopens the exact bundles, validates the artifact digest and
all identities, then mechanically proves source-schema containment. It accepts
only validation-neutral annotation changes, finite source enum/const values
accepted by the target, and optional target-property additions to otherwise
identical object schemas. The semantic attestation is separate: it concludes
that the byte-preserved ESR 140 value shapes retain their documented enterprise
policy meaning on ESR 153.

The exact structural result is 112/112 source policies present in ESR 153:
109 validation projections are identical. The remaining three are target-only
expansions: `Cookies` adds `partition-foreign`; `ExtensionSettings` adds four
optional per-extension fields; and `Homepage` adds optional `NewTabOnRestore`.
No source-valid policy, nested property, enum value, required shape, dynamic
key domain, or default is removed, narrowed, remapped, or materialized.

This makes the static M6-02 report promotable with method
`schema-containment`, zero uncovered locations, and the artifact digest as its
proof identity. The candidate-only M6-03 materializer may use that identity to
render a reviewed Alembic-compatible artifact, but it rejects the current
catalog because ESR 140.13 is still supported. No revision is installed in the
active graph and no runtime profile write is authorized. Activation still
requires actual catalog retirement, deliberate graph installation, verified
backup/restore evidence, and the real PostgreSQL atomic-transaction contour.
