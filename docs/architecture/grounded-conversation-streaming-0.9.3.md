# BPM 0.9.3 Grounded Conversation Streaming, Cancellation, And Backpressure

Backlog item: `BPM093-M7-05`
Status: implemented in memory only; no HTTP route or browser UI is added by this task.

`ConversationStreamController` is the transport-neutral controller over the existing validated
conversation pipeline. M10 will expose the frozen same-origin SSE surface; this module neither
imports FastAPI nor creates a listener. The controller starts no model independently: it invokes
the existing orchestrator and its existing worker-cancellation boundary.

## Bounded Lifecycle

The controller accepts one active request and at most one queued request. A third request is
rejected with `assistant_busy` before it can allocate retrieval or inference work. Each accepted
opaque request receives monotonically increasing epochs and only these event kinds:

- `accepted`;
- `progress` for `scope_check`, `evidence_check`, `generating`, or `validating`;
- one terminal `final`, `cancelled`, or `error` event.

Events carry localized message/action keys and opaque IDs. Final text is the already validated,
citation-bound result from M7-04. The controller never streams model tokens, prompts, evidence,
internal citation IDs, paths, hashes, exceptions, timings, or worker diagnostics. Partial output
is never a `final` answer: cancellation and timeout events set `incomplete: true` and contain no
answer text.

## Stop, Timeout, And Backpressure

An explicit stop or stream disconnect atomically marks the request cancelled, emits one terminal
`assistant_cancelled` event, and invokes the M6 worker process-group cancellation. A later worker
return cannot overwrite that terminal result. A 300-second whole-request deadline takes the same
cancellation path and emits one incomplete `assistant_timeout` error. The active slot remains held
until the worker returns, preventing a replacement generation from running concurrently.

Each request keeps at most eight pending events and the controller retains at most four completed
records in process memory. Slow consumers discard stale nonterminal events rather than blocking
inference; no queue can grow with model output. Validated answer citations are represented only by
fresh opaque source handles scoped to the completed request. The handles are ready for the frozen
M7-01 source operation but do not expose the underlying evidence identity.

The normative machine-readable contract is
`documentation/config/grounded-conversation-streaming-contract-0.9.3.json`.
