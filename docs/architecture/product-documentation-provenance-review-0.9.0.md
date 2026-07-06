# BPM 0.9.0 Product Documentation Source Reuse And Provenance Review

Status: **Approved for BPM 0.9.0**
Decision date: 2026-06-21
Backlog item: `BPM090-M2-09`

## Purpose And Decision Boundary

This review defines which source material BPM product documentation may publish, which material may
only be used for verification or external links, what attribution travels into all six locales, and
who owns updates. The machine-readable decision is
`product-documentation-provenance-matrix-0.9.0.json`.

The operational rule is conservative: **an unregistered source or unclear license is blocked**.
Linking to a public page is not permission to copy it. Open-source code licensing does not grant
trademark rights. Translation, DITA conversion, search indexing, paraphrasing, or generation does
not erase the provenance or restrictions of an input.

This is a project publication policy, not a legal opinion. If a proposed use falls outside the
matrix, especially commercial or benchmark-derived use, the project maintainer must obtain and
record an appropriate rights decision before publication.

## Review Findings

1. BPM source, UI, synthetic fixtures, deployment/run commands, configuration names, and generated
   OpenAPI facts are project material under MPL-2.0 and are the preferred sources for original user,
   administrator, DevOps, and integration guidance.
2. Mozilla `policy-templates` is distributed under MPL-2.0. BPM may generate schema facts and may
   incorporate appropriately identified MPL material, but the default authoring method is original
   BPM prose backed by an exact Mozilla tag, source link, and schema fingerprint.
3. Moving Mozilla web documentation is not assumed to share the repository license. It is link-only
   until the exact page/license is registered. MDN documentation prose is separately licensed under
   CC-BY-SA 2.5 or later and is also link-only for BPM 0.9.0 by default.
4. Mozilla trademark permission is separate from MPL. Descriptive text use of the Firefox wordmark
   is allowed under Mozilla's published guidelines with attribution and no-affiliation language;
   Mozilla logos and visual identity are not BPM documentation assets by default.
5. CIS describes non-member PDF benchmarks under CC-BY-NC-SA 4.0 and separate terms/trademark
   rules. The official PDF stays local and ignored. Benchmark prose, tables, screenshots, and other
   source expression are publication-blocked without a recorded distribution-rights approval.
6. BPM may document its own implemented CIS mappings, values, merge behavior, manual-review states,
   and limitations in original prose while identifying the benchmark/version/recommendation context,
   retaining attribution, and making no certification, endorsement, or complete-compliance claim.
7. Named third-party integration documentation is link-only. The 0.9.0 API and Administrator/DevOps
   guides document generic patterns against BPM's existing API/source-deployment surface and do not
   borrow vendor prose, graphics, or examples or claim a shipped connector.

## Approved Source Matrix

| Source family | Default publication mode | Allowed use | Required notice/provenance | Forbidden by default | Update owner |
| --- | --- | --- | --- | --- | --- |
| BPM product source | allow | Original workflows, behavior, labels, limitations, synthetic examples | BPM revision and MPL-2.0 | Secrets, personal data, unverified behavior | BPM product maintainer |
| BPM localized UI screenshots | allow | Six-locale BPM UI captures from synthetic fixtures | Locale, fixture, capture metadata, MPL-2.0 | External sites, customer data, added third-party logos | Screenshot maintainer |
| BPM OpenAPI contract | allow | Generated endpoint/model/error facts and tested examples | OpenAPI SHA-256 and BPM revision | Invented security/stability guarantees | API contract maintainer |
| Mozilla policy schema facts | allow-with-notice | IDs, key/type/enum/default/version/channel facts; original BPM guidance | Exact tag, URL, schema hash, MPL-2.0, no-affiliation notice | Lost source metadata; claims of live verification | Firefox schema maintainer |
| Mozilla policy documentation prose | allow-with-notice, explicit regions only | Verification; identified MPL-covered excerpt/adaptation when necessary | Exact page/revision/date and retained MPL notice | Unmarked copy/paste or bulk mirroring | Firefox docs maintainer |
| Other Mozilla/SUMO/admin web pages | link-only | External link and review evidence | URL, page title, retrieval date | Copy/adaptation until page-specific license is registered | Firefox docs maintainer |
| MDN prose | link-only | External link and technical review evidence | MDN link | Copy/adaptation as MPL; omitted ShareAlike attribution | Documentation maintainer |
| Mozilla trademarks | allow-with-notice | Truthful descriptive Firefox wordmark use | Trademark attribution and no-affiliation statement | Logos, trade dress, endorsement implications | Product maintainer |
| Official CIS PDF | approval-required | Local mapping review; publication only within recorded approval | Benchmark/version/URL/license plus `rights_approval_id` | Commit/package/index PDF or source expression; certification claims | CIS maintainer + rights approver |
| CIS trademarks/certification marks | allow-with-notice | Accurate wordmark solely to identify benchmark/mapping context | Ownership and independent/no-approval disclaimer | Logos, certified badges, affiliation/certification implications | Product maintainer + rights approver |
| BPM CIS mapping implementation | allow-with-notice | Original explanation of BPM mappings, values, conflicts, manual review, limits | CIS identity/source plus independent/no-certification disclaimer | Benchmark prose or substitute-for-benchmark claims | CIS data maintainer |
| Third-party product docs | link-only | Generic BPM integration pattern plus official external link | Vendor/source link | Vendor content, logos, screenshots, connector/partnership claims | API docs maintainer |
| Synthetic BPM examples | allow | Tested fictional JSON, curl, Python, profile and error examples | Fixture/test ID and BPM revision | Real endpoints, credentials, customer data, copied samples | Documentation test maintainer |
| Localizations | inherit | Human-reviewed translation of an approved English topic | Complete inherited provenance/license and reviewer | Unreviewed machine translation, license change, blocked-source translation | Localization maintainer |
| Generated output/search | inherit | Transform only publishable sources | Aggregate notices and per-source metadata | Treat transformation as license cleansing | Build maintainer |

The JSON matrix is authoritative when this summary is abbreviated. A matrix entry cannot relax an
upstream license or terms; it may deliberately impose a stricter BPM publication rule.

## Guide-Family Ownership And Sources

### User Guide

- Functional owner: BPM product maintainer.
- Primary evidence: BPM routes/templates/static behavior, capability inventory, locale contracts,
  focused browser/API tests, and synthetic fixtures.
- Screenshots show BPM UI only, separately for every locale, with no real user data.
- Firefox names may appear descriptively. Mozilla logos or screenshots of Mozilla sites/products
  require a new rights record and are not part of the default user-guide plan.
- External help pages may be linked for context but are not copied into BPM explanations.

### Firefox Policy Guide

- Functional owner: BPM Firefox schema maintainer.
- Authoritative machine source: bundled Release/ESR schemas carrying
  `x-bpm-source=mozilla-policy-templates-v7.12`, plus their per-policy fingerprints and current
  inventory.
- Generated fields may include exact policy/key names, value shapes, required fields, enums,
  defaults, version/channel facts, and synthetic schema-valid examples.
- Guidance, caveats, task framing, and troubleshooting are written by BPM. A copied/adapted Mozilla
  prose region must be explicitly marked with its source/revision/retrieval date and MPL notice.
- Moving upstream documentation never silently overrides bundled schema facts. Disagreement becomes
  a reviewed source-drift record.

### CIS Settings Guide

- Functional owner: BPM CIS data maintainer; publication also requires the designated BPM
  distribution-rights reviewer.
- The official ignored PDF is a local review input, not a DITA, search, Git, or package input.
- Publishable default content is limited to original descriptions of what BPM actually configures:
  mapping targets and values, layers/presets, merge results, conflicts, manual-review states,
  exceptions not persisted by BPM, verification boundaries, and product limitations.
- Recommendation ID, benchmark name/version/level, and official link identify context. They do not
  import the recommendation's source expression.
- Recommendation titles, rationale, impact, audit, remediation, default-value prose, tables, and
  screenshots from the benchmark remain blocked unless a recorded approval defines redistribution,
  commercial-use, attribution, and ShareAlike handling.
- Every guide/related legal page states that BPM is an independent implementation, is not authorized,
  sponsored, endorsed, certified, or approved by CIS, is not a substitute for the official
  benchmark, and does not prove compliance.

### API Integration Guide

- Functional owner: BPM API contract maintainer.
- Primary evidence: `create_app().openapi()`, API inventory, route/model source, and focused tests.
- Request/response examples use fictional local hosts and deterministic fixtures and contain no
  credentials or production data.
- Other products are described only as generic integration roles unless a connector actually ships.
  A named vendor page may be linked but its text, schemas, screenshots, examples, and logos are not
  copied without a new source-family review.

### Administrator And DevOps Guide

- Functional owner: BPM administrator and DevOps documentation maintainer.
- Primary evidence: repository commands, supported source-deployment paths, configuration names,
  health/readiness endpoints, OpenAPI contracts, focused tests, and generated documentation
  packaging checks.
- The guide may describe current source deployment, source-based updates, operations boundaries,
  and integration runbooks. It must not claim packaged installers, native Windows services,
  production hardening, official reverse-proxy recipes, HA clustering, rolling upgrades, managed
  secrets, or official restore automation until a later distribution/runtime decision implements
  them.
- Third-party operations or DevOps product pages remain link-only unless a separate source-family
  review permits reuse.

## Topic-Level Provenance Contract

Every English topic or generated region declares enough metadata to reproduce the review:

- `source_family_id` from the matrix;
- exact locator and source version/revision;
- retrieval date and content SHA-256 when a snapshot is used;
- license ID and `reuse_mode` (`original`, `generated-facts`, `adapted`, `verbatim`, `link-only`, or
  `restricted-local-review`);
- authoring owner and reviewer identities;
- `rights_approval_id` whenever the matrix says approval-required;
- for non-English topics, `localized_from_topic_id` and human reviewer while inheriting every source
  and license record.

A topic can have multiple source records. Each paragraph, generated table, example, or asset that
uses a different source family must be attributable to the correct record; a single generic
"Sources" link does not legalize mixed untracked content.

The build rejects unknown source families, missing required metadata, a publishable region marked
`link-only` or `restricted-local-review`, approval-required material without `rights_approval_id`,
or a translation whose English source is blocked. Search and manifest generation receive only the
already approved publishable text.

## Attribution And Artifact Notices

The portal artifact contains an accessible legal/sources page and a `licenses/` notice bundle. At a
minimum it carries:

- BPM's MPL-2.0 license and source-revision link;
- Mozilla policy-templates source/tag and MPL-2.0 notice when incorporated;
- Mozilla trademark attribution and independent/no-endorsement statement;
- for CIS mapping context, benchmark identity/version/official link, the applicable terms/license,
  and prominent independent/no-certification/no-substitution language;
- any source-specific attribution and ShareAlike material required by an approved exceptional use;
- DITA/build dependency notices only when those components or their covered material are actually
  distributed, as distinct from build-only tools.

Visible source links belong in policy/CIS reference topics where they help a reader verify claims;
the aggregate page does not replace topic-level provenance. Notices are localized where explanatory
text is user-facing, while license names, URLs, identifiers, and legally required wording retain
their approved form.

## Source Intake And Update Workflow

1. Identify the source family before opening material for reuse. Prefer current local BPM contracts
   and official upstream sources; third-party mirrors are discovery-only.
2. Record exact version/tag/revision, URL, retrieval date, hash where snapshotted, and license/terms.
3. Choose the narrowest reuse mode. Prefer facts, original prose, synthetic examples, and external
   links over copied expression.
4. If the source is unregistered, page-specific terms are unclear, or the planned use exceeds the
   matrix, stop publication and add a reviewed matrix entry or rights approval.
5. Author English first. Run factual, provenance, trademark, security/privacy, and license review.
6. Localize only the approved English source. Translations inherit restrictions and notices and are
   human-reviewed; AI-assisted drafting or localization cannot become publishable until it passes
   human review, provenance, terminology, placeholder, and parity gates.
7. Generate notices, manifest source records, and search only after all records pass.
8. On any source/version/terms change, reopen affected topics and all locale peers. A cached source
   or previous approval is not automatically valid for a new version or new distribution mode.

## Release-Blocking Conditions

The documentation artifact is not releasable if any of these is true:

- a topic, example, image, generated table, or search entry has no registered source family;
- source version, license, retrieval evidence, or required attribution is missing;
- copied Mozilla material lacks explicit MPL provenance/notices;
- Mozilla/CIS/vendor branding implies affiliation, certification, endorsement, or approval;
- a CIS PDF or source expression enters Git, DITA, generated HTML, search, assets, or the package
  without a scoped `rights_approval_id`;
- benchmark-derived content is labeled only MPL-2.0 or its NonCommercial/ShareAlike obligations are
  hidden;
- third-party/MDN/vendor content exceeds link-only policy without a new review;
- a locale drops, changes, or obscures source/license/approval metadata;
- real data, secrets, private hosts, or user-provided screenshots/examples are present;
- unreviewed machine-generated documentation or translation enters this 0.9.0 scope.

## Official Sources Reviewed

Verified on 2026-06-21:

- Mozilla policy-templates repository and MPL-2.0 license:
  `https://github.com/mozilla/policy-templates`
- Mozilla policy documentation: `https://mozilla.github.io/policy-templates/`
- Mozilla trademark guidelines:
  `https://www.mozilla.org/en-US/foundation/trademarks/policy/`
- MDN attribution and licensing:
  `https://developer.mozilla.org/en-US/docs/MDN/Writing_guidelines/Attrib_copyright_license`
- CIS Non-Member Product Terms:
  `https://www.cisecurity.org/terms-of-use-for-non-member-cis-products`
- CIS logo, trademark, and IP use policy:
  `https://www.cisecurity.org/cis-logos-and-trademark-use-policy`
- Creative Commons BY-NC-SA 4.0 license summary and legal-code link:
  `https://creativecommons.org/licenses/by-nc-sa/4.0/`
