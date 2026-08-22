# BPM 0.9.6 Atomic Profile Preparation Lifecycle Contract

Date: 2026-08-20

Backlog item: `BPM096-M2-03`

Status: active planning contract; it deliberately makes no current runtime, API, database, or
rendered-workflow claim.

## Purpose and boundary

This contract freezes the lifecycle shared by the future create and duplicate preparation modes.
It supersedes the *target* draft behavior only when M3/M4 implement it: it does not alter today's
`GET /profiles/new`, generic `POST /api/profiles`, `ProfileService.create`, or the saved-profile
conversion apply endpoint.  In particular, M3 must add dedicated preparation commands rather than
turn generic `ProfileCreate` or generic `PATCH` into an implicit baseline-composition or duplicate
operation.

In this document, a **profile row** means a row in `profiles`.  A duplicate **source snapshot** is
every persisted source field, including identity, name/casefold value, description, schema, flags,
compliance/provenance, revision, lifecycle marker, and database-managed timestamps.  A source
snapshot must compare byte-for-byte/equivalently before and after an attempted duplicate; no
idempotency, planning, audit, or navigation state may be written to the source.

M2-04 owns the durable baseline envelope and M2-05 owns exact duplicate composition and conversion
identities.  This contract owns when those decisions are checked and when their result may become a
saved row.

## Preparation form and read boundary

`/profiles/new` is one preparation surface.  Create mode has no source.  Duplicate mode has one
server-resolved source identity and its expected revision; a missing, archived/ineligible, or
unreadable source is an explicit duplicate-unavailable state, never a silent fallback to create
mode.  A legacy `clone_name` query value is not an authority, reservation, or saved draft in the
target flow.  `include_deleted` never overrides the server's duplicate-eligibility rule.

The in-browser form is only unsaved input, not a profile or a partial profile lifecycle.  Its
permitted submit fields are a profile name, target schema identity, starter identity, CIS
baseline identity, mode, and, for duplicate mode, source ID plus expected source revision.  The
browser also creates one opaque high-entropy `preparation_idempotency_key` for one logical terminal
activation.  It must not submit flags, a composed document, compliance, provenance, a conversion
candidate, or a client-selected destination as authority.

The initial GET, reload, Back, source-state refresh, and read-only duplicate planning do **not**
write a profile row, reserve a name, allocate an idempotency record, persist a plan, or change the
source.  They may read catalogs and the source facts needed to render the form.  M4 must keep the
full Guided editor and policy document out of this preparation response.

The visible form state is `ready`, `submitting`, `rejected`, or `succeeded`.  `submitting` binds
the exact input fingerprint and disables a second activation; `rejected` retains the submitted
field values and associates the localized, recoverable condition with the relevant control;
`succeeded` immediately leaves the form for the one destination below.  A page reload during
`submitting` is a retry/reconciliation problem, not permission to generate a second request key.
M2-02 remains normative for the associated validation, stale-source, atomicity, and recovery copy.

## Server-owned command and validation

M3-04 and M3-05 provide distinct dedicated create and duplicate commands.  Both commands derive
the candidate profile on the server.  Before any insert, and again inside the write transaction
where a condition can race, the service must validate:

| Check | Create | Duplicate |
| --- | --- | --- |
| Request shape, nonblank/valid normalized name, and idempotency key | required | required |
| Current supported schema, starter, and CIS identities | required | required |
| Server-derived target document, provenance, and target validation | required | required |
| Source existence, eligibility, complete snapshot, and expected revision | not applicable | required |
| Same-schema preservation or applicable current cross-schema plan/composition | not applicable | required |
| Database-backed name uniqueness and idempotency-key/fingerprint uniqueness | required | required |

No client preflight, loaded Library name list, GET, or preview reserves a name or authorizes a
write.  The database uniqueness boundary decides concurrent names.  A different request that loses
that race returns `preparation_name_conflict`; it inserts no profile row.  The UI may offer an
optimistic warning, but it is never authoritative.

For a duplicate, the service locks or otherwise conditionally verifies the current source before
deriving the candidate and immediately before insertion.  If the expected revision, lifecycle,
schema identity, source document/compliance/provenance evidence, conversion applicability, or
composition result is no longer current, it rejects instead of using an older preview.  A target
schema is never created by relabeling the source, and a conversion plan is never applied to the
source row.

## Atomic outcome and navigation

The accepted command has one transaction boundary.  It rederives all authoritative data, confirms
the duplicate source if present, checks the database constraints, inserts one complete saved target,
and commits once.  There is no `initializing`, half-composed, cleanup-later, or visible draft row.
Any exception, constraint failure, validation rejection, or failed commit rolls back the entire
attempt before a terminal failure is returned.

A successful command returns one saved profile ID and the server-derived Guided destination
`/profiles/{profile_id}/edit`.  The browser replaces the preparation tab with exactly that path
only after the successful response; it does not open a Guided draft, navigate on a rejected result,
or derive a destination from a source/query/return URL.  One logical success therefore has one new
saved profile and one deterministic Guided-editor destination.  The Library tab is not navigated.

Every terminal rejection has a net delta of zero profile rows.  For duplicate mode, every terminal
rejection **and every success** leaves the complete source snapshot unchanged.  These requirements
cover invalid names, unavailable catalogs, source failures, conversion/composition blockers, name
conflicts, idempotency misuse, race losses, and infrastructure exceptions.

## Retry, idempotency, and interruption

The idempotency key is scoped to the current profile library (and to the authenticated library scope
if authorization is introduced).  Its server fingerprint is a canonical, value-safe digest of mode,
normalized name, selected catalog identities, duplicate source ID/revision when applicable, and
the reviewed plan/composition identities required by M2-04/M2-05.  The key is not scoped merely to
a browser tab or a best-effort timer.

The successful target persists the key and fingerprint under a uniqueness constraint in the same
transaction as the target row.  This is the idempotency boundary: the same key and fingerprint must
return the original successful result and original destination without a second insert; the same
key with a different fingerprint must return `preparation_idempotency_key_reused` and insert
nothing.  A terminal rejection persists neither a profile row nor a durable failed-request marker,
so it cannot leave a hidden row behind.  A concurrent same-key command must wait/reconcile with the
one command or return an explicit in-progress state; it must never start a second insertion.

An interruption before commit is rolled back and is a retryable non-success with zero profile rows.
An interruption after commit but before the client receives a response is **not** a terminal
failure: its client-visible result is indeterminate, and retrying the same key/fingerprint must
reveal the one committed success.  The server must never report a terminal failure after committing
the target.  The client must not mint a new key merely because a request timed out, was cancelled,
or the tab reloaded.

## Normative compact fixture

<!-- bpm096-atomic-preparation-contract-v1 -->
```json
{
  "contract_id": "bpm096-atomic-profile-preparation",
  "contract_version": 1,
  "status": "planning-only-no-runtime-change",
  "preparation_route": "/profiles/new",
  "modes": {
    "create": {"source_required": false, "terminal_action": "create"},
    "duplicate": {"source_required": true, "terminal_action": "duplicate"}
  },
  "form": {
    "unsaved_only": true,
    "get_profile_rows_written": 0,
    "get_reserves_name": false,
    "get_persists_idempotency": false,
    "client_submit_fields": [
      "mode",
      "name",
      "target_schema_id",
      "starter_id",
      "cis_baseline_id",
      "source_id",
      "expected_source_revision",
      "preparation_idempotency_key"
    ],
    "client_forbidden_authority": [
      "flags",
      "composed_document",
      "compliance",
      "provenance",
      "conversion_candidate",
      "destination"
    ]
  },
  "write_boundary": {
    "generic_create_or_patch_authorized": false,
    "server_rederives_candidate": true,
    "single_transaction": true,
    "success_new_profile_rows": 1,
    "terminal_failure_new_profile_rows": 0,
    "source_mutation": "forbidden"
  },
  "success": {
    "saved_profile": true,
    "destination_template": "/profiles/{profile_id}/edit",
    "navigation_after_success_only": true,
    "navigation_count": 1
  },
  "idempotency": {
    "key_scope": "profile-library",
    "same_key_same_fingerprint": "return-original-success-without-insert",
    "same_key_different_fingerprint": "preparation_idempotency_key_reused",
    "terminal_failure_persistence": "none",
    "post_commit_response_loss": "indeterminate-reconcile-same-key"
  },
  "terminal_failures": [
    "preparation_request_invalid",
    "preparation_schema_unavailable",
    "preparation_starter_unavailable",
    "preparation_cis_unavailable",
    "preparation_candidate_invalid",
    "preparation_name_conflict",
    "preparation_duplicate_source_not_found",
    "preparation_duplicate_source_not_eligible",
    "preparation_source_stale",
    "preparation_conversion_blocked",
    "preparation_composition_blocked",
    "preparation_idempotency_key_reused",
    "preparation_transaction_failed"
  ],
  "interruption": [
    {"point": "before-transaction", "profile_rows": 0, "source_changed": false},
    {"point": "before-commit", "profile_rows": 0, "source_changed": false},
    {"point": "after-commit-before-response", "profile_rows": 1, "source_changed": false}
  ]
}
```

## Delivery ownership and proof

- M3-01 supplies the immutable storage change needed for successful-key/fingerprint persistence;
  M3-02 supplies server-owned create composition; M3-03 supplies read-only duplicate planning;
  M3-04/M3-05 implement the two commands; M3-06 publishes the OpenAPI/error envelope; and M3-07
  proves rollback, same-key replay, name races, stale sources, and interruption on SQLite and
  PostgreSQL.
- M4-01/M4-02 render the no-write form and source state; M4-03/M4-04 implement the submit and
  reconciliation state machine; M4-05 replaces legacy clone-query/draft entrypoints; M4-06 proves
  browser navigation, Back/reload, accessibility, and terminal failures.
- The focused contract guard validates the fixture's nonmutation, exact-one, deterministic-route,
  idempotency, and interruption semantics.  It is intentionally not a substitute for M3/M4
  runtime tests, because this milestone must not implement future API or UI behavior.
