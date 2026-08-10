# BPM 0.9.1 Theme Token Audit

Date: 2026-07-07
Status: audit for `BPM091-M3-01`
Target BPM version: `0.9.1`

## Purpose

This audit names the active BPM and documentation CSS tokens or selectors that must be reviewed or
changed during the 0.9.1 visual-theme milestone. It records source findings only; it does not
implement the darker light theme, documentation theme alignment, system mode, or browser visual
verification.

## Scope

Included active source files:

- `app/static/profiles_css/00-foundation.css`
- `app/static/profiles_css/10-library.css`
- `app/static/profiles_css/20-shell.css`
- `app/static/profiles_css/21-settings.css`
- `app/static/profiles_css/22-guided-wizard.css`
- `app/static/profiles_css/23-workspace-editor.css`
- `app/static/profiles_css/24-theme-overrides.css`
- `app/static/profiles_css/30-responsive.css`
- `app/static/profiles_css/40-compact-shell.css`
- `documentation/assets/theme/bpm-docs.css`
- `documentation/assets/theme/bpm-docs-print.css`

Excluded generated, local, and vendor output:

- `app/static/vendor/`
- `app/documentation/site/`
- `documentation/build/`
- `documentation/dist/`
- `documentation/reports/`
- `documentation/.cache/`
- `docs/screenshots/`

## Product Theme Findings

The main BPM light theme already has non-white page background gradients, but too many primary
surfaces are translucent white. `BPM091-M3-02` must change these to comfortable light-gray surface
tokens while preserving hierarchy and contrast.

Tokens requiring 0.9.1 work in `app/static/profiles_css/00-foundation.css`:

| Token or selector | Current issue | Follow-up |
| --- | --- | --- |
| `--bg-top: #f6efe4`, `--bg-mid: #f8f7f1`, `--bg-bottom: #e8f2f0` | Light theme reads warm beige/cream rather than neutral light gray. | Move the page background family toward BPM-aligned light-gray surfaces. |
| `--panel: rgba(255, 255, 255, 0.82)` | Primary panel token is white-based. | Replace with a non-white light-gray panel token. |
| `--panel-strong: rgba(255, 255, 255, 0.92)` | Strong panel token is white-based and visually harsh on large surfaces. | Replace with a stronger gray panel token. |
| `--list-button-bg`, `--list-button-hover-bg`, `--list-button-border` | List rows/buttons are white-based and repeated across Library, Compare, and All Settings rows. | Retokenize list surfaces through the new light-gray row tokens. |
| `.hero-shell` | Uses white gradients and a white border on a large first-viewport surface. | Replace the gradient stops/border with neutral panel tokens. |
| `.metric-tile` | Uses a white inset highlight over `--panel-strong`. | Recheck after `--panel-strong` changes; remove white highlight if it remains visible. |
| `.accent-panel`, `.warm-panel` | Both mix semantic tint with white gradient stops. | Move white stops to neutral surface tokens. |
| `.soft-input`, `.soft-input:hover`, `.soft-input:focus` | Inputs use white-based backgrounds in default light mode. | Replace with form-control light-gray tokens and preserve focus contrast. |
| `.theme-subcard` | Card uses white background and border. | Retokenize as a normal nested light-gray surface. |
| `.editor-frame` | Uses `#f8fafc` plus white inset highlight. | Keep gray frame but remove hardcoded white inset if it produces a white slab. |

Selectors requiring 0.9.1 work in `app/static/profiles_css/10-library.css`:

| Selector | Current issue | Follow-up |
| --- | --- | --- |
| `.library-row-meta-primary` | Uses `rgba(255, 255, 255, 0.58)` for row metadata. | Replace with a shared row-metadata surface token. |
| `[class~="bg-white"]`, `[class~="bg-white/80"]`, `[class~="bg-white/70"]` compatibility selectors | Dark-mode overrides exist, which means light-mode white utility classes can still create white surfaces. | Audit templates using these classes and replace with BPM surface tokens. |
| `.compare-target-name`, `.compare-summary-value`, `.compare-changes-copy`, `.compare-changes-item` | Hardcoded slate colors bypass the theme token set. | Tokenize text colors so light/dark/system stay coherent. |

Selectors requiring 0.9.1 work in the owned `app/static/profiles_css/20-24-*.css` layers:

| Selector group | Current issue | Follow-up |
| --- | --- | --- |
| `.section-nav`, `.section-nav-link:hover` | Sticky navigation and hover state use white-based backgrounds. | Retokenize through neutral toolbar/surface tokens. |
| `.all-settings-domain-card`, `.all-settings-domain-card:disabled:hover`, `.all-settings-review-card`, `.all-settings-review-card:disabled:hover` | All Settings cards use white-based primary row/card backgrounds. | Replace with light-gray card/list tokens before M8 row-link work. |
| `.all-settings-detail-editor .wizard-shell-card` | Detail editor card uses a white-based nested surface. | Replace with the same detail-card token used by All Settings rows. |
| `.wizard-step--active` | Active wizard step uses a white gradient stop. | Replace the white stop with a neutral active-surface token. |
| `.wizard-impact-section`, `.wizard-cis-selector`, `.wizard-proxy-mode-selector` | Wizard control groups use white-based backgrounds. | Retokenize as form/control group surfaces. |
| `.wizard-search-engine-preset`, `.wizard-search-engine-preset:hover`, `.wizard-search-engine-card` | Search-engine preset cards use white backgrounds, white inset overlays, and duplicated background/background-color pairs. | Replace with shared selectable-card tokens. |
| `html[data-theme="light"] .soft-input`, `html[data-theme="light"] .soft-input:hover`, `html[data-theme="light"] .soft-input:focus` | Duplicates the white input values already present in `00-foundation.css`. | Remove duplication or point both definitions at the same form-control tokens. |
| `html[data-theme="light"] .ghost-button:hover` | Light hover state returns to a white-based surface. | Replace with a non-white hover token. |

Selectors requiring 0.9.1 work in `app/static/profiles_css/40-compact-shell.css`:

| Selector | Current issue | Follow-up |
| --- | --- | --- |
| `.compact-toolbar-docs-link`, `.context-help-link`, `.context-help-icon-link` | Help links are visually close to the future All Settings `i` link pattern, but still use separate hardcoded tint values. | Extract/reuse a single help-link token set for M8 row links. |
| `.compact-shell-*` panel gradient near line 247 | Uses a white gradient stop and white inset highlight. | Replace with the same neutral toolbar/panel tokens used by the main shell. |

`app/static/profiles_css/30-responsive.css` does not introduce new light-theme color tokens. Its
responsive selectors should be rechecked after the M3-02/M3-03 token changes to ensure mobile rows
do not overlap or lose contrast.

## Documentation Theme Findings

The documentation portal currently has its own 0.9.0 token family and does not yet mirror the BPM
theme model required by `product-documentation-visual-theme-contract-0.9.1.md`.

Tokens and selectors requiring 0.9.1 work in `documentation/assets/theme/bpm-docs.css`:

| Token or selector | Current issue | Follow-up |
| --- | --- | --- |
| Header comment `BPM 0.9.0 documentation portal theme` | Source still identifies the old theme generation. | Update when the 0.9.1 theme is implemented. |
| `:root { color-scheme: light dark; }` | Theme mode is implicit rather than explicit `light`, `dark`, and `system`. | Add stable `html[data-theme]` hooks in M3-04. |
| `--bpm-docs-surface: #ffffff` | Primary documentation surface is pure white. | Replace with comfortable light-gray documentation surface. |
| `--bpm-docs-bg`, `--bpm-docs-surface-muted`, `--bpm-docs-border`, `--bpm-docs-accent`, `--bpm-docs-focus` | Token names and values are separate from BPM product tokens. | Align or mirror BPM decisions from M3-02 while keeping documentation readability. |
| `@media (prefers-color-scheme: dark) :root` | Dark mode depends only on OS preference. | Keep for system mode but add explicit mode override behavior. |
| `.bpm-docs-header`, `.bpm-docs-sidebar`, `.bpm-docs-main` | Header/sidebar/main surfaces inherit the pure-white `--bpm-docs-surface`. | Retokenize with non-white light surfaces. |
| `.bpm-docs-search`, `.bpm-docs-search-input`, `.bpm-docs-search-result-list li` | Search shell and result surfaces depend on current docs-only tokens and pure-white input/result surfaces. | Align with compact search M4 work and BPM control tokens. |
| `.bpm-docs-main :not(pre) > code`, `.bpm-docs-main th`, `.bpm-docs-main .note*` | Inline code, table header, and note colors are docs-only and need BPM semantic alignment. | Retokenize through docs/BPM semantic surface tokens. |

`documentation/assets/theme/bpm-docs-print.css` intentionally uses white paper and black text for
print output. This is not a light-theme product surface blocker, but it must continue to avoid dark
backgrounds after M3 changes.

## Cross-Cutting Risks

- Pure-white and translucent-white values are duplicated instead of centralized, especially between
  `00-foundation.css` and the owned `20-24-*.css` layers.
- Product and documentation themes use different token namespaces and accent families, making the
  documentation portal feel separate from BPM.
- Documentation supports OS dark mode but lacks explicit `html[data-theme="light"]`,
  `html[data-theme="dark"]`, and `html[data-theme="system"]` behavior.
- Several light-mode selectors hardcode text colors instead of using `--ink`, `--muted`, or docs
  equivalents, so contrast and dark/system behavior need browser verification after retokenization.

## Verification Handoff

- `BPM091-M3-02` must change the product light-theme tokens and direct white selectors listed
  above.
- `BPM091-M3-03` must align documentation tokens and source CSS with the product theme.
- `BPM091-M3-04` must add explicit documentation light/dark/system mode hooks.
- `BPM091-M3-05` must run visual, contrast, and responsive checks across representative pages and
  locales.

No generated documentation output, installed `/help/` site, vendor files, local reports, caches, or
screenshots were inspected or edited for this audit.
