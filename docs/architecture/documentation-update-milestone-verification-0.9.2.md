# BPM 0.9.2 Documentation-Update Milestone Verification

Date: 2026-07-22
Status: verified release evidence
Backlog item: `BPM092-M13-08`

## Scope

This record closes the documentation-update evidence boundary before release handoff. It does not
replace the individual source contracts or quality gates; it links their maintained evidence and
the reproducible checks that accepted the completed scope.

| Milestone task | Verified maintained evidence |
| --- | --- |
| `BPM092-M11-01` | [Compact UI user-documentation review](compact-ui-user-documentation-review-0.9.2.md) and six-locale User Guide topics for the header, Library, editor switching, and surface selection. |
| `BPM092-M11-02` | [Context-help gap review](context-help-gap-review-0.9.2.md), existing localized target ownership, and contextual-target contract. |
| `BPM092-M11-03` | [Compact UI screenshot refresh](compact-ui-screenshot-refresh-0.9.2.md), screenshot matrix, generated manifest/search outputs, and five refreshed scenarios in six locales. |
| `BPM092-M11-04` | [UI-copy classification](ui-copy-classification-contract-0.9.2.md), [audience/editorial contract](documentation-audience-editorial-contract-0.9.2.md), and locale style reviews. |
| `BPM092-M11-05` | Maintained authoring, localization, links/publishing, schema-update, and epic-backlog runbooks, including compact-copy, contextual-target, single-version, and installed-artifact rules. |
| `BPM092-M11-06` | README current-state decision and its release-boundary guard. |
| `BPM092-M11-07` | [Documentation index](../docs-index.md) entries for every maintained 0.9.2 contract and evidence record. |
| `BPM092-M11-08` | Six-locale DITA validation, editorial release gate, link/manifest/search/screenshot/context-target contracts through `make docs-release-check`. |
| `BPM092-M11-09` | Current local portal installed with `make docs-install-dev` for the maintainer's next `make dev`. |
| `BPM092-M12-05` | [Firefox 153 dual-ESR schema contract](firefox-153-dual-esr-schema-contract-0.9.2.md), affected six-locale DITA, policy targets, manifests, search, screenshots, and contextual-help dispositions. |
| `BPM092-M12-06` | Focused schema, migration, locale, documentation, and product/documentation browser evidence; no three-channel documentation exception remains. |

## Accepted commands

The source and generated-documentation checks are reproducible and release-blocking:

- `make docs-release-check`
- `make docs-install-dev`
- `make test-docs-browser`

`make docs-release-check` validates all six DITA locale trees, the accepted editorial gate, and
documentation contracts. `make docs-install-dev` installs the matching local portal artifact; it
does not start the application. `make test-docs-browser` proves the installed portal behavior in
Chromium, including locales, themes, search filters, navigation, context links, responsive
viewports, and keyboard paths.

## Release-contract disposition

`BPM092-G10` is closed by this verification record and its linked M11/M12 evidence. Any later
change to compact copy, localized documentation, context targets, screenshot inputs, schema
channels, manifests, search metadata, or documentation shell behavior reopens the gate under the
release contract's stale-evidence rule.
