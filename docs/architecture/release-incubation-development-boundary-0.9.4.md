# BPM 0.9.4 Release, Incubation, And Development Boundary

`tools/release_boundary_manifest_0_9_4.json` is the authoritative, machine-checked
classification of BPM modules, direct dependencies, Make commands, test fixtures,
and test contours. It distinguishes the default release delivery from optional AI
incubation, development tooling, and the separately optional PostgreSQL integration.

The explicit `ai` extra owns only NumPy, ONNX Runtime, and Tokenizers. Its tests are
collected only by `make test-ai-incubation`; it has no shared repository fixture, so
the optional contour may create only test-local `tmp_path` resources. Release-safe
assistant and local-model transport/installation code stays in the base package to
retain the existing disabled/training-notice surfaces, but it must not initialize
retrieval, inference, model encoders, or RAG runtime.

`make release-boundary` builds a new wheel from a copied source tree, installs it in
a fresh virtual environment without extras, runs `pip check`, verifies the native AI
modules are absent, and exercises the two release-safe HTTP surfaces. CI runs this
same command in its base-runtime job. The focused test uses
`--skip-clean-wheel-smoke` only to validate the manifest quickly; it does not replace
the CI/local clean-wheel proof.
