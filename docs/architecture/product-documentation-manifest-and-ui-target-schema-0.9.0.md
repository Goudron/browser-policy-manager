# BPM 0.9.0 Product Documentation Manifest And UI Target Schema

Status: **Accepted for BPM 0.9.0**  
Decision date: 2026-06-21  
Backlog item: `BPM090-M2-08`

## Decision

The generated documentation artifact has two independently versioned JSON contracts:

- `manifest.json`, validated by `product-documentation-manifest-v1.schema.json`, describes the
  immutable artifact, locales, guides, topics, anchors, output files, assets, search indexes,
  aliases, tombstones, and the target-map file;
- `ui-target-map.json`, validated by `product-documentation-ui-target-map-v1.schema.json`, maps
  stable BPM/domain target IDs to a manifest topic and optional anchor.

Both use JSON Schema Draft 2020-12 and `schema_version: 1`. The schemas and illustrative examples
live under `docs/architecture/` until `BPM090-M3-01` scaffolds the isolated `documentation/` product
area. `BPM090-M3-09` will generate release instances from DITA maps and metadata; `BPM090-M9-*`
will implement the read-only runtime consumer.

The existing `docs/docs-manifest.json` is a maintainer planning ledger for finished historical
backlog contracts. It is not the product documentation artifact manifest, does not implement this
schema, and remains unchanged.

## Maintained Contract Files

| File | Role |
| --- | --- |
| `architecture/schemas/product-documentation-manifest-v1.schema.json` | Structural artifact-manifest contract. |
| `architecture/schemas/product-documentation-ui-target-map-v1.schema.json` | Structural UI/domain-target contract. |
| `architecture/examples/product-documentation-manifest-v1.example.json` | Six-locale, five-guide, topic/anchor/asset/search/compatibility example. |
| `architecture/examples/product-documentation-ui-target-map-v1.example.json` | All six approved target namespaces and cross-document references. |

The examples are architecture fixtures, not publishable product documentation. Their hashes,
titles, home topics, and small topic set are illustrative and must not be copied into a release
artifact as if complete.

## Why Two Documents

The artifact manifest is documentation-owned and can be built and tested without reading BPM
templates or frontend modules. The target map is the narrow bridge from BPM identities to that
artifact. Keeping it separate means:

- portal navigation and static serving do not depend on product UI selectors;
- a contextual-link change can be reviewed against inventories without changing DITA output;
- the runtime can disable contextual links if the target map is missing or incompatible while
  retaining ordinary portal navigation;
- no BPM module needs to import DITA, search-builder, or source-tree code.

The manifest stores the target-map relative path, SHA-256, and schema version. The runtime verifies
those values before exposing contextual links.

## Manifest V1 Contract

### Artifact identity

`artifact` requires the exact BPM version, documentation version, deterministic build SHA-256,
40-character source revision, and pinned DITA-OT version. There is deliberately no build timestamp:
time is not artifact identity and would defeat reproducible output. Release packaging verifies the
manifest fingerprint against the immutable artifact directory.

### Locales and guides

`locales` is exactly, in canonical order, `en`, `ru`, `de`, `zh-CN`, `fr`, and `es-ES`;
`default_locale` is `en`. Every localized text/file/asset/search map requires all six exact keys and
rejects extra locale spellings. This prevents partial artifacts and English-under-another-locale
fallback.

`guides` is a closed object containing exactly `user-guide`, `firefox-policy-guide`,
`cis-settings-guide`, `api-integration-guide`, and `administrator-guide`. Each guide declares its
fixed URL root, a home topic, and six localized titles. The Administrator/DevOps guide uses the
`admin/` root for current source deployment, operations, update, troubleshooting, and integration
content; distribution-specific installer variants remain later guide content and are not implied by
the root.

### Topic registry

`topics` is an object keyed by immutable topic ID rather than an array. Each entry requires its
guide, exact DITA key, locale-independent source slug, guide-relative URL path, topic kind, six
titles, stable anchors, and six generated output paths. IDs are not repeated inside values, so a
strict JSON parser can reject duplicate object keys before schema validation.

The schema validates identifier/path grammar and required fields. Semantic validation additionally
requires `dita_key == "topic.{topic_id}"`, a known guide, unique case-folded source slug, unique full
`{guide-root}/{url-path}`, a home topic owned by its guide, and one output for the same logical topic
in every locale.

`anchors` is an object keyed by stable `a-*` ID. Each anchor has six localized titles and a unique
list of old compatibility anchors. Semantic validation rejects an alias that shadows any canonical
anchor in that topic.

### Assets and search

`assets` is keyed by stable asset ID. Every asset records kind, media type, localization policy,
explicit neutral-reuse approval, and six locale variants with relative safe path and SHA-256.
It also names one or more existing topics that own the asset. Screenshot dimensions are recorded
when applicable. A `shared-approved` asset may reuse bytes or a
path only when `reuse_approved` is true; `per-locale` screenshots must resolve to locale-specific
paths. Asset paths must remain inside the artifact and are validated for collision/traversal.

`search` requires one versioned, hashed index per locale and records the indexed document count.
The schema describes the files only; deterministic tokenization/ranking remains owned by the later
search contract.

### Compatibility and target map

`aliases` and `tombstones` are objects keyed by full locale-independent public path. An alias names
one existing canonical topic/path and optional existing anchor. A tombstone retains a retired topic
identity and status `410`. Semantic checks reject aliases that are canonical paths, unknown or
self targets, chains, case-fold collisions, and paths reserved for assets/search/manifest use.

`ui_target_map` records the artifact-relative map path, its SHA-256, and expected schema version.
The digest is verified against bytes during artifact generation and runtime loading; illustrative
architecture examples use placeholder digests and do not claim byte identity.

## UI Target Map V1 Contract

The map repeats the BPM version, manifest schema version, and exact locale set so incompatible or
partially copied pairs fail closed. `targets` is an object keyed by the accepted namespaces:

| Namespace | Kind | Source identity |
| --- | --- | --- |
| `topic:{topic_id}` | `topic` | Stable documentation topic. |
| `policy:{exact_policy_id}` | `policy` | Exact case-sensitive Firefox policy. |
| `known-preference:{exact.preference.id}` | `known-preference` | BPM managed-preference catalog ID. |
| `cis:{exact.dotted.recommendation_id}` | `cis` | CIS inventory recommendation. |
| `api-operation:{operation_id}` | `api-operation` | Stable API inventory operation ID. |
| `capability:{capability_id}` | `capability` | Stable user-capability inventory ID. |

Each target requires `kind`, exact `source_id`, maintained `source_inventory`, and an existing
`topic_id`; `anchor_id` is optional but must exist in that topic. Multiple targets may map to one
topic or anchor. A target map may not override content by locale: topic identity is shared and the
manifest resolves the locale-specific output.

Semantic validation requires the object key to equal `{kind}:{source_id}`, verifies the source ID
against its maintained inventory, then resolves topic and anchor exactly once. Runtime code asks
for a target ID and locale; it never constructs a URL from policy names, API routes, selectors, or
translated labels.

## Required Validation Pipeline

Schema validation alone cannot enforce cross-document references or uniqueness by an object field.
Every producer and consumer therefore applies these stages in order:

1. Decode UTF-8 JSON with a strict parser that rejects duplicate object keys.
2. Select the supported schema by exact integer `schema_version`; never fetch `$schema` over the
   network.
3. Validate both instances with the bundled Draft 2020-12 schemas and reject unknown properties.
4. Run semantic registry checks for guide/topic/key/path/anchor/asset/search/alias uniqueness and
   reference integrity.
5. Validate every target namespace/source ID against the maintained product inventories, then
   resolve its topic and optional anchor.
6. Verify every referenced artifact file is relative, inside the artifact root, present, regular,
   and matches its recorded SHA-256.
7. Require exact BPM version, six-locale parity, manifest/target schema compatibility, and target-map
   digest agreement before runtime activation.

A failure rejects the new artifact atomically. Runtime must not serve a partially accepted manifest
or mix a previous manifest with new pages/targets. Local development may show the documented
unavailable state; release packaging fails.

## Versioning And Compatibility

Schema versions are positive integers independent of BPM versions. V1 accepts semantic BPM version
fields beyond 0.9.x so a compatible patch/minor release does not require schema churn.

- Additive data is allowed only where the current schema already models it. Both schemas otherwise
  use `additionalProperties: false` to catch producer/consumer drift.
- A required-field change, meaning change, namespace change, or incompatible path/reference rule
  requires a new schema file and integer version.
- Producers may emit only one selected version. Consumers explicitly list supported versions and
  fail closed on newer/unknown versions; they never guess or silently discard fields.
- Migrations create and validate a complete new artifact. Released schema files and compatibility
  fixtures remain immutable so old packaged artifacts can still be diagnosed.

## Security Boundary

Schema `$id` values are identifiers, not network dependencies. Validators use repository/package
copies only. All artifact paths are relative; canonical paths contain only approved lowercase
segments. Strict parsing, closed objects, traversal checks, SHA-256 verification, atomic activation,
and the ownership boundary prevent a manifest from turning documentation serving into arbitrary
filesystem access or remote content loading. Detailed serving headers and CSP remain
`BPM090-M2-10` and `BPM090-M9-*` responsibilities.
