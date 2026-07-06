# Documentation Authoring Runbooks

These runbooks are maintainer instructions for the BPM 0.9.0 product documentation subsystem. They
are not product-guide content and are not served under `/help/`.

Use them when a change touches product documentation source, localized peers, screenshots,
generated factual source, manifests, search, or release packaging.

Covered workflows: topic creation, DITA reuse, localization, screenshots, Firefox/CIS/API refresh,
link changes, manifest changes, debugging, review, and publishing.

## Focused workflow map

| Work | Runbook | First focused checks |
| --- | --- | --- |
| Add or update one DITA topic | `add-or-update-topic.md` | `validate_metadata.py`, one relevant contract, `make docs-validate` |
| Update localized peers or terminology | `localization-and-screenshots.md` | locale parity contract, `make docs-validate` |
| Add or refresh screenshots | `localization-and-screenshots.md` | screenshot matrix/review checks when implemented; meanwhile source review plus `make docs-build` |
| Refresh Firefox, CIS, API, Administrator/DevOps, source-deployment, update, or production-boundary facts | `inventory-refresh.md` | exact inventory builder/test plus `validate_metadata.py` |
| Change links, keys, anchors, targets, or manifest behavior | `links-manifest-and-publishing.md` | manifest/metadata contracts plus `make docs-reproducibility-check` |
| Diagnose a documentation-only failure | `debugging-protocol.md` | smallest focused command, then the next ladder gate only if still needed |
| Prepare reviewed documentation output | `links-manifest-and-publishing.md` | `make docs-package`, `make docs-package-verify` |

Do not ship AI/RAG/embeddings/generative answers, AI-generated screenshot descriptions, or
unreviewed machine output as documentation functionality. AI-assisted drafting or localization is
allowed during development only when the result passes the human review, provenance, terminology,
placeholder, and parity gates in `localization-and-screenshots.md`. If a topic cannot be updated
without rights/source ambiguity, stop at the provenance decision and record the blocker rather than
paraphrasing restricted material.

Before a release handoff, confirm `docs/docs-index.md` lists every maintained `docs/` file exactly
once and that any changed schema, CIS, locale, Administrator/DevOps deployment, integration, update,
or release procedure points to the focused documentation drift gate that protects it.
