# Runbook: Localization And Screenshots

Use this when updating localized prose, UI labels, captions, alt text, or reviewed screenshot source
assets.

## Localization rules

- Published locales are exactly `en`, `ru`, `de`, `zh-CN`, `fr`, and `es-ES`.
- English source ownership: `documentation/src/dita/en/` is the canonical source for authored
  topic structure, warnings, examples, topic IDs, anchors, and source/provenance records. English
  changes are not complete until every affected non-English peer has an explicit translation state
  and release gate.
- Non-English files are reviewed peers with the same content scope. They may not be compact
  summaries, placeholder translations, or silent English fallback. AI-assisted translation is
  allowed during development; shipped localized topics must still be reviewed and human-reviewed for
  terminology, placeholders, examples, source restrictions, and product accuracy.
- Locale peers keep the same topic IDs, anchors, source slugs, DITA keys, asset IDs, and target IDs.
  Titles, navigation labels, captions, alt text, and search terms are localized content.
- Shared DITA metadata remains language-neutral; do not hide English prose in `src/shared/`.
- If a BPM UI label changed, update the affected locale topic/caption and the smallest related
  parity/contract test. Do not scan all locale trees unless the failure requires it.

## Translation states

Use these states in reviews, backlog notes, or future machine-readable locale manifests. A published
release may contain only `source-reviewed` for English and `localized-reviewed` for every other
locale unless an explicit release blocker is recorded.

| State | Applies to | Meaning | Release behavior |
| --- | --- | --- | --- |
| `source-draft` | `en` | English topic, map label, code example, or search alias is being authored. | Blocks localization and package readiness. |
| `source-reviewed` | `en` | English source has factual, provenance, accessibility, and example review. | Opens update propagation to all localized peers. |
| `localization-needed` | non-English | English source changed and a locale peer has not been updated yet. | Blocks release readiness. |
| `localized-draft` | non-English | Locale peer has a full draft, possibly AI-assisted, but no human review yet. | Blocks release readiness. |
| `localized-reviewed` | non-English | Locale peer is content-equivalent and human-reviewed. | Allowed for release. |
| `blocked-source` | any locale | Source/provenance/rights/product behavior is unclear. | Blocks topic publication, search indexing, and screenshots. |

## Review gates

Before a localized topic, map label, screenshot caption, alt text, or search alias can be considered
`localized-reviewed`, check all gates below:

1. Structure gate: DITA element type, topic ID, section IDs, anchors, keyrefs, conditions, warnings,
   step count, notes, examples, and related links match the English source unless a reviewed locale
   exception is recorded.
2. Terminology gate: BPM UI terms, Firefox/Mozilla terminology, CIS terms, API operation names, and
   policy/preference IDs follow the approved glossary or remain in technical English where required.
3. Placeholder gate: variables, XML entities, command placeholders, JSON field names, DITA
   attributes, code comments that are part of examples, and UI string placeholders are preserved
   byte-for-byte where the product/API expects them.
4. Provenance gate: every localized topic inherits the English source records, license notices,
   Mozilla/CIS/trademark disclaimers, and source boundaries. Translation, paraphrase, or AI
   assistance cannot relax a blocked source.
5. Example gate: code, `curl`, Python, JSON, paths, policy IDs, CIS IDs, API operation IDs, schema
   channels, status codes, and response assertions remain executable and language-neutral unless
   the example is explicitly UI text.
6. Screenshot gate: visible BPM UI text, caption, alt text, locale, theme, fixture state, and image
   asset key match the localized topic. Cross-locale image reuse requires a recorded
   language-neutral exception.
7. Search gate: localized search aliases help readers find the topic in that locale while preserving
   stable target IDs and product identifiers. Search aliases must not introduce claims that are not
   present in the reviewed topic.

## Allowed technical English

Keep these strings in English or exact product form across all locales unless the owning product UI
or upstream source provides an approved localized form:

- DITA element names, attributes, key names, topic IDs, anchor IDs, source slugs, target IDs, and
  canonical URL path segments.
- API paths, HTTP methods, status codes, OpenAPI operation IDs, model names, JSON/YAML keys, command
  options, environment variables such as `$BPM_BASE_URL`, and code blocks.
- Firefox policy IDs, preference names, schema channel IDs, CIS recommendation IDs, layer IDs,
  preset IDs, manifest target IDs, and package/runtime filenames.
- Mozilla, Firefox, CIS, BPM, and license names where required for trademark, attribution, or legal
  accuracy.

## Update propagation workflow

When English source changes:

1. Classify the affected surfaces: topic body, title, map label, key, metadata, code/example,
   link/keyref, screenshot caption/alt text, search alias, or provenance notice.
2. Update English first and keep IDs/anchors/keys stable. If an ID must change, use the links and
   manifest runbook before touching localized peers.
3. Mark every non-English peer as `localization-needed` in the task notes until it reaches
   `localized-reviewed`. Do not close the implementation task with compact localized peers unless a
   later release-blocking localization task is explicitly recorded.
4. Propagate structural and semantic changes to `ru`, `de`, `zh-CN`, `fr`, and `es-ES`. Localized
   prose may differ in phrasing, but not in warnings, recovery paths, examples, caveats, or
   supported/unsupported claims.
5. Update search aliases, UI target references, source links, and screenshot/caption/alt-text
   ownership for all six locales when the English change affects discoverability or visible UI.
6. Run the smallest parity/metadata/source-link checks first. If a failure indicates broader drift,
   expand only to the affected guide family.

## Screenshot rules

- Reviewed source screenshots live under `documentation/assets/screenshots/{locale}/`.
- Temporary captures, diffs, masks, and browser diagnostics live under ignored
  `documentation/reports/`.
- Every screenshot uses a stable locale-independent asset ID and a locale-specific file variant.
- Screenshots use synthetic data only and may not contain credentials, real user/customer data,
  private hosts, local paths, or unapproved third-party branding.
- A screenshot must not be the only place where a step, value, error, warning, or policy state is
  documented. Localized alt text and captions explain what the reader should notice.

## Focused checks

Before screenshot automation exists, combine source review with the smallest available checks:

```bash
./.venv/bin/python documentation/tools/validate_metadata.py
make docs-validate
make docs-build
git diff --check -- <changed_files>
```

When screenshot automation lands, use the dedicated documentation screenshot command from the
snapshot/runbook and run browser work with immediate sandbox escalation.

## Done

- Locale-specific visible text, captions, alt text, and screenshot filenames remain aligned.
- No English fallback is served under another locale.
- Reviewed screenshots are source assets; transient captures remain ignored.
