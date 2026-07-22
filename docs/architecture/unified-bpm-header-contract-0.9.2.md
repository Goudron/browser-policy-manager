# BPM 0.9.2 Unified Product Header Contract

Date: 2026-07-17
Status: active contract
Backlog item: `BPM092-M2-05`

## Purpose

Library, Guided editor, All settings, JSON editor, Compare, and documentation are BPM surfaces.
They use one compact product-header contract. Generated documentation does not look like a separate
product, and no surface carries a second documentation version or a route-purpose subtitle.

This contract defines normalized semantics and slots, not an instruction to share a runtime Jinja
partial with the documentation generator. M3 owns the product implementation; M9 owns generated
documentation parity without hand-editing installed output.

## Normalized Structure

Each surface emits a semantic `<header>` with `data-bpm-header` and these slots in document order:

| Slot | Required normalized role | Content and rule |
| --- | --- | --- |
| `skip` | Skip link before the header, when the surface has a document/content landmark. | Targets the main work area; visually hidden until focused. Documentation retains its current skip-to-content behavior. |
| `identity` | `data-bpm-header-brand`; link to the BPM home/Library where navigation is available. | Product name `Browser Policy Manager` and the one BPM product version, derived from package metadata. No documentation version, kicker, or subtitle. |
| `surface` | `nav` with `data-bpm-header-surfaces` and a localized accessible name. | Compact named entries for Library, Guided, All settings, JSON, Compare, and Documentation. The current entry has `aria-current="page"`; unavailable entries use an associated reason, not a paragraph. |
| `actions` | `data-bpm-header-actions`. | Surface-relevant global action only, such as the documentation entry when outside documentation. No duplicate route-purpose prose or open-in-new-tab explanation. |
| `preferences` | `data-bpm-header-preferences`. | Locale and theme controls with concise visible labels, current values, and stable IDs/accessible names. No helper-line text such as “UI language” or “Appearance mode”. |
| `workspace` | Optional `data-bpm-header-workspace`. | A compact current profile/count/state signal only if the current route genuinely needs it. It is not a second source of profile metadata or a tutorial. |

The concrete product and documentation class names may differ for build ownership, but the data
attributes, landmark roles, slot order, labels, and observable states above are the parity
interface. A documentation article title belongs to `<main>`, not the product-header identity slot.

## Product Identity, Titles, And Version Ownership

- The product header displays `Browser Policy Manager` plus the single BPM version derived from
  `pyproject.toml`/runtime package metadata. The same derived version is used by product and
  documentation; it is not duplicated as `Documentation <version>`.
- Browser titles use `{surface or article title} | Browser Policy Manager`. For product routes,
  the localized surface title is first; for documentation topics, the localized topic title is
  first. A browser title does not add a documentation version.
- Documentation is an active surface named `Documentation`, not an external/subproduct brand.
  When documentation is current, it receives `aria-current="page"`; on product routes, its entry
  navigates to the locale-matched documentation home.
- A missing documentation artifact keeps an actionable, localized unavailable state and safe
  fallback route. It does not restore a progress/status subtitle or expose build internals.

## Visual And Responsive Rules

1. Header tokens are product-owned semantic tokens for surface, border, text, muted text, accent,
   focus, control, spacing, radius, elevation, and target size. Documentation deterministically
   mirrors these tokens through maintained source; generated output is never edited.
2. Light, dark, and system mode use the same token meaning and selected-theme convention across a
   product-to-documentation transition. The documentation article/sidebar/search may have
   content-specific styles, but its header is recognizably the same BPM component.
3. Desktop uses one compact header band: identity/surface/actions and preferences may form two
   aligned groups, but no subtitle or control helper line creates an extra explanatory band.
4. At narrow widths and 200% zoom, slots wrap in the same document order. Labels may wrap; selected
   locale/theme values, active surface, focus indicator, and actions may not disappear, overlap,
   or become icon-only without an accessible name.
5. Long localized labels in `ru`, `de`, `zh-CN`, `fr`, and `es-ES` retain usable control width and
   target size. Locale/theme selectors use the same option order and system/light/dark semantics.

## Keyboard And Accessibility Rules

1. Tab order is: skip link, brand, surface navigation in visual order, available action, locale,
   theme, optional workspace controls, then main content. DOM order and visual order agree.
2. Every visible or icon-only action has a localized accessible name. The active surface is exposed
   programmatically; focus rings meet the shared token contract and remain visible in all themes.
3. Select controls retain `<label>` association or an equivalent programmatic name. Helper prose is
   not required for accessibility when the label and current value are present.
4. Documentation navigation/search landmarks remain separate from product-header surface
   navigation; this prevents duplicate landmark names while preserving article navigation.

## Parity Evidence And Failure Conditions

M3/M9 must add focused checks that normalize Jinja and generated documentation headers into the
following tuple: slot sequence, landmark roles, brand/version source, surface names/current state,
locale/theme labels and values, browser-title pattern, focus order, and narrow-layout order.

Parity fails when any of the following is true:

- documentation displays `Documentation <version>` or a separately maintained visible version;
- one surface has a subtitle/helper line or a different locale/theme explanation;
- current surface semantics, keyboard order, theme state, or locale selection differ;
- documentation uses a different product brand/title structure from Library or the editors;
- a long locale label, zoom, or narrow viewport hides a selected value, active state, or focus;
- generated site output was hand-edited instead of produced by the maintained build.

Required final evidence is template/generator contract coverage, six-locale and three-theme checks,
desktop/narrow and 200% zoom browser assertions, keyboard traversal, and representative screenshots
of Library, each editor, Compare, and documentation.
