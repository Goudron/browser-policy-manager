# BPM 0.9.3 Explicit Local-Model Management UI

Date: 2026-07-30
Backlog item: `BPM093-M10-03A`
Status: implemented; it manages only the selected local artifact and does not enable chat.

## Deliberate lifecycle

The documentation portal contains a localized **Manage local model** control within the existing
assistant card. It performs no work while a documentation page loads: no model inspection,
verification, download, status poll, retrieval, worker start or chat request occurs. After the
reader presses the control, the portal reads that locale's static `assistant-copy.json` and makes
one same-origin status request. It then renders the selected artifact's upstream, revision, license,
size, SHA-256, CPU expectation and no-SLA notice as text.

Only explicit controls can request install, verification, cancellation or removal. Install and
removal each use a browser confirmation before their POST. An accepted lifecycle operation alone
starts status polling. Installation progress reports bytes and percentage. The existing dialogue
composer remains disabled, and deterministic documentation search and navigation stay usable before,
during and after every lifecycle state.

## API and safety boundary

`/api/local-model` is a narrow model-lifecycle API, not an assistant chat API. Its state-changing
requests require same-origin JSON headers, exact host matching, an actually streamed 1024-byte body
limit, a strict no-extra-field schema and a per-session rotating CSRF token. The temporary session
identifier is HttpOnly and SameSite=Strict. Status reports the fixed manifest disclosure and bounded
operation state only; it never runs a full checksum or creates a network client.

The controller serializes one selected-artifact operation. It delegates integrity, private fixed
storage, atomic promotion, interruption recovery and symlink-safe removal to the M6 installer.
Cancellation is checked before network connection and between download/copy chunks; a partial file
never becomes ready or runnable. Browser code uses text nodes, not HTML injection, and never sends
paths, prompt text, document content or credentials to this API.

This is intentionally separate from the unresolved chat enablement. No assistant request/SSE route,
retrieval, inference worker, web-evidence adapter or answer renderer is added here. The M10 chat
security and rate-limit gates remain owned by the later dialogue tasks.

The normative record is
`documentation/config/local-model-management-ui-contract-0.9.3.json`.
