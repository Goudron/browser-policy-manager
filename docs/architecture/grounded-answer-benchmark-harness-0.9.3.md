# Grounded Answer Benchmark Harness (BPM 0.9.3)

Status: implemented for `BPM093-M6-02`; no candidate model has been run or selected.

## Comparable, Evidence-First Workload

`documentation/tools/run_grounded_answer_benchmark_0_9_3.py` converts prepared, same-locale
`EvidencePack`-shaped records into requests that are byte-identical for every admitted candidate.
The request contains only the localized question, prior localized dialogue turns, local evidence, and
fixed non-thinking generation settings. The expected disposition and citations remain in the separate
scorer oracle, so they cannot leak into the candidate prompt.

Each supported locale has 32 cases: 16 normal answers, four grounded dialogue follow-ups, four
abstentions, two clarification requests, and six off-topic/injection refusals. Terminal cases are
resolved before model invocation; the harness accepts no candidate response for them.

## Grounding Review And Scores

Candidate output must cite only displayed expected local citations and stays within 96 output tokens.
It cannot contain thought tags and cannot use the network. A mandatory reviewer record covers every
answer case in all six locales. Each factual claim is explicitly marked supported and tied to a
citation emitted in that answer; one unsupported claim fails the run even if the wording, latency, or
resource measurements look good.

The report records grounded answer, citation selection, terminal disposition, language, instruction
following, dialogue continuity, TTFT, completion latency, output-token median, peak RSS, and network
calls. M6-02 makes these measurements comparable; M6-03 applies the target-laptop protocol and
M6-04 selects a model/runtime.

## Isolation And Reproducibility

This is documentation-only benchmark tooling. It does not import the product runtime, start or
download a model, enter the M4 documentation-search path, call external sources, use ordinary search,
or use cross-locale retrieval. All produced workloads, raw outputs, reviews, and reports remain
ignored under `documentation/.cache/bpm093-m6-02/`.

The harness verifies pinned source contracts and emits real, flushed stdout progress after each eight
prepared packets per locale and at each locale score completion. This exposes actual work without
inventing an ETA or chat-side progress messages.
