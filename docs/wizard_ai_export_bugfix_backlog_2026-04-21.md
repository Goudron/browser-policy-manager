# Wizard AI And Export Bugfix Backlog

Date: `2026-04-21`

## Goal

Fix the runtime bugs found during manual QA of the guided wizard, especially the broken AI step and the confusing first viewport of the final export step.

This is a bugfix backlog, not a redesign backlog. Keep the scope narrow: make the existing wizard behavior match the current 8-step product model.

## QA Context

Manual QA was run against `/profiles` with local `uvicorn` and headless Chromium through CDP.

Observed baseline:

- Step navigation from 1 through 8 activates exactly one `.wizard-panel`.
- `aria-hidden` follows the active step correctly.
- Step 8 contains the export sections and download action.
- Existing wizard smoke tests pass, but they do not catch the broken AI runtime behavior.

Main failures:

- Step 7 does not show the main `GenerativeAI` control.
- AI posture presets do not apply a profile change.
- Step 8 starts with generic schema-shell technical coverage copy, so the export destination is visually buried.

## Priority Backlog

### `WIZ-QA-01` Show The Main AI Control On Step 7

Status: Done.

Problem:

`#wizard-generative-ai-card` exists in the DOM but remains `hidden=true` and `display:none` on step 7. The visible AI step shows posture presets and a provider handoff, but not the actual `GenerativeAI` settings control.

Likely areas:

- [app/static/profiles_schema_shell_sections.js](/home/valery/Projects/browser-policy-manager/app/static/profiles_schema_shell_sections.js)
- [app/static/profiles_extensions.js](/home/valery/Projects/browser-policy-manager/app/static/profiles_extensions.js)
- [app/templates/profiles/_page_wizard_step_ai.html](/home/valery/Projects/browser-policy-manager/app/templates/profiles/_page_wizard_step_ai.html)
- Firefox policy schema availability for `GenerativeAI` in Release 149 versus ESR 140.

Fix:

Make the `GenerativeAI` guided card render visibly when the active schema supports it. If ESR 140 does not support the policy, show an explicit unavailable-state message instead of an empty hidden card.

Acceptance:

- On step 7 with Release 149 selected, `#wizard-generative-ai-card` is visible and contains editable settings.
- On schemas without `GenerativeAI`, the step shows clear copy explaining that the policy is unavailable for that schema.
- The AI step never presents `Disable AI` or `Manage availability` as usable actions while the target control is hidden.

### `WIZ-QA-02` Make AI Posture Presets Apply Real State

Status: Done.

Problem:

Clicking `Disable AI`, `Manage availability`, `Providers`, or `Mixed` mostly scrolls/highlights target areas. The editor/profile state does not change, and the active preset remains effectively `Default`.

Likely area:

- [app/static/profiles_extensions.js](/home/valery/Projects/browser-policy-manager/app/static/profiles_extensions.js)

Fix:

Define explicit behavior for each AI posture preset:

- `defaults`: remove guided AI policy values.
- `disable`: set the supported `GenerativeAI` disabled shape.
- `availability`: create or reveal a managed availability baseline.
- `providers`: route to advanced provider/model handoff if provider fields are advanced-only.
- `mixed`: reveal both availability and smart-surface controls, and apply a minimal managed baseline only where appropriate.

Acceptance:

- Each visible AI preset either changes the profile state or clearly opens the only available configuration destination.
- The AI status text updates after every preset click.
- The active preset reflects the actual parsed policy state.
- No preset silently does nothing.

### `WIZ-QA-03` Make Visual Search Fine Tuning Discoverable

Status: Done.

Problem:

`#wizard-ai-surfaces-section` and `#wizard-visual-search-enabled-card` are hidden by default. The `mixed` preset can reveal the surfaces section, but the actual visual-search card still remains hidden in the observed QA run.

Likely areas:

- [app/static/profiles_schema_shell_sections.js](/home/valery/Projects/browser-policy-manager/app/static/profiles_schema_shell_sections.js)
- [app/static/profiles_extensions.js](/home/valery/Projects/browser-policy-manager/app/static/profiles_extensions.js)
- [app/templates/profiles/_page_wizard_step_ai.html](/home/valery/Projects/browser-policy-manager/app/templates/profiles/_page_wizard_step_ai.html)

Fix:

Ensure `VisualSearchEnabled` mounts into `#wizard-visual-search-enabled-card` when the active schema supports it, and make the fine-tuning reveal expose the actual control.

Acceptance:

- Clicking the AI fine-tuning toggle shows `#wizard-visual-search-enabled-card` when supported.
- Clicking the `mixed`/smart-surfaces path reveals a usable visual-search control or a clear unsupported-schema state.

### `WIZ-QA-04` Put Export Actions First In Step 8

Status: Done.

Problem:

Step 8 opens correctly, but the first visible content is generic schema-shell technical coverage text: "Most common settings are available here..." and "Open Advanced document for this step". This makes the final step feel like another technical review step instead of the export destination.

Likely areas:

- [app/templates/profiles/_page_wizard_step_export.html](/home/valery/Projects/browser-policy-manager/app/templates/profiles/_page_wizard_step_export.html)
- [app/templates/profiles/_wizard_macros.html](/home/valery/Projects/browser-policy-manager/app/templates/profiles/_wizard_macros.html)
- [app/static/profiles.css](/home/valery/Projects/browser-policy-manager/app/static/profiles.css)

Fix:

Move, collapse, or visually de-emphasize the schema-shell coverage block on step 8 so the first viewport leads with:

- readiness state
- save action
- validate action
- `Download Firefox policies.json`

Acceptance:

- On entering step 8, the first visible section is clearly "Ready to export" or equivalent.
- Download/save/validate actions are visible without scrolling on a normal desktop viewport.
- Technical coverage remains available, but it does not lead the final step.

### `WIZ-QA-05` Add Runtime Regression Coverage For Wizard Steps

Status: Done.

Problem:

The current smoke tests passed while the AI step was broken. They assert that DOM nodes exist, but not that the user can see or operate the expected controls.

Likely tests:

- [tests/test_ui_smoke_profile_workflow.py](/home/valery/Projects/browser-policy-manager/tests/test_ui_smoke_profile_workflow.py)
- [tests/test_firefox_wizard_shell.py](/home/valery/Projects/browser-policy-manager/tests/test_firefox_wizard_shell.py)
- Add a browser-level smoke slice if the existing test stack supports it.

Fix:

Add assertions for visible runtime behavior, not just static HTML:

- Step 7 has an actionable AI settings area.
- AI presets change state or route to a visible target.
- Step 8 first viewport prioritizes export actions.
- Only one wizard panel is visible after direct step clicks and `Next` navigation.

Acceptance:

- A regression that hides `#wizard-generative-ai-card` fails tests.
- A regression that puts schema-shell technical copy before export actions on step 8 fails tests.
- Existing static smoke tests still cover required IDs.

## Recommended Order

1. `WIZ-QA-01` Show the main AI control.
2. `WIZ-QA-02` Make AI presets apply or route explicitly.
3. `WIZ-QA-03` Make visual-search fine tuning discoverable.
4. `WIZ-QA-04` Reframe the first viewport of export.
5. `WIZ-QA-05` Add runtime regression coverage.

## Definition Of Done

- Step 7 exposes real AI controls or explicit unsupported-schema states.
- AI preset buttons do not silently no-op.
- Step 8 reads as the final export destination immediately after navigation.
- Manual QA can pass the 1 through 8 wizard flow without seeing hidden-target interactions.
- Automated coverage protects the specific AI visibility and export-first-viewport regressions found on `2026-04-21`.
