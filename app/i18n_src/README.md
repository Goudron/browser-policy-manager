# Locale Source Catalogs

Edit locale copy in this directory. Runtime catalogs in `app/i18n/*.json` are
generated from these namespace files with:

```bash
make build-locale-catalogs
```

Use this check before committing locale changes:

```bash
make check-locale-catalogs
```

Use this report when reviewing generated policy-label overrides for obvious
machine-like fragments:

```bash
make locale-quality
```

Namespaces:

- `common`: shared chrome, profile metadata, generic actions, status, errors.
- `library`: profile library, import, compare, clone, lifecycle copy.
- `wizard`: Guided editor copy.
- `settings`: All settings catalog copy.
- `json`: JSON editor and cross-mode handoff copy.
- `policy-labels`: generated schema field labels and policy shell labels.

`catalog-order.json` preserves the runtime key order used by the existing
`app/i18n/*.json` catalogs. Do not edit it unless keys are intentionally added,
removed, or reordered.

Generated segments live under `generated/{locale}/`. Do not edit them directly.
For generated `policy-labels`, the key set comes from Firefox schema/catalog
metadata and `overrides/{locale}/policy-labels.json` stores manual/localized
copy that differs from generated fallbacks.
