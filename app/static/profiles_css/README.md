# Profiles CSS Layers

`app/static/profiles.css` is the generated browser-facing bundle. Edit these source
layers instead, then run `make build-profiles-css`.

Order:

1. `00-foundation.css`: theme tokens, base page primitives, status chips, shared controls.
2. `10-library.css`: profile library list/table, compare panel, library dark-mode patches.
3. `20-editor-wizard.css`: app shell, editor chrome, guided wizard, all-settings, advanced review.
4. `30-responsive.css`: shared responsive overrides for library, editor, wizard, and dock surfaces.
5. `40-compact-shell.css`: compact toolbar/editor shell and its responsive overrides.
