# BPM 0.9.0 Documentation Identifiers And URL Conventions

Status: **Accepted for BPM 0.9.0**  
Decision date: 2026-06-21  
Backlog item: `BPM090-M2-07`

## Purpose

This decision separates documentation identity from titles, translations, source filenames,
generated filenames, and current BPM implementation paths. A translated heading, UI refactor,
Firefox schema update, CIS benchmark refresh, or API route change must not silently break a DITA
link, BPM contextual-help target, bookmark, or search result.

The versioned manifest and validation schemas are defined by `BPM090-M2-08`. This decision defines
the names and invariants those schemas must enforce; it does not create routes, redirects, DITA
maps, or generated files early.

## Identifier Layers

| Layer | Example | Stability and ownership |
| --- | --- | --- |
| Guide ID | `user-guide` | Immutable identity of one of the five guide families. |
| Topic ID | `fx-policy-AIControls` | Global, locale-independent semantic identity; also the root DITA topic `@id`. |
| Anchor ID | `a-value-shape` | Stable semantic location within one topic; also the source element `@id`. |
| DITA key | `topic.fx-policy-AIControls` | Locale-independent indirection used by maps and topics instead of filenames. |
| Target ID | `policy:AIControls` | BPM/domain identity resolved by the manifest to a topic and optional anchor. |
| Source slug | `fx-policy-aicontrols` | Explicit case-fold-safe physical filename stem; never translated. |
| URL path | `policies/ai-controls` | Explicit immutable topic path relative to its guide root; never inferred at request time. |
| Asset ID | `shot-ug-task-create-first-profile-library-empty` | Locale-independent identity shared by six localized screenshot variants. |
| Alias | `firefox/policies/ai-controls-policy` | Retired path or anchor retained as a one-hop compatibility mapping. |

Titles, navigation labels, search terms, captions, and alternative text are localized content and
are never identifiers. IDs are never translated, reused for a different meaning, or regenerated
from the latest English title.

## Common Syntax And Registry Rules

XML-facing guide, topic, anchor, and asset IDs use ASCII and must be valid XML names: they start
with an ASCII letter and then contain only ASCII letters, digits, `.`, `_`, or `-`. Colons,
whitespace, `/`, `#`, percent escapes, Unicode, and locale codes are forbidden in those IDs. The
maximum length is 128 characters. Topic IDs are globally unique; guide IDs, target IDs, anchor IDs
within a topic, and asset IDs each have their own declared uniqueness scope. Domain target IDs use
the separately defined namespace syntax below and are not copied into XML `@id` values.

The registry compares all filename stems and URL paths using Unicode normalization plus ASCII
case-folding even though their allowed public syntax is lowercase ASCII. This prevents collisions
on case-insensitive filesystems and inconsistent proxies. No generated path may contain `..`, an
empty segment, a leading dot, repeated slash, encoded slash, backslash, or control character.

Once a logical ID, source slug, canonical URL path, or public anchor ships, it is append-only:

- changing prose, location in a map, topic type, or UI ownership does not change it;
- a split retains the old identity on the primary successor and assigns new IDs to other topics;
- a merge keeps one canonical ID and turns the other IDs and paths into aliases;
- removal creates an alias to an equivalent successor or a tombstone; the value is not recycled;
- a mistaken but released spelling is preserved and may receive a better display title;
- a pre-release identifier may change only while no maintained manifest or release artifact has
  exposed it, and the change must update every inventory in the same review.

The manifest build rejects duplicate IDs, case-fold collisions, aliases that shadow canonical
values, alias chains, alias loops, unknown targets, and references to tombstoned content.

## Guide And Topic IDs

The five guide IDs and canonical URL roots are fixed:

| Guide ID | URL root below `/help/{locale}/` |
| --- | --- |
| `user-guide` | `user/` |
| `firefox-policy-guide` | `firefox/` |
| `cis-settings-guide` | `cis/` |
| `api-integration-guide` | `api/` |
| `administrator-guide` | `admin/` |

Topic IDs describe semantic ownership, not a current directory. Existing inventory IDs are adopted
without renaming:

- User Guide: `ug-task-*`, `ug-concept-*`, `ug-reference-*`, and `ug-troubleshoot-*`;
- Firefox policies: `fx-policy-{exact_policy_id}`, preserving the exact case-sensitive Mozilla
  policy ID, for example `fx-policy-AIControls`;
- managed preferences: `fx-pref-{normalized_preference_id}`, using the already inventoried
  lowercase dot-to-hyphen form, for example `fx-pref-browser-download-dir`;
- CIS recommendations: `cis-rec-{recommendation_id_with_dots_as_hyphens}`, for example
  `cis-rec-1-1-1-1`; provenance-only records keep `cis-source-{exact_dotted_id}` and are not
  publishable topic IDs;
- API guide references: the inventoried `api-ref-*` IDs, such as `api-ref-update-profile`;
- Administrator/DevOps guide topics: `admin-*` IDs reserved for source deployment, operations,
  update, troubleshooting, and integration runbooks. Distribution-specific installer topics stay
  reserved for later distribution work and must not reuse source-deployment topic IDs.

A Firefox policy rename is not assumed to be the same policy. The schema-update review either
keeps the old topic and adds a new topic, or records an explicit semantic successor alias. Channel
or browser versions never enter a policy topic ID. Similarly, a CIS benchmark version/level and a
BPM API route or HTTP method are metadata, not topic identity; a truly new semantic operation gets
a new ID rather than inheriting an unrelated old one.

Every locale uses the same topic ID for equivalent content. The root element of each localized
topic has that exact `@id`. A missing localized peer fails the release matrix rather than creating a
locale-suffixed ID or falling back to English.

## Source Files And DITA Keys

Source files use an explicit `source_slug` recorded in shared metadata:

```text
documentation/src/dita/{locale}/{guide-area}/{source_slug}.dita
```

`source_slug` is lowercase ASCII kebab case (`[a-z0-9]+(?:-[a-z0-9]+)*`), identical in all six
locale trees, and unique after case-folding. It is not recomputed when a topic title or logical ID
changes. For mixed-case policy IDs, the initial slug may be a readable lowercase/kebab projection;
if two upstream IDs collide, the maintainer assigns an explicit stable disambiguating suffix before
publication. Generated HTML filenames are build details and are never used as source identifiers.

Every publishable topic has exactly one primary key `topic.{topic_id}`. Other namespaces are:

- `guide.{guide_id}` for guide landing maps;
- `asset.{asset_id}` for images and downloadable examples;
- `term.{stable-term-id}` for reusable language-neutral product identifiers;
- `xref.{stable-relation-id}` only when one semantic relationship needs a reusable destination.

DITA maps own key definitions. Topics link internally with `keyref`/`conkeyref`, not relative paths,
translated filenames, generated `.html` names, or hard-coded `/help/` URLs. Direct DITA `href` is
allowed only for a same-topic fragment or an explicitly classified external resource. Key names are
identical in every locale map, and every locale must resolve them to its own source tree.

## Anchors

The topic root is the canonical destination and needs no fragment. Stable subsection destinations
use lowercase ASCII `a-{semantic-kebab-slug}`, for example `a-value-shape` or
`a-validation-errors`. They describe meaning, not a translated heading number, generated DOM
position, tab index, policy schema version, or CSS selector.

The DITA source element uses the anchor ID as its `@id`. A DITA cross-reference uses
`#topic-id/anchor-id`; published HTML exposes exactly `#anchor-id`. Anchor IDs are unique within a
topic and immutable after release. Heading text, level, and surrounding markup may change without
changing the anchor.

When a section moves, the new canonical page retains the same anchor where possible. If it cannot,
the old page or successor page emits a non-visible compatibility anchor that points users to the
new semantic section without JavaScript. Because URL fragments are not sent to the server, a path
redirect alone cannot migrate an old fragment. The manifest therefore records anchor aliases
separately and validation requires every released fragment to resolve on the final page.

Generated headings, code-line IDs, footnotes, and search highlight IDs use a reserved `gen-`
prefix and are not link contracts. Authors may not publish or register them as contextual targets.

## Canonical URLs

The public canonical topic form is:

```text
/help/{locale}/{guide-root}/{url-path}/
/help/{locale}/{guide-root}/{url-path}/#a-{anchor-slug}
```

The exact locale segment is mandatory and limited to `en`, `ru`, `de`, `zh-CN`, `fr`, and
`es-ES`. Locale matching is case-sensitive at the canonical layer; non-canonical locale spellings
may redirect to the exact registered spelling. `/help/` may choose the current BPM locale and
redirect to that locale's guide home, but it is not itself a canonical content URL. Canonical URLs
never omit the locale, use a query parameter for locale, or include the BPM/Firefox/CIS version.

`guide-root` and guide-relative `url-path` are lowercase ASCII path segments. Their combination is
stored explicitly in the manifest rather than inferred from a title. A canonical path ends with
`/` and has no `.html`. Examples:

```text
/help/en/user/tasks/create-first-profile/
/help/ru/firefox/policies/ai-controls/
/help/de/cis/recommendations/1-1-1-1/
/help/zh-CN/api/reference/update-profile/#a-validation-errors
```

Translated titles and transliterated words never appear in canonical paths. Query parameters may
hold non-identity UI state such as a highlighted search term, but search/filter state is not a
canonical URL and must not alter canonical metadata. The generated artifact can use internal
`index.html` files; runtime routing hides that layout.

All canonical pages declare their canonical URL. Locale peers declare alternate-language links to
the same logical topic. A locale switch uses topic ID plus manifest resolution, not path string
replacement; if parity validation somehow failed, it goes to the target locale guide home with an
explicit unavailable-topic state rather than serving English under another locale URL.

## Redirects, Aliases, And Tombstones

Canonical path changes are exceptional. Each released manifest carries a cumulative alias registry
with the old locale-independent path, canonical topic ID, replacement path or tombstone, reason,
and first/last BPM version metadata.

- A path alias resolves directly to one canonical destination with an HTTP `308` for `GET`/`HEAD`.
- Redirect chains and locale-crossing aliases are forbidden; the current locale is preserved.
- Query strings may be preserved only for allowlisted non-identity state.
- Old anchor IDs remain compatibility anchors in generated HTML; they are not solved only by HTTP.
- A removed topic with no honest successor returns `410` through the runtime manifest and links to
  the localized guide/search home. It must not redirect to a vaguely related topic.
- Canonical and alias paths are checked together for duplicates, case-fold collisions, traversal,
  and collisions with reserved `/help/assets/`, `/help/search/`, and `/help/manifest` namespaces.

Aliases are compatibility contracts, not alternate navigation entries. They do not appear in the
table of contents or search results and cannot become targets for new UI links.

## Domain And UI Targets

BPM templates and JavaScript store target IDs, never documentation URLs. `BPM090-M2-08` maps each
target to one canonical topic and optional anchor for every locale. Target namespaces are:

| Domain | Target form | Identity rule |
| --- | --- | --- |
| General topic | `topic:{topic_id}` | Exact stable topic ID. |
| Firefox policy | `policy:{exact_policy_id}` | Exact case-sensitive Mozilla/BPM policy ID, such as `policy:AIControls`. |
| Managed preference | `known-preference:{exact.preference.id}` | Exact BPM preference catalog ID. |
| CIS recommendation | `cis:{exact.dotted.recommendation_id}` | Exact benchmark recommendation identity, independent of level/version metadata. |
| API operation | `api-operation:{operation_id}` | Stable inventoried operation ID, for example `api-operation:API-PROFILE-005`. |
| Product capability | `capability:{capability_id}` | Stable inventory ID, for example `capability:CAP-LIB-001`. |

The colon is allowed in target IDs because they are manifest/domain identifiers, not XML IDs or URL
paths. Target values preserve source-system case. A route, CSS selector, translated UI label,
OpenAPI-generated function name, schema channel, or screen position is not a target identity.

The existing Firefox inventory's `policy:*` and `known-preference:*` targets are authoritative. CIS
recommendation and API operation targets are introduced by the manifest task from the exact
`recommendation_id` and inventory `Operation ID`; they do not replace their topic IDs. Multiple
operations may intentionally resolve to one shared topic, as the three service-status operations
do, while retaining separate operation targets and anchors.

## Screenshot And Asset IDs

Screenshots are linked by locale-independent `asset_id`, not by a relative filename. Screenshot IDs
use `shot-{primary-topic-id}-{semantic-view}` plus a stable variant only when two captures serve
different documented purposes. Viewport dimensions, locale, capture date, hash, file extension,
BPM patch version, and translated caption are metadata and must not enter the logical asset ID.

Each required screenshot has six variants at:

```text
documentation/assets/screenshots/{locale}/{asset_id}.{extension}
```

The filename stem and DITA `asset.{asset_id}` key are identical across locales. Captions and alt text
live in localized DITA. Replacing or recapturing the same semantic view retains the asset ID;
changing what the image proves creates a new ID. Language-neutral image reuse is allowed only when
the screenshot matrix explicitly approves it, as defined by the ownership decision.

Published asset paths may be content-hashed and are not stable deep-link contracts. Topics and UI
resolve them through keys and the generated manifest; external documentation links should target
the containing canonical topic and anchor.

## Validation And Change Review

The focused documentation contract must eventually validate, across all six locales:

1. grammar, length, namespace, global/scope uniqueness, and case-fold uniqueness;
2. exact parity of topic IDs, keys, required anchors, and screenshot IDs;
3. every key, target, canonical URL, alias, anchor alias, and asset resolves exactly once;
4. no topic links by translated/source/generated filename or hard-coded locale URL;
5. no canonical URL is generated from a title or current filesystem layout;
6. no alias chain, loop, shadow, cross-locale redirect, or dishonest successor exists;
7. Firefox policy/preference, CIS recommendation, API operation, and capability targets agree with
   their maintained inventories;
8. removed identifiers are retained as aliases or tombstones and are never reused.

Any change to a released identifier requires a compatibility note, alias/tombstone update, broken-
link check, all-locale manifest build, search-index rebuild, and contextual UI target check. A
schema or localization refresh that only changes metadata/content must leave identities untouched.

## Consequences

- Authors gain stable semantic linking and may reorganize maps without URL churn.
- Locales remain equivalent without translated filenames or path-string locale switching.
- Exact Firefox/CIS/API identities stay available for automation while public URLs remain readable,
  lowercase, and safe on common filesystems.
- The manifest must carry explicit slugs and compatibility history; this is deliberate data rather
  than clever derivation.
- Runtime work in `BPM090-M9-*` must implement manifest resolution and safe redirects, not duplicate
  these rules in templates or frontend modules.
