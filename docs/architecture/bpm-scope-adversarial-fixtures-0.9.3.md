# BPM 0.9.3 Multilingual Adversarial Scope Fixtures

Backlog item: `BPM093-M8-03`
Status: implemented as fixed fail-closed fixtures without an HTTP route, browser UI, model load,
retrieval, worker or network action.

The M8-03 fixture contract supplies one reviewed case per locale for jailbreak, role change,
translation trick, encoded request, prompt extraction, fictional framing, long-padding and attempt
to redirect an active BPM conversation off topic. It also fixes mixed-script, percent-encoded,
Unicode-escaped and explicitly Base64-prefixed code-switched cases. The fixture runner sends every
case through the production M7 orchestrator with counting retrieval and inference boundaries.

Every case must end as `scope_off_topic_or_forbidden` before semantic similarity, E5 query
encoding, same-locale retrieval, evidence packing or the local Qwen worker. The checks do not
classify a language switch as a retrieval fallback: a technical BPM anchor can still be valid in an
ordinary request, while any hostile instruction found in the active input fails closed.

Encoding inspection is intentionally narrow. The gate decodes at most one percent or Unicode layer
and only Base64 tokens no larger than 512 decoded bytes. It uses the result only for deterministic
refusal matching and never turns it into a prompt, a tool request or a source. The normative
fixture contract is `documentation/config/bpm-scope-adversarial-fixtures-0.9.3.json`.
