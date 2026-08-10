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

`vendor-lock.json`
- Local checksum lock for the checked-in vendor outputs
- Verified by `make verify-frontend-vendor`
- Update only after an intentional vendor rebuild with
  `make rebuild-frontend-vendor`

`profiles_monaco.js`
- Upstream package: `monaco-editor`
- Version: `0.56.0`
- Source URL: `https://registry.npmjs.org/monaco-editor/-/monaco-editor-0.56.0.tgz`
- Built from: `monaco-editor/esm`
- Related outputs: `profiles_monaco.css`, `monaco-editor.worker.js`, `monaco-json.worker.js`, and
  `vendor/monaco-assets/codicon-KP4OV2OO.ttf`
- License files: `monaco.LICENSE` and `monaco.ThirdPartyNotices.txt`

Monaco `0.56.0` bundles these audited upstream implementations:
- `DOMPurify` `3.4.13` (npm override of Monaco's vulnerable `3.4.8` dependency and ESM source),
  with `dompurify.LICENSE-APACHE` and `dompurify.LICENSE-MPL`
- `marked` `14.0.0`, with `marked.LICENSE`

`tools/build_monaco_bundle.sh` overlays the resolved DOMPurify `3.4.13` ESM source into Monaco's
bundled source tree before esbuild runs. Vendor verification requires the resulting browser bundle
to identify `DOMPurify 3.4.13`; a clean npm audit alone is not accepted as bundle evidence.

Update procedure:
1. Download the pinned upstream browser build for the new version.
2. Update `app/static/vendor/profiles_tailwind.css` if new `/profiles` utility classes are introduced.
3. Update `package.json` and `package-lock.json` only for intentional dependency changes.
4. Replace `app/static/vendor/monaco.LICENSE` if the upstream version changes.
5. Run `make rebuild-frontend-vendor`.
6. Keep `app/templates/profiles.html` pointing at local assets only.
7. Run `make verify-frontend-vendor`, `ruff check .`, `mypy app`, and `pytest -q`.
