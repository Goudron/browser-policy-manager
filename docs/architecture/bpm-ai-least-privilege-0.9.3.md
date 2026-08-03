# BPM 0.9.3 Local Assistant Least Privilege

Backlog item: `BPM093-M8-05`
Status: implemented without an HTTP route, browser UI, listener, external web provider or ordinary
documentation-search change.

The default local worker now receives one BPM-owned `data/ai` root. Before it verifies or starts an
artifact, the runtime archive, model artifact and temporary worker root must be absolute children of
that root. Traversal, symlinks at any component, shell-shaped path components and non-regular
runtime/model files fail as `assistant_unsafe_execution_path`. The command remains a fixed direct
argument vector: it never invokes a shell and does not turn a request or model value into an
executable, option, extension or plugin.

The child has only fixed locale and path environment values: an empty `PATH`, `LC_ALL=C`, empty
proxy variables and `NO_PROXY=*`. It remains `--offline`, has no server or listener executable, and
uses BPM-owned stdin/stdout only. The selected model download is still an explicit operation against
its checksum-pinned HTTPS source; production HTTP client construction no longer follows redirects or
inherits proxy environment variables. No external web evidence can enter before M9.

M7 keeps one active and one queued conversation, a 48-KiB request bound and a 3.5-GiB aggregate
worker/retrieval RSS ceiling. M8-05 also supplies a transport-neutral future assistant request guard:
only a bounded JSON `POST` whose Origin, Host and optional `Sec-Fetch-Site` all prove same origin is
admitted. It deliberately adds no FastAPI route; M10 must compose this guard with CSRF and the
versioned assistant API contract rather than inheriting BPM's general CORS policy.

The normative contract is `documentation/config/bpm-ai-least-privilege-contract-0.9.3.json`.
