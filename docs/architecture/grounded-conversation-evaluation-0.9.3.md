# BPM 0.9.3 Grounded Conversation Conformance Evaluation

Backlog item: `BPM093-M7-07`
Status: deterministic six-locale M7 conformance evaluation implemented and executed.

The evaluator drives the implemented M7 orchestration, memory-only context and strict answer
validator with a reviewed locale-native fixture matrix. Each locale has a grounded answer, a
same-topic follow-up, a no-evidence abstention and an off-topic refusal. The answer fixture must
resolve only to current same-locale local evidence; the follow-up must use only bounded trusted
topic context; terminal cases invoke no fixture worker.

Every locale must score 100% for grounded answers, citation resolution, dialogue continuity,
abstention and refusal. The evaluator reports only locale counts and metric outcomes. Prompts,
answers, evidence text, session handles, citation identities, paths, model output and review data
are not written to the report. Output is restricted to
`documentation/.cache/bpm093-m7-07/` and stdout reports real per-locale completion.

This is a conformance evaluation of implemented M7 boundaries, not a second Qwen benchmark or a
claim about model language quality. M6 remains the selected model's runtime evidence. A later
production integration evaluation must exercise the real M8 scope-policy, E5/index adapters and M10
route/UI composition after those owners exist.

The normative machine-readable contract is
`documentation/config/grounded-conversation-evaluation-0.9.3.json`.
