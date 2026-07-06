# Runbook: Add Or Update One Topic

Use this when changing one user, Firefox policy, CIS, or API-integration topic without broad
generation or runtime work.

## Inputs

- Current approved backlog task and the relevant inventory/architecture decision from
  `documentation/PROJECT_SNAPSHOT.md`.
- English source topic, the same topic in exactly the affected locale if this is a localized change,
  direct key map, direct subject/condition metadata, and one focused test.
- Synthetic examples only. Do not include secrets, private hosts, production data, licensed CIS
  source expression, copied vendor prose, or AI-generated content.

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

## Focused checks

Run the narrowest relevant checks first:

```bash
./.venv/bin/python documentation/tools/validate_metadata.py
./.venv/bin/pytest -q -m docs_contract tests/<one_relevant_contract>.py
./documentation/.cache/toolchain/python-venv/bin/pytest -q documentation/tests/<focused_test>.py
make docs-validate
git diff --check -- <changed_files>
```

Escalate to `make docs-reproducibility-check`, `make docs-package`, and
`make docs-package-verify` when the change affects maps, manifest output, generated files, theme,
assets, package policy, or release evidence.

## Done

- The topic still builds from DITA source and has no hidden dependency on ignored output.
- Links, keys, anchors, metadata, examples, and locale peers are validated or explicitly deferred by
  the approved backlog task.
- The completion note names the focused checks that passed and any broader release checks not run.
