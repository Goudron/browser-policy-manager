from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pytest

from app.ai.local_inference_worker import InferenceRequest, InferenceResult
from app.documentation.conversation import (
    ConversationRequest,
    GroundedConversationOrchestrator,
    ParsedGeneration,
    ScopeDecision,
)
from app.documentation.conversation_context import (
    ABSOLUTE_SESSION_TTL_SECONDS,
    IDLE_SESSION_TTL_SECONDS,
    MAX_CONTEXT_PAIRS,
    MAX_CONTEXT_TURNS,
    ConversationContextStore,
    ConversationContextUnavailable,
)
from app.documentation.evidence import EvidencePacker
from app.documentation.retrieval import LocalCitation, RetrievalResult, RetrievedEvidence


def _citation(topic: str) -> LocalCitation:
    return LocalCitation(f"topic:{topic}", f"/help/en/user/{topic}.html", topic, "root")


def _result(topic: str) -> RetrievalResult:
    citation = _citation(topic)
    return RetrievalResult(
        "raggen-v1-0123456789abcdef0123",
        "en",
        (
            RetrievedEvidence(
                chunk_id=f"ragc-v1:en:{topic}:root:0",
                ordinal=0,
                guide_id="user",
                documentation_version="0.9.3",
                bpm_version="0.9.3",
                source_sha256="a" * 64,
            heading_path=(topic,),
            text=f"Approved BPM {topic} evidence.",
            score=0.9,
            citation=citation,
            identifiers=("ESR",) if topic == "firefox-esr" else (),
        ),
        ),
    )


@dataclass
class _Retriever:
    result: RetrievalResult
    queries: list[str] = field(default_factory=list)

    def retrieve(self, *, locale: str, query_vector: np.ndarray, limit: int) -> RetrievalResult:
        assert locale == "en" and query_vector.shape == (768,) and limit == 5
        return self.result


@dataclass
class _Worker:
    requests: list[InferenceRequest] = field(default_factory=list)

    def generate(self, request: InferenceRequest) -> InferenceResult:
        self.requests.append(request)
        return InferenceResult("raw", request.locale, 1)


def _orchestrator(
    store: ConversationContextStore,
    retriever: _Retriever,
    worker: _Worker,
    parsed: list[ParsedGeneration],
) -> GroundedConversationOrchestrator:
    def encode(question: str) -> np.ndarray:
        retriever.queries.append(question)
        return np.concatenate(([1.0], np.zeros(767, dtype=np.float32)))

    def parse(_: InferenceResult, __: object) -> ParsedGeneration:
        return parsed.pop(0)

    return GroundedConversationOrchestrator(
        scope_gate=lambda _: ScopeDecision("allow", "scope_allowed"),
        query_encoder=encode,
        retriever=retriever,
        evidence_packer=EvidencePacker(lambda value: len(value.split()), bpm_version="0.9.3"),
        worker=worker,  # type: ignore[arg-type]  # Narrow generation protocol is deliberate.
        generation_parser=parse,
        context_store=store,
        bpm_version="0.9.3",
    )


def test_same_locale_follow_up_uses_bounded_resolved_context_and_new_citation() -> None:
    store = ConversationContextStore()
    session_id = store.create(locale="en", bpm_version="0.9.3")
    retriever = _Retriever(_result("firefox-esr"))
    worker = _Worker()
    orchestrator = _orchestrator(
        store,
        retriever,
        worker,
        [
            ParsedGeneration("answer", "Use ESR 140.", ("topic:firefox-esr",), ("ESR 140",)),
            ParsedGeneration("answer", "ESR remains supported.", ("topic:firefox-esr",)),
        ],
    )

    first = orchestrator.ask(
        ConversationRequest("en", "ESR?", session_id=session_id)
    )
    follow_up = orchestrator.ask(
        ConversationRequest("en", "ESR?", session_id=session_id)
    )

    assert first.disposition == follow_up.disposition == "answer"
    assert "Resolved BPM entities: ESR 140, firefox-esr" in retriever.queries[1]
    assert tuple(worker.requests[1].dialogue) == (
        ("user", "ESR?"),
        ("assistant", "Use ESR 140."),
    )
    assert [citation.citation_id for citation in follow_up.citations] == ["topic:firefox-esr"]


def test_topic_change_keeps_bounded_dialogue_but_never_reuses_old_citations() -> None:
    store = ConversationContextStore()
    session_id = store.create(locale="en", bpm_version="0.9.3")
    retriever = _Retriever(_result("alpha"))
    worker = _Worker()
    orchestrator = _orchestrator(
        store,
        retriever,
        worker,
        [
            ParsedGeneration("answer", "Alpha answer.", ("topic:alpha",)),
            ParsedGeneration("answer", "Beta answer.", ("topic:beta",)),
        ],
    )
    assert (
        orchestrator.ask(ConversationRequest("en", "Alpha?", session_id=session_id)).disposition
        == "answer"
    )

    retriever.result = _result("beta")
    changed = orchestrator.ask(ConversationRequest("en", "Beta?", session_id=session_id))

    assert changed.disposition == "answer"
    assert [citation.citation_id for citation in changed.citations] == ["topic:beta"]
    assert worker.requests[1].dialogue == (
        ("user", "Alpha?"),
        ("assistant", "Alpha answer."),
    )
    snapshot = store.snapshot(session_id=session_id, locale="en", bpm_version="0.9.3")
    assert snapshot.topic_ids == ("beta",)
    assert [turn.text for turn in snapshot.turns] == [
        "Alpha?",
        "Alpha answer.",
        "Beta?",
        "Beta answer.",
    ]

    stale_session = store.create(locale="en", bpm_version="0.9.2")
    before = len(retriever.queries)
    stale = orchestrator.ask(ConversationRequest("en", "Question", session_id=stale_session))
    assert stale.reason_code == "assistant_session_version_changed"
    assert len(retriever.queries) == before


def test_eviction_and_clear_remove_old_memory_deterministically() -> None:
    store = ConversationContextStore()
    session_id = store.create(locale="en", bpm_version="0.9.3")
    citation = _citation("alpha")
    for number in range(9):
        store.record(
            session_id=session_id,
            locale="en",
            bpm_version="0.9.3",
            question=f"question-{number}",
            answer=f"answer-{number}",
            citations=(citation,),
        )
    snapshot = store.snapshot(session_id=session_id, locale="en", bpm_version="0.9.3")

    assert MAX_CONTEXT_PAIRS == 8
    assert len(snapshot.turns) == MAX_CONTEXT_TURNS == 16
    assert [(turn.role, turn.text) for turn in snapshot.turns] == [
        pair
        for number in range(1, 9)
        for pair in (("user", f"question-{number}"), ("assistant", f"answer-{number}"))
    ]
    assert store.clear(session_id) is True
    assert store.clear(session_id) is False
    with pytest.raises(ConversationContextUnavailable, match="assistant_session_unavailable"):
        store.snapshot(session_id=session_id, locale="en", bpm_version="0.9.3")


def test_idle_absolute_expiry_clear_all_and_process_restart_retain_no_context() -> None:
    now = 0.0
    store = ConversationContextStore(
        idle_ttl_seconds=5.0,
        absolute_ttl_seconds=10.0,
        clock=lambda: now,
    )
    session_id = store.create(locale="en", bpm_version="0.9.3")
    now = 4.0
    assert store.snapshot(session_id=session_id, locale="en", bpm_version="0.9.3").turns == ()
    now = 9.0
    with pytest.raises(ConversationContextUnavailable, match="assistant_session_expired"):
        store.snapshot(session_id=session_id, locale="en", bpm_version="0.9.3")

    absolute_store = ConversationContextStore(
        idle_ttl_seconds=100.0,
        absolute_ttl_seconds=10.0,
        clock=lambda: now,
    )
    now = 0.0
    absolute_session = absolute_store.create(locale="en", bpm_version="0.9.3")
    now = 9.0
    absolute_store.snapshot(session_id=absolute_session, locale="en", bpm_version="0.9.3")
    now = 10.0
    with pytest.raises(ConversationContextUnavailable, match="assistant_session_expired"):
        absolute_store.snapshot(session_id=absolute_session, locale="en", bpm_version="0.9.3")

    fresh = store.create(locale="en", bpm_version="0.9.3")
    assert store.clear_all() == 1
    with pytest.raises(ConversationContextUnavailable, match="assistant_session_unavailable"):
        store.snapshot(session_id=fresh, locale="en", bpm_version="0.9.3")
    assert ConversationContextStore().clear_expired() == 0
    assert IDLE_SESSION_TTL_SECONDS == 900.0
    assert ABSOLUTE_SESSION_TTL_SECONDS == 28_800.0


def test_ninth_answer_evicts_only_the_oldest_of_eight_grounded_pairs() -> None:
    store = ConversationContextStore()
    session_id = store.create(locale="en", bpm_version="0.9.3")
    retriever = _Retriever(_result("alpha"))
    worker = _Worker()
    orchestrator = _orchestrator(
        store,
        retriever,
        worker,
        [
            ParsedGeneration("answer", f"answer-{number}", ("topic:alpha",))
            for number in range(9)
        ],
    )

    for number in range(9):
        outcome = orchestrator.ask(
            ConversationRequest("en", f"alpha {number}?", session_id=session_id)
        )
        assert outcome.disposition == "answer"

    assert len(worker.requests[8].dialogue) == 16
    assert worker.requests[8].dialogue[0] == ("user", "alpha 0?")
    snapshot = store.snapshot(session_id=session_id, locale="en", bpm_version="0.9.3")
    assert len(snapshot.turns) == 16
    assert snapshot.turns[0] == type(snapshot.turns[0])("user", "alpha 1?")
    assert snapshot.turns[-1] == type(snapshot.turns[-1])("assistant", "answer-8")


@pytest.mark.parametrize(
    ("locale", "question"),
    [
        ("en", "What about ESR?"),
        ("ru", "А что насчёт ESR?"),
        ("de", "Was ist mit ESR?"),
        ("zh-CN", "那 ESR 呢？"),
        ("fr", "Et pour ESR ?"),
        ("es-ES", "¿Y qué ocurre con ESR?"),
    ],
)
def test_follow_up_context_is_locale_private_for_each_supported_locale(
    locale: str, question: str
) -> None:
    store = ConversationContextStore()
    session_id = store.create(locale=locale, bpm_version="0.9.3")
    citation = LocalCitation("topic:esr", f"/help/{locale}/user/esr.html", "esr", "root")

    for number in range(MAX_CONTEXT_PAIRS):
        store.record(
            session_id=session_id,
            locale=locale,
            bpm_version="0.9.3",
            question=f"{question} {number}",
            answer=f"ESR {number}",
            citations=(citation,),
            resolved_entities=("ESR",),
        )
    snapshot = store.snapshot(session_id=session_id, locale=locale, bpm_version="0.9.3")

    assert snapshot.locale == locale
    assert snapshot.resolved_entities == ("ESR", "esr")
    assert len(snapshot.turns) == MAX_CONTEXT_TURNS
    assert snapshot.turns[0].text == f"{question} 0"
    assert snapshot.turns[-1].text == "ESR 7"


def test_context_store_rejects_invalid_identity_updates_and_mismatches() -> None:
    with pytest.raises(ConversationContextUnavailable, match="assistant_invalid_session_identity"):
        ConversationContextStore().create(locale="en-US", bpm_version="0.9.3")
    with pytest.raises(ValueError, match="TTL"):
        ConversationContextStore(idle_ttl_seconds=0)

    store = ConversationContextStore()
    session_id = store.create(locale="en", bpm_version="0.9.3")
    with pytest.raises(ConversationContextUnavailable, match="assistant_session_locale_mismatch"):
        store.snapshot(session_id=session_id, locale="ru", bpm_version="0.9.3")
    with pytest.raises(ConversationContextUnavailable, match="assistant_invalid_context_update"):
        store.record(
            session_id=session_id,
            locale="en",
            bpm_version="0.9.3",
            question="",
            answer="answer",
            citations=(),
        )
    with pytest.raises(ConversationContextUnavailable, match="assistant_invalid_context_update"):
        store.record(
            session_id=session_id,
            locale="en",
            bpm_version="0.9.3",
            question="question",
            answer="answer",
            citations=(),
            resolved_entities=("x" * 121,),
        )


def test_context_store_prunes_entities_for_a_disjoint_new_topic_and_expires_on_sweep() -> None:
    now = 0.0
    store = ConversationContextStore(idle_ttl_seconds=2, absolute_ttl_seconds=100, clock=lambda: now)
    session_id = store.create(locale="en", bpm_version="0.9.3")
    store.record(
        session_id=session_id,
        locale="en",
        bpm_version="0.9.3",
        question="alpha",
        answer="alpha answer",
        citations=(_citation("alpha"),),
        resolved_entities=("alpha entity",),
    )
    pruned = store.prune_for_evidence(
        session_id=session_id,
        locale="en",
        bpm_version="0.9.3",
        citations=(_citation("beta"),),
    )
    assert pruned.resolved_entities == ()
    assert pruned.topic_ids == ("beta",)
    now = 2.0
    assert store.clear_expired() == 1
    with pytest.raises(ConversationContextUnavailable, match="assistant_session_unavailable"):
        store.snapshot(session_id=session_id, locale="en", bpm_version="0.9.3")


def test_context_store_record_identity_and_topic_reset_are_fail_closed() -> None:
    store = ConversationContextStore()
    session_id = store.create(locale="en", bpm_version="0.9.3")
    store.record(
        session_id=session_id,
        locale="en",
        bpm_version="0.9.3",
        question="alpha",
        answer="alpha answer",
        citations=(_citation("alpha"),),
        resolved_entities=("alpha",),
    )
    switched = store.record(
        session_id=session_id,
        locale="en",
        bpm_version="0.9.3",
        question="beta",
        answer="beta answer",
        citations=(_citation("beta"),),
        resolved_entities=("beta",),
    )
    assert switched.resolved_entities == ("beta",)
    with pytest.raises(ConversationContextUnavailable, match="assistant_session_locale_mismatch"):
        store.record(
            session_id=session_id,
            locale="ru",
            bpm_version="0.9.3",
            question="question",
            answer="answer",
            citations=(),
        )
    with pytest.raises(ConversationContextUnavailable, match="assistant_session_version_changed"):
        store.record(
            session_id=session_id,
            locale="en",
            bpm_version="0.9.4",
            question="question",
            answer="answer",
            citations=(),
        )
    with pytest.raises(ConversationContextUnavailable, match="assistant_session_unavailable"):
        store.snapshot(session_id=None, locale="en", bpm_version="0.9.3")  # type: ignore[arg-type]
