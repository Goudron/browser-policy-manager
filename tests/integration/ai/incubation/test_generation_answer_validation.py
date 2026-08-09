from __future__ import annotations

import json
from dataclasses import replace

from app.ai.local_inference_worker import InferenceResult
from app.documentation.answer_validation import GenerationResponseValidator
from app.documentation.evidence import EvidenceConfidence, EvidencePack
from app.documentation.retrieval import LocalCitation, RetrievedEvidence


def _evidence(*, citation: LocalCitation | None = None) -> EvidencePack:
    actual_citation = citation or LocalCitation(
        "topic:alpha", "/help/en/user/alpha.html", "alpha", "root"
    )
    item = RetrievedEvidence(
        chunk_id="ragc-v1:en:alpha:root:0",
        ordinal=0,
        guide_id="user",
        documentation_version="0.9.3",
        bpm_version="0.9.3",
        source_sha256="a" * 64,
        heading_path=("Alpha",),
        text="Approved extractive BPM evidence.",
        score=0.9,
        citation=actual_citation,
    )
    return EvidencePack(
        "answer",
        "grounded_evidence_ready",
        "en",
        "raggen-v1-0123456789abcdef0123",
        EvidenceConfidence(0.9, None, None, 1),
        "{}",
        1,
        (item,),
        (actual_citation,),
    )


def _result(payload: object, locale: str = "en") -> InferenceResult:
    return InferenceResult(json.dumps(payload, ensure_ascii=False), locale, 1)


def _answer(*sections: dict[str, object]) -> dict[str, object]:
    return {"disposition": "answer", "sections": list(sections)}


def _section(text: str, citation_ids: list[str] | None = None) -> dict[str, object]:
    return {"text": text, "citation_ids": citation_ids or ["topic:alpha"]}


def test_validator_accepts_only_structured_own_word_sections_with_approved_local_citations() -> (
    None
):
    validator = GenerationResponseValidator()

    parsed = validator(
        _result(_answer(_section("Configure the documented setting before applying the profile."))),
        _evidence(),
    )

    assert parsed.disposition == "answer"
    assert parsed.reason_code == "assistant_citations_validated"
    assert parsed.citation_ids == ("topic:alpha",)
    assert parsed.text == "Configure the documented setting before applying the profile."


def test_validator_composes_multiple_grounded_sections_and_deduplicates_source_list() -> None:
    parsed = GenerationResponseValidator()(
        _result(
            _answer(
                _section("First use the documented workflow for the selected profile."),
                _section("Then validate the saved policy before deploying it."),
            )
        ),
        _evidence(),
    )

    assert parsed.disposition == "answer"
    assert parsed.text == (
        "First use the documented workflow for the selected profile.\n\n"
        "Then validate the saved policy before deploying it."
    )
    assert parsed.citation_ids == ("topic:alpha",)


def test_invalid_model_shape_markup_unknown_or_duplicate_citation_abstains() -> None:
    validator = GenerationResponseValidator()
    evidence = _evidence()
    invalid_payloads = [
        "not JSON",
        {
            "disposition": "answer",
            "sections": [_section("<a href='https://bad'>bad</a>")],
        },
        _answer(_section("unsupported", ["topic:other"])),
        _answer(_section("duplicate", ["topic:alpha", "topic:alpha"])),
        {"disposition": "answer", "text": "missing fields"},
    ]

    for payload in invalid_payloads:
        raw = InferenceResult(payload, "en", 1) if isinstance(payload, str) else _result(payload)
        parsed = validator(raw, evidence)
        assert parsed.disposition == "abstain"
        assert parsed.reason_code in {"assistant_output_invalid", "assistant_invalid_citations"}
        assert parsed.text == ""
        assert parsed.citation_ids == ()


def test_nonanswer_cannot_carry_model_sections_and_unsafe_source_abstains() -> None:
    validator = GenerationResponseValidator()

    clarify = validator(_result({"disposition": "clarify", "sections": []}), _evidence())
    invalid_clarify = validator(
        _result({"disposition": "clarify", "sections": [_section("invented")]}), _evidence()
    )
    unsafe = LocalCitation("topic:alpha", "https://example.invalid/alpha", "alpha", "root")
    unsafe_outcome = validator(
        _result(_answer(_section("answer"))),
        _evidence(citation=unsafe),
    )

    assert clarify.disposition == "clarify"
    assert clarify.reason_code == "assistant_clarify"
    assert invalid_clarify.disposition == "abstain"
    assert invalid_clarify.reason_code == "assistant_output_invalid"
    assert unsafe_outcome.disposition == "abstain"
    assert unsafe_outcome.reason_code == "assistant_citation_context_invalid"


def test_validator_rejects_locale_mismatch_before_using_evidence() -> None:
    validator = GenerationResponseValidator()
    result = replace(
        _result(_answer(_section("answer"))),
        locale="ru",
    )

    parsed = validator(result, _evidence())

    assert parsed.disposition == "abstain"
    assert parsed.reason_code == "assistant_citation_context_invalid"


def test_validator_rejects_a_long_contiguous_quote_from_the_cited_evidence() -> None:
    extract = (
        "Approved extractive BPM evidence describes a supported documented configuration workflow "
        "with validated profile application steps and an explicit verification stage."
    )
    citation = LocalCitation("topic:alpha", "/help/en/user/alpha.html", "alpha", "root")
    evidence = _evidence(citation=citation)
    item = replace(evidence.evidence[0], text=extract)
    quoted_evidence = replace(evidence, evidence=(item,))

    validator = GenerationResponseValidator()
    result = _result(_answer(_section(extract)))
    parsed = validator(result, quoted_evidence)
    rewrite = validator.candidate_for_excessive_quote(result, quoted_evidence)

    assert parsed.disposition == "abstain"
    assert parsed.reason_code == "assistant_excessive_quotation"
    assert rewrite is not None
    assert rewrite.draft == extract
    assert rewrite.citation_ids == ("topic:alpha",)


def test_validator_never_exposes_a_rewrite_candidate_for_other_invalid_output() -> None:
    validator = GenerationResponseValidator()
    evidence = _evidence()

    assert (
        validator.candidate_for_excessive_quote(
            _result(_answer(_section("unsupported", ["topic:other"]))), evidence
        )
        is None
    )
    assert (
        validator.candidate_for_excessive_quote(
            _result({"disposition": "abstain", "sections": []}), evidence
        )
        is None
    )


def test_validator_covers_all_terminal_payload_and_candidate_rejections() -> None:
    validator = GenerationResponseValidator()
    evidence = _evidence()

    assert validator(_result({"disposition": "unknown", "sections": []}), evidence).reason_code == (
        "assistant_output_invalid"
    )
    assert validator(_result({"disposition": "answer", "sections": {}}), evidence).reason_code == (
        "assistant_output_invalid"
    )
    assert validator(_result({"disposition": "abstain", "sections": []}), evidence).reason_code == (
        "assistant_abstain"
    )
    assert validator(_result({"disposition": "refuse", "sections": []}), evidence).reason_code == (
        "assistant_refuse"
    )
    assert (
        validator.candidate_for_excessive_quote(
            replace(_result(_answer(_section("safe"))), locale="ru"), evidence
        )
        is None
    )
    assert (
        validator.candidate_for_excessive_quote(
            _result({"disposition": "answer", "sections": {}}), evidence
        )
        is None
    )
    assert validator._parse_object("x" * (16 * 1024 + 1)) is None


def test_validator_rejects_invalid_section_bounds_answer_length_and_citation_identity() -> None:
    validator = GenerationResponseValidator()
    evidence = _evidence()
    assert (
        validator._assess_answer_sections([], {"topic:alpha": evidence.citations[0]}, evidence)
        is None
    )
    assert (
        validator._assess_answer_sections(
            ["not-a-section"], {"topic:alpha": evidence.citations[0]}, evidence
        )
        is None
    )
    oversized_answer = [_section("x" * 1_000) for _ in range(5)]
    assert (
        validator._assess_answer_sections(
            oversized_answer, {"topic:alpha": evidence.citations[0]}, evidence
        )
        is None
    )

    duplicate = replace(evidence, citations=(evidence.citations[0], evidence.citations[0]))
    assert validator._approved_citations(duplicate) == {}
    for citation in (
        replace(evidence.citations[0], source_kind="external"),
        replace(evidence.citations[0], anchor_id_or_root="section"),
        replace(evidence.citations[0], citation_id="topic:other"),
    ):
        assert validator._safe_local_citation(citation, "en") is False


def test_quote_check_skips_evidence_not_supporting_the_section() -> None:
    evidence = _evidence()
    other = LocalCitation("topic:other", "/help/en/user/other.html", "other", "root")
    resolution = GenerationResponseValidator()._resolve_all(
        ("topic:alpha",), {"topic:alpha": evidence.citations[0]}
    )

    assert resolution is not None
    unsupported = replace(evidence.evidence[0], citation=other)
    assert (
        GenerationResponseValidator._contains_excessive_evidence_quote(
            "x" * 100, resolution, replace(evidence, evidence=(unsupported,))
        )
        is False
    )
