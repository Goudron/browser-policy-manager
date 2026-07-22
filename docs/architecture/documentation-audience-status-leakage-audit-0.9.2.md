# BPM 0.9.2 Documentation Audience And Status-Leakage Audit

Date: 2026-07-18
Status: audit
Backlog item: `BPM092-M10-01`

## Scope and method

This audit covers rendered product DITA under `documentation/src/dita` for
`en`, `ru`, `de`, `zh-CN`, `fr`, and `es-ES`. It separates a current
product or support boundary from implementation narration and internal source
work. English is the wording source for the corrective work; each listed topic
has the six locale peers shown in the table.

The audit does not treat a supported source-deployment command, a factual
unsupported boundary, or an API request/response contract as leakage merely
because it is technical. Those are retained only when they serve the named
Administrator/DevOps or API-integrator audience.

## Findings and dispositions

| ID | Guide and English topic | Audience | Locale peers | Finding | Disposition |
| --- | --- | --- | --- | --- | --- |
| A01 | CIS Guide — `cis/cis-concept-orientation.dita` | `security-reviewer` | `en, ru, de, zh-CN, fr, es-ES` | “plans 53 recommendation topics” reports documentation-work progress rather than a reader decision. | **remove** the planned-topic count; retain only current mapped/provenance facts needed for review. |
| A02 | Administrator/DevOps Guide — `admin/admin-concept-integration-audience.dita` | `administrator devops integrator security-reviewer` | `en, ru, de, zh-CN, fr, es-ES` | The reader list includes “maintainers”; the evidence paragraph names generated contracts, source files, and tests. | **rewrite as current support boundary**: name API integrators, security reviewers, and release engineers, then state only the exposed API and unsupported guarantees. |
| A03 | Administrator/DevOps Guide — `admin/admin-task-gate-control-product-startup.dita` | `administrator devops integrator` | `en, ru, de, zh-CN, fr, es-ES` | `M12-08` makes a health-gate procedure read as a backlog implementation note. | **remove** the task identifier; retain the current probe scope and stale-evidence recovery rule. |
| A04 | Firefox Policy Guide — `firefox/fx-concept-release-esr-differences.dita` | `user administrator` | `en, ru, de, zh-CN, fr, es-ES` | “Future schema refreshes must …” is a maintenance instruction embedded in a reader-facing channel statement. | **rewrite as current support boundary**: state the currently documented channel comparison and direct readers to revalidate against the selected schema. |
| A05 | Administrator/DevOps Guide — `admin/admin-task-plan-devops-storage-logs-backups.dita` | `administrator devops` | `en, ru, de, zh-CN, fr, es-ES` | “future update-from-source runbook” promises a later procedure that already has a current operational owner. | **rewrite as current support boundary**: link or refer to the current update procedure and its backup stop condition. |
| A06 | Administrator/DevOps Guide — `admin/admin-task-verify-source-update-rollback-stop.dita` | `administrator devops` | `en, ru, de, zh-CN, fr, es-ES` | “future production/HA/reverse-proxy planning” is roadmap narration, not an operational result. | **remove** the future-planning wording; keep the accepted/stopped/restored update outcome and handoff evidence. |
| A07 | Administrator/DevOps Guide — `admin/admin-troubleshoot-documentation-portal-build-links.dita` | `administrator devops` | `en, ru, de, zh-CN, fr, es-ES` | DITA source paths, generated-output ownership, focused test files, and documentation build commands are author/maintainer troubleshooting rather than supported product operation. | **move to maintainer docs**; retain in an internal documentation runbook, leaving only a user-visible portal availability/escalation boundary if one is required. |
| A08 | Administrator/DevOps Guide — `admin/admin-troubleshoot-failed-startup-probes.dita` | `administrator devops` | `en, ru, de, zh-CN, fr, es-ES` | “before changing code”, generated-artifact/database-row guidance, and `make test-fast` / documentation test commands mix developer recovery with probe troubleshooting. | **rewrite as current support boundary**: preserve safe evidence collection and escalation to the runtime owner; move source/test repair commands to maintainer material. |
| A09 | Administrator/DevOps Guide — `admin/admin-task-review-devops-configuration-sources.dita` | `administrator devops` | `en, ru, de, zh-CN, fr, es-ES` | The prose exposes `app/core/config.py` as the authority and frames absent facilities as a release-status note. | **rewrite as current support boundary**: document supported environment and local `.env` inputs plus the present absence of an application-managed secret store, without source paths or release narration. |
| A10 | Administrator/DevOps Guide — `admin/admin-task-verify-windows-wsl-source-deployment.dita` | `administrator devops` | `en, ru, de, zh-CN, fr, es-ES` | “before changing BPM code” and the narrow test command divert a deployment reader into developer work. | **rewrite as current support boundary**: keep WSL route, bind, and filesystem recovery; replace code/test work with an escalation role and captured evidence. |
| A11 | Administrator/DevOps Guide — five `admin-task-install-*-source.dita` topics and `admin-task-run-source-update-migrations-docs.dita` | `administrator devops` | `en, ru, de, zh-CN, fr, es-ES` | Documentation toolchain setup, `make docs-validate`, and `make docs-build` appear in source deployment/update flows even though they are documentation-maintenance gates, not prerequisites for operating BPM. | **move to maintainer docs**; keep source checkout, dependencies, migration, runtime, backup, and current product-availability checks in the Administrator/DevOps Guide. |
| A12 | Administrator/DevOps Guide — `admin/admin-task-verify-linux-source-deployment.dita` | `administrator devops` | `en, ru, de, zh-CN, fr, es-ES` | `make test-fast` is a source-maintenance verification rather than a supported deployment-health decision. | **rewrite as current support boundary**: retain health/UI/log verification and its non-production-certification warning; move the test-suite command to maintainer material. |
| A13 | Administrator/DevOps Guide — `admin/admin-task-use-reusable-api-examples.dita` and API request/response procedures | `administrator devops integrator` | `en, ru, de, zh-CN, fr, es-ES` | Curl/Python examples, status codes, revisions, hashes, and external-evidence handling are technical, but they describe the exposed integration contract rather than implementation progress. | **retain as genuine API-integrator content** with the existing no-secrets and explicit-response-boundary rules. |
| A14 | User Guide — `user/ug-task-add-managed-preference.dita` | `user` | `en, ru, de, zh-CN, fr, es-ES` | “not yet configured” describes the profile’s current state, not product implementation status. | No corrective action; this is an explicit false-positive exclusion for the later drift gate. |
| A15 | Administrator/DevOps Guide — `admin/admin-task-plan-monitoring-backup-update-windows.dita` | `administrator devops` | `en, ru, de, zh-CN, fr, es-ES` | Documentation validation/build commands were listed as a source-update prerequisite. | **move to maintainer docs**; retain only downtime, revision/dependency, migration, and runtime-verification decisions. |
| A16 | Administrator/DevOps Guide — `admin/admin-troubleshoot-schema-cache-validation.dita` | `administrator devops` | `en, ru, de, zh-CN, fr, es-ES` | A documentation-contract test command and generated-artifact remediation were presented as operator recovery. | **rewrite as current support boundary**: preserve request/configuration classification and deployment-owner escalation without source/test repair steps. |
| A17 | Administrator/DevOps Guide — `admin/admin-task-prepare-source-update-evidence.dita` | `administrator devops` | `en, ru, de, zh-CN, fr, es-ES` | “before changing code” addresses an implementation activity instead of the administrator’s source-revision change. | **rewrite as current support boundary**: retain the backup/export stop condition and name the source revision as the operation. |
| A18 | Administrator/DevOps Guide — `admin/admin-troubleshoot-import-export-failures.dita` | `administrator devops` | `en, ru, de, zh-CN, fr, es-ES` | A documentation-contract test command was presented as import/export recovery. | **rewrite as current support boundary**: retain the API request/response evidence and retry stop condition without maintenance commands. |

## Handoff to corrective tasks

`BPM092-M10-02` changes the English sources for A01–A12 and A15–A18. It must not change
topic IDs, guide ownership, API URLs, response contracts, or factual
unsupported-production boundaries while doing so. `BPM092-M10-03` then applies
the accepted meaning to the five localized peers. A13 and A14 are retained
controls for `BPM092-M10-11`: a textual gate must not reject legitimate API
material or ordinary profile-state wording.
