"""Deterministic evidence packing and pre-generation abstention gates."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, replace
from typing import Final, Literal

from app.documentation.content_boundary import (
    MAX_PACKED_EVIDENCE_BYTES,
    sanitize_evidence_text,
)
from app.documentation.retrieval import LocalCitation, RetrievalResult, RetrievedEvidence

EvidenceDisposition = Literal["answer", "clarify", "abstain"]
TokenCounter = Callable[[str], int]

MAX_CONTEXT_TOKENS: Final[int] = 2048
MAX_EVIDENCE_CHUNKS: Final[int] = 4
MINIMUM_TOP_SCORE: Final[float] = 0.45


class EvidencePackingError(ValueError):
    """The caller did not provide a usable exact token counter or evidence input."""


@dataclass(frozen=True)
class EvidenceConfidence:
    """Deterministic retrieval confidence inputs; it is not user-facing probability prose."""

    top_score: float | None
    runner_up_score: float | None
    margin: float | None
    candidate_count: int


@dataclass(frozen=True)
class EvidencePack:
    """The only evidence/context artifact that a later generator may receive."""

    disposition: EvidenceDisposition
    reason_code: str
    locale: str
    generation_id: str
    confidence: EvidenceConfidence
    context_jsonl: str
    context_tokens: int
    evidence: tuple[RetrievedEvidence, ...]
    citations: tuple[LocalCitation, ...]


def _confidence(candidates: tuple[RetrievedEvidence, ...]) -> EvidenceConfidence:
    if not candidates:
        return EvidenceConfidence(None, None, None, 0)
    top_score = candidates[0].score
    runner_up_score = candidates[1].score if len(candidates) > 1 else None
    margin = top_score - runner_up_score if runner_up_score is not None else None
    return EvidenceConfidence(top_score, runner_up_score, margin, len(candidates))


def _empty(result: RetrievalResult, reason_code: str, confidence: EvidenceConfidence) -> EvidencePack:
    return EvidencePack("abstain", reason_code, result.locale, result.generation_id, confidence, "", 0, (), ())


def _record(candidate: RetrievedEvidence) -> str:
    return json.dumps(
        {
            "anchor_id_or_root": candidate.citation.anchor_id_or_root,
            "bpm_version": candidate.bpm_version,
            "chunk_id": candidate.chunk_id,
            "citation_id": candidate.citation.citation_id,
            "documentation_version": candidate.documentation_version,
            "guide_id": candidate.guide_id,
            "heading_path": candidate.heading_path,
            "ordinal": candidate.ordinal,
            "published_url": candidate.citation.published_url,
            "source_kind": candidate.citation.source_kind,
            "source_sha256": candidate.source_sha256,
            "text": candidate.text,
            "topic_id": candidate.citation.topic_id,
            "trust": "untrusted_documentation_data",
        },
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _safe_candidate(candidate: RetrievedEvidence) -> RetrievedEvidence | None:
    """Keep only local inert data; a later web adapter needs its own quarantine boundary."""

    if candidate.citation.source_kind != "local":
        return None
    text = sanitize_evidence_text(candidate.text)
    guide_id = sanitize_evidence_text(candidate.guide_id)
    heading_path: list[str] = []
    for part in candidate.heading_path:
        sanitized_part = sanitize_evidence_text(part)
        if sanitized_part is None:
            return None
        heading_path.append(sanitized_part)
    if text is None or guide_id is None:
        return None
    return replace(candidate, text=text, guide_id=guide_id, heading_path=tuple(heading_path))


class EvidencePacker:
    """Choose bounded, non-duplicative local evidence before any model invocation."""

    def __init__(
        self,
        token_counter: TokenCounter,
        *,
        bpm_version: str,
        maximum_context_tokens: int = MAX_CONTEXT_TOKENS,
        maximum_chunks: int = MAX_EVIDENCE_CHUNKS,
        minimum_top_score: float = MINIMUM_TOP_SCORE,
    ) -> None:
        if not bpm_version or maximum_context_tokens < 1 or not 1 <= maximum_chunks <= 5:
            raise EvidencePackingError("invalid_evidence_packing_configuration")
        if not 0.0 <= minimum_top_score <= 1.0:
            raise EvidencePackingError("invalid_evidence_packing_configuration")
        self._token_counter = token_counter
        self._bpm_version = bpm_version
        self._maximum_context_tokens = maximum_context_tokens
        self._maximum_chunks = maximum_chunks
        self._minimum_top_score = minimum_top_score

    def _count_tokens(self, context_jsonl: str) -> int:
        try:
            tokens = self._token_counter(context_jsonl)
        except Exception as error:
            raise EvidencePackingError("token_counter_failed") from error
        if not isinstance(tokens, int) or isinstance(tokens, bool) or tokens < 0:
            raise EvidencePackingError("token_counter_returned_invalid_count")
        return tokens

    def pack(self, result: RetrievalResult, *, scope_admitted: bool) -> EvidencePack:
        """Return an answer-ready pack or a terminal pre-generation disposition."""
        ranked = tuple(
            candidate for item in result.candidates if (candidate := _safe_candidate(item)) is not None
        )
        confidence = _confidence(ranked)
        if not scope_admitted:
            return _empty(result, "scope_not_admitted", confidence)
        if not result.candidates:
            return _empty(result, "no_evidence", confidence)
        if not ranked:
            return _empty(result, "unsafe_evidence", confidence)
        if any(
            candidate.bpm_version != self._bpm_version or candidate.documentation_version != self._bpm_version
            for candidate in ranked
        ):
            return _empty(result, "stale_evidence", confidence)
        if len({candidate.chunk_id for candidate in ranked}) != len(ranked):
            return _empty(result, "duplicate_chunk_identity", confidence)
        citation_sources: dict[str, str] = {}
        for candidate in ranked:
            existing = citation_sources.setdefault(candidate.citation.citation_id, candidate.source_sha256)
            if existing != candidate.source_sha256:
                return _empty(result, "contradictory_evidence", confidence)
        if confidence.top_score is None or confidence.top_score < self._minimum_top_score:
            return _empty(result, "low_confidence", confidence)
        selected: list[RetrievedEvidence] = []
        seen_citations: set[str] = set()
        for candidate in ranked:
            if candidate.citation.citation_id in seen_citations:
                continue
            seen_citations.add(candidate.citation.citation_id)
            selected.append(candidate)
            if len(selected) == self._maximum_chunks:
                break
        source_ordered = sorted(
            selected,
            key=lambda candidate: (
                candidate.citation.topic_id,
                candidate.citation.anchor_id_or_root,
                candidate.ordinal,
                candidate.chunk_id,
            ),
        )
        packed: list[RetrievedEvidence] = []
        context_jsonl = ""
        for candidate in source_ordered:
            next_context = "\n".join([context_jsonl, _record(candidate)]).lstrip("\n")
            if len(next_context.encode("utf-8")) > MAX_PACKED_EVIDENCE_BYTES:
                continue
            if self._count_tokens(next_context) > self._maximum_context_tokens:
                continue
            packed.append(candidate)
            context_jsonl = next_context
        if not packed:
            return _empty(result, "context_budget_exceeded", confidence)
        citations = tuple(candidate.citation for candidate in packed)
        return EvidencePack(
            "answer",
            "grounded_evidence_ready",
            result.locale,
            result.generation_id,
            confidence,
            context_jsonl,
            self._count_tokens(context_jsonl),
            tuple(packed),
            citations,
        )
