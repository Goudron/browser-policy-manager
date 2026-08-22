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
  terminology, placeholders, examples, source restrictions, and product accuracy. Only that
  reviewed, published locale peer is eligible for future same-locale assistant review only; 0.9.3
  does not create or update an assistant corpus. A draft, translation working copy, or generated
  answer may not be used.
- Locale peers keep the same topic IDs, anchors, source slugs, DITA keys, asset IDs, and target IDs.
  Titles, navigation labels, captions, alt text, and search terms are localized content.
- Shared DITA metadata remains language-neutral; do not hide English prose in `src/shared/`.
- If a BPM UI label changed, update the affected locale topic/caption and the smallest related
  parity/contract test. Do not scan all locale trees unless the failure requires it.
- Rendered product documentation addresses its actual user, administrator, DevOps, API-integrator,
  or security-reviewer audience. Do not address a maintainer or developer, narrate implementation
  progress, or expose internal source/test/build work as reader instructions.
- Documentation displays the one BPM product version derived from product metadata. Do not add a
  separately owned documentation version in prose, portal chrome, captions, screenshots, or locale
  metadata.
- English source carries meaning and structure; it is not a grammar, word-order, capitalization, or
  punctuation template for another locale. Apply the
  [locale editorial style policy](../../docs/architecture/documentation-locale-editorial-style-0.9.2.md)
  before approving visible localized prose.
- When a locale change reaches compact UI copy or the documentation shell, cite the exact
  [UI copy classification contract](../../docs/architecture/ui-copy-classification-contract-0.9.2.md)
  disposition. Do not restore routine explanation; preserve the essential or safety/accessibility
  meaning at the point of action.

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
8. Natural-language gate: titles and headings follow the locale's native convention rather than a
   literal English construction. In Russian, use an idiomatic nominal heading where natural, such as
   `Изменение языка интерфейса`, not the calqued `Изменить язык интерфейса`.
9. Compact-shell gate: when a screenshot or topic covers documentation chrome/search, confirm that
   the normalized BPM header, locale/theme state, and one derived BPM product version match the
   product UI. An advanced filter panel remains collapsed or expanded only by its explicit toggle;
   search, URL/history hydration, result updates, and clear do not change that choice.

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

## Terminology and visible-English workflow

Treat the runtime UI catalog as the authority for every interface name shown in documentation.
Resolve the source key in `app/i18n_src/` and use its exact value for the topic locale; do not
translate labels independently in titles, navigation, prose, captions, alt text, or search text.
`documentation/config/interface-name-authority-0.9.1.json` records the covered surfaces and
`documentation/config/locale-terminology-authority-0.9.1.json` records the terminology authority.

For each changed localized surface:

1. Compare it with the English source and the corresponding runtime UI catalog key. Include topic
   titles, short descriptions, headings, prose, lists, tables, notes, warnings, navigation/search
   strings, captions, and alt text in the review scope.
2. Use Mozilla Pontoon first for established Firefox UI terminology and Mozilla SUMO second for
   reviewed user-facing help vocabulary. Record the lookup URL, source term, selected localized
   term, and decision in the terminology evidence. Use a documented maintainer fallback only for a
   BPM-specific concept absent from Pontoon/SUMO or conflicting source evidence.
3. Classify every remaining visible English occurrence. English is permitted only for a reviewed
   brand, abbreviation, identifier, command/path/API value, or placeholder covered by the authority
   allowlist. An allowlist entry must identify the exact term and occurrence, cite its authority and
   rationale, and be removed when that occurrence disappears. Never convert known translation debt
   into an allowlist entry.
4. Verify placeholders and runtime catalog keys byte-for-byte, then update the visible-English
   inventory, replacement evidence, anti-anglicism guard, and human QA evidence when their reviewed
   scope changes.
5. Run the focused terminology gates before broader documentation validation:

```bash
./.venv/bin/pytest -q -m docs_contract \
  documentation/tests/contract/test_interface_name_authority.py \
  documentation/tests/contract/test_interface_name_replacement.py \
  documentation/tests/contract/test_locale_terminology_authority.py \
  documentation/tests/contract/test_locale_visible_english_inventory.py \
  documentation/tests/contract/test_locale_anglicism_replacement.py \
  documentation/tests/contract/test_locale_anti_anglicism_guard.py \
  documentation/tests/contract/test_documentation_semantic_contracts_0_9_4.py \
  documentation/tests/contract/test_locale_human_qa.py
```

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

## Minimal User Guide screenshot workflow

`documentation/config/user-guide-screenshot-matrix-0.9.1.json` is the maintained source of truth.
For BPM 0.9.6 it has eleven approved User Guide scenarios in all six published locales (66 rows),
including create/duplicate preparation and the dedicated URLs/sites/navigation, certificates/trust,
and extensions views. The accepted BPM 0.9.1 visual-QA record covers its historical six-scenario,
36-row scope only; it does not accept later source rows or rendered site/PDF output. Do not add
Administrator Guide, DevOps Guide, API, or decorative captures, and do not add an asset outside the
matrix.

For every screenshot change:

1. Update or select the matrix row first. Review its locale, scenario, topic ID, route, viewport,
   theme, fixture state, filename, asset path, caption key, and alt-text key. A new scenario expands
   release scope and therefore requires explicit backlog approval before capture.
2. Start BPM separately with the documented synthetic fixture state, then capture the selected
   matrix rows with the dedicated command. The command reads the matrix; it must not discover extra
   pages or silently reuse another locale's asset.

```bash
./.venv/bin/python documentation/tools/capture_user_guide_screenshots.py
```

3. Keep clean PNG source assets under `documentation/assets/screenshots/{locale}/` and temporary
   captures, diffs, masks, and diagnostics under `documentation/reports/screenshots/`. Preserve the
   matrix filename pattern, viewport byte limit, allowed PNG chunks, orphan rule, and cross-locale
   hash rule.
4. Integrate each image only into its matrix User Guide topic. Author its caption and alt text in
   that topic's locale, using the matrix keys and exact localized UI catalog terminology. Verify
   that no localized topic resolves its image, caption, or alt text from another locale.
5. Reconcile all affected rows in the visual-QA evidence against locale, scenario, viewport, theme,
   filename, dimensions, and asset path. If the matrix expands, record source capture separately
   from rendered visual acceptance; do not promote a historical acceptance record to the new scope.
   Run the matrix and visual checks before broad validation:

```bash
./.venv/bin/pytest -q -m docs_contract \
  documentation/tests/contract/test_user_guide_screenshot_matrix.py \
  documentation/tests/contract/test_user_guide_screenshot_visual_qa.py \
  documentation/tests/contract/test_locale_human_qa.py
```

6. When a visible control is simplified, reconcile every circled-info target against its exact
   classification disposition. Each affected locale has either a localized manifest-backed target
   or the recorded reviewed no-link disposition; do not add a generic help link for routine prose.

## Focused checks

After the workflow-specific checks, run the shared documentation gates:

```bash
./.venv/bin/python documentation/tools/validate_metadata.py
make docs-validate
make docs-build
git diff --check -- <changed_files>
```

When the change affects product-documentation source, documentation build tooling, generated portal
behavior, or a served documentation-version surface, also run `make docs-install-dev` before
handoff. It refreshes the artifact for the maintainer's subsequent `make dev`; do not start the
development server for that handoff.

## Done

- Locale-specific visible text, captions, alt text, and screenshot filenames remain aligned.
- No English fallback is served under another locale.
- Every visible-English exception is narrowly allowlisted with authority and occurrence evidence;
  stale exceptions are removed.
- Every reviewed screenshot is represented by exactly one matrix row. The historical 36 approved
  rows retain localized caption/alt-text parity; each later row needs its own current source and
  rendered-review evidence.
- Reviewed screenshots are source assets; transient captures remain ignored.
