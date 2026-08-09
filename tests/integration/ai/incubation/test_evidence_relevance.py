from __future__ import annotations

import pytest

from app.documentation.conversation import ConversationRequest
from app.documentation.evidence_relevance import EvidenceRelevanceGate
from app.documentation.retrieval import LocalCitation, RetrievalResult, RetrievedEvidence


def _candidate(
    locale: str,
    *,
    topic_id: str,
    text: str,
    guide_id: str = "administrator-guide",
    identifiers: tuple[str, ...] = (),
    score: float = 0.9,
) -> RetrievedEvidence:
    return RetrievedEvidence(
        chunk_id=f"ragc-v1:{locale}:{topic_id}:root:0",
        ordinal=0,
        guide_id=guide_id,
        documentation_version="0.9.3",
        bpm_version="0.9.3",
        source_sha256="a" * 64,
        heading_path=(topic_id,),
        text=text,
        score=score,
        citation=LocalCitation(
            f"topic:{topic_id}", f"/help/{locale}/admin/{topic_id}.html", topic_id, "root"
        ),
        identifiers=identifiers,
    )


@pytest.mark.parametrize(
    ("locale", "question", "matching_text"),
    [
        ("en", "How do I install BPM on Ubuntu 26.04?", "Install BPM on Ubuntu 26.04."),
        ("ru", "Как установить BPM на Ubuntu 26.04?", "Установка BPM в Ubuntu 26.04."),
        ("de", "Wie installiere ich BPM auf Ubuntu 26.04?", "BPM unter Ubuntu 26.04 installieren."),
        ("zh-CN", "如何在 Ubuntu 26.04 上安装 BPM？", "在 Ubuntu 26.04 上安装 BPM。"),
        ("fr", "Comment installer BPM sur Ubuntu 26.04 ?", "Installer BPM sur Ubuntu 26.04."),
        ("es-ES", "¿Cómo instalar BPM en Ubuntu 26.04?", "Instalar BPM en Ubuntu 26.04."),
    ],
)
def test_platform_release_relevance_keeps_the_published_ubuntu_context(
    locale: str, question: str, matching_text: str
) -> None:
    correct = _candidate(locale, topic_id="ubuntu-26-04", text=matching_text, score=0.70)
    debian = _candidate(
        locale,
        topic_id="debian-13-5",
        text="Install BPM from source on Debian 13.5.",
        score=0.95,
    )

    decision = EvidenceRelevanceGate().filter(
        ConversationRequest(locale, question),
        RetrievalResult("raggen-v1-0123456789abcdef0123", locale, (debian, correct)),
    )

    assert decision.reason_code == "assistant_relevance_ready"
    assert decision.result.candidates == (correct,)


def test_topic_identifier_role_and_bpm_version_must_all_match() -> None:
    matching = _candidate(
        "en",
        topic_id="aicontrols-admin",
        text="Configure the AIControls policy in BPM 0.9.3.",
        identifiers=("AIControls",),
    )
    wrong_role = _candidate(
        "en",
        topic_id="aicontrols-user",
        text="Configure the AIControls policy in BPM 0.9.3.",
        guide_id="user-guide",
        identifiers=("AIControls",),
    )
    wrong_identifier = _candidate(
        "en",
        topic_id="extensions-admin",
        text="Configure ExtensionSettings in BPM 0.9.3.",
        identifiers=("ExtensionSettings",),
    )
    wrong_version = _candidate(
        "en",
        topic_id="aicontrols-old",
        text="Configure AIControls in BPM 0.9.2.",
        identifiers=("AIControls",),
    )

    decision = EvidenceRelevanceGate().filter(
        ConversationRequest("en", "How can an administrator configure AIControls in BPM 0.9.3?"),
        RetrievalResult(
            "raggen-v1-0123456789abcdef0123",
            "en",
            (wrong_role, wrong_identifier, wrong_version, matching),
        ),
    )

    assert decision.reason_code == "assistant_relevance_ready"
    assert decision.result.candidates == (matching,)


def test_conflicting_or_cross_locale_candidates_fail_closed_before_evidence_packing() -> None:
    debian = _candidate(
        "ru", topic_id="debian-13-5", text="Установка BPM из исходников в Debian 13.5."
    )
    no_match = EvidenceRelevanceGate().filter(
        ConversationRequest("ru", "Как установить BPM на Ubuntu?"),
        RetrievalResult("raggen-v1-0123456789abcdef0123", "ru", (debian,)),
    )
    wrong_locale = EvidenceRelevanceGate().filter(
        ConversationRequest("ru", "Как установить BPM?"),
        RetrievalResult("raggen-v1-0123456789abcdef0123", "en", (debian,)),
    )

    assert no_match.result.candidates == ()
    assert no_match.reason_code == "assistant_relevance_no_matching_evidence"
    assert wrong_locale.result.candidates == ()
    assert wrong_locale.reason_code == "assistant_relevance_locale_mismatch"


def test_platform_release_constraint_rejects_a_different_ubuntu_release() -> None:
    wrong_release = _candidate("en", topic_id="ubuntu-24-04", text="Install BPM on Ubuntu 24.04.")

    decision = EvidenceRelevanceGate().filter(
        ConversationRequest("en", "How do I install BPM on Ubuntu 26.04?"),
        RetrievalResult("raggen-v1-0123456789abcdef0123", "en", (wrong_release,)),
    )

    assert decision.reason_code == "assistant_relevance_no_matching_evidence"
    assert decision.result.candidates == ()


def test_empty_same_locale_retrieval_is_already_relevance_ready() -> None:
    result = RetrievalResult("raggen-v1-0123456789abcdef0123", "en", ())

    decision = EvidenceRelevanceGate().filter(
        ConversationRequest("en", "How do I configure BPM?"), result
    )

    assert decision.reason_code == "assistant_relevance_ready"
    assert decision.result is result
