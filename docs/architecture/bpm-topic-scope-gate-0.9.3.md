# BPM 0.9.3 Pre-Generation Topic Scope Gate

Backlog item: `BPM093-M8-02`
Status: implemented without an HTTP route, browser UI, retrieval, LLM or network action.

`TopicScopeGate` consumes the reviewed M8-02 locale alias contract and produces only the existing
M7 `allow`, `clarify` or `refuse` decisions. It is injected into the M7 orchestration boundary, so
a refusal or clarification returns before E5 retrieval, evidence packing, the local worker or
optional web mode. It does not import or change deterministic documentation search.

The gate applies deterministic refusal aliases first. A destructive request, control-override
attempt or clear off-topic request remains refused even if it contains BPM or Firefox terms. The
reviewed adversarial patterns cover the six supported locales. For the sole purpose of detecting a
control override, it also makes one bounded percent, Unicode-escape or Base64 decode attempt before
matching; the decoded text is not passed to retrieval, evidence or the worker. It then allows
policy-shaped identifiers and reviewed BPM aliases, permits one unambiguous bounded context
follow-up, and clarifies generic Firefox, greeting and underspecified requests. Only a request with
no deterministic result reaches the injected local cosine similarity adapter. A score at least 0.82
allows, a score from 0.50 through 0.819 clarifies, and every missing, invalid or non-finite score
fails closed before retrieval.

`CosineScopeSimilarity` accepts a caller-owned local E5-sized 768-dimensional query encoder and one
fixed normalized centroid per supported locale. It has no model installation, listener, disk,
retrieval, ordinary-search, tool or network path. A later production composition supplies the
verified E5 adapter and locale centroids; the gate never falls back to another locale.

Allowed scope is authorization to inspect same-locale evidence, not an answer guarantee. The
evidence policy still returns clarification or abstention when current evidence is ambiguous or
missing. The normative machine-readable contract is
`documentation/config/bpm-topic-scope-gate-contract-0.9.3.json`.
