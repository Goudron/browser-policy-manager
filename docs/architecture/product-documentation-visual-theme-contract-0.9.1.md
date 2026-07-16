# BPM 0.9.1 Product Documentation Visual Theme Contract

Date: 2026-07-06
Status: accepted for BPM 0.9.1
Backlog item: `BPM091-M2-03`

## Purpose

This contract defines how the generated BPM documentation portal must visually align with the main
BPM interface during the 0.9.1 documentation completion epic. It is a contract for implementation
tasks, not evidence that the current `bpm-docs.css` already satisfies every rule.

The portal remains a static generated artifact. Theme implementation must happen in documentation
source assets, shell generation, and focused tests, then be rebuilt into generated output. Generated
HTML, installed `app/documentation/site/` files, and search indexes must not be hand-edited.

## Source Alignment

Documentation theme work must align with these product sources:

- Main BPM theme tokens and layout primitives: `app/static/profiles_css/00-foundation.css`.
- Documentation theme source assets: `documentation/assets/theme/bpm-docs.css` and
  `documentation/assets/theme/bpm-docs-print.css`.
- Documentation shell generation: `documentation/tools/build_docs.py`.
- Documentation search behavior: `documentation/assets/theme/bpm-docs-search.js`.
- Accessibility and security baseline:
  `docs/architecture/product-documentation-accessibility-security-contract-0.9.0.md`.
- Current 0.9.1 blocker evidence:
  `docs/architecture/documentation-portal-blocker-audit-0.9.1.md`.

## Theme Modes

The portal must support exactly these theme modes:

- `light`: explicit light mode using comfortable light-gray primary surfaces.
- `dark`: explicit dark mode using the main BPM dark-mode direction.
- `system`: follows `prefers-color-scheme` until the user chooses an explicit mode.

The generated shell must expose a stable mode hook, such as `html[data-theme]`, that can represent
`light`, `dark`, or `system`. System mode may use media queries, but explicit light and dark modes
must not depend on operating-system preference after the user selects them.

Theme selection must be consistent with main BPM conventions for persistence and locale-safe labels.
No theme behavior may require remote assets, inline script, inline style, telemetry, or a hosted
runtime service.

## Light Theme Surfaces

Light theme must not use pure white as a primary surface. The following requirements are
release-blocking:

- Page background, shell header, sidebar, main content surface, search surface, cards, table
  containers, code-adjacent panels, and form controls use light-gray or softly tinted BPM-aligned
  surfaces rather than `#ffffff`, `white`, or equivalent pure-white primary backgrounds.
- Pure white may appear only as tiny glyph-level contrast, image content, or an explicitly reviewed
  exceptional state where no primary surface is created.
- Main content and navigation surfaces remain visually distinct by border, spacing, and token
  hierarchy, not by returning to a harsh white slab.
- Documentation and product light-theme tokens must be reviewed together in `BPM091-M3-01` and
  implemented in `BPM091-M3-02` and `BPM091-M3-03`.

## Visual Surface Contract

The documentation portal must look like part of BPM, while preserving documentation readability:

- Surfaces: header, sidebar/tree, search, main topic body, footer, callouts, tables, result rows,
  and status pages use the same quiet operational style as BPM surfaces.
- Typography: documentation headings are smaller inside tool surfaces than hero-scale product
  marketing type; body measure remains readable and does not exceed the maintained documentation
  measure.
- Controls: inputs, selects if introduced, buttons, links, disclosure controls, search filters, and
  tree controls use BPM-like borders, focus, spacing, and disabled states.
- Links: contextual links, topic links, breadcrumbs if retained, and tree links have clear
  visited/current/focus/hover states and do not rely on color alone.
- Code blocks: keep monospace readability, horizontal overflow, copy-safe text, and contrast in
  both light and dark mode.
- Tables: captions, headers, borders, zebra or row separation if used, and narrow viewport behavior
  must remain readable without horizontal page overflow.
- Notes and warnings: note bodies, warning borders, icons if introduced, and tone colors must match
  BPM status semantics without overwhelming the page.
- Screenshots: screenshots sit on neutral documentation surfaces, do not become decorative cards
  inside cards, and preserve visible locale text without clipping.

## Accessibility And Media

Implementation must preserve the existing accessibility/security contract and add focused 0.9.1
theme evidence:

- Normal text contrast is at least WCAG 2.2 AA; non-text focus indicators and control boundaries
  are at least 3:1 against adjacent colors.
- Focus states remain visible in light, dark, system, forced-colors, and high-contrast modes.
- `prefers-reduced-motion` disables non-essential transitions and animations.
- `forced-colors: active` keeps content, controls, links, and tree/search states visible.
- Print output hides interactive chrome where appropriate, preserves topic text, tables, notes,
  links, and code, and does not print dark backgrounds.
- Layout remains stable at 320 CSS pixels and at representative desktop widths; text must not
  overlap controls or preceding/subsequent content.
- The palette must not become one-note. Documentation may reuse BPM accent/status colors, but the
  full page must not read as a single hue family or a dominant purple, dark-slate, beige, or
  brown/orange theme.

## Verification

Implementation tasks must add or preserve focused checks for these outcomes:

- `BPM091-M3-01`: audit current BPM and documentation tokens, including pure-white surfaces and
  mismatched values.
- `BPM091-M3-02`: verify main BPM light theme uses non-white primary backgrounds.
- `BPM091-M3-03`: verify documentation shell, search, navigation/tree, topic body, code, tables,
  notes, status pages, and screenshots use BPM-aligned tokens.
- `BPM091-M3-04`: verify explicit light/dark/system documentation modes and `prefers-color-scheme`
  behavior.
- `BPM091-M3-05`: verify representative pages across all six locales and narrow/desktop
  viewports.

Final release gates remain `make test-docs-contract`, `make test-docs-ui`, `make
test-docs-browser`, `make test-ui`, and `make test-release` as applicable to the touched surfaces.

## Non-Goals

- This contract does not implement the theme.
- This contract does not approve generated-output hand edits.
- This contract does not require new product branding, marketing pages, external fonts, remote
  imagery, or AI-generated visual assets.
- This contract does not expand screenshot scope beyond the approved minimal User Guide matrix.
