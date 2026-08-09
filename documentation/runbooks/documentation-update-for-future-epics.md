# Runbook: Update Product Documentation For A Future Epic

Use this runbook for every epic that changes a BPM capability, user flow,
administrator procedure, supported Firefox schema, CIS mapping, API contract,
deployment boundary, locale-visible UI term, or documentation presentation.
Apply it before the final quality milestone. It supplements, rather than
replaces, the focused topic, localization, inventory, and publishing runbooks.

`documentation/tools/build_docs.py` is the stable command façade. Its owned
implementation is split across `documentation/buildlib/`: `sources` validates
DITA/source ownership, `catalog` and `portal` build navigation/search and site
data, `artifacts` and `publishing` stage and promote artifacts, `pdf` owns print
generation/verification, and `lifecycle`/`shared` provide the common progress
and atomic handoff rules. Do not add a second coordinator or hand-edit generated
site, search, manifest, package, or PDF output.

## Scope and source of truth

1. Identify the affected reader and guide: User Guide, Firefox Policy Guide,
   CIS Settings Guide, or Administrator Guide. Update the English DITA source
   first and propagate the same product scope to `ru`, `de`, `zh-CN`, `fr`, and
   `es-ES`.
2. Start from the actual released behavior and its authoritative product
   contract. Do not document an experiment, backlog item, test fixture, build
   artifact, future feature, or implementation detail as a reader capability.
   Source-install commands belong only in the administrator procedures that a
   BPM operator actually performs.
3. Reconcile the map, title, short description, procedure/result/recovery,
   related links, search aliases, screenshots, and contextual-help target of
   every changed topic. Keep released IDs, keys, anchors, canonical paths, and
   source provenance stable.
4. Review all four guide maps when a new capability spans more than one
   audience. A guide with at most twelve topics can remain flat; otherwise use
   the reviewed section taxonomy. Keep minimum system requirements as the first
   Administrator Guide topic.

## Editorial and terminology review

Apply the [Microsoft Writing Style Guide](https://learn.microsoft.com/en-us/style-guide/)
to the English source: use concise sentence-case headings, parallel task names,
one action per procedural step, and an introduction only when it adds context.
Use the [Microsoft globalization guidance](https://learn.microsoft.com/en-us/style-guide/global-communications/writing-tips)
to keep the source easy to localize; do not copy its English grammar into a
localized heading.

For every visible localized term:

1. Use the BPM runtime locale catalog for a rendered BPM interface name.
2. For Firefox UI terminology, check the approved Firefox translation in
   [Mozilla Pontoon](https://pontoon.mozilla.org/projects/firefox/).
3. For explanatory Firefox support vocabulary, check the corresponding
   [Mozilla SUMO article](https://support.mozilla.org/), preferring its target
   locale when it exists.
4. Record the checked URLs, source term, selected term, and any conflict in the
   terminology authority or task evidence. Pontoon controls an in-product label;
   SUMO controls surrounding help prose. A BPM-specific term without Mozilla
   evidence needs a documented maintainer decision.
5. Apply the locale editorial policy to titles and headings: Russian uses an
   idiomatic nominal phrase; German task headings use an infinitive without
   `Sie`; Simplified Chinese uses compact Chinese phrasing and no word spacing;
   French and Spanish task headings use infinitives and sentence case.

Do not translate brands, API paths, commands, identifiers, schema channels,
policy IDs, preference IDs, placeholders, filenames, or code literals unless
their owning authority explicitly supplies a localized UI form.

## Completeness and exclusion review

For each affected guide, confirm that a reader can find the purpose,
prerequisites, task or concept explanation, expected outcome, limitation or
support boundary, recovery path where applicable, and related task. Confirm
that the guide covers every released user-visible change once, in the audience
that owns it; do not duplicate administrator deployment content in the User
Guide.

Remove or rewrite reader-facing content that exposes maintainer workflow, CI or
test instructions, source-tree internals, transient evidence, credentials,
private hosts, unapproved third-party prose, obsolete product behavior, or a
future capability presented as available. Keep an explicit unsupported or
deferred boundary when omitting it would cause unsafe operation. Product
documentation may state that a feature is unavailable, but must not turn its
unshipped architecture into operator instructions.

For the BPM documentation assistant, document only the delivered behavior for
the target release and keep it separate from deterministic documentation search.
Do not expose model weights, prompts, embeddings, vector generations, chat
transcripts, provider configuration, or external responses as product-guide
content.

## Required checks and release evidence

Run the narrowest affected contract first. Use `make docs-fast-check` with the
changed documentation paths for a bounded source/tooling check; it is not a
release substitute. When a guide map, localization, presentation, search source,
package, or PDF changes, run the complete documentation release checks:

```bash
make docs-fast-check DOCS_CHANGED='documentation/src/dita/en/user/example.dita'
make test-docs-contract
make docs-validate
make docs-release-check
make docs-reproducibility-check
```

Record the exact completed commands and their generated evidence, including
locale, guide, manifest/search target, PDF verification, package verification,
and the installed-artifact result. An incomplete audit is a release blocker;
do not substitute a narrative status statement for a failing or unrun gate.

For any changed user or administrator guide, rebuild both guide PDFs in every
published locale and verify them. Inspect at least the title page, contents,
section hierarchy, code blocks, screenshots, link targets, dark/light styling,
and CJK glyph rendering; reduce screenshots to the printable page area
instead of clipping them. The PDF pipeline must transform the reviewed DITA
maps to HTML5 and render the print bundle with local Chromium. Do not replace
it with FOP for CJK content: Chromium supplies the single Unicode shaping
engine that prevents mixed Chinese prose and `codeph` literals from acquiring
incompatible baseline metrics. In a CJK PDF, inspect paragraphs containing
inline API paths, identifiers, and response values: no literal may overlap
surrounding prose. Preserve semantic `codeph` markup and its exact literal.
Keep commands, payloads, and other multi-line examples in `codeblock`
elements; do not remove their technical values or replace them with
screenshots. The renderer must run headless with background networking
disabled and must not start a BPM development server.

For every PDF change, keep the M11 print contract fail-closed. The title page
must state the actual final page count and place the visible copyright at the
bottom. Build that copyright from the same UI-footer template and locale
catalog values: Russian uses `Валерий Ледовской` and `Лицензия`; every other
published locale uses `Valery Ledovskoy` and `Licensed under`. The
release-scoped `ui_footer_year` in the PDF generation contract freezes the
same year range that the rendered UI shows for that release. Every page after
the title page must carry its actual PDF sequence number, centered at the
bottom for printed copies.

The contents is a binary navigation contract, not a visual list. Use the
two-pass Chromium render to measure the real page of every stable section and
topic destination, then render that number and an internal link into the
contents entry. The final verifier must use `qpdf` structure data to prove that
each displayed destination page equals the actual named-destination page and
that every destination has a link annotation. It must use positioned
`pdftotext` output to prove the localized page-count text, bottom title-page
copyright, absence of a page number on page 1, and one centered, correct page
number on every later page. Preserve zero-gap CJK text such as `页数：103`
when reconstructing positioned lines. Never edit generated PDFs manually.

```bash
make docs-pdf-build
make docs-pdf-verify
make docs-pdf-reproducibility
make docs-pdf-deliver
make docs-pdf-delivery-verify
make docs-package
make docs-package-verify
make docs-install-dev
```

Long-running build, render, package, or validation commands must print flushed
real-work progress to stdout: phase or locale, completed and total units, cache
state where relevant, and a final success or failure boundary. Keep progress in
the command output, not in maintainer chat. Do not start the development server
as part of the `make docs-install-dev` handoff.

## Done

- All affected guide maps have a logical, localized, scannable structure.
- Headings follow Microsoft guidance for English and native conventions for the
  five localized languages; UI and Firefox terminology has a recorded authority.
- The guides are complete for the released scope and exclude stale, internal,
  unsafe, and unshipped reader claims.
- DITA, generated site, both guide PDFs in all six locales, delivery directory,
  and documentation package have been rebuilt only from source and verified.
- PDF title-page totals, localized UI-footer copyright, linked/page-numbered
  contents, named destinations, and printed page numbers pass binary
  verification and an independent 13-file SHA-256 reproducibility comparison.
- The epic backlog records this runbook in its documentation milestone and the
  successful `make docs-install-dev` handoff.
