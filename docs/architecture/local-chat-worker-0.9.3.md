# BPM 0.9.3 Bounded Local Chat Worker

Backlog item: `BPM093-M6-06`
Status: implemented without a browser or HTTP API.

## Runtime Boundary

The worker accepts only the M6-05 verified Qwen3 0.6B Q8_0 model and the immutable `llama.cpp`
`b9637` Linux x64 archive. It re-verifies the retained 15,512,345-byte archive with SHA-256
`a50ee14f021a9d8e92e30f622f7e3be1318ee1125bb9a9ba8d2025388df48743` on every start, then extracts
only `llama-cli` and `lib*` shared libraries to a private temporary directory. `llama-server`,
`rpc-server`, and every other executable from the upstream archive are never extracted.

The child is started without a shell through stdin/stdout, with `--offline`, CPU device `none`, four
inference and batch threads, context 4,096, an explicit 512-output-token resource bound,
deterministic sampling, Jinja, and
non-thinking mode. It has a minimal environment and no listener, browser connection, tool,
function-call, plugin, API, or web capability.

M13-06B additionally supplies a fixed local llama.cpp GBNF grammar. It permits only the exact
sectioned answer object or an empty-section terminal object; the model cannot emit prose, Markdown,
an old response shape or extra top-level fields. This is a syntax boundary only: the server still
binds citations to current same-locale evidence, rejects unsafe/unsupported/excessively extractive
prose, and fails closed when the resulting JSON is not a valid grounded answer. The child also uses
`--no-show-timings`: its stdout is a JSON machine protocol, so llama.cpp's human timing footer is
not permitted to follow a response.

The native conversation template is started in one fresh `llama-cli` child for every generation,
then that child and its private extracted runtime are released immediately after the response. BPM
itself sends the exact retained eight-pair dialogue inside each bounded request, after current
same-locale retrieval. A child is never reused, so its opaque native KV history cannot turn an
earlier independent request into context for the next one. The retained verified model archive and
model artifact are unaffected; the response-time preview therefore correctly treats every new
generation as cold.

## Lifecycle And Failure

The worker is disabled by default and is not started by BPM startup, `make dev`, page load, search,
status polling, or retry. A later approved controller may invoke it only after model/runtime checks.
Only one generation is active; input, dialogue, evidence and output limits are bounded.

While the child is active BPM sums the Linux `VmRSS` counters of the worker and its controller
process (which hosts retrieval). Exceeding the hard 3.5 GiB worker/retrieval ceiling terminates the
process group with the stable `assistant_resource_limit` reason; the counters themselves are neither
logged nor returned by health.

Cancellation and timeout terminate the entire child process group. Explicit unload removes the
private extracted bundle and in-memory conversation state. A crash, timeout, protocol failure, or
unverified artifact fails closed. Safe worker health reports only state, readiness, reason code and
runtime identity. It does not change core `/health/ready`; normal documentation search remains
available in every worker state.

## Development Runtime

`make ai-runtime-install-dev` copies the checksum-pinned M6-03 archive into the persistent
`data/ai/runtime` store. `make dev` verifies that stored archive but does not start the worker.
`clean-local-artifacts` preserves `data/ai`; removal needs separate confirmed lifecycle action and
an explicit maintainer instruction. This developer bootstrap is not release UI evidence: the UI is
owned by `BPM093-M10-03A`.

The normative contract is `documentation/config/local-chat-worker-contract-0.9.3.json`.
