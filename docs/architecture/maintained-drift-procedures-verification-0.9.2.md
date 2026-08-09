# BPM 0.9.2 Maintained Drift-Procedures Verification

Status: verified release evidence
Backlog item: `BPM092-M13-11`

## Scope

This record verifies that the maintained procedures which can be invalidated by BPM 0.9.2 fail
closed. It does not replace the procedures; it identifies their owners, required revalidation, and
the evidence that must be refreshed before release readiness is restored.

| Change family | Maintained procedure | Required fail-closed disposition |
| --- | --- | --- |
| Firefox Release/ESR schema matrix, migrations, UI placement, or labels | [Firefox schema update runbook](../firefox-schema-update-runbook.md) | Declare every current channel and retired-channel destination before editing; never migrate one supported ESR to another by version ordering. Regenerate each schema from its own source row, prove policy availability by channel, update locale catalogs and help targets, then run schema, locale, documentation, and browser gates. |
| CIS benchmark, mapping, preset, or recommendation ownership | [CIS Firefox update runbook](../cis_firefox_update_runbook_2026-04-13.md) and [inventory refresh](../../documentation/runbooks/inventory-refresh.md) | Preserve source-rights and provenance boundaries; refresh affected DITA, locale peers, manifest/search/target records, reviewed no-link dispositions, and screenshots before release readiness. |
| UI copy, locale wording, terminology, or compact shell behavior | [Locale update runbook](../locale_update_runbook_2026-06-01.md) and [localization and screenshots](../../documentation/runbooks/localization-and-screenshots.md) | Preserve six-locale key and placeholder parity; reject accidental English, unreviewed terminology, restored routine explanation, and non-local contextual-target fallback. Revalidate header/version parity and collapsed-filter state. |
| DITA topic, route, key, target, manifest, search, theme, screenshot, or installed documentation artifact | [Links, manifest, review, and publishing](../../documentation/runbooks/links-manifest-and-publishing.md) | Regenerate rather than edit artifacts, preserve stable public identities, rerun affected manifest/search/navigation and browser evidence, and run `make docs-install-dev` before the maintainer's `make dev`. |
| Administrator/DevOps deployment, update-from-source, or API integration behavior | [Links, manifest, review, and publishing](../../documentation/runbooks/links-manifest-and-publishing.md) and Administrator/DevOps DITA runbooks | Invalidate affected live-install evidence, retain its immutable transcript and resource boundary, preserve Administrator API ownership, and do not claim Windows/WSL validation without the actual-host runner. |
| Release boundary or final evidence | [Release contract](product-documentation-release-contract-0.9.2.md) and [epic backlog creation runbook](../epic-backlog-creation-runbook.md) | Reopen every affected evidence gate; a task status, README text, or changelog entry cannot substitute for passing current evidence. |

## BPM 0.9.2 Firefox Matrix

The schema procedure currently protects three independent channels:

- Firefox Release 153;
- Firefox ESR 153.0;
- Firefox ESR 140.13.

The migration destination is explicit: retired ESR 140.12 normalizes to ESR 140.13, while ESR
153.0 remains a distinct supported channel. The complete provenance and migration boundary is in
the [Firefox 153 dual-ESR schema contract](firefox-153-dual-esr-schema-contract-0.9.2.md).

## Verification

The following contracts must remain green whenever their corresponding procedure changes:

```bash
./.venv/bin/pytest -q \
  tests/contract/testing/test_runbook_make_targets_contract.py \
  tests/contract/ui/localization/test_ui_locale_glossary.py \
  documentation/tests/contract/test_authoring_runbooks.py \
  documentation/tests/contract/test_documentation_update_milestone_verification_0_9_2.py \
  documentation/tests/contract/test_firefox_153_dual_esr_schema_contract_0_9_2.py
make test-firefox-schema-contract
make test-locale-contract
make docs-release-check
```

If a documentation source, tooling, shell, or served version changes, run `make docs-install-dev`
after the passing checks. The maintainer runs `make dev` manually.
