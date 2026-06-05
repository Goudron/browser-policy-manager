# Epic Backlog Creation Runbook

Use this runbook whenever a user asks to create a backlog for a new BPM epic, theme, refactor,
feature area, optimization stream, or release effort.

Every new epic backlog is treated as a target BPM product version. The user must provide that target
version in the request, for example `0.8.6`. If the version is missing or ambiguous, ask for the
target version before creating the backlog.

All new BPM epic backlogs must pass through this runbook.

Product source, UI copy, README, changelog, and maintained documentation use English as the primary
product language. The working chat with the maintainer can be in Russian; do not turn that into
Russian product copy unless the task is explicitly about Russian localization.

## Required Inputs

Collect these values before writing the backlog:

| Field | Required | Example |
| --- | --- | --- |
| Target BPM version | yes | `0.8.6` |
| Epic/theme name | yes | `Schema bump automation` |
| Backlog date | yes | `2026-06-05` |
| Scope boundary | yes | Refactor only, product behavior change, test-platform work, docs cleanup |
| Known non-goals | recommended | No live Firefox behavior expansion |
| Release risk | recommended | Low, medium, high |

If the target version is supplied as prose, normalize it into:

- version string: `0.8.6`
- compact epic id: `BPM086`
- filename prefix: `bpm_0_8_6`

## Backlog File

Create one maintained backlog file under `docs/`:

```text
docs/bpm_<version_with_underscores>_<short_topic>_backlog_<yyyy-mm-dd>.md
```

Example:

```text
docs/bpm_0_8_6_schema_bump_automation_backlog_2026-06-05.md
```

Then add the file to `docs/docs-index.md` with status `backlog`. Do not put a new active backlog in
`docs/archive/`; archive only after it is superseded or completed.

## Backlog Structure

Each backlog must include:

1. Title with target version and theme.
2. Scope summary.
3. Current-state assessment.
4. Non-goals and assumptions.
5. Milestones grouped by meaning, not by implementation convenience.
6. Numbered task table for every milestone.
7. Final quality milestone.
8. Execution protocol for approval task by task.

Use this task table shape:

| ID | Task | Essence | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- |
| `BPM086-M1-01` | Update product version surfaces to `0.8.6`. | Move all user-visible and package metadata to the target version. | low | Version surfaces, README, changelog, and package metadata agree. |

Task IDs must use:

```text
<EPIC_ID>-M<milestone_number>-<two_digit_task_number>
```

Example: `BPM086-M3-04`.

## Minimal Reasoning Field

Every task must specify the minimum sufficient ChatGPT-5.5 reasoning level:

| Level | Use when |
| --- | --- |
| `low` | Mechanical metadata, docs index updates, small copy changes, direct command wrappers. |
| `medium` | Local refactors, focused tests, one subsystem, clear existing patterns. |
| `high` | Cross-module behavior, migrations, frontend route wiring, schema/localization/test-platform contracts. |
| `extra high` | Release-critical architecture decisions, broad migrations, coverage recovery across many surfaces, hard-to-reproduce browser behavior. |

Use the lowest level that should still let the task be done safely. Do not inflate reasoning levels
as a substitute for splitting a task.

## Mandatory Version Transition

The first milestone must include the target-version transition. It should cover every relevant
product surface for that epic:

- package/project metadata such as `pyproject.toml`, `package.json`, and lockfiles when present;
- README version copy and supported-version notes;
- changelog entry for the target version;
- docs index, active architecture notes, and release-readiness docs when they name the current
  release;
- UI-visible version strings if the product exposes them;
- tests that assert the current version.

By the end of the backlog, the repository should not describe the new work as belonging to the
previous target version except in historical notes, archive files, or explicit migration context.

## README And Changelog

Every epic backlog must include README and changelog work for the target version.

README must be updated after the main backlog implementation is complete, not only at backlog
creation time. It should describe the actual current product state after the epic, including changed
surfaces, commands, supported versions, test workflow, and user-facing behavior.

When editing README:

- keep the maintainer copyright at the bottom;
- keep the existing information about email topics / message themes;
- keep the primary product language English;
- remove or revise stale feature descriptions that no longer match the product;
- do not delete historical or legal footer material while refreshing the main product copy.

`CHANGELOG.md` must receive an entry for the target version. Preserve older version history; append
or insert the new version entry without overwriting previous release notes.

## Milestone Guidance

Prefer milestones like these when applicable:

- M1: version transition and release anchors;
- M2: current-state audit and safety contracts;
- M3..N: implementation milestones grouped by product or subsystem ownership;
- final milestone: quality, coverage, visual smoke, README, changelog, commit, push handoff, and
  release-readiness checks.

Do not create one large "implementation" milestone. If a milestone mixes backend, frontend,
localization, schema, tests, and docs without a clear shared purpose, split it.

## Task Sizing

Each task should be small enough for one focused implementation pass. Split a task when it:

- touches unrelated ownership areas;
- needs both architecture decisions and bulk mechanical edits;
- cannot be tested with a focused command;
- would require broad context loading just to understand the acceptance condition.

Each task should name the likely verification layer, for example focused unit tests, contract tests,
locale contract, browser UI smoke, or release suite.

## Final Quality Milestone

Every backlog must end with a final quality milestone. Include tasks for:

1. Run `mypy`.
2. Run `ruff`.
3. Run `pytest -q`.
4. Run coverage with code-surface reporting.
5. Bring covered code surface to 100% if it is below 100%.
6. Run Chromium/Selenium smoke tests for BPM product logic.
7. Update README so it matches the actual product after the main epic work, while preserving the
   maintainer copyright and email-topic information.
8. Update `CHANGELOG.md` for the target version while preserving older version history.
9. Update docs index if final verification changes maintained documentation.
10. Create a git commit for the completed epic.
11. Provide the maintainer with the exact `git push` command to run manually.

The coverage task must explicitly say that falling below 100% is not accepted as "known debt" for
the epic. Either add focused tests, shrink untested dead code, or document and remove unreachable
code paths as part of the backlog execution.

Use current project targets where possible:

```bash
make typecheck
make lint
pytest -q
make coverage
make test-ui
```

If Make targets change in a future epic, update this runbook and the backlog together.

Do not push from the backlog execution step. The assistant creates the commit when requested by the
backlog flow, then prints the push command for the maintainer to run.

## Approval Protocol

When executing a backlog interactively with the user:

1. Show exactly one next task with its ID, essence, acceptance, and minimal reasoning.
2. Wait for explicit approval.
3. Execute only that approved task.
4. Report what changed and which checks passed.
5. Show the next task for approval.

Do not start executing a backlog task just because the backlog exists.

## Backlog Creation Acceptance Checklist

Before calling a new backlog ready, confirm:

- target BPM version is present and normalized;
- epic id and task IDs are stable;
- milestones are grouped by meaning;
- every task has `low`, `medium`, `high`, or `extra high` as minimal reasoning;
- first milestone includes version transition across product surfaces;
- final milestone includes mypy, ruff, `pytest -q`, coverage-to-100%, and Selenium smoke;
- final milestone includes README refresh, changelog entry, git commit, and maintainer-run push
  command;
- README instructions preserve maintainer copyright and email-topic information;
- changelog instructions preserve previous version history;
- runbook notes that product language is English while maintainer chat may be Russian;
- docs index includes the new backlog;
- assumptions and non-goals are explicit;
- execution protocol says each task requires separate user approval.
