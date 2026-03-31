Vendor assets used by the `/profiles` page.

`profiles_tailwind.css`
- Local asset: checked-in utility subset replacing Tailwind Play CDN
- Scope: only the utility classes currently used by `/profiles`
- Notes: this is intentionally maintained locally instead of vendoring the Tailwind runtime or introducing a build toolchain

Related local bootstrap assets outside `vendor/`:
- `app/static/profiles_head_bootstrap.js`
- `app/static/profiles_page_bootstrap.js`
- `app/static_src/profiles_monaco_entry.js`
- `tools/build_monaco_bundle.sh`

These keep theme selection, Monaco bundle wiring, and initial locale bootstrapping self-hosted without inline executable scripts.

`js-yaml.js`
- Upstream package: `js-yaml`
- Version: `4.1.0`
- Source URL: `https://cdn.jsdelivr.net/npm/js-yaml@4.1.0/dist/js-yaml.min.js`
- License file: `js-yaml.LICENSE`

`profiles_monaco.js`
- Upstream package: `monaco-editor`
- Version: `0.52.0`
- Built from: `monaco-editor/esm`
- Related outputs: `profiles_monaco.css`, `monaco-editor.worker.js`, `monaco-json.worker.js`
- License file: `monaco.LICENSE`

Update procedure:
1. Download the pinned upstream browser build for the new version.
2. Update `app/static/vendor/profiles_tailwind.css` if new `/profiles` utility classes are introduced.
3. Replace `app/static/vendor/js-yaml.js`.
4. Replace `app/static/vendor/js-yaml.LICENSE`.
5. Install frontend dependencies with `npm install`.
6. Run `npm run build:monaco`.
7. Replace `app/static/vendor/monaco.LICENSE` if the upstream version changes.
8. Keep `app/templates/profiles.html` pointing at local assets only.
9. Run `ruff check .`, `mypy app`, and `pytest -q`.
