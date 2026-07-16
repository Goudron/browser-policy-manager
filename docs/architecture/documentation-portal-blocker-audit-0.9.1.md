# BPM 0.9.1 Documentation Portal Blocker Audit

Date: 2026-07-06
Status: active audit
Backlog item: `BPM091-M2-01`

## Scope

This is the bounded baseline audit for the BPM 0.9.1 documentation completion
epic. It inspects the current documentation portal, DITA source, generated
manifest/search artifacts, navigation shell, screenshot source area, theme
assets, localized output, Administrator/DevOps source-install topics, and All
Settings help-link surface only where they affect the approved 0.9.1 blockers.

Historical 0.9.0 architecture contracts, inventories, source-provenance files,
and archive records are not reopened by this audit. Generated output under
`app/documentation/site/` is evidence only and must be regenerated through the
documentation build pipeline instead of hand-edited.

## Inspected Evidence

- `documentation/PROJECT_SNAPSHOT.md` and `documentation/README.md` still
  describe the implemented documentation workspace as BPM 0.9.0.
- `app/documentation/site/manifest.json` has artifact `bpm_version` and
  `documentation_version` equal to `0.9.0`; it lists six locales, five guide
  families, and 156 topics.
- `app/documentation/site/ui-target-map.json` has `bpm_version` equal to
  `0.9.0` and 452 generated targets.
- `app/documentation/site/search/{en,ru,de,zh-CN,fr,es-ES}/index.json` exists;
  representative non-English indexes keep English facet labels such as
  `API area`, `Guide family`, and `DITA topic kind`.
- `documentation/src/dita/{en,ru,de,zh-CN,fr,es-ES}/maps/` contains the five
  guide maps, locale key maps, and portal maps for all active locales.
- `documentation/assets/screenshots/{en,ru,de,zh-CN,fr,es-ES}/` contains only
  `.gitkeep` placeholders; no reviewed publishable screenshots are present.
- `documentation/assets/theme/bpm-docs.css` is a BPM 0.9.0 portal stylesheet
  and defines `--bpm-docs-surface: #ffffff` for the light theme.
- Representative generated pages such as
  `app/documentation/site/en/index.html` and
  `app/documentation/site/en/user/ug-task-use-all-settings.html` render the
  current shell with a full search block, duplicate guide lists, flat sidebar
  anchors, and breadcrumbs that do not name the active guide/topic hierarchy.
- `documentation/src/dita/en/admin/admin-task-prepare-linux-source-deployment.dita`,
  `admin-task-set-up-linux-source-checkout.dita`, and
  `admin-task-configure-linux-source-runtime.dita` document a generic 0.9.0
  source workflow, not exact source-install commands for the selected five
  Linux distributions required by 0.9.1.
- `app/static/profiles_all_settings_list.js` renders each All Settings row as
  one selectable button with setting and value cells; no per-row circled-info
  documentation link exists in the row markup.

## Confirmed Gaps

| Gap | Confirmed blocker | Affected files or generated artifacts | Closing task |
| --- | --- | --- | --- |
| `DOC091-AUDIT-G01` | Installed documentation metadata and workspace notes still identify the documentation artifact as BPM 0.9.0. | `documentation/PROJECT_SNAPSHOT.md`, `documentation/README.md`, `documentation/config/artifact-policy.json`, `documentation/config/toolchain-lock.json`, `documentation/tools/build_docs.py`, `app/documentation/site/manifest.json`, `app/documentation/site/ui-target-map.json`, search indexes. | `BPM091-M9-02`, `BPM091-M9-04`, `BPM091-M12-05` |
| `DOC091-AUDIT-G02` | The localized User Guide screenshot blocker is still open: the locale screenshot source directories have no reviewed assets and no 0.9.1 minimal matrix. | `documentation/assets/screenshots/{locale}/`, `documentation/fixtures/screenshot-states/screenshot-states-0.9.0.json`, User Guide DITA topics that will receive figures. | `BPM091-M2-02`, `BPM091-M5-01`, `BPM091-M5-02`, `BPM091-M5-03`, `BPM091-M5-04`, `BPM091-M5-05` |
| `DOC091-AUDIT-G03` | Documentation theme assets are not aligned with the 0.9.1 BPM UI target and still use pure-white light surfaces; explicit light/dark/system product-style theme behavior is not yet implemented in the portal shell. | `documentation/assets/theme/bpm-docs.css`, `bpm-docs-print.css`, `bpm-docs-search.js`, generated locale assets under `app/documentation/site/*/assets/`. | `BPM091-M2-03`, `BPM091-M3-01`, `BPM091-M3-03`, `BPM091-M3-04`, `BPM091-M3-05` |
| `DOC091-AUDIT-G04` | Documentation search is not compact by default. The first rendered pages show heading, query label, help text, filters details, status, and result container on initial load instead of one compact row with deliberate expansion. | `documentation/tools/build_docs.py`, `documentation/assets/theme/bpm-docs.css`, `documentation/assets/theme/bpm-docs-search.js`, generated pages under `app/documentation/site/{locale}/`. | `BPM091-M2-04`, `BPM091-M4-01`, `BPM091-M4-02` |
| `DOC091-AUDIT-G05` | Search filter parameter labels are not localized in non-English indexes. Facet labels come from the shared 0.9.0 config and render English strings in `ru`, `de`, `zh-CN`, `fr`, and `es-ES`. | `documentation/config/search-facets-filters-0.9.0.json`, `documentation/tools/build_docs.py`, generated `app/documentation/site/search/{locale}/index.json`, `documentation/assets/theme/bpm-docs-search.js`. | `BPM091-M2-04`, `BPM091-M4-03`, `BPM091-M7-01`, `BPM091-M7-03`, `BPM091-M7-04`, `BPM091-M7-05` |
| `DOC091-AUDIT-G06` | Navigation is flat and duplicated. Guide names appear in both header navigation and the left sidebar, sidebar guide links point to same-page anchors instead of a real tree, and topic breadcrumbs do not provide reliable guide/topic parent context. | `documentation/tools/build_docs.py`, generated pages under `app/documentation/site/{locale}/`, manifest guide/topic metadata. | `BPM091-M2-05`, `BPM091-M4-04`, `BPM091-M4-05`, `BPM091-M4-06`, `BPM091-M4-07` |
| `DOC091-AUDIT-G07` | Documentation sufficiency is not yet re-reviewed for 0.9.1. Existing User Guide and Administrator/DevOps topics include useful structure, but Linux source-install content is generic and still references 0.9.0 rather than exact commands for five selected distributions. | User Guide DITA topics, Administrator/DevOps Linux source-deployment DITA topics, sufficiency fixtures and future review records. | `BPM091-M2-06`, `BPM091-M2-07`, `BPM091-M6-01`, `BPM091-M6-03`, `BPM091-M6-04`, `BPM091-M6-05`, `BPM091-M6-06`, `BPM091-M6-07` |
| `DOC091-AUDIT-G08` | All Settings rows do not expose per-setting circled-info documentation links. Existing documentation links cover page/surface contextual help and selected deep help targets, not every policy/setting row. | `app/static/profiles_all_settings_list.js`, `app/static/profiles_all_settings_detail.js`, `app/static/profiles_platform.js`, `app/i18n/*.json`, `app/documentation/site/ui-target-map.json`, relevant UI tests. | `BPM091-M2-08`, `BPM091-M8-01`, `BPM091-M8-02`, `BPM091-M8-03`, `BPM091-M8-04`, `BPM091-M8-05`, `BPM091-M8-06` |

## Non-Gaps Preserved

- Six active locale source trees and guide maps already exist.
- The current generated portal has manifest, target-map, static search index,
  and runtime `/help/` serving contracts from the 0.9.0 implementation.
- The search implementation remains deterministic, local, offline, and non-AI.
- Existing 0.9.0 architecture inventories remain valid provenance for their
  original scope and must not be renamed or rewritten by 0.9.1 UX tasks.

## Decision

The next 0.9.1 tasks must close the gaps through their focused contracts and
implementation tasks. This audit does not approve broad 0.9.0-to-0.9.1
replacement, hand-edits to generated portal artifacts, or unrelated
documentation architecture redesign outside the listed blockers.
