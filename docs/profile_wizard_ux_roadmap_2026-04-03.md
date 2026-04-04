# Profile Wizard UX Roadmap

Date: `2026-04-03`

## Decision

We will follow the recommended sprint order for the profile wizard UX work.
The goal is to improve confidence, guidance, and task speed in guided mode without turning the main flow back into a schema editor.

## Sprint Order

### Sprint 1

1. Coverage transparency in guided mode.
   Show what the current step covers directly, what remains in the advanced document, and what will still be preserved.

2. Privacy rhythm pass.
   Bring privacy to the same `main choice -> status -> fine tuning` interaction model used by the stronger guided steps.

3. Better empty states.
   Replace passive `nothing configured yet` copy with messages that explain Firefox defaults and when a person would usually change them.

4. First-screen compression.
   Reduce the amount of non-actionable vertical space before the first real control, especially on mobile and smaller laptops.

### Sprint 2

1. Recommended baseline layer.
   Promote the curated policy set into clearer opinionated shortcuts for common profile types.

2. Guided-to-advanced handoff.
   Replace generic advanced-mode entry points with targeted jumps into the exact advanced area that still needs attention.

3. Compact extensions and add-ons cards.
   Improve scanability and reduce mobile height in the heaviest cards.

### Sprint 3

1. Scenario-first wizard entry.
   Start from user goals such as corporate, kiosk, hardened, or add-on-managed setups instead of raw browser areas alone.

2. First guided-coverage expansion cluster.
   Expand policy coverage by value and frequency, not by trying to cover every policy evenly.

### Sprint 4+

1. Continue guided coverage by policy clusters.
2. Accessibility polish for disclosure-heavy areas.
3. UX regression hardening.

## Delivery Rules

- Guided mode stays task-first and human-readable.
- Advanced document remains available, but not required for the common path.
- Coverage growth should not come at the cost of clarity.
- Prefer iterative slices that preserve current serialization and validation behavior.

## Current Focus

Progress has moved well past the initial Sprint 1 starting point.

Completed:

1. Sprint 1:
   coverage transparency, privacy rhythm, empty-state improvements, and first-screen compression
2. Sprint 2:
   recommended baselines, guided-to-advanced handoff, compact add-on cards
3. Sprint 3:
   scenario-first entry and the first guided-coverage expansion cluster
4. Sprint 4+:
   guided coverage expansion across multiple policy clusters, accessibility polish, regression hardening
5. `P2.7` follow-up viewport QA pass on `2026-04-03`:
   guided setup now lands on the first screen at the target mobile and small-desktop widths after moving the command deck below the wizard

Next backlog refresh should start from a new post-redesign roadmap rather than the original sprint starter list.

## Post-roadmap Addendum

After the original sprint roadmap was completed, work continued as a guided-first polish stream rather than a new policy-coverage sprint. These follow-up blocks are also completed.

### Completed Post-roadmap Polish

1. Mobile toolbar simplification.
   Reduced header and toolbar height on smaller screens so the first guided control lands higher in the viewport.

2. Header and workspace language cleanup.
   Replaced more internal-tool wording with product-facing setup language.

3. Dock, details, and advanced copy pass.
   Simplified heavy editor/document wording and made advanced-mode labels clearer.

4. Status, validation, and error language pass.
   Reworded system feedback so it speaks about profile setup and document state more naturally.

5. Library and selection state cleanup.
   Made the starting point read more like `open a profile or start a draft` and less like a raw editor state.

6. Profile lifecycle language and confirm-flow cleanup.
   Reframed archive, delete, restore, and library reset language into calmer and more consistent lifecycle actions.

7. Command deck action hierarchy.
   Grouped main actions, document utility, and lifecycle actions into clearer priority bands.

8. Before/after selection state contrast.
   Added stronger empty, draft, active, and archived visual states across overview and action surfaces.

9. Export and command deck state coupling.
   Synchronized lifecycle cues so command deck and export talk about the same state in the same moment.

10. Advanced and guided mode entry clarity.
    Added clearer mode summaries and mode cards so the difference between guided work and advanced work is more obvious.

11. Advanced document empty states and first actions.
    Added neutral advanced-mode onboarding with direct actions for profile details, full document editing, and validation.

12. Advanced document utility hierarchy.
    Reframed advanced mode around `details -> full document -> validation/downloads` and separated saved-file downloads more clearly.

13. Advanced document review visibility.
    Added a local advanced review strip so save state, validation state, and download state are visible next to the editor.

14. Advanced and guided copy convergence.
    Aligned review terminology across both modes so they share the same language for edits, validation, and download readiness.

## Consolidated Status

At this point the profile wizard no longer has just a completed redesign roadmap; it also has a completed post-roadmap polish layer focused on:

- guided-first entry and readability
- stronger state visibility
- clearer advanced-mode onboarding
- tighter copy consistency across guided and advanced paths
- safer mobile and small-viewport behavior

## Quality Milestone

Date: `2026-04-04`

- Non-live automated coverage for `app/` reached `100%` statement and branch coverage under the current test suite.
- The last uncovered paths were closed in [`app/db.py`](/home/valery/Projects/browser-policy-manager/app/db.py) with targeted tests in [`tests/test_db_helpers.py`](/home/valery/Projects/browser-policy-manager/tests/test_db_helpers.py).
- This milestone protects the current guided, advanced, lifecycle, compare, and export behavior with full non-live code coverage, while live Firefox scenarios remain intentionally outside that coverage target.

The next roadmap refresh can start from product-level opportunities again rather than from cleanup debt inside the current wizard shell.

## Post-roadmap Backlog

This backlog starts after the completed redesign roadmap, after the completed post-roadmap polish stream, and after the completed `PB` product backlog. It is intentionally smaller and focused on keeping the wizard cohesive as the product matures.

### PR0: Polish And Consistency

1. `PR0.1` unified interface vocabulary.
   Keep terms such as `profile`, `draft`, `saved profile`, `Guided setup`, and `Advanced document` consistent across copy, status surfaces, and empty states.

2. `PR0.2` empty-state cleanup.
   Make empty states equally useful across the product by always clarifying what is ready, what is missing, and what to do next.

3. `PR0.3` workflow block consistency. Completed.
   Align all governance, workflow, and checklist blocks to the same visual and textual pattern so new guided layers feel like one system instead of a set of local inventions.

### PR1: Guided Flow Acceleration

4. `PR1.1` stronger next actions inside heavy steps. Completed.
   Add clearer local next-step actions so users do not just see status, but also see the best immediate move inside the current step.

5. `PR1.2` preset impact previews inside steps.
   Extend the `what will change` preview model beyond startup baselines into the major presets used inside heavy steps.

6. `PR1.3` smarter recent-changes memory. Completed.
   Improve the `recently changed` layer with better step summaries and direct jump-back affordances.

### PR2: Review And Handoff Refinement

7. `PR2.1` compare UX by wizard areas. Completed.
   Reframe comparison output so it groups differences by guided wizard areas instead of only by raw metadata, policies, and preferences.

8. `PR2.2` stronger clone-and-adjust handoff. Completed.
   After cloning, highlight the areas that usually deserve review in derived profiles so the user starts from the most likely adjustments.

9. `PR2.3` clearer lifecycle review visuals.
   Make lifecycle review easier to scan without turning it into a heavyweight audit log.

### PR3: Advanced Experience Refinement

10. `PR3.1` more targeted review-to-advanced jumps. Completed.
    Take users from review and drill-down surfaces into the most relevant advanced area instead of into advanced mode in general.

11. `PR3.2` simpler advanced entry for first-time users.
    Further reduce the chance that someone enters advanced mode too early when guided mode already covers the task.

12. `PR3.3` richer advanced review strip.
    Make the advanced-side review strip explain not just state, but also the main reason something is blocked or not ready.

### PR4: Trust And Quality

13. `PR4.1` expanded UX regression coverage. Completed.
    Add more regression protection around compare, clone, lifecycle review, recent changes, and the newer workflow checklist surfaces.

14. `PR4.2` accessibility follow-up pass. Completed.
    Do a final keyboard and assistive-tech pass across grouped controls, disclosure panels, and jump flows.

15. `PR4.3` viewport regression pack. Completed.
    Lock in the current mobile and narrow-screen quality with a dedicated regression check set.

### Recommended Order For Post-roadmap Backlog

All currently defined post-roadmap backlog items are completed.

## Next Product Backlog

This backlog starts after the completed redesign roadmap and after the completed post-roadmap polish layer. It is intentionally product-facing again.

### PB0: Guided Productivity

1. Preset diff preview.
   Show what a baseline, scenario, or major preset will change before the user commits to it.

2. Step-level undo and reset.
   Let a person roll back the current step or reset only one area without losing the rest of the profile.

3. Cross-step change memory.
   Surface a small `recently changed` summary so users can see what changed across the last few steps without jumping to export.

### PB1: Review And Handoff

4. Shareable guided summary.
   Create a concise exportable summary of the profile in human language for review by teammates who do not want to read JSON or YAML.

5. Stronger export explainability.
   Make the finish step show not only readiness, but also `what changed since last save`, `what this handoff contains`, and `what still lives only in Advanced document`.

6. Advanced review drill-down.
   Let users open a tighter review surface for advanced-only items, deprecated keys, and unknown keys without leaving the finish flow entirely.

### PB2: Policy Coverage Strategy

7. Coverage prioritization by external enterprise evidence.
   When local profile data is weak or absent, rank future coverage by official Firefox Enterprise signals, recurring enterprise scenarios, and UX fit instead of by schema adjacency alone.
   Completed on 2026-04-04 via [`docs/profile_wizard_coverage_priority_register_2026-04-04.md`](./profile_wizard_coverage_priority_register_2026-04-04.md), which records cluster priority, wizard-fit decisions, and the recommended execution order.

8. Guided coverage for priority enterprise clusters.
   Use that ranking to grow guided mode in the next high-value scenario bands rather than by adding isolated one-off controls.

9. Advanced-only boundary register.
   Keep a deliberate list of policies and policy shapes that should remain handoff-only or advanced-only, so the wizard does not regress into a schema mirror.

### PB2 Priority Order

1. `PB2.8a` kiosk and shared-device profiles.
   Prioritize a stronger task-first path for kiosk, lab, and shared-device setups by combining site allow/block rules, homepage/startup posture, private-session behavior, and cleanup on shutdown.

2. `PB2.8b` certificates, trust, and enterprise authentication.
   Expand guided coverage for enterprise roots, certificate trust posture, and common authentication scenarios such as SPNEGO/NTLM/delegation.

3. `PB2.8c` extensions rollout governance.
   Continue improving install posture, origin allowlists, managed rollouts, and curated extension packs before going deeper into niche extension dictionaries.

4. `PB2.8d` privacy and security hardening bundles.
   Keep growing opinionated hardening bundles around telemetry, studies, HTTPS-only, shutdown cleanup, and adjacent privacy controls rather than exposing every raw toggle.

5. `PB2.8e` updates and browser upkeep.
   Add stronger guided decisions for update posture, release management expectations, and day-to-day browser upkeep controls.
   Completed on 2026-04-04 with an upkeep workflow layer over existing step-2 guided controls.

6. `PB2.8f` site access and intranet routing.
   Improve task-first entry for blocked sites, exceptions, protocol/file handlers, and intranet-oriented navigation behavior.
   Completed on 2026-04-04 with a site-access workflow layer that unifies blocked sites, handler rules, and intranet-routing handoff over the existing guided controls.

7. `PB2.8g` home, startup, and search surfaces.
   Keep these as meaningful user-facing experience controls, but behind the more operationally important enterprise clusters above.
   Completed on 2026-04-04 with home/startup and search workflow layers that unify homepage, landing surfaces, Firefox Home, managed engines, and Firefox Suggest over the existing guided controls.

8. `PB2.8h` language and locale governance.
   Treat locale, translation, and language management as a narrower enterprise band that follows the broader operational clusters.
   Completed on 2026-04-04 with a language governance workflow layer over requested locales and translation posture, while keeping the AI step as a separate adjacent handoff.

9. `PB2.8i` AI surface controls.
   Keep AI in guided mode at the surface and posture level, but continue to treat provider/model detail as handoff-heavy until it forms a stronger recurring admin scenario.
   Completed on 2026-04-04 with an AI governance workflow layer over built-in AI availability and smart browser surfaces, while keeping provider/model detail intentionally handoff-heavy.

### PB2 Decision Rules

- Promote a cluster into guided mode when Mozilla enterprise documentation and product judgment both suggest a recurring admin task and when the cluster can be expressed as a clear scenario-first flow.
- Keep a cluster as `quick focus + handoff` when the user task is real but the underlying shape is still too irregular for a stable guided UI.
- Keep a cluster advanced-only when it is low-frequency, highly technical, structurally open-ended, or likely to bloat the wizard more than it helps.
- Prefer growing guided mode by scenario bundles such as `kiosk`, `corp trust`, or `managed add-on rollout`, not by copying individual schema branches one by one.
- Any `PB2.8x` slice is only complete when guided controls, coverage accounting, step-level coverage messaging, and final review/export summaries all reflect the new guided coverage consistently.
- Expanding guided coverage must not remove the corresponding technical path; promote the scenario into guided mode, but keep the advanced route as the canonical full-control fallback.
- `PB2.9` is tracked in [`docs/profile_wizard_advanced_only_boundaries_2026-04-04.md`](./profile_wizard_advanced_only_boundaries_2026-04-04.md) and should stay visible in finish-step guidance whenever an area remains intentionally advanced-only.
- `PB2.7` is tracked in [`docs/profile_wizard_coverage_priority_register_2026-04-04.md`](./profile_wizard_coverage_priority_register_2026-04-04.md) and should be the default planning input whenever future guided coverage is discussed.

### PB3: Multi-profile Workflows

10. Compare two profiles. Completed on 2026-04-04.
    Added a task-first diff for admins who need to review the currently open profile against another saved profile, using one canonical profile snapshot diff so future policy and preference changes flow into comparison automatically.

11. Clone-and-adjust flow. Completed on 2026-04-04.
    Added an explicit `Clone and adjust` path from the library, kept provenance in one shared clone-source state, and surfaced `based on X` context consistently in the workspace, wizard, and export summary.

12. Review lifecycle history. Completed on 2026-04-04.
    Added a trusted lifecycle review based on real profile metadata plus a narrow restore-in-session marker, so the UI shows creation, latest save, current state, origin, and recent restore context without pretending to be a full audit log.

## Recommended Order After Consolidation

1. `PB0.1` preset diff preview
2. `PB1.4` shareable guided summary
3. `PB0.2` step-level undo and reset
4. `PB1.5` stronger export explainability
5. `PB2.7` coverage prioritization by external enterprise evidence
6. `PB3.10` compare two profiles
   Completed on 2026-04-04 with one canonical snapshot diff so future profile-shape changes flow into comparison automatically.

## New Definition Of Done

- Guided mode not only explains configuration, but also helps people predict the impact of their choices.
- Review and handoff work for people who never open the full document.
- Coverage expansion is driven by real value, not by the temptation to mirror the whole schema.
- Advanced mode remains deliberate and useful, not a dumping ground.
- When a policy cluster moves into guided mode, it stops being counted as `advanced-only` in coverage and finish-line summaries.
