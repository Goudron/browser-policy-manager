# BPM 0.9.0 Product Documentation Content Coverage Audit

Status: **Accepted with release blockers**  
Audit date: 2026-07-06  
Backlog item: `BPM090-M14-07`

## Purpose

This audit is the final BPM 0.9.0 documentation content-coverage reconciliation. The
machine-readable source of truth is
`product-documentation-content-coverage-audit-0.9.0.json`.

The audit does not replace the detailed inventories. It ties them together and applies the M14 rule:
every shipped capability, source-deployment admin path, update procedure, DevOps integration path,
production-readiness boundary, API operation, supported Firefox policy, CIS recommendation, locale,
required screenshot, manifest target, and search index is either covered by source-backed evidence or
named as a release blocker.

## Coverage Summary

| Domain | State | Evidence |
| --- | --- | --- |
| User-facing BPM capabilities | Covered | 106 capabilities mapped to 89 User Guide topics in six locales. |
| Linux source deployment | Covered | 4 Administrator/DevOps topics with command/config/source checks. |
| Windows 10/11 WSL source deployment | Covered | 4 Administrator/DevOps topics with WSL caveats and source checks. |
| DevOps operations | Covered | 4 Administrator/DevOps topics for config, storage/logs/backups, network/CORS/security, and operational boundaries. |
| Update from source | Covered | 4 Administrator/DevOps topics for evidence, revision/dependency refresh, migrations/docs rebuild, and rollback-stop decision points. |
| API/integration ownership | Covered | 13 migrated Administrator/DevOps integration topics plus current OpenAPI drift gates. |
| External control-product runbooks | Covered | 5 Administrator/DevOps runbooks for pull/list/read, validate-before-apply, import-review-export, startup gating, and failure audit evidence. |
| Troubleshooting/diagnostics | Covered | 6 Administrator/DevOps diagnostics topics for startup, schema cache, import/export, storage, WSL, and documentation portal failures. |
| Production-readiness boundaries | Covered | 4 topics describe current source-run readiness and explicitly defer unsupported HA/reverse-proxy/production-hardening claims. |
| Firefox schema documentation | Covered | 120 policy IDs, 62 managed preferences, and 8 Release-only policies are inventoried and gated. |
| CIS settings documentation | Covered | 55 recommendation records: 53 publishable topics and 2 provenance-only non-publishable records. |
| API operation inventory | Covered | 15 integration operations and 6 web routes are reconciled against current OpenAPI. |
| Locale parity | Covered | All five guide families ship DITA peers for `en`, `ru`, `de`, `zh-CN`, `fr`, and `es-ES`; compact fallback prose is not accepted. |
| Localized screenshots | **Release blocker** | Screenshot fixture exists, but complete locale-specific capture/review and `make docs-screenshots-check` are not complete. |
| Manifest and UI target map | Covered | Five guide families, six locales, manifest schema, UI target map, runtime route, and header/contextual/deep-link contracts are gated. |
| Deterministic search indexes | Covered | Six locale indexes, normalization, aliases, ranking, facets, quality, integrity, and non-AI boundary are gated. |
| Portal runtime | Covered | `/help/`, header documentation link, contextual help, deep help icons, status pages, CSP/security, and OpenAPI `/docs` coexistence are gated. |

## Release Blockers Recorded By This Audit

The audit intentionally preserves the current release blockers instead of hiding them:

- release extraction policy from the verified documentation package into the runtime site;
- localized screenshot capture and review;
- final manual QA and defect disposition for the installed documentation flow.

The content-specific blocker is localized screenshots. Other blockers remain part of the broader
runtime/package handoff and final release disposition.

## Verification

Focused rerun:

```bash
./.venv/bin/pytest -q -m docs_contract documentation/tests/contract/test_product_documentation_content_coverage_audit.py
```

Full non-browser documentation release rerun:

```bash
make docs-release-check
```

