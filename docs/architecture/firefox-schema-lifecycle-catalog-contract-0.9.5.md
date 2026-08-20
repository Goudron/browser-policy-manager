# Firefox Schema Lifecycle Catalog Contract (BPM 0.9.5.1)

Status: active runtime catalog; all four schemas are independently generated
and loaded through the M3-03 lifecycle catalog.

## Purpose and authority

This is the single lifecycle-catalog contract for Firefox policy schemas in
BPM 0.9.5.1.  Its machine-readable companion,
[`firefox-schema-lifecycle-catalog-contract-0.9.5.json`](firefox-schema-lifecycle-catalog-contract-0.9.5.json),
is the normative catalog fixture. The Markdown explains the rules; M3-01/02
provision and generate the fourth bundle, and M3-03 wires its runtime catalog.
UI, converter, and migration are outside this contract task.

The contract is deliberately fail-closed.  A row is not inferred from a tuple,
the largest version string, an existing filename, or a product label.  A row
must supply every field in the fixture and pass its contract test before it can
be implemented.  M3-02 replaced the fixture's `m2-contract-only` phase with
independently generated four-row schema evidence. M3-03 made those artifacts
the runtime catalog; it does not treat this fixture as an ESR 115 schema
artifact.

The reviewed Mozilla source and support facts come from the active
[four-channel provenance matrix](firefox-four-channel-provenance-matrix-0.9.5.md).
That matrix remains the evidence owner.  This contract owns lifecycle roles,
ordering, API shape, and transition meaning.

## Canonical identity and provenance fields

Each catalog row has these identities, which must not be conflated:

| Field | Meaning and rule |
| --- | --- |
| `line_id` | Stable lifecycle identity. ESR lines are `esr-115`, `esr-140`, and `esr-153`; a same-line patch refresh retains this value. `release-153` is the current Release-line identity. |
| `artifact_id` and `channel_id` | Exact persisted/public schema artifact identifier. They are equal in BPM 0.9.5.1: `esr-115.39`, `esr-140.13`, `esr-153.0`, or `release-153`. A patch refresh creates a new exact artifact/channel ID; it is not a new ESR line. |
| `family` and `line_number` | `family` is `esr` or `release`. `line_number` is a numeric line comparison key. ESR ordering uses it, never lexical identifier order. |
| `artifact_version` | Exact schema/browser-version surface represented by the artifact, separate from its lifecycle line. |
| `label` and `i18n_key` | English product fallback and the stable source-locale key. Labels are localized only through the key; identifiers never localize. |
| `source` | Exact `source_tag`, upstream tag, raw input URLs, SHA-256 values, cache input paths, output path, and filename. Output identity must match the generated schema metadata once M3 creates it. |

`support` is a verified lifecycle assertion, not a browser label.  It contains
the product-details field and observed browser version, evidence URLs,
`verified_on`, a truthful support end (`not-announced` or a month/date), and a
mandatory `recheck_on`.  ESR 115's `2027-03` end is intentionally month-granular:
Mozilla's reviewed notice says through March 2027 and then re-evaluation, not a
specific final day.  Its legacy-OS critical-security caveat is required on the
row and must not be represented as general-current-ESR support.

## BPM095 normative four-channel example

The target catalog has exactly these supported and selectable artifacts. ESR
115 is an independently generated bundle from verified v5.12 inputs and is an
active runtime row.

| Artifact/channel ID | Stable line | Family | Support role | Lifecycle role | Label/key |
| --- | --- | --- | --- | --- | --- |
| `release-153` | `release-153` | Release | supported | only default Release; never an ESR recommendation or ESR successor | Release 153 / `profiles.firefox_schema_release_153` |
| `esr-153.0` | `esr-153` | ESR | supported | only latest ESR and only product default | ESR 153.0 / `profiles.firefox_schema_esr_153_0` |
| `esr-140.13` | `esr-140` | ESR | supported older | recommends ESR 153; prospective retirement successor is ESR 153 | ESR 140.13 / `profiles.firefox_schema_esr_140_13` |
| `esr-115.39` | `esr-115` | ESR | supported older, limited legacy-OS security support through March 2027/recheck | recommends ESR 153; prospective retirement successor is ESR 140 | ESR 115.39 / `profiles.firefox_schema_esr_115_39` |

The word **prospective** matters.  It records the successor that an approved
future retirement transition must use.  It does not perform a write and does
not turn a supported profile into a migration candidate.

## Separate selection, recommendation, and retirement meanings

These values have different owners and must never be derived from one another:

| Meaning | BPM095 value | Write behavior |
| --- | --- | --- |
| Product creation default | exact artifact `esr-153.0` | Used only when a newly created profile does not explicitly choose a channel. |
| Default Release | exact artifact `release-153` | Used only by an explicit Release-specific product choice. |
| Latest-ESR recommendation target | stable line `esr-153`, resolved to the latest supported artifact `esr-153.0` | `esr-115.39` and `esr-140.13` may recommend an explicit, previewable user conversion to ESR 153. A recommendation never writes or changes the stored artifact. |
| Retirement successor | immediate newer stable ESR line | Used only by the M6 Alembic-owned, total-convertibility-gated retirement transition. Current chain: `esr-115` -> `esr-140` -> `esr-153`. |

Therefore a supported ESR 115 or ESR 140 profile recommends ESR 153 but is
**not** automatically migrated.  If ESR 115 is retired, its automatic
successor is ESR 140; if ESR 140 is retired, its automatic successor is ESR
153.  A runtime must never choose a successor by `max()`, version tuple, list
position, or the recommendation target.

The successor reference is a stable `line_id`.  M6 resolves and freezes the
exact target artifact in a reviewed transition plan, so a later patch refresh
cannot silently change an already approved migration target.

## Ordering and roles

Declaration order is non-normative.  Every selector and header sorts from the
fixture's ordering rule: Release family first, then ESR lines by descending
numeric `line_number`, then descending parsed artifact version for a same-line
refresh.  For the current target, both public sequences are:

```text
release-153, esr-153.0, esr-140.13, esr-115.39
```

The role invariants are exact:

1. Exactly one supported selectable ESR row has `latest_esr=true`.
2. Exactly one supported selectable row has `product_default=true`; it is the
   latest ESR row.
3. Exactly one supported selectable Release row has `default_release=true`.
4. A supported row is selectable. A retired row is never selectable, never a
   creation default, and never included in public selector/header lists.
5. Non-ESR rows cannot be latest ESR, an ESR recommendation source/target, or
   a retirement successor in the ESR graph.

## Retirement graph validation

The graph contains only `retirement_successor_line_id` references among ESR
rows.  It must be acyclic, same-family, upward in numeric ESR order, and point
to the one immediately newer *supported* ESR line.  If an intermediate
supported line exists, a jump over it is invalid.  The latest ESR has no
successor.  A release transition is outside this ESR graph.

When a line's support state changes to `retired`, M6-01 validates a previous
and candidate catalog, resolves the declared successor line to exactly one
supported bundled artifact, and emits a deterministic value-free transition
plan. M6-02 proves total conversion before a later Alembic transition applies
it. It is forbidden to infer a target during startup, validation,
GET/list, rendering, or any other runtime read path.

## Public serialization and compatibility

M3's catalog serializer must emit catalog version `1` and retain all current
top-level fields, with the exact types shown below.  Arrays use the derived
selector order; mappings use exact `artifact_id` keys.  The option object keeps
its existing `value`, `label`, and `i18n_key` fields and only adds fields.

```json
{
  "catalog_version": 1,
  "supported_channels": ["release-153", "esr-153.0", "esr-140.13", "esr-115.39"],
  "default_channel": "esr-153.0",
  "default_release_channel": "release-153",
  "latest_esr_channel": "esr-153.0",
  "esr_channels": ["esr-153.0", "esr-140.13", "esr-115.39"],
  "selector_channels": ["release-153", "esr-153.0", "esr-140.13", "esr-115.39"],
  "header_channels": ["release-153", "esr-153.0", "esr-140.13", "esr-115.39"],
  "default_label": "ESR 153.0",
  "labels": {"artifact_id": "localized label"},
  "filenames": {"artifact_id": "firefox-...json"},
  "mozilla_versions": {"artifact_id": "exact artifact version"},
  "sources": {"artifact_id": "mozilla-policy-templates-v..."},
  "options": [{
    "value": "artifact_id",
    "label": "localized label",
    "i18n_key": "profiles.firefox_schema_...",
    "line_id": "esr-...",
    "artifact_id": "artifact_id",
    "family": "esr",
    "support_state": "supported",
    "selectable": true,
    "is_latest_esr": false,
    "is_product_default": false,
    "is_default_release": false,
    "recommendation_target": "esr-153.0"
  }]
}
```

`recommendation_target` is an exact currently-resolved artifact ID or `null`.
The canonical fixture remains the source for provenance, support-window, and
successor-line fields not needed by a browser selector.

Compatibility rules:

- `supported_channels`, `default_channel`, `default_release_channel`,
  `esr_channels`, `default_label`, `labels`, `filenames`,
  `mozilla_versions`, `sources`, and the three old option fields are retained.
  Their values change only under the explicit lifecycle rules above.
- Consumers must stop using declaration order, `SCHEMA_CHANNELS` tuple order,
  or an option's ordinal as a semantic signal.  `selector_channels` and
  `header_channels` are the ordered public APIs.
- `CURRENT_ESR_SCHEMA_CHANNEL` is deprecated at the M2 boundary and must be
  removed rather than carried into M3.  No singular current-ESR alias may
  select, normalize, or migrate persisted profile data.  A product default is
  not a migration destination.
- A same-line artifact refresh is a distinct catalog transition.  Existing
  exact persisted artifact IDs remain interpretable only under the future
  refresh/retirement transition contract; they must not be silently rewritten
  by a web request.

## Unknown and retired API behavior

The public catalog lists only `supported` selectable artifacts.  An unknown or
retired value supplied as a create/update/validation/conversion target fails
without mutation as HTTP `422`, respectively
`schema_channel_unknown` or `schema_channel_retired`.  A stored profile that
contains an unknown value, or a known retired artifact before its required
Alembic transition, must not be relabelled, defaulted, or normalized by a read
path.  It is a read-only operator-recovery condition reported as HTTP `409`,
respectively `schema_channel_unknown` or
`schema_channel_retired_requires_migration`, with the stored value retained in
diagnostics.

M6 may fail an unupgraded deployment before these routes are served, but it
cannot change the no-runtime-write or error-code contract.  API work later in
the backlog owns endpoint implementation and OpenAPI detail; this task defines
the shared lifecycle meaning only.

## Required catalog validation

The focused contract test validates the fixture, including all of these gates:

1. unique `line_id`, exact `artifact_id`/`channel_id`, output filename, and
   `i18n_key`;
2. support evidence, truthful end/recheck shape, and supported/selectable
   relationship;
3. exact latest-ESR, product-default, and default-Release role cardinality;
4. numeric, declaration-independent selector/header order;
5. recommendation targets that resolve only to the latest supported ESR and
   do not imply a write;
6. acyclic same-family immediate successor edges with no supported ESR skip;
7. the four-row runtime `schema_channels.py`, build-target, input-manifest,
   and generated-schema metadata have the same source/output identity;
8. generated ESR 115 is independently loadable and selectable in the runtime
   catalog; and
9. stable public payload and unknown/retired error shape.

## Relationship to the Firefox 153 dual-ESR contract

`firefox-153-dual-esr-schema-contract-0.9.2.md` remains historical evidence;
the following table is the complete current interpretation of its lifecycle
rules.

| 0.9.2 rule | BPM095 disposition |
| --- | --- |
| Release 153, ESR 153.0, and ESR 140.13 are independent schemas; a label change cannot substitute for generation; master/v7.12 provenance remains separate. | **Preserved.** The same rule now applies to ESR 115/v5.12 and every future artifact. |
| Release 153 and ESR 153.0 remain different BPM channels despite a shared policy surface. | **Preserved.** Family and exact artifact identity remain explicit. |
| Moving between still-supported ESR lines is an explicit user choice followed by validation; no cross-ESR automatic migration occurs while both lines are supported. | **Preserved.** ESR 115/140 profiles recommend ESR 153 but remain unchanged until an explicit conversion. |
| A singular `CURRENT_ESR_SCHEMA_CHANNEL` must not determine persistence migration during a dual-ESR period. | **Strengthened.** The alias is deprecated/removed; no singular current ESR controls persistence in any lifecycle state. |
| The support matrix is exactly three rows and ESR 140.13 is the default schema. | **Superseded.** The target matrix has four rows and the product default is latest ESR 153.0. |
| ESR 153.0 is never an automatic migration target, and a static table defines all automatic migration destinations. | **Superseded narrowly.** Automatic cross-ESR conversion is permitted only after the source line is retired, only through its declared immediate newer successor, and only under the future M6 proof and Alembic gate. Thus a retired ESR 140 may move to ESR 153; a supported ESR 140 may not. |

No other 0.9.2 source-provenance, independent-generation, or supported-line
manual-conversion rule is superseded by this contract.

## Handoff boundary

M3-01/02 own ESR 115 provision/generation; M3-03 owns the completed runtime
catalog wiring; M4/M5 own explicit conversion and recommendation flows; M6
owns retirement validation and the only automatic writer. This contract does
not add those later behaviors.
