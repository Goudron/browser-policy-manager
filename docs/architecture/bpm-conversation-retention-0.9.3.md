# BPM 0.9.3 Private Conversation Retention Defaults

Backlog item: `BPM093-M8-06`
Status: implemented without an HTTP route, browser UI, persistence layer, telemetry, external web
provider or ordinary documentation-search change.

Documentation-assistant conversations are private, session-local process memory by default. A
session belongs to exactly one locale and BPM version, retains at most four chronological turns, and
expires after 15 minutes of inactivity or eight hours from creation. An expired, cleared, mismatched
or restarted session cannot provide prior question text, answers, entities, topics or citation
identities to retrieval or generation. The controller can delete one exact opaque session immediately
and can clear all memory for an explicit reset or process shutdown; no persistence exists to restore.

The stream controller drops a completed active request's question immediately after it has returned
from the worker; a cancelled queued request is dropped immediately. Pending events are consumed by
poll, and completed request records, including opaque citation-source handles, expire after 15
minutes and remain capped at four. This preserves the existing bounded cancellation lifecycle while
avoiding a durable transcript.

Operational diagnostics expose only stable state/error classes, compatibility booleans and a coarse
queue class. They never return prompts, answers, evidence excerpts, paths, artifact content or an
untrusted worker-reason string. Local mode keeps content logging, telemetry, personalization,
browser storage, disk/database persistence and network calls off. The deterministic documentation
search remains independent from this assistant retention logic.

Optional local conversation persistence is deliberately not implemented. It needs a separately
reviewed explicit user control, defined retention/deletion behavior and a new contract before it can
store any conversation data.

The normative contract is `documentation/config/bpm-conversation-retention-contract-0.9.3.json`.
