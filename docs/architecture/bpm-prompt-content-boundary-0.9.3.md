# BPM 0.9.3 Prompt And Untrusted-Content Boundary

Backlog item: `BPM093-M8-04`
Status: implemented without an HTTP route, browser UI, web provider, ordinary-search change or model
startup.

`EvidencePacker` now admits only local documentation candidates that can be made inert. It keeps an
8-KiB cap for each untrusted text field, a 24-KiB cap for the serialized evidence packet and the
existing exact-token and chunk limits. Script/style blocks, tags, Markdown link targets, active URL
schemes, control characters and bidi controls are stripped. A candidate containing a control
override, role change, prompt extraction or request for tool, network or file behavior is discarded
as a whole, including bounded percent, Unicode-escape and Base64 forms. If every candidate is
discarded, the conversation abstains with `unsafe_evidence` before the worker.

The local worker wraps canonical JSON Lines between fixed
`BPM_UNTRUSTED_EVIDENCE_DATA` delimiters and labels it `untrusted_documentation_data`. Its fixed
system policy places question, dialogue and evidence below the controller: no content in those
fields can change role, tools, active locale, response schema, citation policy, network or file
behavior. The worker still has no tool, product API, arbitrary file or network capability. Current
`EvidencePacker` rejects source kinds other than `local`; M9 must add a separate quarantined web
ingress rather than reusing this boundary.

Generated output is display data too. The validator continues to accept only the exact
`disposition`/`text`/`citation_ids` JSON shape, rejects active content, and resolves citation IDs
only against the accepted local evidence pack. Unknown authority-bearing fields such as `locale`,
`tool_calls` or network controls therefore downgrade to bounded server-selected extractive evidence
or abstention. The normative contract is
`documentation/config/bpm-prompt-content-boundary-contract-0.9.3.json`.
