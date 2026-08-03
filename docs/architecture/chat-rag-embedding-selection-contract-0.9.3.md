# BPM 0.9.3 Chat-Only RAG Embedding Selection Contract

Date: 2026-07-29

Backlog item: `BPM093-M5-03B`

Status: **Accepted contract; it selects no model and changes no runtime.**

## Decision

RAG is an optional, explicitly enabled assistant capability for user chat. It is not a replacement,
fallback, reranker, or hybrid extension of the accepted M4 deterministic documentation search. The
ordinary search implementation neither calls RAG nor depends on its model, index, availability, or
external-source state.

For every chat request, retrieval uses only chunks in the active user locale. Cross-locale prose
retrieval and fallback are prohibited. An embedding candidate therefore is not evaluated against
ordinary-search relevance: a chat may retrieve less relevant material, but it must never turn an
uncertain result into an unsupported factual answer. Missing or insufficient local evidence leads
to abstention or clarification; displayed local claims require resolvable published citations.

## Candidate-selection boundary

`documentation/config/chat-rag-embedding-selection-contract-0.9.3.json` freezes the next
benchmark's source eligibility, six active locales, exact artifact metadata, same-locale rule,
checksum/license/runtime/resource evidence, citation readiness, no-evidence disposition, and
ordinary-search isolation. `BPM093-M5-03C` will evaluate at least two candidates under this
contract. A changed swap counter invalidates selection; a tie is no selection. The candidate report
may rank safe artifacts by same-locale evidence coverage, but it cannot call a lower coverage result
successful merely because it is more resource-efficient.

The earlier M5-03 and M5-03A dense-only and cross-language measurements remain reproducible
historical diagnostics. They do not decide the chat-only selection because their purpose differed.

## Optional external evidence

External sources are disabled by default. A later M7/M8 implementation may issue an external
request only after explicit user opt-in, reviewed provider/scope policy, and a visible
external-source state. Local BPM evidence is retrieved and labelled independently before any such
request; conflicts are not silently merged. External content never becomes a local chunk, embedding,
index, training input, or persistent chat knowledge, and every external claim has its own labelled
external citation.

## Verification

`documentation/tests/contract/test_chat_rag_embedding_selection_contract_0_9_3.py` rejects a
contract that reintroduces a dependency on ordinary search, cross-locale fallback, an uncited
factual answer, silent web access, or external content in local knowledge.
