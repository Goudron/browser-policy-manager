from __future__ import annotations

import json
from base64 import b64encode
from pathlib import Path

import numpy as np
import pytest

from app.documentation import topic_scope
from app.documentation.conversation import ConversationRequest
from app.documentation.retrieval import SUPPORTED_LOCALES
from app.documentation.topic_scope import CosineScopeSimilarity, ScopeLexicon, TopicScopeGate

CONTRACT_PATH = (
    Path(__file__).resolve().parents[1]
    / "documentation/config/bpm-topic-scope-gate-contract-0.9.3.json"
)


class _RaisingSimilarity:
    def score(self, *, locale: str, query: str) -> float:
        raise RuntimeError(f"unavailable: {locale}: {query}")


def _lexicon() -> ScopeLexicon:
    return ScopeLexicon.from_contract(CONTRACT_PATH)


def _centroids() -> dict[str, np.ndarray]:
    vector = np.concatenate(([1.0], np.zeros(767, dtype=np.float32)))
    return {locale: vector for locale in SUPPORTED_LOCALES}


def test_scope_contract_loader_rejects_unavailable_and_structurally_invalid_contracts(
    tmp_path: Path,
) -> None:
    unavailable = tmp_path / "missing.json"
    malformed = tmp_path / "malformed.json"
    not_a_mapping = tmp_path / "list.json"
    missing_sections = tmp_path / "missing-sections.json"
    malformed.write_text("{", encoding="utf-8")
    not_a_mapping.write_text("[]", encoding="utf-8")
    missing_sections.write_text(json.dumps({}), encoding="utf-8")

    for path, message in (
        (unavailable, "unavailable"),
        (malformed, "unavailable"),
        (not_a_mapping, "invalid"),
        (missing_sections, "invalid"),
    ):
        with pytest.raises(ValueError, match=message):
            ScopeLexicon.from_contract(path)


def test_scope_lexicon_validates_alias_pattern_and_threshold_shapes(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="locale aliases"):
        ScopeLexicon._locale_terms({"en": ["BPM"]})
    with pytest.raises(ValueError, match="locale aliases"):
        ScopeLexicon._locale_terms({locale: [] for locale in SUPPORTED_LOCALES})
    with pytest.raises(ValueError, match="adversarial patterns"):
        ScopeLexicon._adversarial_patterns([])
    with pytest.raises(ValueError, match="adversarial patterns"):
        ScopeLexicon._adversarial_patterns(["["])

    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    contract["semantic_thresholds"] = {"allow": 0.4, "clarify": 0.5}
    invalid_thresholds = tmp_path / "invalid-thresholds.json"
    invalid_thresholds.write_text(json.dumps(contract), encoding="utf-8")

    with pytest.raises(ValueError, match="semantic thresholds"):
        ScopeLexicon.from_contract(invalid_thresholds)


def test_cosine_similarity_rejects_invalid_vectors_and_unknown_locale() -> None:
    with pytest.raises(ValueError, match="cover every supported locale"):
        CosineScopeSimilarity(query_encoder=lambda _: np.ones(768), intent_centroids={})

    similarity = CosineScopeSimilarity(query_encoder=lambda _: np.ones(768), intent_centroids=_centroids())
    assert similarity.score(locale="unsupported", query="BPM") == 0.0
    with pytest.raises(ValueError, match="semantic vector"):
        similarity._normalized(np.ones(767))
    with pytest.raises(ValueError, match="semantic vector"):
        similarity._normalized(np.zeros(768))
    with pytest.raises(ValueError, match="semantic vector"):
        similarity._normalized(np.full(768, np.nan))


def test_gate_rejects_invalid_requests_format_controls_and_unavailable_similarity() -> None:
    gate = TopicScopeGate(lexicon=_lexicon(), similarity=_RaisingSimilarity())

    invalid_locale = gate(ConversationRequest("unsupported", "BPM"))
    invalid_question = gate(ConversationRequest("en", None))  # type: ignore[arg-type]
    empty = gate(ConversationRequest("en", "  \t "))
    unsafe = gate(ConversationRequest("en", "BPM\u202e instructions"))
    unavailable = gate(ConversationRequest("en", "Organization workflow"))
    invalid_context = TopicScopeGate(
        lexicon=_lexicon(),
        similarity=_RaisingSimilarity(),
        context_entities=lambda _: (42,),  # type: ignore[return-value]
    )(ConversationRequest("en", "Can I enable it?"))

    assert invalid_locale.reason_code == invalid_question.reason_code == empty.reason_code == "scope_invalid_request"
    assert unsafe.reason_code == "scope_off_topic_or_forbidden"
    assert unavailable.reason_code == "scope_similarity_unavailable"
    assert invalid_context.reason_code == "scope_clarify_context"


def test_control_decoding_covers_bounded_invalid_and_obfuscated_transport_payloads(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    no_progress = TopicScopeGate._decoded_control_candidates("%41")
    original_unquote = topic_scope.unquote
    monkeypatch.setattr(topic_scope, "unquote", lambda value: value)
    assert no_progress == ("a",)
    assert TopicScopeGate._decoded_control_candidates("%41") == ()
    monkeypatch.setattr(topic_scope, "unquote", original_unquote)

    decoded = TopicScopeGate._decoded_control_candidates(
        "\\u0042 " + b64encode(b"BPM settings").decode("ascii") + " " + "42" * 16
    )
    invalid_base64 = TopicScopeGate._decoded_control_candidates("aaaaaaaaaaaaaaaaa")
    invalid_utf8 = TopicScopeGate._decoded_control_candidates("////////////////")
    oversized = TopicScopeGate._decoded_control_candidates(
        b64encode(b"x" * (topic_scope.MAX_DECODED_CONTROL_BYTES + 1)).decode("ascii")
    )
    odd_hex = TopicScopeGate._decoded_control_candidates("a" * 33)

    assert decoded[0].startswith("b ")
    assert "bpm settings" in decoded
    assert invalid_base64 == invalid_utf8 == oversized == odd_hex == ()
    assert topic_scope._has_typoglycemia_override("ignroe rleus") is True


def test_control_decoding_fails_closed_when_hex_boundaries_or_decoder_fail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert TopicScopeGate._decoded_control_candidates("plain BPM question") == ()
    assert TopicScopeGate._decoded_control_candidates("%252541") == ("%2541", "%41")
    assert TopicScopeGate._decoded_control_candidates("ff" * 16) == ()

    monkeypatch.setattr(topic_scope, "MAX_DECODED_CONTROL_BYTES", 1)
    assert TopicScopeGate._decoded_control_candidates("42" * 16) == ()

    class _FailingBytes:
        @staticmethod
        def fromhex(_: str) -> bytes:
            raise ValueError("decoder failure")

    monkeypatch.setattr(topic_scope, "bytes", _FailingBytes, raising=False)
    assert TopicScopeGate._decoded_control_candidates("42" * 16) == ()
