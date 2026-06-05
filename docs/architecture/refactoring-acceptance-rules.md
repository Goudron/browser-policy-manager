# BPM 0.8.5 Refactoring Acceptance Rules

Date: 2026-06-01

These rules define when a BPM 0.8.5 refactoring task is acceptable. They keep the release focused on safer structure, lower fragility, lower context cost, and faster checks without changing product behavior by accident.

## Default Rule

Refactoring tasks should preserve public behavior unless the backlog task explicitly says otherwise. If behavior must change, update the task notes, user-facing docs, and tests in the same change.

## Public Contracts To Preserve

- Web routes listed in `docs/architecture/current-system-map.md` keep their status codes, route semantics, route titles, and expected editor surfaces.
- API routes keep their request/response shape, OpenAPI summaries, validation semantics, and error status families.
- Firefox `policies.json` remains the product import/export boundary.
- Supported schema channels stay centralized in `app/core/schema_channels.py`.
- Runtime locale catalogs keep active-locale key parity and placeholder parity.
- Existing saved profile lifecycle behavior remains stable: create, edit, duplicate, archive, restore, hard-delete, import, export, validate.
- Generated/vendor files remain reproducible through documented scripts or checks.

## Refactor Task Definition Of Done

A refactor task is done only when:

1. The ownership boundary is clearer than before.
2. The changed code has no unrelated formatting churn.
3. Tests are moved or renamed with the behavior they protect.
4. The smallest relevant test layer passes.
5. Any changed docs point to the current file path and command names.
6. Large generated/vendor outputs are not hand-edited unless the task is explicitly about vendor refresh.
7. `make repo-health` still runs when the task changes repository shape, test timing, locales, docs, generated assets, or local artifact handling.

## Test Movement Rules

- When code is split, split tests by behavior or route ownership, not by implementation accident.
- Keep high-level contract tests for public routes/API behavior.
- Move static-source assertions toward helper-driven tests or snapshots when the implementation becomes modular.
- Do not drop coverage for archived/deleted profile behavior, schema-specific behavior, locale fallback, Firefox import/export, or CIS layer generation.
- Browser UI and live Firefox checks may stay separate from default local checks, but any task that changes those surfaces must name the relevant follow-up check.

## Compatibility And Legacy Removal

Legacy or compatibility surfaces can be removed only when all of these are true:

1. The surface is listed as removable in the backlog or a follow-up decision note.
2. README/docs no longer present it as a primary workflow.
3. Tests that asserted compatibility are updated to assert the new contract.
4. The replacement route/API/command has an obvious migration path.

Current known candidates:

- Route-time legacy schema normalization.
- Scattered legacy schema guards in CI/tests.

## Documentation Rules

- Active architecture docs should be short and current.
- Historical audit/backlog files should move behind an index/archive process, not disappear.
- Tests should prefer docs manifests or specific invariant snippets over long exact-text coupling.
- New playbook steps should point to executable Make targets or scripts whenever possible.

## Review Checklist

Use this checklist before closing each BPM 0.8.5 refactor task:

- Public route/API behavior intentionally preserved or explicitly changed.
- Relevant tests pass and are no broader than needed.
- No unrelated cleanup mixed into the patch.
- New files have a clear owner/location.
- Docs and command names match the new shape.
- The next backlog task can start from less context than this one required.
