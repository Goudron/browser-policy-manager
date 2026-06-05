# Wizard Final UX Cleanup Backlog

## Goal

Close the last guided-flow UX gaps before we treat the Firefox policy wizard redesign as stable.
This backlog is intentionally short and focused on polish, consistency, and real-world usability, not on another structural rewrite.

## Priorities

### P0: Finish the guided experience

1. Simplify the export step for guided users.
   Problem:
   [app/templates/profiles/_page_wizard_step_export.html](/home/valery/Projects/browser-policy-manager/app/templates/profiles/_page_wizard_step_export.html) still leads with editor/workspace vocabulary that feels closer to an internal tool than to a "ready to download" finish line.
   Fix:
   Reframe the first card around `Ready to save`, `Ready to validate`, and `Ready to download`, and make the guided path read as a release checklist rather than editor state.
   Acceptance:
   A user can understand what to do next without seeing the words `editor`, `workspace`, or `document state` in the guided review flow.

2. Bring the privacy step to the same interaction rhythm as other steps.
   Problem:
   [app/templates/profiles/_page_wizard_step_privacy.html](/home/valery/Projects/browser-policy-manager/app/templates/profiles/_page_wizard_step_privacy.html) still relies heavily on large toggle grids, while `Network`, `Home`, `Search`, and `Features` already use clearer `main choice -> status -> fine tuning` framing.
   Fix:
   Add status strips for the privacy and lockdown sections, and consider one compact `Strictness` framing layer before the full toggle matrix.
   Acceptance:
   Privacy feels like the same product as the other guided steps, not like an older leftover panel.

3. Remove the last schema-key phrasing from guided hints and empty states.
   Problem:
   Some guided copy still leaks implementation details such as `SearchEngines.Add`, `SearchEngines.Remove`, `Homepage.Additional`, `raw JSON`, and mixed `advanced/raw` wording in user-adjacent strings.
   Fix:
   Sweep guided copy in [app/templates/profiles/](/home/valery/Projects/browser-policy-manager/app/templates/profiles), [app/i18n/en.json](/home/valery/Projects/browser-policy-manager/app/i18n/en.json), and [app/i18n/ru.json](/home/valery/Projects/browser-policy-manager/app/i18n/ru.json) for any remaining schema-first phrasing.
   Acceptance:
   Guided mode explains Firefox behavior, not storage keys.

### P1: Make the product feel more finished

4. Decide on stable naming for the JSON editor.
   Problem:
   The product currently mixes `JSON editor`, `JSON editor`, `document view`, `raw JSON/YAML`, and Russian text with untranslated `JSON editor`.
   Fix:
   Pick one canonical product name and localize it consistently across [app/templates/profiles/_page_workspace.html](/home/valery/Projects/browser-policy-manager/app/templates/profiles/_page_workspace.html), [app/templates/profiles/_page_wizard_step_export.html](/home/valery/Projects/browser-policy-manager/app/templates/profiles/_page_wizard_step_export.html), [app/templates/profiles/_wizard_macros.html](/home/valery/Projects/browser-policy-manager/app/templates/profiles/_wizard_macros.html), [app/i18n/en.json](/home/valery/Projects/browser-policy-manager/app/i18n/en.json), and [app/i18n/ru.json](/home/valery/Projects/browser-policy-manager/app/i18n/ru.json).
   Acceptance:
   The JSON editor has one name in EN and one deliberate localized name in RU.

5. Add action-oriented empty states to the heaviest guided cards.
   Problem:
   Status lines like `No homepage overrides yet` or `No Firefox Suggest overrides yet` are cleaner than before, but they still do not always help the user decide what to do next.
   Fix:
   Upgrade the empty states for `Home`, `Search`, `Firefox Suggest`, `Extensions`, `Website behavior`, `Permissions`, and `Cookies` to say what Firefox will do by default and when the user would usually change it.
   Acceptance:
   Empty states feel instructional, not just informational.

6. Tighten the largest add-on cards.
   Problem:
   The curated add-on cards in [app/templates/profiles/_page_wizard_step_sync.html](/home/valery/Projects/browser-policy-manager/app/templates/profiles/_page_wizard_step_sync.html) are much better than before, but they are still tall and repetitive, especially on mobile.
   Fix:
   Consider a more compact per-add-on layout with a short summary row and a nested `Details` reveal for URL and secondary toggles.
   Acceptance:
   A user can scan multiple known add-ons quickly without reading full card bodies every time.

### P2: Real-device polish and resilience

7. Run a real viewport QA pass.
   Problem:
   Responsive CSS is now much stronger, but we have not yet captured concrete QA notes for actual narrow widths like `390x844`, `393x852`, `412x915`, and small laptop widths.
   Fix:
   Do a manual browser pass and record any overflow, overly tall cards, awkward button stacking, or summary-card rhythm problems.
   Acceptance:
   We have a small written list of actual viewport issues instead of inferred mobile polish only.
   Notes:
   See [docs/archive/2026-q2/wizard_viewport_qa_2026-03-31.md](archive/2026-q2/wizard_viewport_qa_2026-03-31.md).

8. Add light accessibility polish to disclosure-heavy areas.
   Problem:
   The wizard now uses many reveal controls such as `Show fine tuning` and `Show more rules`, so consistency of labels, focus order, and state announcements matters more than before.
   Fix:
   Review disclosure buttons, jump actions, and large toggle cards for predictable focus movement and clearer accessible names.
   Acceptance:
   Guided flow remains understandable when navigated by keyboard and screen reader.

9. Add one UI-oriented regression test slice for guided mode.
   Problem:
   Current smoke coverage protects core rendering, but not the final UX assumptions around guided vs advanced visibility and compact mobile-oriented structure.
   Fix:
   Extend [tests/test_web_profiles_page.py](/home/valery/Projects/browser-policy-manager/tests/test_web_profiles_page.py) and/or [tests/test_ui_smoke_profile_workflow.py](/home/valery/Projects/browser-policy-manager/tests/test_ui_smoke_profile_workflow.py) with assertions for the guided export framing, JSON-editor naming, and key fine-tuning controls.
   Acceptance:
   We have at least one test slice guarding the last UX cleanup decisions.
   Status:
   Completed on 2026-03-31 in [tests/test_web_profiles_page.py](/home/valery/Projects/browser-policy-manager/tests/test_web_profiles_page.py).

## Recommended order

1. P0.1 export copy and finish-line framing
2. P0.2 privacy rhythm pass
3. P0.3 guided copy sweep
4. P1.4 JSON-editor naming
5. P1.5 empty-state improvements
6. P1.6 compact add-on cards
7. P2.7 viewport QA pass
8. P2.8 accessibility pass
9. P2.9 regression-test follow-up

## Definition of done

- Guided mode reads as a browser-setup flow, not a schema editor.
- The JSON editor has one stable product name.
- `Home`, `Search`, `Privacy`, and `Features` follow the same interaction rhythm.
- Mobile feels intentionally designed, not merely collapsed.
- Export feels like a confident finish step.
