# BPM AI component update runbook

`BPM093-M11-05` requires a maintainer to pin a candidate version, review its license and advisories,
download only from the approved source, verify checksum and provenance, then run the component's
benchmark and compatibility/retrieval validation. Build a private candidate generation, canary it,
and atomically promote it only after validation. Retain the prior verified generation for rollback.

Offline updates use the same manifest verification and fixed staging destination. Never float a
dependency, silently download on page load, expose a model service, or delete the prior verified
artifact before the candidate is accepted. On any failure, quarantine/remove only the candidate and
continue with the prior verified generation or lexical-search fallback.
