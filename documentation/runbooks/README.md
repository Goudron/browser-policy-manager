# Documentation Authoring Runbooks

These runbooks are maintainer instructions for the maintained BPM product documentation subsystem. They
are not product-guide content and are not served under `/help/`.

Use them when a change touches product documentation source, localized peers, screenshots,
generated factual source, manifests, search, or release packaging.

Covered workflows: topic creation, DITA reuse, localization, screenshots, Firefox/CIS/API refresh,
link changes, manifest changes, debugging, review, and publishing.

## Focused workflow map

| Work | Runbook | First focused checks |
| --- | --- | --- |
| Add or update one DITA topic | `add-or-update-topic.md` | `validate_metadata.py`, one relevant contract, `make docs-validate` |
| Review and refresh documentation for an epic | `documentation-update-for-future-epics.md` | heading/terminology contracts, `make docs-release-check` |
| Update localized peers or terminology | `localization-and-screenshots.md` | locale parity contract, `make docs-validate` |
| Add or refresh screenshots | `localization-and-screenshots.md` | screenshot matrix/review checks when implemented; meanwhile source review plus `make docs-build` |
| Refresh Firefox, CIS, API, Administrator/DevOps, source-deployment, update, or production-boundary facts | `inventory-refresh.md` | exact inventory builder/test plus `validate_metadata.py` |
| Change links, keys, anchors, targets, or manifest behavior | `links-manifest-and-publishing.md` | manifest/metadata contracts plus `make docs-reproducibility-check` |
| Diagnose a documentation-only failure | `debugging-protocol.md` | smallest focused command, then the next ladder gate only if still needed |
| Prepare reviewed documentation output | `links-manifest-and-publishing.md` | `make docs-package`, `make docs-package-verify` |

The BPM documentation assistant is a separate product-chat surface, not an alternative
documentation-authoring or deterministic-search workflow. In 0.9.3 it returns only the localized
local-model-training notice. It does not use RAG, citations, external evidence, prompts,
transcripts, embeddings, or indexes. Any future assistant work requires a separately approved
release scope; its artifacts and output never become product-source content.

AI-assisted drafting or localization is allowed during development only when the result passes the
human review, provenance, terminology, placeholder, and parity gates in
`localization-and-screenshots.md`. Unreviewed AI-authored prose, generated chat output, and
AI-generated screenshot descriptions are not publishable documentation. If a topic cannot be
updated without rights/source ambiguity, stop at the provenance decision and record the blocker
rather than paraphrasing restricted material.

Before a release handoff, confirm `docs/docs-index.md` lists every maintained `docs/` file exactly
once and that any changed schema, CIS, locale, Administrator/DevOps deployment, integration, update,
or release procedure points to the focused documentation drift gate that protects it.
