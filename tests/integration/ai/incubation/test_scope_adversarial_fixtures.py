from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from app.ai.local_inference_worker import InferenceRequest, InferenceResult
from app.documentation.conversation import (
    ConversationRequest,
    GroundedConversationOrchestrator,
    ParsedGeneration,
)
from app.documentation.evidence import EvidencePacker
from app.documentation.retrieval import RetrievalResult
from app.documentation.topic_scope import ScopeLexicon, TopicScopeGate

ROOT = Path(__file__).resolve().parents[4]
SCOPE_CONTRACT_PATH = ROOT / "documentation/config/bpm-topic-scope-gate-contract-0.9.3.json"
FIXTURES_PATH = ROOT / "documentation/config/bpm-scope-adversarial-fixtures-0.9.3.json"


@dataclass
class FailingSimilarity:
    calls: int = 0

    def score(self, *, locale: str, query: str) -> float:
        self.calls += 1
        raise AssertionError(f"adversarial query reached similarity: {locale}: {query}")


@dataclass
class CountingRetriever:
    calls: int = 0

    def retrieve(self, *, locale: str, query_vector: np.ndarray, limit: int = 5) -> RetrievalResult:
        self.calls += 1
        return RetrievalResult("raggen-v1-0123456789abcdef0123", locale, ())


@dataclass
class CountingWorker:
    calls: int = 0

    def generate(self, request: InferenceRequest) -> InferenceResult:
        self.calls += 1
        return InferenceResult("{}", request.locale, 1)


def _fixture_queries(contract: dict) -> tuple[tuple[str, str, str], ...]:
    queries: list[tuple[str, str, str]] = []
    expected_categories = set(contract["required_categories"])
    for locale in contract["locales"]:
        cases = contract["locale_cases"][locale]
        assert set(cases) == expected_categories
        for category, value in cases.items():
            if category == "long_padding":
                assert set(value) == {"prefix", "repeat", "suffix"}
                assert isinstance(value["repeat"], int)
                query = value["prefix"] * value["repeat"] + value["suffix"]
            else:
                assert isinstance(value, str)
                query = value
            queries.append((locale, category, query))
    for case in contract["code_switched_cases"]:
        queries.append((case["locale"], case["category"], case["query"]))
    return tuple(queries)


def test_adversarial_scope_fixtures_fail_closed_before_similarity_retrieval_or_worker() -> None:
    contract = json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))
    similarity = FailingSimilarity()
    gate = TopicScopeGate(
        lexicon=ScopeLexicon.from_contract(SCOPE_CONTRACT_PATH),
        similarity=similarity,
        context_entities=lambda _: ("profile-policy-settings",),
    )
    retriever = CountingRetriever()
    worker = CountingWorker()
    orchestrator = GroundedConversationOrchestrator(
        scope_gate=gate,
        query_encoder=lambda _: (_ for _ in ()).throw(
            AssertionError("adversarial query reached query encoding")
        ),
        retriever=retriever,
        evidence_packer=EvidencePacker(lambda value: len(value.split()), bpm_version="0.9.3"),
        worker=worker,  # type: ignore[arg-type]  # The test asserts no worker call occurs.
        generation_parser=lambda _, __: ParsedGeneration("abstain", ""),
    )

    outcomes = [
        (locale, category, orchestrator.ask(ConversationRequest(locale, query)))
        for locale, category, query in _fixture_queries(contract)
    ]

    assert len(outcomes) == len(contract["locales"]) * len(contract["required_categories"]) + len(
        contract["code_switched_cases"]
    )
    assert all(
        outcome.disposition == contract["acceptance"]["expected_disposition"]
        for _, _, outcome in outcomes
    )
    assert all(
        outcome.reason_code == contract["acceptance"]["expected_reason_code"]
        for _, _, outcome in outcomes
    )
    assert similarity.calls == retriever.calls == worker.calls == 0
