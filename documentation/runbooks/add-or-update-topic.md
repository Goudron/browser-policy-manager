# Runbook: Add Or Update One Topic

Use this when changing one user, Firefox policy, CIS, or API-integration topic without broad
generation or runtime work.

## Inputs

- Current approved backlog task and the relevant inventory/architecture decision from
  `documentation/PROJECT_SNAPSHOT.md`.
- English source topic, the same topic in exactly the affected locale if this is a localized change,
  direct key map, direct subject/condition metadata, and one focused test.
- Synthetic examples only. Do not include secrets, private hosts, production data, licensed CIS
  source expression, copied vendor prose, or unreviewed AI-authored content.

## Steps

1. Confirm the stable topic ID, source slug, DITA key, canonical URL path, guide, audience, platform,
   BPM version, and any policy/CIS/API metadata before writing prose.
2. Author or edit English DITA first. Use DITA 1.3 topic/task/concept/reference structures. Do not
   add Markdown, hand-authored HTML, raw HTML passthrough, inline scripts, or inline styles.
3. Link with `keyref`/`conkeyref` where possible. Direct `href` is only for same-topic fragments or
   approved external `https` references.
4. Preserve released IDs and anchors. New public subsection anchors use `a-{semantic-kebab-slug}`;
   generated IDs and visual heading numbers are not link contracts.
5. Keep steps case-oriented: user goal, prerequisites, action, expected result, warning/recovery, and
   related tasks. Do not drift into administrator/distribution guidance in 0.9.0.
6. If examples are needed, validate them against current BPM contracts where practical and label
   intentionally invalid examples with expected errors.
7. Update only the peer localized topic(s) that are in scope. If all six localized peers are required
   but not available yet, leave an explicit backlog blocker; do not silently fall back to English.
8. Update keys/maps/manifest source metadata only when the topic identity or navigation contract
   actually changes.

## Compact UI and product-documentation boundary

Before adding or restoring visible UI copy, classify the exact rendered node under the
[UI copy classification contract](../../docs/architecture/ui-copy-classification-contract-0.9.2.md).
Do not add routine workflow narration, a repeated purpose sentence, or a helper line that merely
restates an adjacent label, value, or action. Keep essential and safety/accessibility text at the
point of action: labels, current state, validation, consequence, unavailable reason, and recovery
are never moved into documentation.

Add a circled-info/contextual-help target only when the classification records a genuine remaining
comprehension gap. The target must be a localized, manifest-backed stable topic or anchor and must
not become a generic substitute for concise UI copy. If the label, value, action, and accessible
name already make the control clear, do not add a help link.

Write rendered product documentation for the user, administrator, DevOps operator, API integrator,
or security reviewer who needs it. Do not address a maintainer or developer, narrate implementation
progress, expose internal source/test/build instructions, or present a separately owned
documentation version. Retain complete task explanations in DITA where they are needed; compact UI
work does not authorize removal of prerequisites, warnings, results, support boundaries, or
recovery.

## Focused checks

Run the narrowest relevant checks first:

```bash
./.venv/bin/python documentation/tools/validate_metadata.py
./.venv/bin/pytest -q -m docs_contract tests/<one_relevant_contract>.py
./documentation/.cache/toolchain/python-venv/bin/pytest -q documentation/tests/<focused_test>.py
make docs-validate
git diff --check -- <changed_files>
```

When the change affects product-documentation source, documentation build tooling, generated portal
behavior, or a served documentation-version surface, run `make docs-install-dev` before handoff.
This refreshes the artifact for the maintainer's subsequent `make dev`; do not start the development
server as part of this runbook.

Escalate to `make docs-reproducibility-check`, `make docs-package`, and
`make docs-package-verify` when the change affects maps, manifest output, generated files, theme,
assets, package policy, or release evidence.

## Done

- The topic still builds from DITA source and has no hidden dependency on ignored output.
- Links, keys, anchors, metadata, examples, and locale peers are validated or explicitly deferred by
  the approved backlog task.
- The completion note names the focused checks that passed and any broader release checks not run.
