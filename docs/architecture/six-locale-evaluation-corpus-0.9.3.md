# BPM 0.9.3 Six-Locale Search And Dialogue Evaluation Corpus

Date: 2026-07-28

Backlog item: `BPM093-M2-03`

Status: **Accepted corpus; maintainer-confirmed locale review is recorded.**

## Corpus Source And Expansion

`documentation/config/search-rag-evaluation-corpus-0.9.3.json` is hand-authored synthetic source data for future search/RAG evaluation. It has four grounded domains — Profile Library, Firefox AI controls, API validation, and CIS baseline selection — each with one expected local topic and citation identifier. Per-locale templates plus boundary cases deterministically expand to:

| Locale | Search cases | Answer/dialogue cases |
| --- | ---: | ---: |
| `en` | 40 | 24 |
| `ru` | 40 | 24 |
| `de` | 40 | 24 |
| `zh-CN` | 40 | 24 |
| `fr` | 40 | 24 |
| `es-ES` | 40 | 24 |

The 40 search cases combine four domains with exact identifier, direct term, alias, natural question, morphology/inflection, typo, compound/accent, and context forms, plus eight boundary cases. The 24 answer/dialogue cases combine four grounded domains with four question forms plus eight follow-up, ambiguity, no-evidence, off-topic, and prompt-injection cases.

Every grounded domain names an expected topic and citation. Boundary cases name `answer`, `clarify`, `abstain`, or `refuse`; off-topic and injection cases are intended to prove the later pre-inference scope gate, not to invoke a language model.

## Review State

The project maintainer confirmed locale-review acceptance interactively on 2026-07-28. The corpus
configuration records the acceptance for `en`, `ru`, `de`, `zh-CN`, `fr`, and `es-ES`. It confirms
source factual/difficulty review for English and localized review of natural phrasing, morphology,
compounds, accents/CJK segmentation, typo plausibility, technical identifiers, citation
expectations, refusal/privacy meaning, and equivalent boundary meaning for the other five locales.

This acceptance makes the corpus eligible for future M3/M5/M7/M8 evaluation runners. It does not
by itself satisfy search, retrieval, answer, scope, resource, security, or release quality gates;
those tasks must execute the frozen cases against their selected implementation.

## Preserved Boundaries

- Inputs are synthetic; no user prompts, chat transcripts, production data, secrets, private hosts, or external corpora are included.
- Expected evidence resolves to reviewed local topics and stable identifiers only. The fixture adds no product fact, browser policy semantics, model training input, telemetry, or network behavior.
- `M2-04` owns corpus/source eligibility for RAG chunks. `M3`, `M5`, `M7`, and `M8` own later search, retrieval, dialogue, and scope runners; they may not silently alter case intent or expected disposition.

## Result

The accepted structural corpus requirement is implemented and guarded. Future quality gates must
use it without silently changing case intent, expected evidence, or disposition.
