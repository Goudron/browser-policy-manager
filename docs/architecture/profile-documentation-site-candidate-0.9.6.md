# BPM 0.9.6 profile documentation site candidate

Date: 2026-08-21

Backlog item: `BPM096-M10-07`

Status: completed. This record covers one verified static site candidate only.
It does not create PDFs, a package, an installed development site, or a
development server; those remain owned by later M10 tasks.

## Candidate and publication boundary

The site owner is `make docs-build`. It builds a disposable candidate beneath
`documentation/build/`, validates source and generated output, then uses the
owner's rollback-safe atomic promotion only after the candidate's manifest
validation succeeds. Generated HTML, navigation, search, manifests, and image
assets were never edited manually.

The first owner build completed all six DITA HTML5 transforms but failed before
publication while assembling portal metadata. Its candidate was quarantined by
the owner. The failure correctly found two category values present in the
Firefox documentation inventory but absent from the deterministic search-facet
declaration: `sync_accounts` and `urls_sites_navigation`.

The source repair was deliberately limited to:

- `documentation/config/search-facets-filters-0.9.0.json`, which now declares
  both values;
- `documentation/buildlib/shared.py`, which gives both values native visible
  labels in all six locales; and
- `documentation/tests/contract/test_search_facets_filters.py`, which prevents
  either declaration or six-locale labels from regressing to an identifier.

The focused search contracts passed (`18 passed`) and the smallest invalidated
preflight, `make docs-fast-check` over the changed configuration and contract,
passed for the six locale-owned search outputs. The one permitted owner-build
retry then completed source validation, all six locale transforms, candidate
validation, and atomic promotion to `documentation/build/site`.

## Published candidate verification

The published candidate, rather than a hand-inspected generated copy, was
checked through its owners:

| Surface | Evidence |
| --- | --- |
| Atomic publication | Owner progress reached `site promotion` `3/3` only after candidate validation; the failed predecessor remained quarantined. |
| HTML, links, safe static output, and screenshot references | `validate_output(documentation/build/site)` passed. |
| Manifest, navigation, search, aliases, and locale parity | `validate_manifest_files(documentation/build/site)` passed; manifest navigation and search records contain exactly `en`, `ru`, `de`, `zh-CN`, `fr`, and `es-ES`. |
| Published screenshots | Each locale-owned output tree contains 11 PNG assets; source matrix/caption contracts passed. |
| Portal shell, generated manifest, and theme | `make test-docs-ui-contract` passed: `11 passed`. |
| Contextual help, CSP/runtime boundary, search integrity, navigation, and localized screenshots | The focused M10 contract group passed: `52 passed in 2.92s`. |

The successful candidate is therefore eligible for the subsequent M10 release
steps. `BPM096-M10-08` remains the owner of both PDF guides and their visual
review; no PDF command, development-site installation, or development server
was run here.
