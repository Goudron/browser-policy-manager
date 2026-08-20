# Firefox Schema Conversion UI Copy And Interaction Contract (BPM 0.9.5.1)

Status: active normative target; implementation begins in `BPM095-M5-01`.

## Purpose and non-implementation boundary

This contract classifies the new recommendation, preview, confirmation, apply,
success, unavailable, and recovery states required by the Firefox schema
lifecycle and pairwise-conversion work. Its machine-readable companion is
[`firefox-schema-conversion-ui-copy-interaction-contract-0.9.5.json`](firefox-schema-conversion-ui-copy-interaction-contract-0.9.5.json),
validated by
[`schemas/firefox-schema-conversion-ui-interaction-contract-v1.schema.json`](schemas/firefox-schema-conversion-ui-interaction-contract-v1.schema.json).
The JSON fixture is normative for stable state IDs, English source keys and
copy, surface and locale ownership, error mapping, accessibility, recovery,
and privacy constraints.

M2-06 does not implement a template, browser module, API, locale catalog,
schema artifact, converter, migration, help target, or generated asset. M3
owns the four-channel product catalog, M4 owns preview/apply behavior, M5 owns
the product UI and six localized catalogs, and M6 owns retired-ESR migration.
The fixture describes target interaction states; it does not claim that the
current three-channel runtime can render them.

## Inherited UI-copy rule

The active
[`ui-copy-classification-contract-0.9.2.md`](ui-copy-classification-contract-0.9.2.md)
remains active and is not superseded. New schema-conversion labels and current
states are `essential`; consequences, blockers, validation, unavailable
reasons, accessible descriptions, and recovery are `safety-accessibility`.
When one node has both meanings, safety and recovery win.

No state in this contract is routine explanatory narration. A shorter future
string is acceptable only if its exact action, current state, consequence,
accessible meaning, and recovery remain next to the action. None may be
removed under `remove-explanation`, and none may be replaced by a help link.

## Recommendation and retirement are different products

An active saved profile on a **supported older ESR** line receives a manual
recommendation to the lifecycle catalog's exact **latest supported ESR**
artifact. In this contract both ESR 115.39 and ESR 140.13 recommend ESR 153.0.
Opening that recommendation performs no write. It leads to a preview; only a
current applicable preview followed by explicit confirmation can apply.

Release 153, ESR 153.0, unknown, retired, unsaved, and archived/deleted
profiles do not receive this recommendation. Their truthful current state or
recovery state remains visible; the UI must not render a disabled or invented
recommendation merely to fill the space.

Retirement is not the same target rule. ESR 115's immediate retirement
successor is ESR 140 while ESR 140 is supported; ESR 140's successor is ESR
153. The retired-ESR state is operator/upgrade guidance only. It cannot offer
a manual profile conversion, invoke an HTTP apply operation, or imply that a
runtime read will migrate data. Alembic remains the sole retirement writer.

## Surface ownership

The conversion flow extends the five existing product surfaces; it does not
create a sixth editor.

| Owner | UI responsibility | Apply boundary |
| --- | --- | --- |
| Library | Show one compact eligible-row recommendation and enter preview without mutation. Filtering, pagination, or locale changes cannot duplicate the action. | Never applies directly. |
| Compare | Remain read-only. It may link an authorized selected profile to preview. | Never confirms or applies. |
| Guided | Preserve saved/dirty state and hand off an active saved profile to review. | Shared review applies only after the unsaved-work gate. |
| All settings | Preserve editing and focus state, then hand off to review. | Shared review applies only after the unsaved-work gate. |
| JSON | Preserve Monaco dirty and validation state, then hand off to review. | Shared review applies only after the explicit save/discard/cancel decision. |
| Shared review | A future route-owned component used by those surfaces owns target selection, preview, blocker summary, confirmation, apply, success, and recovery. | It may submit exactly one current confirmed plan. It is not an editor. |

The shared editor chrome remains the current-profile and current-channel
context owner. A surface-specific entry action retains its return/focus target;
the conversion review owns no policy editing and cannot overwrite browser-local
work.

## Stable states

The exact source keys, English strings, owners, accessible names/descriptions,
focus rules, confirmation class, recovery action, telemetry fields, and error
codes live in the JSON fixture. This table is the concise interaction map.

| Stable state ID | Trigger and retained meaning | Apply/recovery rule |
| --- | --- | --- |
| `schema-conversion.older-esr-recommendation` | Active saved supported older ESR; name exact localized source and ESR 153 target and say that preview does not write. | Open review only. |
| `schema-conversion.recommendation-not-eligible` | Release/latest/unknown/retired/unsaved/inactive states. | Render no misleading recommendation; keep the actual state owner. |
| `schema-conversion.manual-target-selection` | User selects a distinct supported/selectable exact artifact. | Selection refreshes preview and never writes. |
| `schema-conversion.preview-pending` | Preview request is in flight. | Prevent duplicates; keep Cancel available; announce once. |
| `schema-conversion.preview-available` | `applicable=true`, target validation valid, zero blockers. | Show aggregate unchanged/transformed/warning/compliance meaning; enable explicit confirmation. |
| `schema-conversion.preview-blocked` | One or more blockers or invalid target candidate. | Apply is unavailable; focus and announce blocker summary; resolve or choose another target. |
| `schema-conversion.preview-unavailable` | Exact source/target artifact cannot produce preview, including planned ESR 115 before M3 promotion. | No confirmation; retry only after exact artifact recovery or choose another target. |
| `schema-conversion.unsaved-work-decision` | Guided, All settings, or JSON has unsaved browser-local work. | Save and preview, discard and preview, or cancel; never overwrite silently. |
| `schema-conversion.confirmation-ready` | Applicable preview and all bound identities remain current. | State exact saved fields affected and preserved; require one explicit apply action. |
| `schema-conversion.apply-in-progress` | Confirmed apply is in flight. | Disable close, target change, cancellation, and duplicate submission until a terminal result. Do not infer success from timeout. |
| `schema-conversion.apply-success` | Atomic apply succeeded and the exact result revision was reloaded. | Announce target/revision, then offer a user-controlled return to authoritative saved state. |
| `schema-conversion.stale-revision` | `conversion_revision_stale`. | Remove stale Apply, reload, and create a fresh preview. |
| `schema-conversion.plan-or-validation-changed` | Source, plan, schema, or recipe identity changed. | Invalidate confirmation and require a newly reviewed preview. |
| `schema-conversion.source-not-active` | Profile is missing, archived, deleted, or otherwise inactive for manual conversion. | Restore through the lifecycle owner or return to Library; then preview anew. |
| `schema-conversion.target-unavailable` | Target is unknown, retired, unsupported, or missing. | Choose an exact currently supported available target; never default silently. |
| `schema-conversion.source-invalid` | Source document/channel/schema cannot support conversion. | Use validation or operator recovery; no Apply. |
| `schema-conversion.apply-failed-retry` | Apply failed with the server guarantee `mutation=none`. | Reload authoritative saved state and obtain a fresh preview; no automatic retry. |
| `schema-conversion.retirement-operator-boundary` | Unupgraded database requires retired-ESR Alembic migration. | Profile routes remain unavailable/read-only; show backup/preflight/upgrade guidance, never a manual recommendation. |

`apply-in-progress` is allowed because M2-04 defines an atomic server operation
with a terminal success or nonmutating error. It is not an optimistic-success
state. The UI must keep the operation singular, announce a stable pending
state once, and wait for the response before changing the rendered profile.

## Error and validation mapping

The fixture exhaustively maps the M2-04 manual conversion failure vocabulary.
Its state-level groups are:

- missing/inactive source: `conversion_profile_not_found`,
  `conversion_source_not_active`;
- lifecycle source/target: `schema_channel_unknown`,
  `schema_channel_retired`, `schema_channel_retired_requires_migration`;
- unsupported/identical target: `conversion_target_unsupported`,
  `conversion_target_identical`;
- invalid or missing exact schema: `conversion_source_invalid`,
  `conversion_source_schema_missing`, `conversion_target_schema_missing`;
- stale reviewed input: `conversion_revision_stale`,
  `conversion_source_identity_stale`, `conversion_plan_stale`,
  `conversion_schema_identity_stale`, `conversion_recipe_registry_stale`;
- blocked/apply failure: `conversion_plan_blocked`,
  `conversion_apply_failed`.

Every one of those errors has `mutation=none`. UI copy must say that nothing
was converted, disable the reviewed Apply action, and identify the next local
recovery. A retry that can change the plan always starts with a fresh preview;
the client never resubmits an old revision or digest.

M2-05 errors are classified only into the operator boundary. Static-gate,
manifest, backup, preflight, transaction, partial-state, and downgrade codes
never become profile-level manual actions. In particular,
`retirement_partial_state_detected` requires a new clean candidate restored
from verified backup, and `retirement_downgrade_unsupported` is not a button
that reverses converted profiles.

## Accessibility contract

Every state supplies a localized accessible name and associated localized
description. A visible primary label cannot stand in for a consequence when
the consequence controls safe use.

1. Opening review focuses its heading. Changing a target keeps focus on the
   selector while a polite status announces the refreshed preview.
2. Pending work is a single polite status and an `aria-busy` review region;
   it must not repeatedly announce timers or progress decoration.
3. Blocked, unavailable, stale, invalid, and failed terminal states are alerts
   and receive focus at their summary. Recovery controls follow immediately in
   logical order.
4. Confirmation uses a modal only if focus is trapped, Escape is Cancel, the
   opener regains focus on cancel, and unrelated Enter presses cannot apply.
5. Apply is absent from the accessibility tree when it is not permitted. A
   disabled control, when retained for context, is programmatically associated
   with the exact blocker.
6. Success is announced politely and never auto-redirects. The user chooses
   when to return to the originating surface.
7. Policy values, dynamic keys, and sensitive pointers cannot be placed in
   accessible labels, DOM data attributes, URLs, or focus targets.

M5 browser evidence must cover keyboard-only use, screen-reader names and
descriptions, focus restoration, live-region announcements, long localized
labels, narrow viewports, and both themes.

## English source and six-locale ownership

The fixture plans `profiles.schema_conversion_*` and
`profiles.schema_retirement_*` keys; it does not add them to catalogs yet.
English (`en`) is the reviewed source. `ru`, `de`, `zh-CN`, `fr`, and `es-ES`
are separate human-reviewed translations owned by the project maintainer
under [`../locale_ownership_2026-06-01.md`](../locale_ownership_2026-06-01.md).
English sentence structure is not a translation template.

M5-04 must place shared review and state copy in the smallest appropriate
source namespace and keep Library/Guided/All settings/JSON entry copy in its
surface namespace. All six source catalogs change together, placeholders and
technical identifiers remain identical, locale-specific terminology is
reviewed, and runtime catalogs are rebuilt through their owner. No final
non-English translation is approved by this M2 fixture.

## Help and local consequence

The five existing manifest-owned surface targets remain:

- Library: `topic:ug-task-use-profile-library`;
- Compare: `topic:ug-task-compare-profiles`;
- Guided: `topic:ug-task-use-guided-editor`;
- All settings: `topic:ug-task-use-all-settings`;
- JSON: `topic:ug-task-use-json-editor`.

No new help target or circled-information control is authorized here. A future
link requires an explicit source-key owner, stable manifest target, six-locale
destination, localized accessible name, keyboard reachability, and the local
action/consequence/recovery copy still present. An external URL, generic
“learn more,” or documentation-only explanation cannot replace the inline
state.

## Privacy and telemetry

Plan and error payloads can reveal enterprise configuration even without raw
values. UI telemetry, URLs, client storage, DOM data attributes, and logs must
omit policy values and presence, policy IDs, JSON pointers, dynamic keys,
profile ID/name/description, compliance values/notes, full plan/document
digests, and localized copy.

Allowed telemetry is locale-neutral and aggregate: outcome/error code, exact
source/target artifact or line IDs, surface ID, compatibility status, and
aggregate counts. The server never accepts localized reason text from the
client and localized text never participates in preview identity. The UI does
not reconstruct or render raw values from a conversion plan that deliberately
omits them.

## Handoff and verification

M5 implementation must consume the stable IDs rather than infer state from
English text, HTTP status alone, tuple order, or the presence of a button.
Focused tests must reject a state missing its local consequence, accessible
name/description, focus behavior, recovery, locale owner, error mapping, or
manifest-owned help boundary. M5-05 adds semantic DOM, module, and real-browser
evidence; this M2 contract changes no current UI behavior.
