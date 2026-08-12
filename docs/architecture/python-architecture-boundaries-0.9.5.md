# BPM 0.9.5 Python Architecture Boundaries

Status: active executable contract

## Purpose

`make architecture` runs Import Linter without a graph cache. It is a fast mandatory quality gate:
it checks the maintained application, documentation tooling and repository tools before the broad
test contour. The contract configuration is versioned in `pyproject.toml`; the focused proof is
`tests/integration/app/test_python_architecture_contracts.py`.

## Dependency Directions

The ordinary profile application has one downward direction:

```text
app.main
  -> app.api | app.web
  -> app.services | app.compliance
  -> app.models | app.schemas | app.db | app.middleware
  -> app.core
```

Layers on the same line are independent. Import Linter also rejects cycles among owned API, web,
service, compliance, core, model and schema siblings. This contract intentionally does not force
the optional documentation-assistant implementation into the profile-layer diagram.

## Protected And Optional Boundaries

- `app.core.schemas_loader` is available only inside `app.core`.
- `app.services.firefox_policy_ui_registry` remains behind the service layer.
- The local AI/RAG assembly and E5 runtime are protected. The only non-assembly importer is the
  explicitly named offline answer benchmark; it is not release runtime.
- `app.main` cannot directly or transitively reach the local worker, E5 runtime, RAG bootstrap or
  local-assistant assembly.
- Release API/web/services cannot import `documentation.tools.*` build internals.

The release assistant uses `app.documentation.assistant_contracts` for transport data. That module
is deliberately data-only; the controller and local worker remain optional and are loaded only by
their explicit incubation assembly. Its locale tuple also owns release assistant locale admission,
so the training notice and API router do not import vector retrieval merely to share a constant.

NumPy, ONNX Runtime and Tokenizers are declared only by the `ai` extra. Install an AI development
environment with `python -m pip install -e ".[dev,ai]"`, verify it with
`make ai-extra-check`, and run the isolated implementation contour with
`make test-ai-incubation`. Ordinary base startup and the default test contour must not collect or
import that implementation. The assistant remains a training-notice surface; installing the extra
does not activate it.

## Change Procedure

Run `make architecture` after a package-boundary change. Do not add broad wildcard exceptions.
If an exceptional direct importer is necessary, record its exact module, its owner and why it is
not part of the release graph in this document and add a focused test. A changed contract must
continue to reject both direct and indirect imports; the test fixture proves the latter behavior.
