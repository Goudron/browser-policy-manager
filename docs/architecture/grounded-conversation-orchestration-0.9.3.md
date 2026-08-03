# BPM 0.9.3 Grounded Conversation Orchestration

Backlog item: `BPM093-M7-02`
Status: implemented without an HTTP route or browser control.

`GroundedConversationOrchestrator` is the only local pipeline that may connect an admitted user-chat
request to E5 retrieval, M5 evidence and the M6 worker. It is not a FastAPI router and it does not
import or invoke BPM's deterministic documentation search.

The fixed sequence is: bounded request validation, M8 scope decision, optional-web consent boundary,
same-locale E5 query encoding, exact local retrieval, M5 evidence packing, local worker generation,
M7-04 parsing/support validation, and server-side citation binding. Every stage has an explicit
dependency-injected boundary. This prevents an incomplete M8 scope classifier, E5 runtime loader, or
output parser from silently granting authority: missing or invalid results stop with a stable
non-answer outcome before the next sensitive stage.

Only the exact request locale may reach the retriever. A mismatched retrieval result, unavailable
artifacts, empty/stale/contradictory/over-budget evidence, invalid request or scope denial
never invokes the worker. The worker receives M5's bounded, same-locale canonical JSON Lines only.
The output parser is required to return a terminal disposition; an answer additionally requires
nonempty text and unique citation IDs that belong to the evidence pack. Neither model-created nor
client-provided URLs are resolved.

`request_web` remains a non-network, explicit consent boundary until M9 provides a reviewed provider:
after scope admission it returns `assistant_web_not_available` without encoding, retrieval, worker or
provider work. Normal local requests make no network call. The module has no persistence, session
state, endpoint, browser control, external provider, scope classifier or E5 runtime loader; their
later owners plug into the frozen protocols.

The normative machine-readable contract is
`documentation/config/grounded-conversation-orchestration-contract-0.9.3.json`.
