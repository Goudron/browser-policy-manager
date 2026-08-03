# BPM 0.9.3 Grounded Conversation Context

Backlog item: `BPM093-M7-03`
Status: implemented as memory-only controller state; no HTTP, browser storage or persistence.

`ConversationContextStore` creates an opaque controller-owned session for exactly one BPM locale,
browser tab and product version. It retains at most eight completed user-question/assistant-answer
pairs (sixteen chronological entries), eight resolved entities of at most 120 characters, and the
current evidence topic identities. Retention is only in the BPM process: no cookie value, database
row, disk artifact, telemetry, model summary or browser storage is created. Tab-aware Clear removes
the complete exact session and its handles.

For a same-locale follow-up, only the resolved entities from previously accepted local evidence are
added to the fresh retrieval query. The fresh request still exact-scans the active locale and creates
a new M5 evidence pack. Prior citation IDs are never accepted as citations for a new answer.

If current accepted evidence has no topic in common with the session, stale resolved entities are
discarded before the worker sees the new request while the bounded dialogue remains available. The
new request still gets fresh same-locale retrieval and evidence; prior citation IDs are never reused.
A locale mismatch rejects the context. A BPM version mismatch deletes the session before retrieval or
inference. These rules preserve a real support conversation without carrying stale entities or
citations across product/topic changes.

The normative machine-readable contract is
`documentation/config/grounded-conversation-context-contract-0.9.3.json`.
