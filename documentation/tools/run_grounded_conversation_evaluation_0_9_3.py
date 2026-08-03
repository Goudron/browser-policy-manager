"""Run the deterministic six-locale M7 conversation-conformance evaluation for BPM 0.9.3.

The evaluator drives the implemented orchestration, context and answer-validation boundaries with
reviewed locale-native fixtures.  It does not start or score the selected chat model; M6 owns that
separate runtime benchmark.  Reports contain counts and outcomes only, never prompts, answers,
evidence text or conversation handles.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

DOCUMENTATION_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = DOCUMENTATION_ROOT.parent
CONFIG_PATH = DOCUMENTATION_ROOT / "config/grounded-conversation-evaluation-0.9.3.json"

if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from app.ai.local_inference_worker import InferenceRequest, InferenceResult  # noqa: E402
from app.documentation.answer_validation import GenerationResponseValidator  # noqa: E402
from app.documentation.conversation import (  # noqa: E402
    ConversationRequest,
    GroundedConversationOrchestrator,
    ScopeDecision,
)
from app.documentation.conversation_context import ConversationContextStore  # noqa: E402
from app.documentation.evidence import EvidencePacker  # noqa: E402
from app.documentation.retrieval import (  # noqa: E402
    LocalCitation,
    RetrievalResult,
    RetrievedEvidence,
)


class EvaluationError(RuntimeError):
    """The deterministic M7 acceptance fixture or its pinned contract is invalid."""


@dataclass(frozen=True)
class LocaleFixture:
    """One reviewed, locale-native answer and same-topic follow-up pair."""

    locale: str
    first_question: str
    follow_up_question: str
    first_answer: str
    follow_up_answer: str


FIXTURES: tuple[LocaleFixture, ...] = (
    LocaleFixture(
        "en",
        "How do I configure policies in a profile?",
        "What should I verify afterwards?",
        "Configure the documented policy settings in the selected profile.",
        "Verify the saved profile against the documented policy settings before export.",
    ),
    LocaleFixture(
        "ru",
        "Как настроить политики в профиле?",
        "Что нужно проверить после этого?",
        "Настройте документированные параметры политик в выбранном профиле.",
        "Перед экспортом проверьте сохранённый профиль по документированным параметрам политик.",
    ),
    LocaleFixture(
        "de",
        "Wie konfiguriere ich Richtlinien in einem Profil?",
        "Was muss ich danach prüfen?",
        "Konfigurieren Sie die dokumentierten Richtlinieneinstellungen im ausgewählten Profil.",
        "Prüfen Sie das gespeicherte Profil vor dem Export anhand der dokumentierten Richtlinieneinstellungen.",
    ),
    LocaleFixture(
        "zh-CN",
        "如何在配置文件中设置策略？",
        "之后需要检查什么？",
        "在所选配置文件中设置已记录的策略选项。",
        "导出前，请按照已记录的策略选项检查已保存的配置文件。",
    ),
    LocaleFixture(
        "fr",
        "Comment configurer des stratégies dans un profil ?",
        "Que dois-je vérifier ensuite ?",
        "Configurez les paramètres de stratégie documentés dans le profil sélectionné.",
        "Avant l’exportation, vérifiez le profil enregistré avec les paramètres de stratégie documentés.",
    ),
    LocaleFixture(
        "es-ES",
        "¿Cómo configuro políticas en un perfil?",
        "¿Qué debo comprobar después?",
        "Configure los ajustes de políticas documentados en el perfil seleccionado.",
        "Antes de exportar, compruebe el perfil guardado con los ajustes de políticas documentados.",
    ),
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_config(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise EvaluationError("invalid evaluation contract") from error
    if not isinstance(value, dict):
        raise EvaluationError("evaluation contract must be an object")
    return value


def _verify_pins(config: dict[str, Any]) -> None:
    for name, entry in config["pins"].items():
        path = REPOSITORY_ROOT / entry["path"]
        if _sha256(path) != entry["sha256"]:
            raise EvaluationError(f"{name} contract drifted")


def _citation(locale: str) -> LocalCitation:
    return LocalCitation(
        "topic:profile-policy-settings",
        f"/help/{locale}/user/profile-policy-settings.html",
        "profile-policy-settings",
        "root",
    )


def _retrieval_result(fixture: LocaleFixture) -> RetrievalResult:
    evidence_text = f"{fixture.first_question} {fixture.follow_up_question}"
    evidence = RetrievedEvidence(
        chunk_id=f"ragc-v1:{fixture.locale}:profile-policy-settings:root:0",
        ordinal=0,
        guide_id="user",
        documentation_version="0.9.3",
        bpm_version="0.9.3",
        source_sha256="a" * 64,
        heading_path=("Profile policy settings",),
        text=evidence_text,
        score=0.9,
        citation=_citation(fixture.locale),
    )
    return RetrievalResult("raggen-v1-0123456789abcdef0123", fixture.locale, (evidence,))


class _FixtureRetriever:
    def __init__(self, fixture: LocaleFixture, *, no_evidence: bool = False) -> None:
        self._fixture = fixture
        self._no_evidence = no_evidence
        self.locales: list[str] = []

    def retrieve(self, *, locale: str, query_vector: np.ndarray, limit: int = 5) -> RetrievalResult:
        if locale != self._fixture.locale or query_vector.shape != (768,) or limit != 5:
            raise EvaluationError("retrieval fixture contract violated")
        self.locales.append(locale)
        result = _retrieval_result(self._fixture)
        if self._no_evidence:
            return RetrievalResult(result.generation_id, locale, ())
        return result


class _FixtureWorker:
    def __init__(self, fixture: LocaleFixture) -> None:
        self._answers = {
            fixture.first_question: fixture.first_answer,
            fixture.follow_up_question: fixture.follow_up_answer,
        }
        self.invocations = 0

    def generate(self, request: InferenceRequest) -> InferenceResult:
        payload = json.loads(request.question)
        question = payload.get("user_question")
        answer = self._answers.get(question)
        if not isinstance(answer, str):
            raise EvaluationError("worker received an unexpected fixture question")
        self.invocations += 1
        return InferenceResult(
            json.dumps(
                {
                    "disposition": "answer",
                    "sections": [
                        {
                            "text": answer,
                            "citation_ids": ["topic:profile-policy-settings"],
                        }
                    ],
                },
                ensure_ascii=False,
                separators=(",", ":"),
            ),
            request.locale,
            self.invocations,
        )


class _FixtureEncoder:
    def __init__(self, encoded: list[str]) -> None:
        self._encoded = encoded

    def __call__(self, query: str) -> np.ndarray:
        self._encoded.append(query)
        return np.concatenate(([1.0], np.zeros(767, dtype=np.float32)))


def _orchestrator(
    fixture: LocaleFixture,
    *,
    scope: ScopeDecision | None = None,
    no_evidence: bool = False,
) -> tuple[
    GroundedConversationOrchestrator,
    ConversationContextStore,
    _FixtureRetriever,
    _FixtureWorker,
    list[str],
]:
    retriever = _FixtureRetriever(fixture, no_evidence=no_evidence)
    worker = _FixtureWorker(fixture)
    encoded: list[str] = []
    context_store = ConversationContextStore()

    return (
        GroundedConversationOrchestrator(
            scope_gate=lambda _: scope or ScopeDecision("allow", "scope_allowed"),
            query_encoder=_FixtureEncoder(encoded),  # type: ignore[arg-type]  # NumPy plugin loses callable protocol shape.
            retriever=retriever,
            evidence_packer=EvidencePacker(lambda value: len(value.split()), bpm_version="0.9.3"),
            worker=worker,  # type: ignore[arg-type]  # The fixture implements the narrow worker boundary.
            generation_parser=GenerationResponseValidator(),
            context_store=context_store,
        ),
        context_store,
        retriever,
        worker,
        encoded,
    )


def _evaluate_locale(fixture: LocaleFixture) -> dict[str, float | int]:
    orchestrator, context_store, retriever, worker, encoded = _orchestrator(fixture)
    session_id = context_store.create(locale=fixture.locale, bpm_version="0.9.3")
    first = orchestrator.ask(
        ConversationRequest(fixture.locale, fixture.first_question, session_id=session_id)
    )
    follow_up = orchestrator.ask(
        ConversationRequest(fixture.locale, fixture.follow_up_question, session_id=session_id)
    )
    no_evidence, _, no_evidence_retriever, no_evidence_worker, _ = _orchestrator(
        fixture, no_evidence=True
    )
    abstention = no_evidence.ask(ConversationRequest(fixture.locale, fixture.first_question))
    refusal, _, refusal_retriever, refusal_worker, _ = _orchestrator(
        fixture, scope=ScopeDecision("refuse", "scope_off_topic")
    )
    refused = refusal.ask(ConversationRequest(fixture.locale, fixture.first_question))
    citation_id = "topic:profile-policy-settings"
    checks = {
        "grounded_answer_rate": int(
            first.disposition == follow_up.disposition == "answer"
            and first.text == fixture.first_answer
            and follow_up.text == fixture.follow_up_answer
        )
        / 1,
        "citation_resolution_rate": int(
            [citation.citation_id for citation in first.citations] == [citation_id]
            and [citation.citation_id for citation in follow_up.citations] == [citation_id]
        )
        / 1,
        "dialogue_continuity_rate": int(
            len(encoded) == 2
            and "Resolved BPM entities: profile-policy-settings" in encoded[1]
            and retriever.locales == [fixture.locale, fixture.locale]
            and worker.invocations == 2
        )
        / 1,
        "abstention_rate": int(
            abstention.disposition == "abstain"
            and abstention.reason_code == "no_evidence"
            and no_evidence_retriever.locales == [fixture.locale]
            and no_evidence_worker.invocations == 0
        )
        / 1,
        "refusal_rate": int(
            refused.disposition == "refuse"
            and refused.reason_code == "scope_off_topic"
            and refusal_retriever.locales == []
            and refusal_worker.invocations == 0
        )
        / 1,
    }
    if not all(value == 1.0 for value in checks.values()):
        raise EvaluationError(f"{fixture.locale}: deterministic conformance check failed")
    return {**checks, "answer_case_count": 2, "terminal_case_count": 2}


def run(config_path: Path = CONFIG_PATH) -> dict[str, Any]:
    """Execute the reviewed local fixtures and return a content-free acceptance report."""

    config = _read_config(config_path)
    _verify_pins(config)
    locales = config["locales"]
    if [fixture.locale for fixture in FIXTURES] != locales:
        raise EvaluationError("fixture locale matrix drifted")
    print(
        "M7-07 evaluation: verified pinned M7 contracts; starting six-locale conformance",
        flush=True,
    )
    per_locale: dict[str, dict[str, float | int]] = {}
    for index, fixture in enumerate(FIXTURES, start=1):
        print(
            f"M7-07 evaluation: locale {index}/{len(FIXTURES)} {fixture.locale}: "
            "running answer, follow-up, abstention, and refusal checks",
            flush=True,
        )
        per_locale[fixture.locale] = _evaluate_locale(fixture)
        print(
            f"M7-07 evaluation: locale {index}/{len(FIXTURES)} {fixture.locale}: 4/4 checks passed",
            flush=True,
        )
    floors = config["quality_floors"]
    failures = [
        f"{locale}:{metric}"
        for locale, metrics in per_locale.items()
        for metric, minimum in floors.items()
        if metrics[metric] < minimum
    ]
    report = {
        "schema_version": 1,
        "backlog_item": config["backlog_item"],
        "evaluation_contract_sha256": _sha256(config_path),
        "locales": locales,
        "per_locale": per_locale,
        "quality_floors": floors,
        "boundaries": {
            "network_calls": 0,
            "ordinary_search_calls": 0,
            "cross_locale_retrieval_calls": 0,
            "chat_model_started": False,
            "fixture_conversation_content_retained": False,
        },
        "status": "pass" if not failures else "fail",
        "failures": failures,
    }
    print(f"M7-07 evaluation: complete; status={report['status']}", flush=True)
    return report


def _write_report(report: dict[str, Any], output: Path) -> None:
    cache_root = (DOCUMENTATION_ROOT / ".cache").resolve()
    if cache_root not in (output.resolve(), *output.resolve().parents):
        raise EvaluationError("evaluation output must remain under documentation/.cache")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=CONFIG_PATH)
    args = parser.parse_args()
    try:
        report = run(args.config)
        _write_report(report, args.output)
    except EvaluationError as error:
        parser.error(str(error))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
