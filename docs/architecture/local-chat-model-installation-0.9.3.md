# BPM 0.9.3 Explicit Local Chat Model Installation

Backlog item: `BPM093-M6-05`
Status: implemented; no inference worker or chat endpoint is introduced.

## Decision

Only the selected `Qwen3-0.6B-Q8_0.gguf` artifact may be installed. Its immutable source revision,
Apache-2.0 license, 639,446,688-byte size, and SHA-256
`9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031` are disclosed before the
explicit install command runs. The six locale-owned disclosures also say that local chat is optional,
uses the computer's CPU, and has no fixed response-time SLA under the accepted M6-04A policy.

`python -m app.ai.model_installation` is an operator lifecycle command, not a server feature:

```text
python -m app.ai.model_installation describe --locale ru
python -m app.ai.model_installation verify
python -m app.ai.model_installation install --locale ru --confirm
python -m app.ai.model_installation install-local --artifact /path/to/Qwen3-0.6B-Q8_0.gguf --locale ru --confirm
python -m app.ai.model_installation remove --confirm
```

`install` is the only networked command and requires `--confirm`. It emits bounded download progress
to stdout at zero, every five percentage points, and completion. No request, page load, normal
documentation search, status check, failed chat request, or retry may download the model.
`install-local` is the offline alternative for a pre-obtained GGUF. It also requires confirmation,
accepts only a direct regular non-symlink source file, copies it into the fixed staging location, and
applies the identical manifest verification before promotion.

## Development Handoff And Retention

`make ai-model-install-dev` is the explicit development bootstrap. `make dev` runs it after the
documentation installation, so it downloads the pinned artifact once when absent and only verifies
the already-verified artifact on later starts. Its progress remains in the command output.

This development artifact is persistent local state. `clean-local-artifacts` preserves `data/ai`,
and neither normal cleanup nor a later `make dev` may remove, downgrade, or replace it. Its removal
requires a separate confirmed lifecycle command and an explicit maintainer instruction. This
developer handoff does not replace the future release UI: `BPM093-M10-03A` owns the product-facing
installation, progress, cancellation, inspection, and removal controls.

## Artifact Boundary

The artifact belongs only below `<BPM DATA_DIR>/ai/models`, in a fixed model directory. Staging and
quarantine have fixed names as well. The lifecycle accepts regular, non-symlink files only; verifies
byte count, SHA-256, metadata identity and provenance; resumes only the fixed partial file; then
atomically promotes it. Interrupted, wrong-size, wrong-checksum, metadata, path, disk-space, HTTP,
or architecture failures remain unready and fail closed. Removal requires confirmation and can delete
only these manifest-owned fixed paths; it refuses symlinks.

The selected model is targeted to x86_64. This check is a compatibility gate only; it does not claim
that M6-05 can execute the model.

## Explicit Non-Goals

M6-05 adds neither `llama.cpp`, an inference process, model execution, an HTTP or TCP listener, a
browser-facing chat route, automatic enablement, nor external web search. M6-06 retains ownership of
the bounded worker and M6-07 of runtime/fallback evidence. The ordinary deterministic documentation
search remains unchanged and independent.

The normative machine-readable contract and tests are
`documentation/config/local-chat-model-installation-contract-0.9.3.json`,
`tests/test_local_model_installation.py`, and
`documentation/tests/contract/test_local_chat_model_installation_contract_0_9_3.py`.
