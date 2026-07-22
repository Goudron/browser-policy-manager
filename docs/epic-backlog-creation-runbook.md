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

| ID | Task | Essence | Model | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- | --- |
| `BPM086-M1-01` | Update product version surfaces to `0.8.6`. | Move package metadata, active release surfaces, and versioned tests to the target version. | GPT-5.6 Luna | Light | Version surfaces, package metadata, and version assertions agree; README does not receive a target-version anchor or release-history entry. |

Task IDs must use:

```text
<EPIC_ID>-M<milestone_number>-<two_digit_task_number>
```

Example: `BPM086-M3-04`.

## Model And Reasoning Fields

Every task must specify both the minimum sufficient GPT-5.6 model and the minimum sufficient
reasoning level. Model capability and reasoning effort are independent choices; do not encode both
decisions in one vague complexity label.

The model tiers follow OpenAI's current model guidance:

| Model | Use when |
| --- | --- |
| `GPT-5.6 Luna` | Cost-sensitive, high-volume, well-bounded work with deterministic steps and cheap verification: metadata, docs-index maintenance, repetitive edits after a mapping is approved, direct command wrappers, formatting, and simple contract updates. |
| `GPT-5.6 Terra` | Default for everyday engineering that needs a balance of capability and cost: focused feature work, local refactors, test design, documentation, localization review, and UI/backend changes that follow established project patterns. |
| `GPT-5.6 Sol` | Flagship model for genuinely complex professional work: ambiguous cross-system architecture, security-critical reasoning, broad migrations, difficult multi-surface debugging, and release-critical decisions where Terra is not a safe minimum. |

Use this project vocabulary for reasoning effort:

| Level | Use when |
| --- | --- |
| `Light` | Mechanical or directly specified work with little ambiguity, a short context path, and immediate deterministic verification. |
| `Medium` | Standard reasoning for a focused subsystem, local trade-offs, adjacent tests, and clear existing patterns. |
| `High` | Extended reasoning for cross-file behavior, migrations, frontend/backend wiring, or schema, localization, browser, and test-platform contracts. |
| `Extra High` | The highest allowed effort for release-critical architecture, broad failure analysis, coverage recovery across many surfaces, or hard-to-reproduce behavior. |

In API terminology, the runbook's `Light` and `Extra High` labels correspond to `low` and `xhigh`.
The project intentionally uses only `Light`, `Medium`, `High`, and `Extra High`; do not add `none`
or `max` unless this runbook is revised.

Choose economically in this order:

1. Start with Luna and promote to Terra only when the task needs engineering judgment that Luna is
   not a safe minimum.
2. Use Terra as the normal default. Prefer Terra with a higher reasoning level when the work is
   deep but remains bounded and follows known project patterns.
3. Promote to Sol only when capability, ambiguity, risk, or cross-domain breadth makes Terra unsafe.
   Every Sol assignment must include a short task-specific justification in the task essence or
   acceptance text.
4. Split an oversized task before selecting a larger model or inflating reasoning effort.

Use the lowest model and reasoning level that should still let the task be completed safely. Final
quality commands, release metadata, and other mechanically verifiable work do not become Sol tasks
merely because they occur late in the backlog.

Selection guidance is based on OpenAI's current descriptions of
[GPT-5.6 model tiers](https://developers.openai.com/api/docs/models) and
[reasoning levels](https://help.openai.com/en/articles/20001354-gpt-56-in-chatgpt/). Re-check these
official sources when creating a backlog if model names, availability, or effort controls may have
changed.

## Mandatory Version Transition

The first milestone must include the target-version transition. It should cover every relevant
product surface for that epic:

- package/project metadata such as `pyproject.toml`, `package.json`, and lockfiles when present;
- local environment metadata for the editable BPM package, so `pip show browser-policy-manager`
  and equivalent environment probes report the target version after the version transition;
- supported external component pins and minimum dependency requirements, including Python,
  frontend vendor packages, documentation toolchain components, and test/dev dependencies that are
  part of the product workflow;
- changelog entry for the target version;
- docs index, active architecture notes, and release-readiness docs when they name the current
  release;
- UI-visible version strings if the product exposes them;
- tests that assert the current version.

By the end of the backlog, the repository should not describe the new work as belonging to the
previous target version except in historical notes, archive files, or explicit migration context.
README is not a version surface for this purpose. Do not add a README task to identify the active
target version, reserve version-specific copy, or create a release anchor. Version-specific
planning, release status, and completed-version summaries belong in the backlog and `CHANGELOG.md`,
not in README.

## README, Product Documentation, And Changelog

Every epic backlog must include product-documentation and changelog work. Include README work only
when the completed epic changes the durable current product state that README describes.

README must be updated after the main backlog implementation is complete, not only at backlog
creation time. It should describe the actual current product state after the epic, including current
surfaces, installation and product-start commands, supported external/runtime versions where they
are product facts, and user-facing behavior. README is for installers, users, and administrators:
do not add developer, maintainer, CI, test-workflow, source-tree, release-handoff, or author-routing
prose. If the epic does not change durable README content, the backlog should explicitly say that no
README update is needed.

README must not summarize what changed in a specific BPM version or list which earlier BPM version
introduced a feature. Release history, "what changed", and target-version completion notes belong in
`CHANGELOG.md`.
README must also not identify the active target version, reserve a future-version section, mention
that something is planned for a particular version, or contain a version-specific completion
placeholder. The only version-like facts allowed in README are durable product facts such as
supported external/runtime versions, schema channels, command names, or compatibility constraints.

When editing README:

- retain the legal license/copyright footer when it is user-facing;
- keep the primary product language English;
- remove developer, maintainer, test/CI, source-tree, and email-routing instructions;
- remove release-note phrasing such as "what's included in <version>", "planned for <version>", or
  "introduced in <version>";
- remove target-version anchors, active-target notes, and future-version placeholders;
- remove or revise stale feature descriptions that no longer match the product;
- do not delete historical or legal footer material while refreshing the main product copy.

Whenever an epic changes the README audience or boundary, inventory every repository test that reads
`README.md`, update its expectation in the same task, and run `pytest -q` after the final README
edit. Focused README checks alone are insufficient because a locale, API, deployment, or release
contract can also encode stale README prose.

Product documentation must be updated after the epic changes functionality. Add a dedicated
documentation-update milestone before the final quality milestone whenever the epic changes
user-visible behavior, administrator/operator procedures, API behavior, supported schemas, locale
behavior, security posture, deployment steps, or troubleshooting flow. That milestone should update
the DITA/User/Admin/API/CIS/Firefox topics, screenshots or screenshot blockers, manifests/search
targets, and documentation tests needed to make the documentation describe the product after the
epic.

### Maintainer `make dev` documentation handoff

When a task changes product-documentation source, documentation build tooling, generated portal
behavior, or a served documentation version surface, run `make docs-install-dev` before reporting
the task complete. This installs the current documentation artifact consumed by the maintainer's
subsequent `make dev`; it is not a request for the assistant to start the development server.

Every affected backlog must include a documentation-milestone task that makes this handoff explicit.
Its acceptance must require the task report to record the successful `make docs-install-dev` command
and confirm that the served artifact derives its visible version from the current BPM product version.

### Compact UI-copy and documentation guard

When an epic removes, shortens, or introduces visible UI copy, include a pre-implementation task
that classifies each affected rendered node against the active UI-copy classification contract. The
backlog may remove routine explanation and duplicate presentation only; it must retain labels,
state, validation, consequences, unavailable reasons, accessible names, and recovery at the point
of action. A contextual circled-info link is a task only for a recorded genuine comprehension gap,
not a default replacement for removed prose.

When an epic changes rendered product documentation, include its audience and locale review in the
documentation milestone: documentation serves users, administrators, DevOps operators, API
integrators, and security reviewers, not maintainers or implementation progress. Require one BPM
product version, no separately owned documentation version, and locale-native headings rather than
English-calqued grammar; Russian task/reference headings use an idiomatic nominal form where
natural. Cite the active documentation audience/editorial and locale style contracts in the task.

`CHANGELOG.md` must receive an entry for the target version. Preserve older version history; append
or insert the new version entry without overwriting previous release notes.

## Milestone Guidance

Prefer milestones like these when applicable:

- M1: version transition and release anchors;
- M2: current-state audit and safety contracts;
- M3..N: implementation milestones grouped by product or subsystem ownership;
- pre-final documentation milestone: update maintained product documentation and, only when the
  durable current product state changed, refresh README current-state copy without version-specific
  release notes or target-version anchors;
- final milestone: quality, coverage, visual smoke, changelog, commit, push handoff, and
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
7. Verify the dedicated documentation-update milestone is complete and its focused documentation
   checks have passed.
8. Update `CHANGELOG.md` for the target version while preserving older version history.
9. Verify README has no target-version anchor, release-history entry, planned-for-version copy, or
   version-specific completion placeholder; update README only if the durable current product state
   changed. If README audience/boundary changed, update every README-reading contract and rerun
   `pytest -q` after the final edit.
10. Update docs index if final verification changes maintained documentation.
11. Verify schema, CIS, locale, Administrator/DevOps deployment, DevOps integration, update, and
    release procedures include documentation drift gates when the epic changed those areas.
12. Create a git commit for the completed epic.
13. Provide the maintainer with the exact `git push` command to run manually.

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

Browser/Selenium tests are known to require access outside the Codex filesystem sandbox. When
running `make test-ui` or any Selenium/browser UI command during backlog execution, request sandbox
escalation immediately. Do not first try the browser test command inside the sandbox.

If Make targets change in a future epic, update this runbook and the backlog together.

Do not push from the backlog execution step. The assistant creates the commit when requested by the
backlog flow, then prints the push command for the maintainer to run.

## Approval Protocol

When executing a backlog interactively with the user:

1. Show exactly one next task with its ID, essence, acceptance, minimum model, and minimal reasoning.
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
- every task names exactly one minimum model: `GPT-5.6 Luna`, `GPT-5.6 Terra`, or `GPT-5.6 Sol`;
- every task has `Light`, `Medium`, `High`, or `Extra High` as minimal reasoning;
- Luna is preferred for deterministic high-volume work, Terra is the normal default, and every Sol
  assignment has a task-specific justification showing why Terra is unsafe;
- first milestone includes version transition across product surfaces;
- first milestone includes local editable-package metadata refresh and external dependency
  currency checks for Python, frontend vendor packages, documentation toolchain components, and
  test/dev dependencies;
- first milestone does not include README target-version anchors, active-target notes, or
  future-version placeholders;
- a dedicated documentation-update milestone appears before the final quality milestone when the
  epic changes product behavior or operating procedures;
- documentation-changing tasks require `make docs-install-dev` before handoff so the maintainer's
  later `make dev` serves the current artifact and current BPM version;
- final milestone includes mypy, ruff, `pytest -q`, coverage-to-100%, and Selenium smoke;
- Selenium/browser UI verification notes require immediate sandbox escalation, without a sandboxed
  trial run;
- final milestone verifies documentation-update completion and includes changelog entry, git commit,
  and maintainer-run push command;
- final milestone verifies README has no version-specific release notes, active-target marker, or
  planned/completion placeholder; README updates are limited to durable current-state product facts;
- final milestone verifies maintained runbooks and docs index include documentation drift gates for
  changed schema, CIS, locale, Administrator/DevOps deployment, DevOps integration, update, and
  release procedures;
- README is limited to installer/user/administrator information, retains only its legal footer, and
  forbids developer, maintainer, email-routing, release-history, and version-change summaries;
- any README audience/boundary change inventories every README-reading contract and reruns
  `pytest -q` after the final README edit;
- changelog instructions preserve previous version history;
- runbook notes that product language is English while maintainer chat may be Russian;
- docs index includes the new backlog;
- assumptions and non-goals are explicit;
- execution protocol says each task requires separate user approval.
