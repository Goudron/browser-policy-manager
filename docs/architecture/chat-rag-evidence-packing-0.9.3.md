# BPM 0.9.3 Chat Evidence Packing And Abstention Contract

Date: 2026-07-29

Backlog item: `BPM093-M5-07`

Status: **Implemented pre-generation evidence gate; no language-model invocation yet.**

## Decision

`app/documentation/evidence.py` adds `EvidencePacker` after same-locale retrieval and before any
future local language-model call. It has no model/runtime loader, HTTP route, worker, ordinary-search
import, external evidence path, or network client. Its only output is either bounded citable local
evidence or a terminal `answer`, `clarify`, or `abstain` disposition. A later caller must not invoke
generation unless the disposition is `answer`.

The packer requires the caller to supply the deterministic scope-gate admission result. A request
that is not admitted produces `abstain/scope_not_admitted` without packing text or invoking a model.
M8 will own the multilingual scope classifier and refusal UI; this boundary ensures its rejection
already stops the downstream path.

## Budget and serialization

The frozen context budget is **2,048 exact tokens** and at most four evidence chunks. The future
selected chat model supplies its immutable exact tokenizer counter. Character, word, byte, and
estimated-token counters are prohibited for production use, so a model change cannot silently alter
the budget. If no citable record fits, the packer returns `abstain/context_budget_exceeded`.

Selected records become canonical sorted-key JSON Lines. Each contains local citation identity and
URL, topic/anchor, guide, source hash, version, source ordinal, heading path, and reviewed text as
data. This keeps instruction-looking text inert for the later structured prompt boundary and retains
the metadata required to resolve citations server-side.

## Selection and safe terminal outcomes

Retrieval order remains the relevance input. The packer retains no more than one highest-ranked
record per exact citation, then writes selected records in stable source order: topic, anchor,
ordinal, and chunk ID. It retains top score, runner-up score, margin, and candidate count only as
internal diagnostics; it never renders fabricated probability to users.

The fixed answer-readiness threshold is top score `0.45`.  The packer keeps a runner-up score and
margin only as diagnostics; it does not treat a small difference between distinct current topics as
question ambiguity.  An admitted BPM question may need several citable local topics, while the
scope gate asks for clarification before retrieval when the user's subject itself is ambiguous:

- no evidence, low score, stale version, duplicate chunk ID, incompatible source mapping, no scope
  admission, or an over-budget context leads to abstention;
- a citation identity associated with different source hashes is contradictory and leads to
  abstention;
- only current, locale-private, deduplicated, citable evidence within the exact budget is
  answer-ready.

This does not claim semantic contradiction detection across unrelated documentation statements;
that requires the later grounded-answer and review gates. It prevents the mechanical inconsistency
that would make one displayed citation identify two source revisions.
