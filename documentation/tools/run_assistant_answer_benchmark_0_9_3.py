"""Run the M13-06A same-locale local-assistant benchmark with visible, content-free progress.

The runner exercises the released assembly directly, not a browser route.  It starts at most one
local stdio worker and always unloads it.  Its ignored report intentionally retains no prompt,
answer, evidence text, source URL, credential, or model output: only outcome counts, lengths,
digests, and already-public citation identities are retained for a later human content review.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import threading
import time
from collections import Counter
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

DOCUMENTATION_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = DOCUMENTATION_ROOT.parent
CONFIG_PATH = DOCUMENTATION_ROOT / "config/assistant-answer-benchmark-0.9.3.json"
DEFAULT_OUTPUT = DOCUMENTATION_ROOT / ".cache/bpm093-m13-06a/local-answer-benchmark.json"

if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from app.core.config import Settings  # noqa: E402
from app.documentation.conversation import ConversationRequest  # noqa: E402
from app.documentation.local_assistant_runtime import (  # noqa: E402
    LocalAssistantRuntime,
    assemble_local_assistant,
)

PROGRESS_SECONDS = 5.0
TERMINAL_STATES = frozenset({"answer", "clarify", "abstain", "refuse", "cancelled", "error"})


class BenchmarkError(RuntimeError):
    """The benchmark cannot produce complete, comparable, local-only evidence."""


class _Service(Protocol):
    def ask(self, *, request: ConversationRequest, session_id: str) -> object: ...

    def events(self, *, request_id: str, session_id: str) -> Iterable[object] | None: ...

    def source(self, *, request_id: str, source_id: str, session_id: str) -> object | None: ...

    def clear(self, *, session_id: str, locale: str | None = None, tab_id: str | None = None) -> bool: ...


@dataclass(frozen=True)
class BenchmarkCase:
    locale: str
    question_id: str
    question: str


NATIVE_QUESTIONS: dict[str, dict[str, str]] = {
    "en": {
        "local-capabilities": "What questions can you answer?",
        "local-ubuntu-install": "How do I install BPM on Ubuntu 26.04?",
        "local-minimum-requirements": "What are the minimum system requirements for BPM?",
        "local-create-profile": "How do I create a Firefox policy profile in BPM?",
        "local-import-policy": "How do I import policies.json and validate it?",
        "local-supported-schemas": "How do I choose a supported Firefox schema for a profile?",
        "local-apply-policy": "How do I configure a Firefox policy in BPM and verify that it applies?",
        "local-profile-revision": "How do I export a profile and restore the required revision?",
        "local-health-api": "How do I check the BPM health and readiness endpoints through the API?",
        "local-assistant-and-sources": "How do I use the BPM AI assistant and enable external sources?",
    },
    "ru": {
        "local-capabilities": "На какие вопросы ты можешь отвечать?",
        "local-ubuntu-install": "Как установить BPM на Ubuntu 26.04?",
        "local-minimum-requirements": "Какие минимальные системные требования у BPM?",
        "local-create-profile": "Как создать профиль политик Firefox в BPM?",
        "local-import-policy": "Как импортировать policies.json и проверить его корректность?",
        "local-supported-schemas": "Как выбрать поддерживаемую схему Firefox для профиля?",
        "local-apply-policy": "Как настроить политику Firefox в BPM и проверить её применение?",
        "local-profile-revision": "Как экспортировать профиль и восстановить нужную ревизию?",
        "local-health-api": "Как через API BPM проверить работоспособность и готовность сервиса?",
        "local-assistant-and-sources": "Как пользоваться ИИ-помощником BPM и включить внешние источники?",
    },
    "de": {
        "local-capabilities": "Welche Fragen können Sie beantworten?",
        "local-ubuntu-install": "Wie installiere ich BPM auf Ubuntu 26.04?",
        "local-minimum-requirements": "Wie lauten die minimalen Systemanforderungen für BPM?",
        "local-create-profile": "Wie erstelle ich in BPM ein Firefox-Richtlinienprofil?",
        "local-import-policy": "Wie importiere ich policies.json und prüfe die Datei?",
        "local-supported-schemas": "Wie wähle ich ein unterstütztes Firefox-Schema für ein Profil aus?",
        "local-apply-policy": "Wie konfiguriere ich eine Firefox-Richtlinie in BPM und prüfe ihre Anwendung?",
        "local-profile-revision": "Wie exportiere ich ein Profil und stelle die benötigte Revision wieder her?",
        "local-health-api": "Wie prüfe ich über die API die BPM-Health- und Readiness-Endpunkte?",
        "local-assistant-and-sources": "Wie nutze ich den BPM-KI-Assistenten und aktiviere externe Quellen?",
    },
    "zh-CN": {
        "local-capabilities": "你可以回答哪些问题？",
        "local-ubuntu-install": "如何在 Ubuntu 26.04 上安装 BPM？",
        "local-minimum-requirements": "BPM 的最低系统要求是什么？",
        "local-create-profile": "如何在 BPM 中创建 Firefox 策略配置文件？",
        "local-import-policy": "如何导入 policies.json 并验证其正确性？",
        "local-supported-schemas": "如何为配置文件选择受支持的 Firefox 架构？",
        "local-apply-policy": "如何在 BPM 中配置 Firefox 策略并验证其已生效？",
        "local-profile-revision": "如何导出配置文件并恢复所需的修订版本？",
        "local-health-api": "如何通过 API 检查 BPM 的健康状态和就绪状态端点？",
        "local-assistant-and-sources": "如何使用 BPM AI 助手并启用外部来源？",
    },
    "fr": {
        "local-capabilities": "À quelles questions pouvez-vous répondre ?",
        "local-ubuntu-install": "Comment installer BPM sur Ubuntu 26.04 ?",
        "local-minimum-requirements": "Quelles sont les exigences système minimales de BPM ?",
        "local-create-profile": "Comment créer un profil de stratégies Firefox dans BPM ?",
        "local-import-policy": "Comment importer policies.json et vérifier sa validité ?",
        "local-supported-schemas": "Comment choisir un schéma Firefox pris en charge pour un profil ?",
        "local-apply-policy": "Comment configurer une stratégie Firefox dans BPM et vérifier son application ?",
        "local-profile-revision": "Comment exporter un profil et restaurer la révision nécessaire ?",
        "local-health-api": "Comment vérifier les points de terminaison de santé et de disponibilité de BPM via l’API ?",
        "local-assistant-and-sources": "Comment utiliser l’assistant IA de BPM et activer les sources externes ?",
    },
    "es-ES": {
        "local-capabilities": "¿Qué preguntas puedes responder?",
        "local-ubuntu-install": "¿Cómo instalo BPM en Ubuntu 26.04?",
        "local-minimum-requirements": "¿Cuáles son los requisitos mínimos del sistema para BPM?",
        "local-create-profile": "¿Cómo creo un perfil de políticas de Firefox en BPM?",
        "local-import-policy": "¿Cómo importo policies.json y compruebo su validez?",
        "local-supported-schemas": "¿Cómo elijo un esquema de Firefox compatible para un perfil?",
        "local-apply-policy": "¿Cómo configuro una política de Firefox en BPM y verifico que se aplique?",
        "local-profile-revision": "¿Cómo exporto un perfil y restauro la revisión necesaria?",
        "local-health-api": "¿Cómo compruebo los puntos de estado y disponibilidad de BPM mediante la API?",
        "local-assistant-and-sources": "¿Cómo uso el asistente de IA de BPM y activo las fuentes externas?",
    },
}

REPRESENTATIVE_QUESTION_IDS: dict[str, str] = {
    "en": "local-ubuntu-install",
    "ru": "local-minimum-requirements",
}


def _read_config(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise BenchmarkError("assistant benchmark configuration is unreadable") from error
    if not isinstance(value, dict):
        raise BenchmarkError("assistant benchmark configuration must be an object")
    return value


def _cases(config: dict[str, Any]) -> tuple[BenchmarkCase, ...]:
    locales = config.get("locales")
    questions = config.get("local_questions")
    if not isinstance(locales, list) or not all(isinstance(value, str) for value in locales):
        raise BenchmarkError("assistant benchmark locales are invalid")
    if not isinstance(questions, list) or len(questions) != 10:
        raise BenchmarkError("assistant benchmark must contain ten local questions")
    ids = [question.get("id") for question in questions if isinstance(question, dict)]
    if len(ids) != len(questions) or not all(isinstance(value, str) for value in ids):
        raise BenchmarkError("assistant benchmark question identities are invalid")
    if len(set(ids)) != len(ids):
        raise BenchmarkError("assistant benchmark question identities are duplicated")
    if set(NATIVE_QUESTIONS) != set(locales) or any(
        set(NATIVE_QUESTIONS[locale]) != set(ids) for locale in locales
    ):
        raise BenchmarkError("native benchmark question matrix drifted")
    return tuple(
        BenchmarkCase(locale, question_id, NATIVE_QUESTIONS[locale][question_id])
        for locale in locales
        for question_id in ids
    )


def _execution_locales(config: dict[str, Any]) -> tuple[str, ...]:
    """Return the maintainer-approved live sample without weakening prompt coverage."""

    configured = config.get("local_benchmark_locales")
    supported = config.get("locales")
    if (
        not isinstance(configured, list)
        or not configured
        or not all(isinstance(locale, str) for locale in configured)
        or len(set(configured)) != len(configured)
        or not isinstance(supported, list)
        or any(locale not in supported for locale in configured)
    ):
        raise BenchmarkError("assistant benchmark execution locales are invalid")
    return tuple(configured)


def _execution_cases(
    cases: tuple[BenchmarkCase, ...], locales: tuple[str, ...]
) -> tuple[BenchmarkCase, ...]:
    selected = tuple(case for case in cases if case.locale in locales)
    if not selected:
        raise BenchmarkError("assistant benchmark execution matrix is empty")
    return selected


def _safe_output_path(path: Path) -> Path:
    cache_root = (DOCUMENTATION_ROOT / ".cache").resolve()
    resolved = Path(path).resolve()
    if cache_root not in (resolved, *resolved.parents):
        raise BenchmarkError("benchmark output must remain under documentation/.cache")
    return resolved


def _representative_cases(
    cases: tuple[BenchmarkCase, ...], locales: list[str]
) -> tuple[BenchmarkCase, ...]:
    if set(REPRESENTATIVE_QUESTION_IDS) != set(locales):
        raise BenchmarkError("representative benchmark locale matrix drifted")
    selected = tuple(
        next(
            (
                case
                for case in cases
                if case.locale == locale and case.question_id == REPRESENTATIVE_QUESTION_IDS[locale]
            ),
            None,
        )
        for locale in locales
    )
    if any(case is None for case in selected):
        raise BenchmarkError("representative benchmark question matrix drifted")
    return tuple(case for case in selected if case is not None)


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _collect_events(
    service: _Service,
    worker: object,
    *,
    request_id: str,
    session_id: str,
    prefix: str,
) -> tuple[object, ...]:
    result: list[object] = []
    failure: list[BaseException] = []

    def collect() -> None:
        try:
            events = service.events(request_id=request_id, session_id=session_id)
            if events is not None:
                result.extend(events)
        except BaseException as error:  # The direct failure is re-raised in this benchmark thread.
            failure.append(error)

    thread = threading.Thread(target=collect, daemon=True)
    thread.start()
    started = time.monotonic()
    while thread.is_alive():
        thread.join(PROGRESS_SECONDS)
        if thread.is_alive():
            health = worker.health()
            state = getattr(health, "state", "unknown")
            elapsed = round(time.monotonic() - started, 1)
            print(f"{prefix}: worker={state}, elapsed={elapsed}s", flush=True)
    if failure:
        raise BenchmarkError("assistant event stream failed") from failure[0]
    return tuple(result)


def _terminal(events: tuple[object, ...]) -> object:
    terminals = [event for event in events if getattr(event, "state", None) in TERMINAL_STATES]
    if len(terminals) != 1:
        raise BenchmarkError("assistant request did not produce one terminal event")
    return terminals[0]


def _failure_category(reason_code: str) -> str:
    if reason_code.startswith("assistant_relevance") or reason_code in {
        "no_evidence",
        "grounded_evidence_unavailable",
        "assistant_evidence_unavailable",
    }:
        return "retrieval_or_relevance"
    if reason_code in {"assistant_output_invalid", "assistant_excessive_quotation", "assistant_invalid_citations"}:
        return "composition"
    if reason_code.startswith("assistant_generation") or reason_code.startswith("assistant_timeout"):
        return "model_quality"
    return "evidence"


def _case_record(
    service: _Service,
    *,
    terminal: object,
    request_id: str,
    session_id: str,
    locale: str,
    question_id: str,
    elapsed_seconds: float,
) -> dict[str, Any]:
    disposition = getattr(terminal, "disposition", None)
    reason_code = getattr(terminal, "reason_code", "assistant_internal_error")
    text = getattr(terminal, "text", "")
    source_ids = getattr(terminal, "source_ids", ())
    if not isinstance(disposition, str) or not isinstance(reason_code, str) or not isinstance(text, str):
        raise BenchmarkError("assistant terminal event is malformed")
    if not isinstance(source_ids, tuple) or not all(isinstance(value, str) for value in source_ids):
        raise BenchmarkError("assistant source event is malformed")
    sources = [service.source(request_id=request_id, source_id=source_id, session_id=session_id) for source_id in source_ids]
    source_locales = tuple(getattr(source, "locale", "") for source in sources if source is not None)
    source_kinds = tuple(getattr(source, "source_kind", "") for source in sources if source is not None)
    structurally_grounded = (
        disposition == "answer"
        and bool(text.strip())
        and len(sources) == len(source_ids)
        and bool(source_ids)
        and all(source_locale == locale for source_locale in source_locales)
        and all(kind == "local" for kind in source_kinds)
    )
    return {
        "locale": locale,
        "question_id": question_id,
        "disposition": disposition,
        "reason_code": reason_code,
        "elapsed_seconds": round(elapsed_seconds, 3),
        "answer_characters": len(text),
        "answer_sha256": _hash_text(text) if text else None,
        "citation_count": len(source_ids),
        "citation_locales": source_locales,
        "citation_kinds": source_kinds,
        "structurally_grounded": structurally_grounded,
        "failure_category": None if structurally_grounded else _failure_category(reason_code),
        "content_review": "required",
    }


def run(
    output_path: Path = DEFAULT_OUTPUT,
    config_path: Path = CONFIG_PATH,
    *,
    case_limit: int | None = None,
    representative_smoke: bool = False,
    assembly_factory: Callable[[Settings], LocalAssistantRuntime] = assemble_local_assistant,
) -> dict[str, Any]:
    """Execute the approved bilingual local-only matrix and write a content-free report."""

    output_path = _safe_output_path(output_path)
    config = _read_config(config_path)
    prompt_coverage_cases = _cases(config)
    execution_locales = _execution_locales(config)
    all_cases = _execution_cases(prompt_coverage_cases, execution_locales)
    expected_cases = config.get("scoring", {}).get("local", {}).get("cases")
    if expected_cases != len(all_cases):
        raise BenchmarkError("assistant benchmark case count drifted")
    if case_limit is not None and not 1 <= case_limit <= len(all_cases):
        raise BenchmarkError("assistant benchmark case limit is invalid")
    if representative_smoke and case_limit is not None:
        raise BenchmarkError("representative smoke cannot use a case limit")
    cases = (
        _representative_cases(all_cases, list(execution_locales))
        if representative_smoke
        else all_cases
        if case_limit is None
        else all_cases[:case_limit]
    )
    print("M13-06A: verifying local artifacts and assembling the released assistant", flush=True)
    runtime = assembly_factory(Settings(AI_LOCAL_CHAT_ENABLED=True, WEB_EVIDENCE_ENABLED=False))
    results: list[dict[str, Any]] = []
    started = time.monotonic()
    try:
        for ordinal, case in enumerate(cases, start=1):
            locale_position = execution_locales.index(case.locale) + 1
            question_position = next(
                position
                for position, question in enumerate(config["local_questions"], start=1)
                if question["id"] == case.question_id
            )
            prefix = (
                f"M13-06A: locale {locale_position}/{len(execution_locales)} {case.locale}; "
                f"question {question_position}/10 {case.question_id}"
            )
            print(f"{prefix}: started", flush=True)
            session_id = f"m13-06a-{case.locale}-{ordinal:02d}"
            admission = runtime.service.ask(
                request=ConversationRequest(locale=case.locale, question=case.question),
                session_id=session_id,
            )
            request_id = getattr(admission, "request_id", None)
            if not isinstance(request_id, str):
                raise BenchmarkError(f"{case.locale}:{case.question_id}: admission failed")
            case_started = time.monotonic()
            events = _collect_events(
                runtime.service,
                runtime.worker,
                request_id=request_id,
                session_id=session_id,
                prefix=prefix,
            )
            terminal = _terminal(events)
            record = _case_record(
                runtime.service,
                terminal=terminal,
                request_id=request_id,
                session_id=session_id,
                locale=case.locale,
                question_id=case.question_id,
                elapsed_seconds=time.monotonic() - case_started,
            )
            results.append(record)
            runtime.service.clear(session_id=session_id, locale=case.locale)
            print(
                f"{prefix}: {record['disposition']}; grounded={record['structurally_grounded']}; "
                f"elapsed={record['elapsed_seconds']}s",
                flush=True,
            )
    finally:
        runtime.shutdown()
        print("M13-06A: local worker unloaded", flush=True)

    failures = [record for record in results if not record["structurally_grounded"]]
    categories = Counter(
        record["failure_category"] for record in failures if record["failure_category"] is not None
    )
    report = {
        "schema_version": 1,
        "backlog_item": "BPM093-M13-06A",
        "benchmark_contract_sha256": hashlib.sha256(config_path.read_bytes()).hexdigest(),
        "status": (
            "partial_structural_pass_pending_human_content_review"
            if (case_limit is not None or representative_smoke) and not failures
            else "partial_structural_fail"
            if case_limit is not None or representative_smoke
            else "structural_pass_pending_human_content_review"
            if not failures
            else "structural_fail"
        ),
        "completed_cases": len(results),
        "expected_cases": len(cases),
        "full_matrix_cases": len(all_cases),
        "localized_prompt_coverage_cases": len(prompt_coverage_cases),
        "structurally_grounded_cases": len(results) - len(failures),
        "failures_by_category": dict(sorted(categories.items())),
        "results": results,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "boundaries": {
            "network_calls": 0,
            "external_provider_calls": 0,
            "ordinary_search_calls": 0,
            "cross_locale_retrieval": False,
            "model_weight_change": False,
            "worker_unloaded": True,
            "report_contains_prompt_answer_or_evidence_text": False,
        },
    }
    output_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        f"M13-06A: complete {len(results)}/{len(cases)}; status={report['status']}; "
        f"elapsed={report['elapsed_seconds']}s",
        flush=True,
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", nargs="?", default="run")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--config", type=Path, default=CONFIG_PATH)
    parser.add_argument("--limit", type=int, help="run only a prefix for lifecycle smoke validation")
    parser.add_argument(
        "--representative-smoke",
        action="store_true",
        help="run the real EN/RU M13-06B structured-generation smoke",
    )
    arguments = parser.parse_args()
    try:
        report = run(
            arguments.output,
            arguments.config,
            case_limit=arguments.limit,
            representative_smoke=arguments.representative_smoke,
        )
    except BenchmarkError as error:
        print(f"M13-06A: failed: {error}", file=sys.stderr, flush=True)
        return 2
    return 0 if "structural_fail" not in report["status"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
