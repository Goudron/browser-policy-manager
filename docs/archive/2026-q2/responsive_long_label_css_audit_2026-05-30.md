# Responsive Long Label CSS Audit

Backlog item: `GLOC-506`

Scope: Responsive CSS fixes for long labels across buttons, segmented controls, cards, table cells, and review panels exposed by the new locale catalogs.

Findings and changes:

- No locale-specific selectors or one-off language hacks were added.
- Base buttons now use border-box sizing, `min-width: 0`, max-width bounds, normal wrapping, and normal word breaking so labels can wrap without clipping controls.
- Scenario, starter, search preset, scope, summary, export, and review cards now carry generic `min-width: 0` and wrap guards where their copy can grow.
- Segmented controls for CIS, proxy mode, editor mode, and review filters are width-bounded and can wrap labels inside their existing responsive grids.
- All settings review cards and list cells keep count badges stable while allowing translated text to wrap.
- Library row action buttons keep the earlier no-broken-Russian-word contract while retaining full-width mobile behavior.

Verification:

- Static contract: `tests/test_responsive_long_label_css_contract.py`
- Existing locale overflow contracts remain the route-level references for German, French, Spanish, and Simplified Chinese.
