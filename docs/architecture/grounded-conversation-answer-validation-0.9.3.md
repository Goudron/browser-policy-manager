# BPM 0.9.3 Grounded Answer And Citation Validation

Backlog item: `BPM093-M13-06`
Status: implemented without HTTP or browser rendering.

The controller passes the worker a fixed output-schema instruction and the untrusted user question in
separate JSON fields. A usable model response is exactly one JSON object with `disposition` and
`sections`. For an answer, `sections` is a bounded nonempty ordered list of `{text, citation_ids}`
objects. Each section must be plain text in the model's own words and carry one or more unique
accepted citation identities; the server composes the final answer by joining the validated sections.
Clarify, abstain and refuse have an empty section list. Markup-like tags, control characters,
extra/missing fields, malformed JSON and unsupported values are not accepted.

`GenerationResponseValidator` resolves every section citation exclusively against the current M5
EvidencePack. It verifies the exact topic/anchor identity and a relative local `/help/{locale}/` URL
with no host, scheme, query, fragment, traversal or percent-encoded path. A URL or anchor proposed by
the model is never resolved or returned as a source. The final orchestrator maps only those accepted
IDs back to local citations; raw chunks, vectors, scores, paths, hashes and model output remain
private. A normalized contiguous 96-character-or-longer extract from the evidence item cited by a
section is rejected. This prevents a retrieved chunk from being presented as a generated answer while
allowing short technical terms and commands where exact wording is necessary.

Malformed, unsupported, uncited or excessively extractive output is an empty terminal abstention.
The server never replaces it with a raw evidence excerpt. Thus untrusted generated prose cannot
become a confident BPM answer and a user never mistakes a retrieval dump for a model response.

For the one recoverable case—a response that otherwise passes schema, plain-text and current-citation
validation but copies a 96-character span—M13-06C permits one local rewrite attempt. The controller
keeps the first draft private, unloads the worker to discard its native context, then starts a fresh
worker with only that untrusted draft and the already-accepted citation IDs. It does not forward the
EvidencePack or dialogue. The second response is checked against the original EvidencePack with the
same citation, quotation and safety rules; a failed or still-extractive rewrite is an abstention.
Neither draft is logged, persisted or rendered.

The normative machine-readable contract is
`documentation/config/grounded-conversation-answer-validation-contract-0.9.3.json`.
