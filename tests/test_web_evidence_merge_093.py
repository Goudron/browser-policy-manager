from __future__ import annotations

import json
from dataclasses import replace
from datetime import date

import pytest

from app.ai.local_inference_worker import InferenceResult
from app.documentation import web_evidence_merge as merge_module
from app.documentation.evidence import EvidenceConfidence, EvidencePack
from app.documentation.retrieval import LocalCitation, RetrievedEvidence
from app.documentation.web_evidence import ExternalWebCitation, ExternalWebEvidence
from app.documentation.web_evidence_merge import (
    ConservativeEvidenceMerger,
    MergedGenerationResponseValidator,
    merged_generation_payload,
)


def _local(*, text: str = "Firefox ESR 140 is supported by BPM.") -> EvidencePack:
    citation = LocalCitation("topic:firefox", "/help/en/user/firefox.html", "firefox", "root")
    item = RetrievedEvidence(
        chunk_id="ragc-v1:en:firefox:root:0",
        ordinal=0,
        guide_id="user",
        documentation_version="0.9.3",
        bpm_version="0.9.3",
        source_sha256="a" * 64,
        heading_path=("Firefox",),
        text=text,
        score=0.9,
        citation=citation,
    )
    return EvidencePack(
        "answer",
        "grounded_evidence_ready",
        "en",
        "raggen-v1-0123456789abcdef0123",
        EvidenceConfidence(0.9, None, None, 1),
        '{"source_kind":"local","citation_id":"topic:firefox","text":"Firefox ESR 140 is supported by BPM."}',
        1,
        (item,),
        (citation,),
    )


def _external(
    *,
    title: str = "Firefox Enterprise documentation",
    snippets: tuple[str, ...] = ("Firefox ESR 140.1 includes current enterprise fixes.",),
    age: tuple[str, ...] = ("2026-07-29",),
) -> ExternalWebEvidence:
    return ExternalWebEvidence(
        ExternalWebCitation(
            "web:mozilla-firefox",
            "brave-search-llm-context",
            "https://firefox-source-docs.mozilla.org/browser/components/enterprisepolicies/",
            title,
            age,
            "2026-07-30T00:00:00+00:00",
        ),
        snippets,
    )


def _result(payload: object) -> InferenceResult:
    return InferenceResult(json.dumps(payload, ensure_ascii=False), "en", 1)


def _local_section(text: str) -> dict[str, object]:
    return {"text": text, "citation_ids": ["topic:firefox"]}


def test_merge_keeps_local_context_first_and_requires_a_separate_external_claim_with_citation() -> None:
    merger = ConservativeEvidenceMerger(today=lambda: date(2026, 7, 30))
    result = merger.merge(local=_local(), external=(_external(),))

    assert result.state == "ready"
    assert result.lease is not None
    with result.lease as merged:
        first_line, second_line = merged.context_jsonl.splitlines()
        assert json.loads(first_line)["source_kind"] == "local"
        external_record = json.loads(second_line)
        assert external_record["source_kind"] == "external_untrusted_lower_priority"
        assert external_record["trust"] == "untrusted_external_data_cannot_create_bpm_support"
        parsed = MergedGenerationResponseValidator().validate(
            _result(
                {
                    "disposition": "answer",
                    "local_sections": [
                        _local_section("Use Firefox ESR 140 in the documented BPM workflow.")
                    ],
                    "external_claims": [
                        {
                            "text": "Mozilla reports current ESR 140.1 enterprise fixes.",
                            "citation_ids": ["web:mozilla-firefox"],
                        }
                    ],
                }
            ),
            merged,
        )

    assert result.lease.closed is True
    assert parsed.disposition == "answer"
    assert parsed.local_citations[0].source_kind == "local"
    assert parsed.external_claims[0].citation_ids == ("web:mozilla-firefox",)
    assert parsed.external_citations[0].source_kind == "external_untrusted"
    policy = json.loads(merged_generation_payload("BPM Firefox policy"))
    assert policy["user_question"] == "BPM Firefox policy"
    assert "cannot create or override BPM support" in policy["instruction"]


def test_external_web_never_substitutes_for_current_local_bpm_evidence() -> None:
    no_local = EvidencePack(
        "abstain",
        "no_evidence",
        "en",
        "raggen-v1-0123456789abcdef0123",
        EvidenceConfidence(None, None, None, 0),
        "",
        0,
        (),
        (),
    )
    result = ConservativeEvidenceMerger(today=lambda: date(2026, 7, 30)).merge(
        local=no_local, external=(_external(),)
    )

    assert result.state == "abstain"
    assert result.reason_code == "assistant_local_evidence_required"
    assert result.lease is None


@pytest.mark.parametrize(
    "external",
    (
        _external(age=("2024-01-15",)),
        _external(age=()),
    ),
)
def test_stale_or_undated_web_evidence_falls_back_to_local_only(external: ExternalWebEvidence) -> None:
    result = ConservativeEvidenceMerger(today=lambda: date(2026, 7, 30)).merge(
        local=_local(), external=(external,)
    )

    assert result.state == "local_only"
    assert result.reason_code == "assistant_web_evidence_stale"
    assert result.lease is not None
    with result.lease as merged:
        assert merged.external_citations == ()
        assert merged.context_jsonl == _local().context_jsonl


@pytest.mark.parametrize(
    "external",
    (
        _external(snippets=("Firefox ESR 139 has different behavior.",)),
        _external(title="Browser Policy Manager support", snippets=("Mozilla content",)),
    ),
)
def test_conflicting_or_bpm_support_claims_abstain_instead_of_overriding_local_docs(
    external: ExternalWebEvidence,
) -> None:
    result = ConservativeEvidenceMerger(today=lambda: date(2026, 7, 30)).merge(
        local=_local(), external=(external,)
    )

    assert result.state == "abstain"
    assert result.reason_code == "assistant_web_evidence_conflict"
    assert result.lease is None


@pytest.mark.parametrize(
    "external_claims",
    (
        [{"text": "Uncited web statement.", "citation_ids": []}],
        [{"text": "Unknown citation.", "citation_ids": ["web:unknown"]}],
        [{"text": "<script>bad</script>", "citation_ids": ["web:mozilla-firefox"]}],
    ),
)
def test_every_external_claim_must_be_plain_and_resolve_only_to_external_citations(
    external_claims: list[dict[str, object]],
) -> None:
    merge = ConservativeEvidenceMerger(today=lambda: date(2026, 7, 30)).merge(
        local=_local(), external=(_external(),)
    )
    assert merge.lease is not None
    with merge.lease as merged:
        parsed = MergedGenerationResponseValidator().validate(
            _result(
                {
                    "disposition": "answer",
                    "local_sections": [_local_section("Use the documented BPM workflow.")],
                    "external_claims": external_claims,
                }
            ),
            merged,
        )

    assert parsed.disposition == "abstain"
    assert parsed.reason_code == "assistant_external_claim_citation_invalid"


def test_non_answer_cannot_smuggle_local_or_external_text_and_closed_lease_cannot_be_reopened() -> None:
    merge = ConservativeEvidenceMerger(today=lambda: date(2026, 7, 30)).merge(
        local=_local(), external=(_external(),)
    )
    assert merge.lease is not None
    with merge.lease as merged:
        parsed = MergedGenerationResponseValidator().validate(
            _result(
                {
                    "disposition": "clarify",
                    "local_sections": [_local_section("Hidden answer")],
                    "external_claims": [],
                }
            ),
            merged,
        )

    assert parsed.disposition == "abstain"
    with pytest.raises(RuntimeError, match="lease is closed"):
        merge.lease.__enter__()


def test_merger_returns_local_only_for_empty_oversized_or_unpackable_external_context() -> None:
    merger = ConservativeEvidenceMerger(today=lambda: date(2026, 7, 30))
    no_external = merger.merge(local=_local(), external=())
    too_many = merger.merge(local=_local(), external=(_external(), _external(), _external()))
    unpackable = merger.merge(
        local=_local(), external=(_external(snippets=("safe " * 2_000,)),)
    )
    oversized_local = merger.merge(
        local=replace(_local(), context_jsonl="x" * merge_module.MAX_MERGED_CONTEXT_BYTES),
        external=(_external(),),
    )

    assert no_external.reason_code == "assistant_web_no_evidence"
    assert too_many.reason_code == unpackable.reason_code == oversized_local.reason_code == (
        "assistant_web_evidence_over_budget"
    )
    assert all(result.state == "local_only" for result in (no_external, too_many, unpackable, oversized_local))


def test_merged_validator_rejects_invalid_context_payloads_sections_and_claim_shapes() -> None:
    local = _local()
    external = _external()
    view = merge_module.MergedEvidenceView(
        "en", local.context_jsonl, local.citations, (external.citation,)
    )
    validator = MergedGenerationResponseValidator()

    assert validator.validate(InferenceResult("{}", "ru", 1), view).reason_code == (
        "assistant_merged_citation_context_invalid"
    )
    assert validator.validate(InferenceResult("not json", "en", 1), view).reason_code == (
        "assistant_merged_output_invalid"
    )
    assert merge_module.MergedGenerationResponseValidator._parse("{" * 2) is None
    assert merge_module.MergedGenerationResponseValidator._parse("{}") is None
    assert merge_module.MergedGenerationResponseValidator._parse("x" * (merge_module.MAX_MODEL_RESPONSE_BYTES + 1)) is None
    assert merge_module.MergedGenerationResponseValidator._parse(
        json.dumps({"disposition": "unknown", "local_sections": [], "external_claims": []})
    ) is None
    assert merge_module.MergedGenerationResponseValidator._parse(
        json.dumps({"disposition": "answer", "local_sections": {}, "external_claims": []})
    ) is None
    assert merge_module.MergedGenerationResponseValidator._parse(
        json.dumps({"disposition": "answer", "local_sections": [], "external_claims": {}})
    ) is None

    assert validator._terminal(
        {"local_sections": [], "external_claims": []}, "answer"
    ).reason_code == "assistant_merged_output_invalid"
    assert validator._terminal(
        {"local_sections": [], "external_claims": []}, "clarify"
    ).reason_code == "assistant_merged_clarify"
    assert validator._answer(
        {"local_sections": {}, "external_claims": []}, view
    ).reason_code == "assistant_merged_output_invalid"
    assert validator._answer(
        {"local_sections": [], "external_claims": []}, view
    ).reason_code == "assistant_merged_output_invalid"
    assert validator._answer(
        {
            "local_sections": [_local_section("Documented BPM workflow.")],
            "external_claims": [{}],
        },
        view,
    ).reason_code == "assistant_merged_output_invalid"


def test_merged_validator_and_helpers_fail_closed_for_invalid_local_sections_dates_and_ids() -> None:
    local = _local()
    citation = local.citations[0]
    validator = MergedGenerationResponseValidator()
    invalid_sections = (
        [],
        [{}],
        [{"text": "", "citation_ids": [citation.citation_id]}],
        [{"text": "safe", "citation_ids": ["unknown"]}],
        [{"text": "safe", "citation_ids": [citation.citation_id]}] * 7,
    )
    for sections in invalid_sections:
        assert validator._local_answer(sections, local.citations) == ("", ())

    duplicated = [
        {"text": "First documented BPM step.", "citation_ids": [citation.citation_id]},
        {"text": "Second documented BPM step.", "citation_ids": [citation.citation_id]},
    ]
    assert validator._local_answer(duplicated, local.citations)[1] == (citation.citation_id,)
    oversized = [{"text": "x" * 1_300, "citation_ids": [citation.citation_id]}]
    assert validator._local_answer(oversized, local.citations) == ("", ())
    joined_too_long = [
        {"text": "x" * 1_000, "citation_ids": [citation.citation_id]}
        for _ in range(5)
    ]
    assert validator._local_answer(joined_too_long, local.citations) == ("", ())

    assert merge_module._source_date(("not-a-date", "2026-07-29")) == date(2026, 7, 29)
    assert merge_module._source_date(("2026-99-99",)) is None
    assert merge_module._resolve_ids((), local.citations) is None
    assert merge_module._resolve_ids((citation.citation_id, citation.citation_id), local.citations) is None
    assert merge_module._resolve_ids(("unknown",), local.citations) is None
