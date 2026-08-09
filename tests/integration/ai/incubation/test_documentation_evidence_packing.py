from __future__ import annotations

import json
from dataclasses import replace

import pytest

from app.documentation.evidence import EvidencePacker, EvidencePackingError
from app.documentation.retrieval import LocalCitation, RetrievalResult, RetrievedEvidence


def _evidence(
    chunk_id: str,
    *,
    topic_id: str,
    score: float,
    ordinal: int = 0,
    source_sha256: str = "a" * 64,
    version: str = "0.9.3",
) -> RetrievedEvidence:
    return RetrievedEvidence(
        chunk_id=chunk_id,
        ordinal=ordinal,
        guide_id="user-guide",
        documentation_version=version,
        bpm_version=version,
        source_sha256=source_sha256,
        heading_path=[topic_id],
        text=f"Reviewed evidence for {topic_id}.",
        score=score,
        citation=LocalCitation(
            f"topic:{topic_id}", f"/help/en/user/{topic_id}.html", topic_id, "root"
        ),
    )


def _result(*candidates: RetrievedEvidence) -> RetrievalResult:
    return RetrievalResult("raggen-v1-0123456789abcdef0123", "en", candidates)


def _exact_counter(context: str) -> int:
    return len(context.split())


def test_packer_bounds_context_deduplicates_citations_and_preserves_source_order() -> None:
    ranked = _result(
        _evidence("ragc-v1:en:topic-b:root:0", topic_id="topic-b", score=0.91),
        _evidence("ragc-v1:en:topic-a:root:0", topic_id="topic-a", score=0.70),
        _evidence("ragc-v1:en:topic-a:root:1", topic_id="topic-a", score=0.60, ordinal=1),
    )

    pack = EvidencePacker(_exact_counter, bpm_version="0.9.3", maximum_context_tokens=200).pack(
        ranked, scope_admitted=True
    )

    assert pack.disposition == "answer"
    assert pack.reason_code == "grounded_evidence_ready"
    assert pack.context_tokens <= 200
    assert [item.chunk_id for item in pack.evidence] == [
        "ragc-v1:en:topic-a:root:0",
        "ragc-v1:en:topic-b:root:0",
    ]
    assert [citation.citation_id for citation in pack.citations] == [
        "topic:topic-a",
        "topic:topic-b",
    ]
    assert [json.loads(line)["chunk_id"] for line in pack.context_jsonl.splitlines()] == [
        "ragc-v1:en:topic-a:root:0",
        "ragc-v1:en:topic-b:root:0",
    ]
    assert pack.confidence.margin == pytest.approx(0.21)


@pytest.mark.parametrize(
    ("result", "scope_admitted", "expected_disposition", "reason_code"),
    [
        (_result(), True, "abstain", "no_evidence"),
        (
            _result(_evidence("ragc-v1:en:low:root:0", topic_id="low", score=0.44)),
            True,
            "abstain",
            "low_confidence",
        ),
        (
            _result(
                _evidence("ragc-v1:en:a:root:0", topic_id="a", score=0.90),
                _evidence("ragc-v1:en:b:root:0", topic_id="b", score=0.87),
            ),
            True,
            "answer",
            "grounded_evidence_ready",
        ),
        (
            _result(_evidence("ragc-v1:en:ok:root:0", topic_id="ok", score=0.90)),
            False,
            "abstain",
            "scope_not_admitted",
        ),
    ],
)
def test_packer_stops_before_generation_for_empty_low_confidence_or_unadmitted_evidence(
    result: RetrievalResult, scope_admitted: bool, expected_disposition: str, reason_code: str
) -> None:
    pack = EvidencePacker(_exact_counter, bpm_version="0.9.3").pack(
        result, scope_admitted=scope_admitted
    )

    assert pack.disposition == expected_disposition
    assert pack.reason_code == reason_code
    if expected_disposition == "answer":
        assert pack.context_jsonl
        assert [citation.citation_id for citation in pack.citations] == ["topic:a", "topic:b"]
    else:
        assert pack.context_jsonl == ""
        assert pack.evidence == ()
        assert pack.citations == ()


def test_packer_rejects_stale_contradictory_and_over_budget_evidence() -> None:
    packer = EvidencePacker(_exact_counter, bpm_version="0.9.3")
    stale = packer.pack(
        _result(
            _evidence("ragc-v1:en:stale:root:0", topic_id="stale", score=0.90, version="0.9.2")
        ),
        scope_admitted=True,
    )
    contradictory = packer.pack(
        _result(
            _evidence(
                "ragc-v1:en:same:root:0", topic_id="same", score=0.90, source_sha256="a" * 64
            ),
            _evidence(
                "ragc-v1:en:same:root:1",
                topic_id="same",
                score=0.60,
                ordinal=1,
                source_sha256="b" * 64,
            ),
        ),
        scope_admitted=True,
    )
    over_budget = EvidencePacker(
        _exact_counter, bpm_version="0.9.3", maximum_context_tokens=1
    ).pack(
        _result(_evidence("ragc-v1:en:large:root:0", topic_id="large", score=0.90)),
        scope_admitted=True,
    )

    assert stale.reason_code == "stale_evidence"
    assert contradictory.reason_code == "contradictory_evidence"
    assert over_budget.reason_code == "context_budget_exceeded"


def test_packer_rejects_an_invalid_exact_token_counter_or_configuration() -> None:
    with pytest.raises(EvidencePackingError, match="invalid_evidence_packing_configuration"):
        EvidencePacker(_exact_counter, bpm_version="", maximum_context_tokens=0)
    with pytest.raises(EvidencePackingError, match="invalid_evidence_packing_configuration"):
        EvidencePacker(_exact_counter, bpm_version="0.9.3", minimum_top_score=1.1)
    packer = EvidencePacker(lambda _: -1, bpm_version="0.9.3")
    with pytest.raises(EvidencePackingError, match="token_counter_returned_invalid_count"):
        packer.pack(
            _result(_evidence("ragc-v1:en:ok:root:0", topic_id="ok", score=0.90)),
            scope_admitted=True,
        )


def test_packer_rejects_unsafe_heading_duplicate_identity_and_failed_counter() -> None:
    candidate = _evidence("ragc-v1:en:ok:root:0", topic_id="ok", score=0.90)
    unsafe_heading = replace(candidate, heading_path=("ok", ""))
    unsafe = EvidencePacker(_exact_counter, bpm_version="0.9.3").pack(
        _result(unsafe_heading), scope_admitted=True
    )
    duplicate = EvidencePacker(_exact_counter, bpm_version="0.9.3").pack(
        _result(candidate, replace(candidate, ordinal=1)), scope_admitted=True
    )

    def _failed_counter(_: str) -> int:
        raise RuntimeError("counter unavailable")

    with pytest.raises(EvidencePackingError, match="token_counter_failed"):
        EvidencePacker(_failed_counter, bpm_version="0.9.3").pack(
            _result(candidate), scope_admitted=True
        )

    assert unsafe.reason_code == "unsafe_evidence"
    assert duplicate.reason_code == "duplicate_chunk_identity"


def test_packer_rejects_nonlocal_or_empty_evidence_fields() -> None:
    candidate = _evidence("ragc-v1:en:ok:root:0", topic_id="ok", score=0.90)
    nonlocal_candidate = replace(
        candidate, citation=replace(candidate.citation, source_kind="external")
    )
    empty_text = replace(candidate, text="")

    external = EvidencePacker(_exact_counter, bpm_version="0.9.3").pack(
        _result(nonlocal_candidate), scope_admitted=True
    )
    empty = EvidencePacker(_exact_counter, bpm_version="0.9.3").pack(
        _result(empty_text), scope_admitted=True
    )

    assert external.reason_code == empty.reason_code == "unsafe_evidence"


def test_packer_limits_selected_chunks_and_skips_oversized_later_context() -> None:
    limited = EvidencePacker(_exact_counter, bpm_version="0.9.3", maximum_chunks=1).pack(
        _result(
            _evidence("ragc-v1:en:a:root:0", topic_id="a", score=0.90),
            _evidence("ragc-v1:en:b:root:0", topic_id="b", score=0.80),
        ),
        scope_admitted=True,
    )
    large_text = "reviewed BPM documentation " * 280
    candidates = tuple(
        replace(
            _evidence(
                f"ragc-v1:en:large-{index}:root:0",
                topic_id=f"large-{index}",
                score=0.90 - index / 100,
            ),
            text=large_text,
        )
        for index in range(4)
    )
    bounded = EvidencePacker(
        _exact_counter,
        bpm_version="0.9.3",
        maximum_chunks=4,
        maximum_context_tokens=100_000,
    ).pack(_result(*candidates), scope_admitted=True)

    assert len(limited.evidence) == 1
    assert 0 < len(bounded.evidence) < len(candidates)
