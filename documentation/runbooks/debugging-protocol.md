# Documentation-only debugging protocol

Use this protocol when a documentation task fails, when CI reports a documentation-only failure, or
when a maintainer needs to choose the cheapest reliable check before a broader release gate.

The rule is simple: start with the smallest command that owns the failure, read only the files named by that failure, and say what remains unverified before moving to the next layer.

## Debugging ladder

| Situation | First command | What it proves | Still unverified |
| --- | --- | --- | --- |
| One changed topic, map, image reference, JSON config, or fixture | `make docs-fast-check DOCS_CHANGED="<changed paths>"` | The changed source inputs are well-formed, directly linked references are valid, and the failure report names the affected locale, guide, search, and output areas. | Full DITA-OT output, generated HTML links, all locale peers, browser behavior, packaging, and product release gates. |
| DITA metadata, keys, subject scheme, guide map, topic model, or locale parity failure | `make test-docs-contract` or the exact `documentation/tests/contract/...` file named by the failure | The maintained documentation contract for the affected area still matches source, inventories, maps, localization peers, and fixtures. | Real browser rendering, full DITA transform, package contents, and product-wide release behavior. |
| Build, manifest, target-map, generated links, search index, or package shape concern | `make docs-validate`, then `make docs-build` or `make docs-reproducibility-check` if generated output must be compared | Six-locale DITA validation, source/generated link integrity, manifest and search generation, and deterministic build behavior. | Browser-only interactions, screenshots, installed-runtime packaging, and general BPM tests. |
| `/help/`, BPM header link, contextual help, deep help icon, responsive portal, asset loading, search UI shell, or OpenAPI `/docs` preservation concern | `make test-docs-ui-contract` for static contracts; `make test-docs-browser` for real Chromium behavior | Non-browser contracts prove manifest/UI target wiring; browser smoke proves new-tab flow, locale switching, assets/search index loading, responsive width, and `/docs` preservation through a compact installed artifact. | Full screenshot capture/review, full generated-site visual inspection, and product-wide UI regression. |
| Local documentation assistant wording, readiness, scope, or external-mode boundary | The exact assistant contract plus its focused service/UI test | The 0.9.3 localized training notice and deterministic-search independence remain explicit; no model, RAG, citation, or external-source behavior is implied. | Future provider behavior, model/index installation, browser rendering, package, and product-wide release behavior unless a separately approved task requires them. |
| Screenshot source, localized screenshot matrix, or visual evidence concern | `make test-docs-browser` for current smoke; future `make docs-screenshots-check` when implemented | Current smoke proves a reviewed source asset can load in the portal and that browser diagnostics stay out of source. | Deterministic capture, locale-specific screenshot freshness, image review, and complete screenshot matrix remain unverified until the screenshot task lands. |
| Coverage, diagnostics, or fixture isolation concern | `make docs-coverage`, `make test-docs-contract`, or the named policy/fixture contract | Documentation-owned helper coverage, compact fixture boundaries, and ignored diagnostic artifact policy are enforced. | DITA rendering, browser behavior, and release packaging. |
| Release readiness or a change that could affect multiple documentation areas | `make docs-release-check`, then `make test-release` when product release validation is required | Full six-locale DITA validation and all documentation contracts run before the general non-live BPM release suite. | Browser-backed `make test-docs-ui`, future screenshot capture, full `make coverage`, `make test-ui`, live Firefox, manual QA, commit, and push handoff unless those gates are run separately. |

## Failure handling

1. Copy the failing command and rerun the smallest focused command named in the failure, not the
   broad release command.
2. If `make docs-fast-check` emits a diagnostic path under `documentation/reports/diagnostics/`,
   inspect that ignored JSON artifact for topic ID, locale, guide, source line, target URL, query,
   screenshot state, and focused rerun command. Do not commit the report.
3. Read the relevant source file, adjacent fixture/config, and the owning contract only. Do not scan all locale trees, generated HTML, full search indexes, browser downloads, or unrelated BPM
   modules until the focused failure points there.
4. Fix source, transform, config, or generator code. Never patch `documentation/build/`,
   `documentation/dist/`, `documentation/reports/`, generated search indexes, manifests, or packaged
   artifacts by hand.
5. After a focused check passes, state the remaining unverified layers from the table above. Move up
   the ladder only when the task acceptance or risk requires it.

## Browser and release escalation

`make test-docs-browser`, `make test-docs-ui`, Selenium, Chromium, Firefox, and screenshot capture
require immediate sandbox escalation. Do not try a sandboxed browser run first.

`make docs-release-check` is documentation-only and non-browser. It is a prerequisite of
`make test-release`, but it does not replace `make test-docs-browser`, future screenshot checks,
manual documentation QA, product coverage, product UI smoke, or live Firefox gates.

## Reporting template

Use this compact report after a documentation debugging task:

```text
Changed: <smallest source/config/tool/test surface>
Passed: <focused commands>
Not run / still unverified: <browser, screenshot, package, release, manual QA, or live gates>
Next smallest rerun if this fails again: <one command or test path>
```
