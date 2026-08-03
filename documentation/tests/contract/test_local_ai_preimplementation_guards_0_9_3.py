from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
CONFIG = ROOT / "documentation/config"
GUARDS_PATH = CONFIG / "local-ai-preimplementation-guards-0.9.3.json"
CORPUS_PATH = CONFIG / "search-rag-evaluation-corpus-0.9.3.json"
AVAILABILITY_PATH = CONFIG / "local-ai-availability-fallback-contract-0.9.3.json"

pytestmark = pytest.mark.docs_contract


class GuardViolation(ValueError):
    pass


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _reject_invalid_chunk(chunk: dict, guards: dict) -> None:
    schema = guards["chunk_manifest"]
    missing = set(schema["required_fields"]) - set(chunk)
    if missing:
        raise GuardViolation(f"chunk missing required fields: {sorted(missing)}")
    if chunk["chunk_schema_version"] != schema["required_schema_version"]:
        raise GuardViolation("chunk schema version is not accepted")
    expected_id = schema["id_format"].format(
        locale=chunk["locale"],
        topic_id=chunk["topic_id"],
        anchor_id_or_root=chunk["anchor_id_or_root"],
        ordinal=chunk["ordinal"],
    )
    if chunk["chunk_id"] != expected_id:
        raise GuardViolation("chunk ID is not deterministic")


def _reject_missing_locale_evidence(corpus: dict, guards: dict) -> None:
    evidence = guards["locale_evidence"]
    if corpus["status"] != evidence["corpus_status"]:
        raise GuardViolation("corpus is not accepted")
    if corpus["review_policy"]["english"] != evidence["english_review"]:
        raise GuardViolation("English review is not accepted")
    if corpus["review_policy"]["non_english"] != evidence["non_english_review"]:
        raise GuardViolation("localized review is not accepted")
    expected = {locale: evidence["review_status"] for locale in evidence["required_locales"]}
    if corpus["locale_review"]["locales"] != expected:
        raise GuardViolation("locale review evidence is incomplete or mismatched")


def _reject_unsafe_startup(plan: dict, guards: dict) -> None:
    startup = guards["startup_and_network"]
    if plan["network_requests_after_install"] != startup["local_mode_network_requests_after_install"]:
        raise GuardViolation("local mode network request is forbidden")
    if plan["listener_transport"] in startup["forbidden_listener_transports"]:
        raise GuardViolation("model listener is forbidden")
    if plan["model_started"]:
        missing = set(startup["model_start_requires"]) - set(plan["start_conditions"])
        if missing:
            raise GuardViolation(f"silent model startup misses: {sorted(missing)}")
    forbidden = set(plan["triggers"]) & set(startup["forbidden_implicit_triggers"])
    if forbidden:
        raise GuardViolation(f"implicit startup triggers are forbidden: {sorted(forbidden)}")


def _reject_invalid_capabilities(plan: dict, guards: dict) -> None:
    allowed = guards["capability_boundary"]["allowed_model_tools"]
    if plan["model_tools"] != allowed:
        raise GuardViolation("model tool capability is forbidden")


def _reject_uncited_answer(answer: dict, guards: dict) -> None:
    citation = guards["citation_modes"][answer["disposition"]]
    missing = set(citation["required"]) - set(answer)
    if missing:
        raise GuardViolation(f"answer is missing citation fields: {sorted(missing)}")
    if answer["disposition"] == "answer":
        if not answer["citation_id"] or not answer["published_url"]:
            raise GuardViolation("answer citation is empty")
        if answer["source_kind"] not in citation["allowed_source_kind"]:
            raise GuardViolation("answer citation source kind is invalid")


def _reject_invalid_state_plan(plan: dict, guards: dict, availability: dict) -> None:
    state = guards["state_and_fallback"]
    transitions = availability["transitions"]
    if plan["state"] not in transitions:
        raise GuardViolation("unknown assistant state")
    if plan["next_state"] not in transitions[plan["state"]]:
        raise GuardViolation("unsupported assistant state transition")
    if plan["partial_artifacts"] and plan["assistant_ready"]:
        raise GuardViolation("partial artifacts cannot be ready")
    if plan["lexical_requires_ai"]:
        raise GuardViolation("lexical search cannot depend on AI")
    if not state["assistant_independent_core_health"]:
        raise GuardViolation("assistant must not own core health")


def _reject_resource_overage(plan: dict, guards: dict) -> None:
    ceilings = guards["resource_ceilings"]
    for field, ceiling in (
        ("artifact_disk_gib", ceilings["artifact_disk_gib_max"]),
        ("worker_and_retrieval_rss_gib", ceilings["worker_and_retrieval_rss_gib_max"]),
        ("active_generations", ceilings["maximum_active_generations"]),
        ("queued_generations", ceilings["maximum_queued_generations"]),
    ):
        if plan[field] > ceiling:
            raise GuardViolation(f"resource ceiling exceeded: {field}")


def _valid_chunk() -> dict:
    return {
        "chunk_id": "ragc-v1:en:ug-task-use-profile-library:root:0",
        "chunk_schema_version": "rag-chunk-v1",
        "locale": "en",
        "topic_id": "ug-task-use-profile-library",
        "anchor_id_or_root": "root",
        "ordinal": 0,
        "published_url": "/help/en/user/ug-task-use-profile-library.html",
        "source_revision": "source-revision",
        "source_sha256": "a" * 64,
        "manifest_sha256": "b" * 64,
        "documentation_version": "0.9.3",
        "bpm_version": "0.9.3",
        "provenance_class": "published_reviewed_dita",
        "text_normalization_revision": "v1"
    }


def test_preimplementation_guard_config_is_accepted_and_references_m2_contracts() -> None:
    guards = _json(GUARDS_PATH)

    assert guards["schema_version"] == 1
    assert guards["contract_id"] == "bpm-local-ai-preimplementation-guards-0.9.3"
    assert guards["backlog_item"] == "BPM093-M2-07"
    assert guards["target_bpm_version"] == "0.9.3"
    assert guards["status"] == "accepted-preimplementation-guards"
    assert set(guards["sources"]) == {
        "evaluation_corpus",
        "knowledge_contract",
        "security_contract",
        "availability_contract",
    }
    assert guards["verification"]["negative_cases"] == [
        "unversioned chunk",
        "missing locale evidence",
        "silent model or network startup",
        "answer without citation",
        "exposed model port",
        "unsupported state transition",
        "lexical search dependency on AI",
    ]


def test_guard_rejects_unversioned_or_non_deterministic_chunk() -> None:
    guards = _json(GUARDS_PATH)
    valid = _valid_chunk()

    _reject_invalid_chunk(valid, guards)
    unversioned = deepcopy(valid)
    del unversioned["chunk_schema_version"]
    with pytest.raises(GuardViolation, match="missing required fields"):
        _reject_invalid_chunk(unversioned, guards)
    wrong_id = deepcopy(valid)
    wrong_id["chunk_id"] = "random"
    with pytest.raises(GuardViolation, match="not deterministic"):
        _reject_invalid_chunk(wrong_id, guards)


def test_guard_rejects_missing_or_unaccepted_locale_evidence() -> None:
    guards = _json(GUARDS_PATH)
    corpus = _json(CORPUS_PATH)

    _reject_missing_locale_evidence(corpus, guards)
    missing_locale = deepcopy(corpus)
    del missing_locale["locale_review"]["locales"]["zh-CN"]
    with pytest.raises(GuardViolation, match="incomplete or mismatched"):
        _reject_missing_locale_evidence(missing_locale, guards)
    draft = deepcopy(corpus)
    draft["status"] = "draft-pending-locale-review"
    with pytest.raises(GuardViolation, match="corpus is not accepted"):
        _reject_missing_locale_evidence(draft, guards)


def test_guard_rejects_silent_startup_network_listener_and_tool_capability() -> None:
    guards = _json(GUARDS_PATH)
    safe_plan = {
        "model_started": False,
        "start_conditions": [],
        "network_requests_after_install": 0,
        "listener_transport": "direct child-process pipe",
        "triggers": [],
        "model_tools": []
    }

    _reject_unsafe_startup(safe_plan, guards)
    _reject_invalid_capabilities(safe_plan, guards)
    silent_start = deepcopy(safe_plan)
    silent_start["model_started"] = True
    with pytest.raises(GuardViolation, match="silent model startup"):
        _reject_unsafe_startup(silent_start, guards)
    network = deepcopy(safe_plan)
    network["network_requests_after_install"] = 1
    with pytest.raises(GuardViolation, match="network request"):
        _reject_unsafe_startup(network, guards)
    listener = deepcopy(safe_plan)
    listener["listener_transport"] = "TCP listener"
    with pytest.raises(GuardViolation, match="listener is forbidden"):
        _reject_unsafe_startup(listener, guards)
    tools = deepcopy(safe_plan)
    tools["model_tools"] = ["shell"]
    with pytest.raises(GuardViolation, match="tool capability"):
        _reject_invalid_capabilities(tools, guards)


def test_guard_rejects_uncited_answer_and_invalid_citation_mode() -> None:
    guards = _json(GUARDS_PATH)
    answer = {
        "disposition": "answer",
        "citation_id": "topic:ug-task-use-profile-library",
        "published_url": "/help/en/user/ug-task-use-profile-library.html",
        "source_kind": "local"
    }

    _reject_uncited_answer(answer, guards)
    uncited = deepcopy(answer)
    del uncited["citation_id"]
    with pytest.raises(GuardViolation, match="missing citation fields"):
        _reject_uncited_answer(uncited, guards)
    unlabelled_web = deepcopy(answer)
    unlabelled_web["source_kind"] = "remote"
    with pytest.raises(GuardViolation, match="source kind is invalid"):
        _reject_uncited_answer(unlabelled_web, guards)


def test_guard_rejects_unsupported_transition_partial_ready_and_ai_search_dependency() -> None:
    guards = _json(GUARDS_PATH)
    availability = _json(AVAILABILITY_PATH)
    safe_plan = {
        "state": "ready",
        "next_state": "busy",
        "assistant_ready": True,
        "partial_artifacts": False,
        "lexical_requires_ai": False
    }

    _reject_invalid_state_plan(safe_plan, guards, availability)
    invalid_transition = deepcopy(safe_plan)
    invalid_transition["next_state"] = "downloading"
    with pytest.raises(GuardViolation, match="unsupported assistant state transition"):
        _reject_invalid_state_plan(invalid_transition, guards, availability)
    partial_ready = deepcopy(safe_plan)
    partial_ready["partial_artifacts"] = True
    with pytest.raises(GuardViolation, match="partial artifacts cannot be ready"):
        _reject_invalid_state_plan(partial_ready, guards, availability)
    ai_search = deepcopy(safe_plan)
    ai_search["lexical_requires_ai"] = True
    with pytest.raises(GuardViolation, match="lexical search cannot depend on AI"):
        _reject_invalid_state_plan(ai_search, guards, availability)


def test_guard_rejects_resource_ceiling_overage() -> None:
    guards = _json(GUARDS_PATH)
    safe_plan = {
        "artifact_disk_gib": 2.5,
        "worker_and_retrieval_rss_gib": 3.5,
        "active_generations": 1,
        "queued_generations": 1
    }

    _reject_resource_overage(safe_plan, guards)
    overage = deepcopy(safe_plan)
    overage["worker_and_retrieval_rss_gib"] = 3.6
    with pytest.raises(GuardViolation, match="resource ceiling exceeded"):
        _reject_resource_overage(overage, guards)
