# BPM 0.9.3 Topic Scope Taxonomy And Decision Precedence

Backlog item: `BPM093-M8-01`
Status: accepted architecture contract; no scope gate, route, model, retrieval or network action is
implemented by this task.

The taxonomy makes the controller—not a prompt or guard model—the authority that classifies a chat
request before retrieval, inference or optional web use. It applies to all six active locales and
accepts code-switched product language and technical tokens without allowing cross-locale retrieval.

Allowed intent groups cover BPM product workflows, managed Firefox policy questions, BPM operation
and administration, documented API/CIS workflows, and bounded same-topic follow-ups. A concrete
anchor authorizes only same-locale evidence lookup; it never guarantees an answer. A policy-shaped
unknown identifier is therefore allowed to reach evidence lookup and becomes an abstention if the
evidence is absent or inadequate.

Clarification is reserved for adjacent requests: generic Firefox questions, underspecified
references, active-chat greetings and unclear policy context. Refusal applies first to clearly
unrelated requests, destructive or privileged actions, and attempts to override controls or extract
instructions—even when the text also mentions BPM or Firefox. An answer is possible only after an
allowed request receives answer-ready evidence; ambiguous evidence can clarify and insufficient
evidence abstains.

M8-02 will implement deterministic features and thresholds from this taxonomy; M8-03 will add the
multilingual adversarial fixture set. The normative machine-readable contract is
`documentation/config/bpm-topic-scope-taxonomy-0.9.3.json`.
