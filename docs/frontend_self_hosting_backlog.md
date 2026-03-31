# Frontend Self-Hosting Backlog

## Goal

Move the `/profiles` web UI off runtime CDN dependencies so the page works in:

- restricted enterprise networks,
- offline or air-gapped environments,
- deployments with tighter CSP requirements.

This backlog is intentionally limited to frontend asset delivery and related security hardening.
It does not change the main BPM product behavior.

## Current external runtime dependencies

The `/profiles` page currently loads these assets from CDNs at runtime:

- Tailwind Play CDN via `https://cdn.tailwindcss.com`
- `js-yaml` via `https://cdn.jsdelivr.net/npm/js-yaml@4.1.0/dist/js-yaml.min.js`
- Monaco loader via `https://cdn.jsdelivr.net/npm/monaco-editor@0.52.0/min/vs/loader.min.js`
- Monaco worker/editor assets via `window.require.paths.vs = "https://cdn.jsdelivr.net/npm/monaco-editor@0.52.0/min/vs"`

Related implementation points:

- `app/templates/profiles.html`
- `app/middleware/security.py`
- `app/static/profiles_runtime.js`

## Non-goals

- Rewriting the `/profiles` frontend architecture
- Bundling every static JS file into a single app bundle
- Removing external example URLs inside presets, localization strings, or Firefox policy payloads
- Changing Firefox extension install URLs used as actual exported policy values

## Recommended direction

Prefer a minimal self-hosted vendor strategy over introducing a full frontend toolchain immediately.

Recommended target shape:

- Keep the current Jinja + plain JS architecture
- Vendor only the runtime libraries we actually need under `app/static/vendor/`
- Switch `/profiles` to local asset URLs
- Tighten CSP after CDN removal

This keeps the change small and reversible.

## Backlog

### P0. Asset inventory and freeze

Goal: make the dependency surface explicit before moving files around.

Tasks:

- Record exact pinned versions for Tailwind Play CDN, `js-yaml`, and Monaco currently assumed by the page.
- Decide whether Tailwind stays as Play CDN replacement or is replaced by prebuilt CSS utilities.
- Decide whether Monaco remains AMD/loader-based or gets replaced with a simpler editor fallback.
- Document the chosen source files and their upstream license notices.

Done when:

- We have one written source-of-truth document listing every runtime third-party asset, its version, and its local destination path.

Notes:

- Tailwind Play CDN is the trickiest part because it injects behavior at runtime rather than being just a plain stylesheet.
- `js-yaml` and Monaco are straightforward vendor candidates.

### P1. Self-host `js-yaml`

Goal: remove the lowest-risk CDN dependency first.

Tasks:

- Add a vendored `js-yaml` asset under `app/static/vendor/`.
- Update `app/templates/profiles.html` to load the local file instead of jsDelivr.
- Add a regression test that asserts `/profiles` no longer references CDN `js-yaml`.

Done when:

- `/profiles` works with YAML mode using only local `js-yaml`.
- No `js-yaml` CDN URL remains in the rendered page.

### P2. Self-host Monaco

Goal: remove the editor CDN dependency without changing the editor UX.

Tasks:

- Add a pinned Monaco frontend dependency for reproducible local builds.
- Build a checked-in local browser bundle from `monaco-editor/esm`.
- Serve Monaco and its workers from local static assets only.
- Verify worker loading still functions with the project CSP and URL layout.
- Add regression tests asserting the page references local Monaco URLs only.

Done when:

- The editor initializes normally from local assets.
- JSON and YAML language switching still works.
- No Monaco CDN URL remains in the rendered page.

Notes:

- Prefer the bundle path over keeping Monaco's AMD loader, because the loader keeps `unsafe-eval` in CSP.
- Keep this step isolated from Tailwind so editor regressions are easy to debug.

### P3. Replace Tailwind Play CDN

Goal: remove the highest-risk and most CSP-hostile frontend dependency.

Tasks:

- Choose one of these approaches:
  - Preferred: generate a checked-in compiled stylesheet for the current utility surface.
  - Acceptable: vendor a local Tailwind runtime only if we truly need runtime compilation.
- Move any page-specific theme extensions currently declared in inline `tailwind.config` into local CSS or build inputs.
- Update `app/templates/profiles.html` to stop loading `https://cdn.tailwindcss.com`.
- Confirm the page still renders correctly across the existing smoke surface.
- Add regression tests asserting Tailwind CDN is gone from the page.

Done when:

- `/profiles` renders correctly without the Tailwind CDN script.
- Theme tokens still apply.
- No runtime CSS generation depends on network access.

Notes:

- This is the most likely place to reveal accidental reliance on Tailwind Play behavior.
- If this step starts to sprawl, split it into “compile existing styles” and “cleanup unused utility assumptions”.

### P4. Tighten CSP after CDN removal

Goal: cash in the security benefit after self-hosting is complete.

Tasks:

- Remove `https://cdn.jsdelivr.net` from CSP directives.
- Re-evaluate whether `font-src` still needs anything other than `'self'`.
- Re-evaluate whether `script-src` still needs `'unsafe-eval'` after Monaco is local.
- Reduce inline-script allowances if practical.
- Add security-header tests that assert CDN allowances are no longer present.

Done when:

- CSP no longer whitelists third-party asset CDNs for `/profiles`.
- Header tests explicitly lock the new policy in place.

Notes:

- `unsafe-inline` may still be needed temporarily because `profiles.html` contains inline bootstrapping scripts.
- If we want to remove `unsafe-inline`, treat that as a separate hardening task after asset migration.

### P5. Optional follow-up: move inline bootstrapping to local files

Goal: make CSP tightening easier and reduce template complexity.

Tasks:

- Move theme bootstrap script out of inline HTML where practical.
- Move initial locale/bootstrap globals into a narrowly scoped boot script or `data-*` payload container.
- Revisit CSP again after inline script reduction.

Done when:

- `profiles.html` contains minimal or no inline script blocks.
- CSP can be tightened further without breaking first paint.

## Suggested implementation order

1. P1 `js-yaml`
2. P2 Monaco
3. P3 Tailwind
4. P4 CSP tightening
5. P5 inline bootstrap cleanup

This order removes the easy CDN dependencies first and leaves the most invasive styling change for its own pass.

## Testing checklist

Use this checklist after each phase:

- `ruff check .`
- `mypy app`
- `pytest -q`
- Open `/profiles` and confirm:
  - editor loads,
  - JSON/YAML mode switching works,
  - wizard page still renders,
  - export/download controls still appear,
  - dark/light theme still applies.

## Proposed acceptance bar for the full initiative

The initiative is complete when all of the following are true:

- `/profiles` loads without third-party runtime JS/CSS asset URLs
- CSP no longer whitelists jsDelivr for page assets
- existing smoke and page tests pass
- documentation explains how vendored assets are updated
