# BPM 0.9.6 profile documentation PDF candidate

Date: 2026-08-21

Backlog item: `BPM096-M10-08`

Status: completed. This record covers the source-owned PDF candidate, its
binary and visual review, and atomic PDF delivery. It does not install a
development documentation site, build a documentation package, or start a
development server; those remain owned by later M10 work.

## Source repair before the owner build

The first owner build correctly quarantined its candidate before publication.
DITA-OT found that the M10 localized `Current 0.9.6 behavior` fragments used
`section` directly inside `taskbody`, where DITA permits an `example` before
`postreq` instead. The structural repair covered the same 11 task topics in
each of `en`, `ru`, `de`, `zh-CN`, `fr`, and `es-ES` (66 authored DITA files).
It moved the text into a valid `example`, preserved all localized content and
the 12 administrative literal IDs, and did not edit a generated PDF, map,
catalog, or screenshot.

The smallest invalidated preflight then passed:

```text
make docs-fast-check DOCS_CHANGED='<the exact 66 DITA paths>'
```

It checked all six locales and the User, Firefox Policy, CIS Settings, and
Administrator guide roots. Direct XML parsing also completed `66/66` repaired
topics. The subsequent owner PDF build is the candidate recorded below.

## Owner build and binary verification

`make docs-pdf-build` completed its sequential `6 locales × 2 guides ×
2 render stages` matrix (`24/24`): each locale-guide pair first completed DITA
HTML5 and then Chromium PDF rendering. The owner validated each pair before
storing its verified cache entry, wrote the manifest, and atomically promoted
the candidate to `documentation/build/pdf`.

`make docs-pdf-verify` passed against that published candidate. Its binary
verification checked the complete 12-PDF inventory, PDF structure, title-page
page count and localized footer, unnumbered title page, centered numbering on
every later page, positioned page fit, figure inventory, named destinations,
and clickable contents targets. The contents page numbers equal the actual
named-destination pages; no hand-edited PDF was accepted.

| Locale | User Guide pages | Administrator Guide pages |
| --- | ---: | ---: |
| `en` | 110 | 81 |
| `ru` | 114 | 99 |
| `de` | 112 | 97 |
| `zh-CN` | 109 | 73 |
| `fr` | 112 | 95 |
| `es-ES` | 111 | 97 |

The candidate manifest has 12 declared PDF SHA-256 records and BPM version
`0.9.6`; its source fingerprint is
`acf0e5934dd3ebb4f09afd743f0cc048f57534027b89b8c1bde3d4ce6e0c674c`.

## Rendered visual review

Visual review used rasterized pages from the published PDFs, never a source
mockup or a generated-artifact edit. The following representative pages were
read alongside the owner-wide binary checks:

| Review surface | Pages inspected | Result |
| --- | --- | --- |
| English User title and contents | 1–2 | Visible `0.9.6`, final `Pages: 110`, logical hierarchy, and real contents page values fit the page. |
| English Guided certificate capture | 38 | Step-4 screenshot, caption, controls, and following procedure fit without crop or overlap. |
| English Administrator API literals and code blocks | 42 and 45 | Inline preparation endpoints/envelope literals and multi-line shell examples remain readable and unbroken. |
| Simplified Chinese User title and contents | 1–2 | Chinese title, `页数：109`, headings, and contents rows render as glyphs rather than fallback boxes. |
| Simplified Chinese certificate capture | 37 | Localized Step-4 capture, caption, and surrounding prose fit without clipping. |
| Simplified Chinese Administrator literals and code blocks | 38 and 41 | Chinese prose and adjacent API identifiers keep separate baselines; code blocks remain readable without overlap. |

The owner verifier covers the same title/contents/link/page-number contracts for
every guide and locale. The manual rendered samples additionally confirm CJK
glyph shaping, inline technical literals, long code blocks, screenshots, and
printable page fit in the two highest-risk language/script combinations.

## Reproducibility and atomic delivery

`make docs-pdf-reproducibility` first verified the published candidate and
then rebuilt the complete matrix in an isolated tree with cache bypassed.
Its `24/24` independent render completed and SHA-256 comparison passed for 13
files: the 12 PDFs plus the candidate manifest.

`make docs-pdf-deliver` constructed a verified staging directory and atomically
promoted only `distributions/documentation/0.9.6`. It did not replace or delete
the existing `0.9.3`, `0.9.4`, or `0.9.5` delivery directories. Finally,
`make docs-pdf-delivery-verify` passed: delivery file set, manifest identity,
candidate provenance, all 12 PDF hashes, and delivery checksums match the
verified candidate.

Generated candidate and delivery files were produced only by their owners;
this record is the review evidence, not a substitute artifact.

## Final focused regression verification

The focused PDF regression bundle exited successfully:

```text
.venv/bin/pytest -q documentation/tests/unit/test_build_docs.py \
  documentation/tests/unit/test_deliver_pdfs.py \
  documentation/tests/contract/test_pdf_generation_contract_0_9_3.py \
  documentation/tests/contract/test_pdf_delivery_contract_0_9_3.py \
  documentation/tests/contract/test_localized_figure_captions_0_9_4.py
```

That run exposed and then verified five stale test expectations left behind by
the published M10-07 site: the current BPM version, ten normalization alias
groups, eight English query fixtures, 531 UI targets, and 21 API-operation
targets. The test now derives locale-specific fixture counts from the same
contract as the generator and reads the current BPM version rather than a
stale release literal. These are test-only corrections; no DITA, map,
catalog, screenshot, layout, or other PDF input changed, so they did not
invalidate the completed owner PDF build.

The final owner checks also passed:

```text
make docs-pdf-verify
make docs-pdf-delivery-verify
git diff --check
```

An independent read-only SHA-256 comparison matched all `12/12` candidate and
delivered PDFs against `pdf-build-manifest.json`.
