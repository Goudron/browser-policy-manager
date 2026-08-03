# Runbook: Update Product Documentation For A Future Epic

Use this runbook for every epic that changes a BPM capability, user flow,
administrator procedure, supported Firefox schema, CIS mapping, API contract,
deployment boundary, locale-visible UI term, or documentation presentation.
Apply it before the final quality milestone. It supplements, rather than
replaces, the focused topic, localization, inventory, and publishing runbooks.

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

## Required checks

Run the narrowest affected contract first, then the complete documentation
release checks when a guide map, localization, presentation, search source, or
PDF changes:

```bash
./.venv/bin/python documentation/tools/validate_metadata.py
./.venv/bin/pytest -q -m docs_contract documentation/tests/contract/test_localized_heading_style.py
make docs-validate
make docs-release-check
make docs-reproducibility-check
```

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
- The epic backlog records this runbook in its documentation milestone and the
  successful `make docs-install-dev` handoff.
