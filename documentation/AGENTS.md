# AGENTS.md

These instructions apply to every task under `documentation/` and refine the repository-root
`AGENTS.md`. Follow both; this file is more specific when the task is documentation-only.

## Start Here

Read in this order before expanding context:

1. `documentation/PROJECT_SNAPSHOT.md` for the current implemented state and available commands.
2. `documentation/README.md` for source/generated/artifact ownership.
3. The relevant `documentation/runbooks/` workflow when changing topics, localization, screenshots,
   inventories, links, manifests, debugging, or publishing behavior.
4. The one approved task row and execution-progress section in
   `docs/bpm_0_9_0_product_documentation_portal_backlog_2026-06-20.md`.
5. Only the directly relevant architecture decision or inventory listed in the snapshot.
6. The exact source/config/tool/fixture/test files named by the task or its first focused failure.

Do not begin a documentation-only task from the repository-wide generated snapshot unless the local
snapshot explicitly sends you there. Before editing, state the minimal files you plan to inspect or
change.

## Context Discipline

- Use targeted `rg`/`rg --files` queries. Do not recursively read the repository, all `docs/`, all
  five guides, or all six locale trees.
- Never scan or read `documentation/build/`, `documentation/dist/`, `documentation/reports/`,
  `documentation/.cache/`, dependency/toolchain/vendor/virtual-environment folders, or a complete
  generated site/index.
- Treat `documentation/src/generated/` as generator-owned. Read one generated file only when a
  failing generation/contract task names it; never hand-edit it.
- Do not read ignored CIS PDFs or other licensed source corpora. Use the maintained CIS inventory,
  provenance decision, and the smallest mapping record required by an approved task.
- Do not load a full Firefox schema when an inventory entry, focused definition lookup, or existing
  schema service can answer the question.
- Do not open general BPM modules, databases, migrations, profile services, or frontend bundles for
  content/build/search work. Cross the runtime boundary only for an approved `/help/`, Library-link,
  screenshot, API-contract, or release task.
- If a focused failure points outside this boundary, read the smallest adjacent owner/test first and
  report any material scope expansion.

## Task Routing

| Work | Start with | Normally exclude |
| --- | --- | --- |
| One topic | `runbooks/add-or-update-topic.md`, English topic/map, same topic in the one affected locale, direct keys/assets, one contract | Other topics/locales, generated HTML, `app/` |
| Locale parity | `runbooks/localization-and-screenshots.md`, English peer, one target-locale peer, shared key, relevant glossary/provenance, parity test | Other four locales and runtime catalogs unless a shared BPM label changed |
| Firefox policy topic | `runbooks/inventory-refresh.md`, policy inventory entry, exact bundled definition through a targeted lookup, topic peers, provenance record | Whole schemas, CIS corpus, unrelated policies |
| CIS topic/workflow | `runbooks/inventory-refresh.md`, CIS inventory entry, exact BPM mapping/layer record, provenance/release rules, topic peers | Ignored PDF, long benchmark source data, unrelated recommendations |
| API topic/example | `runbooks/inventory-refresh.md`, API inventory operation, generated OpenAPI fragment, exact route/model contract test, synthetic fixture | Other endpoints, browser UI implementation |
| DITA build/config | Failing map/topic, `config/`, one tool, compact fixture/test, toolchain decision/log | Runtime routes, all topics, screenshots, general tests |
| Manifest/targets | `runbooks/links-manifest-and-publishing.md`, versioned schemas/examples, relevant map metadata, one generator/fixture/contract | Built pages, product services, unrelated UI modules |
| Search | Search tool, compact locale corpus/query fixture, manifest sample, focused unit/contract | Full corpus/site, backend/database, Selenium |
| Fixture catalog | `fixtures/fixture-catalog-0.9.0.json`, one fixture file, `test_documentation_fixture_catalog.py` | Production exports, full corpora, generated sites, browser downloads |
| Failure diagnostics | `config/diagnostics-policy-0.9.0.json`, one failing focused check, generated artifact under `reports/diagnostics/` | Committed reports, full generated sites, secrets/customer data |
| Debugging protocol | `runbooks/debugging-protocol.md`, one failing focused command, the owning contract, and its smallest rerun | Broad release gates, browser runs, generated output, unrelated source trees |
| Screenshot | `runbooks/localization-and-screenshots.md`, one matrix row, locale/topic, deterministic fixture, directly rendered BPM route, capture test | Whole guide corpus, other routes/locales |
| `/help/` serving | Future `app/documentation/`, manifest fixture, config/security bridge, focused app contract | DITA authoring tools and unrelated product logic |
| BPM help link | One template/frontend owner, exact target fixture, six shell labels, focused UI contract | Publisher/search internals and unrelated editors |

## Authoring And Mutation Rules

- Product source is English. Published locales are exactly `en`, `ru`, `de`, `zh-CN`, `fr`, and
  `es-ES`; non-English content is human-authored/reviewed and may not silently fall back to English.
- Do not ship AI/RAG/embeddings/generative answers, AI-generated screenshot descriptions, or
  unreviewed machine output as documentation functionality. AI-assisted drafting or localization is
  allowed during development only after human review, provenance, terminology, placeholder, and
  parity gates.
- Publishable product content is DITA 1.3. Do not add product-guide Markdown, hand-authored HTML,
  inline script/style, raw HTML passthrough, or DITA 2.0 preview syntax.
- Preserve immutable topic IDs, keys, anchors, target IDs, source slugs, asset IDs, and canonical URL
  paths. Use key-based links rather than translated filenames or generated `.html` paths.
- Keep localized prose, navigation, captions, alt text, and search terms in locale sources. Shared
  DITA metadata must remain language-neutral.
- Screenshots under `assets/screenshots/{locale}/` are reviewed source assets, not transient browser
  output. Use synthetic data and keep temporary captures/diffs under ignored `reports/`.
- Fixtures stay compact, deterministic, synthetic, and free of secrets, private hosts, production
  data, full external corpora, and licensed PDFs.
- Documentation tools are build-time only and must never be imported by `app/`.
- Fix source, transform, or generator defects and rebuild. Never patch `build/`, reports, search
  indexes, manifests, or packaged artifacts by hand.

## Generated And External Material

- Every generated source declares generator, source version/revision, and provenance. Generation
  must be reproducible and preserve reviewed hand-authored regions by design.
- Apply `product-documentation-provenance-matrix-0.9.0.json`: unregistered or unclear sources are
  blocked; link-only and approval-required material may not enter publishable DITA/search/output.
- Mozilla-derived facts retain exact tag/hash/MPL attribution and separate trademark notices.
- CIS source expression/PDF content remains blocked without scoped rights approval. BPM may document
  its own mappings and behavior in original attributed prose without certification/endorsement
  claims.
- Translation, DITA conversion, indexing, or format changes do not remove source restrictions.

## Verification Ladder

Use the narrowest implemented check first and state what remains unverified.

Available now from the repository root:

```bash
make setup-docs-toolchain
make setup-docs-toolchain DOCS_TOOLCHAIN_OFFLINE=1
make test-docs
make test-docs-contract
make test-docs-ui
make test-docs-ui-contract
make test-docs-browser
make docs-snapshot
make docs-fast-check DOCS_CHANGED="documentation/src/dita/en/user/example.dita"
make docs-coverage
make docs-release-check
make docs-validate
make docs-build
make docs-install-dev
make docs-reproducibility-check
make docs-package
make docs-package-verify
./.venv/bin/python documentation/tools/validate_metadata.py
./documentation/.cache/toolchain/python-venv/bin/pytest -q documentation/tests/unit/test_bootstrap_toolchain.py
./.venv/bin/pytest -q tests/test_product_documentation_scaffold.py
./.venv/bin/pytest -q -m docs_contract tests/<one_relevant_contract>.py
./.venv/bin/pytest -q -m docs_contract
./.venv/bin/ruff check <changed_python_files>
git diff --check -- <changed_files>
```

The all-`docs_contract` command includes maintained architecture/scaffold checks in the general
`tests/` tree. It is broader than one subsystem test but still excludes browser/live layers.

Use `documentation/runbooks/debugging-protocol.md` to choose the next check after any
documentation-only failure. The protocol records what each cheap check proves and what remains
unverified before browser, screenshot, release, or manual QA gates.

The setup command is explicitly networked unless `DOCS_TOOLCHAIN_OFFLINE=1`; both variants verify
locked archives, exact versions, and a DITA 1.3 HTML5 smoke build. The focused `test-docs*`
commands run only `documentation/tests/` selections. `make test-docs-ui-contract` runs the
non-browser portal/UI contracts. `make test-docs-browser` runs the Chromium/Selenium documentation
portal smoke and requires immediate sandbox escalation; `make test-docs-ui` runs both layers.
`make docs-snapshot` refreshes the bounded documentation subsystem map. `make docs-fast-check` validates changed documentation source
inputs, reports affected locale/guide/search outputs, and does not run DITA-OT or unrelated BPM
code. `make docs-coverage` writes isolated documentation coverage reports
under `documentation/reports/coverage/` and must keep the included coverage-policy scope at 100%.
`make docs-release-check` runs full six-locale DITA validation plus the maintained documentation
contract suite and is a prerequisite of `make test-release`.
The validation, build, dev-install, reproducibility, and packaging commands are offline and use only
that cache. `make docs-install-dev` promotes a validated local build into ignored
`app/documentation/site` so `make dev` can serve `/help/` for maintainer review; it is not release
package extraction evidence.
Planned commands are
**not available yet** and must not be reported as passing:

```text
make docs-screenshots-check # later screenshot/test tasks
```

Update `documentation/PROJECT_SNAPSHOT.md` in the same change whenever a task adds/removes a real
entry point, directory, command, dependency, generated artifact, guide/map, or runtime bridge. Do
not update it with planned behavior presented as implemented.

## Browser And Long-Running Work

- `make test-ui`, `make test-docs-ui`, `make test-docs-browser`, Selenium, Chromium, Firefox, and
  screenshot capture require immediate sandbox escalation. Do not first attempt them inside the
  sandbox.
- Browser work must use deterministic disposable test state and store diagnostics only under ignored
  `documentation/reports/` or the established general test artifact boundary.
- Focused documentation failures may write JSON diagnostics under `documentation/reports/diagnostics/`.
  Keep those artifacts ignored and report their path plus the focused rerun command.
- For long-running build, localization, generation, or browser commands, keep progress or periodic
  status visible. Stop short hangs and report the last completed phase.

## Completion Report

Report the smallest changed surface, exact focused checks that passed, browser/full-suite checks not
run, and any remaining release gate. During interactive backlog execution, show exactly one next
task with ID, essence, acceptance, and minimal reasoning, then wait for approval.
