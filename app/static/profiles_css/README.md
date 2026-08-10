# Profiles CSS Layers

`app/static/profiles.css` is the generated browser-facing bundle. Edit these source
layers instead, then run `make build-profiles-css`.

Order:

1. `00-foundation.css`: theme tokens, base page primitives, status chips, shared controls.
2. `10-library.css`: profile library list/table, compare panel, library dark-mode patches.
3. `20-shell.css`: shared application shell, hero, navigation, and workspace dock layout.
4. `21-settings.css`: settings-search and all-settings surface.
5. `22-guided-wizard.css`: guided wizard, its choices, review, export, and step memory.
6. `23-workspace-editor.css`: workspace dock, editor chrome, JSON workflow, and common editor controls.
7. `24-theme-overrides.css`: final dark-theme overrides. This stays after every owned component
   source so the existing cascade remains compatible.
8. `30-responsive.css`: shared responsive overrides for library, editor, wizard, and dock surfaces.
9. `40-compact-shell.css`: compact toolbar/editor shell and its responsive overrides.

The build order is a compatibility contract, not alphabetical ordering. Do not hand-edit
`../profiles.css`: `make build-profiles-css` is the only writer and `--check` verifies it.
