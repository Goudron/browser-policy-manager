# Documentation Tools

This directory owns documentation-only build, validation, manifest, search-index, localization, and
screenshot adapters. Tools may consume approved BPM contract sources at build time but must not be
imported by the BPM runtime.

`bootstrap_toolchain.py` implements the pinned, repository-local DITA-OT, Temurin JRE, and Python
test-environment bootstrap. Use it through `make setup-docs-toolchain`; it verifies upstream
SHA-256 values, rejects unsafe archives and unsupported platforms, checks tool versions, and runs a
minimal DITA 1.3 HTML5 smoke build.

`validate_metadata.py` validates fixed conditional values and grouped policy/CIS/API identities
against `metadata-vocabulary.json` and the maintained inventories. Run it from the repository root
with `./.venv/bin/python documentation/tools/validate_metadata.py`.

`generate_firefox_policy_skeletons.py` regenerates the committed Firefox policy DITA skeletons,
generated map, and skeleton index from the maintained Firefox policy documentation inventory and
topic model while preserving reviewed regions.

`build_docs.py` is the offline six-locale build and packaging authority behind `make docs-validate`,
`make docs-build`, `make docs-install-dev`, `make docs-reproducibility-check`, `make docs-package`, and
`make docs-package-verify`. It validates metadata, XML, local source links, keys and fragments; runs
the locked DITA-OT HTML5 transform against staged copies of maintained source with explicit
locale/timezone/encoding/temp/output inputs; wraps generated pages in the deterministic accessible
portal shell; copies first-party CSS theme assets into every locale output; generates and validates
one `navigation.json` per locale, `manifest.json`, `ui-target-map.json`, and the current six
placeholder search indexes; rejects
source mutation, broken generated links, invalid shell landmarks, active content, inline styles,
manifest/target-map/schema drift, navigation sources that diverge from manifest/source hierarchy,
labels, ordering, or URLs even after hash replacement, bad artifact references, and absolute
workspace-path leaks;
publishes atomically to ignored `documentation/build/site`; compares two clean trees byte for byte;
and emits a deterministic ignored release-candidate archive plus checksum under
`documentation/dist/`. `make dev` refreshes the ignored `app/documentation/site` copy through
`make docs-install-dev` before starting the app, so maintainer review sees the current local
documentation; `make run` starts only the app when documentation refresh is intentionally skipped.
Release package extraction remains separate.

`search_candidate_prototypes.py` is an M3 documentation-only adapter-contract helper. It creates
compact deterministic input shapes and normalized results for the current search control, Pagefind,
and Meilisearch Community Edition without installing a vendor package, starting a process, opening
a listener, or making a request. It is benchmark-harness input, not the production search engine.

`run_search_relevance_benchmark_0_9_3.py` runs a supplied, hash-checked Pagefind and Meilisearch CE
artifact in an isolated temporary workspace. It writes ignored raw query evidence and a summary,
guards Pagefind fetches and Meilisearch requests to loopback-only origins, and does not select or
install a production engine.

`run_search_resource_benchmark_0_9_3.py` reuses only those supplied, hash-checked artifacts to
measure Pagefind baseline and deterministic growth-fixture index size/time, first-query bytes and
latency, and an isolated clean install/atomic update/rollback transition. Its output directory must
be an ignored benchmark-report location; it never changes BPM runtime artifacts or selects an
engine.

`run_browser_search_tuning_benchmark_0_9_3.py` compares the maintained BPM browser ranker with the
frozen M3 static-control mirror against the compact reviewed six-locale corpus. It loads only the
local browser script through Node, makes no network request or generated-site read, and writes a
requested ignored JSON report. It fails if any locale regresses or lacks a strict relevance gain.

`extract_rag_chunks_0_9_3.py` builds an ignored canonical `rag-chunk-v1` manifest from a validated
temporary six-locale DITA publish tree. It retains only locale/topic/anchor-bounded published text,
typed content blocks, identifiers, source/manifest hashes, provenance, and stable help URLs. It
does not download a model, create embeddings, start a worker, open a listener, access a network,
or change lexical search.

`run_embedding_model_benchmark_0_9_3.py` measures one checksum-verified ONNX embedding candidate
per process against the eligible published chunk manifest and reviewed six-locale answer corpus.
It is offline after installation, samples RSS, rejects changed swap, records locale and
cross-language Recall@5 plus query P95, and can select only a passing immutable artifact from
independent ignored reports. Its `--config` option permits a separately versioned remediation
contract; it feeds only ONNX inputs required by that candidate and applies any declared,
checksum-pinned post-pooling step before L2 normalization. It neither installs a model nor enables
RAG.

`run_chat_rag_embedding_benchmark_0_9_3.py` evaluates checksum-pinned embeddings only for
same-locale chat evidence retrieval. It reads published chunks and their metadata, never invokes
ordinary search or a chat model, rejects cross-locale retrieval, checks resolvable local citations,
uses a local unknown-identifier no-evidence path, rejects changed swap, and produces ignored
candidate/selection reports. It neither installs an embedding artifact nor enables RAG.

`run_chat_rag_vector_storage_benchmark_0_9_3.py` compares a locale-private normalized float32
exact scan and a supplied checksum-verified sqlite-vec extension with deterministic E5-base-shaped
vectors at the current and 10x corpus sizes. It reads no BPM text, model, search index, or runtime
artifact; it has zero network and ordinary-search calls and writes an ignored report only.

`run_local_chat_worker_validation_0_9_3.py` performs one sequential real local-worker probe for
each supported locale after the explicitly retained model and runtime have been verified. It emits
flushed factual stdout progress and writes only ignored output digests and counters; prompts,
evidence and model output are never retained. It is a worker transport/lifecycle check, not a
grounded-answer benchmark or a product chat route.

`run_grounded_conversation_evaluation_0_9_3.py` runs the deterministic M7 six-locale conformance
matrix for grounded answers, same-topic follow-ups, no-evidence abstention and off-topic refusal.
It exercises the implemented orchestration/context/answer-validation boundaries with reviewed test
fixtures, writes only content-free ignored metrics, and emits factual per-locale stdout progress.
It does not start, benchmark or make a language-quality claim about the selected chat model.

`generate_chat_rag_exact_generations_0_9_3.py` builds six immutable E5-base locale-private exact
float32 generations from a reviewed chunk manifest and a checksum-verified locally supplied model.
It verifies cache entries and every promoted file/shape/hash/compatibility key, uses private staging
and an atomic active-generation pointer, and has no network or ordinary-search path.
