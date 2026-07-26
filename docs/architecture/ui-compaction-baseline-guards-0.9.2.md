# BPM 0.9.2 UI Compaction Baseline Guards

Date: 2026-07-17
Status: active guard plan
Backlog item: `BPM092-M2-08`

Fixture: `tests/fixtures/ui_compaction_baseline_guards_0.9.2.json`
Focused test: `tests/test_ui_compaction_baseline_guards_092.py`

## Active M2 Guards

The fixture pins the M2 source census and every maintained M2 contract. The focused test validates
that its detectors reject regression fixtures for: explanatory blocks, unclassified visible prose,
header slot/focus drift, independent visible documentation version, search-triggered filter
expansion, and maintainer/progress narration.

This is a deliberately staged source guard. Current product and documentation sources still contain
the legacy blocks M3-M10 are approved to remove; asserting their absence now would make the
pre-implementation baseline fail. No test is skipped or marked expected-failure. Instead, each
fixture guard names its implementation owner and is bound to the relevant real source as that owner
removes the legacy block.

## Required Source-Guard Activation

| Guard | Source activation owner | Real-source assertion at activation |
| --- | --- | --- |
| Reintroduced explanatory block | M3-M8 | Removed source key/DOM wrapper does not return in the compact route template or dynamic renderer. |
| Unclassified visible prose | M3-M8 | New visible prose has an inventory key and classification before it can ship. |
| Header drift | M3/M9 | Normalized product and generated documentation slots, focus order, locale/theme controls, and active state agree. |
| Independent documentation version | M9 | Generator, assets, manifest compatibility values, and rendered portal contain no separately owned visible docs version. |
| Search auto-expand | M9 | Only the disclosure handler changes `filtersExpanded`; result/status remain available while filters are collapsed. |
| Maintainer/progress narration | M10 | Product DITA and portal chrome contain no prohibited audience/progress language outside internal material. |

M3-M10 may strengthen these tests but may not weaken, skip, or replace them with a manual check.
The M12 release gate runs the activated focused suite together with UI, documentation, locale, and
browser validation.
