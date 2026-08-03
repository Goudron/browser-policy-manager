from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "documentation/config/grounded-answer-benchmark-harness-0.9.3.json"
RUNNER_PATH = ROOT / "documentation/tools/run_grounded_answer_benchmark_0_9_3.py"

pytestmark = pytest.mark.docs_contract

spec = importlib.util.spec_from_file_location("grounded_answer_benchmark", RUNNER_PATH)
assert spec is not None and spec.loader is not None
runner = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = runner
spec.loader.exec_module(runner)


def _config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def _write_jsonl(path: Path, values: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n" for value in values),
        encoding="utf-8",
    )


def _prepared_evidence(config: dict) -> list[dict]:
    _shortlist, corpus = runner._verify_pins(config)
    evidence: list[dict] = []
    for case in runner._oracle_cases(corpus, config):
        is_answer = case["expected_disposition"] == "answer"
        evidence.append(
            {
                "request_id": case["request_id"],
                "locale": case["locale"],
                "evidence_disposition": case["expected_disposition"],
                "context_jsonl": json.dumps({"citation_id": case["expected_citation_ids"][0]}) if is_answer else "",
                "citation_ids": case["expected_citation_ids"],
                "dialogue_turns": [{"role": "user", "content": case["query"]}] if case["requires_dialogue"] else [],
                "model_invocation_count": 0,
            }
        )
    return evidence


def _responses_and_reviews(workload_root: Path, candidate_id: str) -> tuple[list[dict], list[dict]]:
    oracle = [json.loads(line) for line in (workload_root / "oracle.jsonl").read_text(encoding="utf-8").splitlines()]
    responses: list[dict] = []
    reviews: list[dict] = []
    for case in oracle:
        if case["expected_disposition"] != "answer":
            continue
        citations = case["expected_citation_ids"]
        responses.append(
            {
                "request_id": case["request_id"],
                "candidate_id": candidate_id,
                "answer_text": "Grounded BPM answer.",
                "citation_ids": citations,
                "output_tokens": 4,
                "ttft_ns": 1_000_000,
                "completion_ns": 2_000_000,
                "worker_peak_rss_bytes": 1_000_000,
                "network_calls": 0,
            }
        )
        reviews.append(
            {
                "request_id": case["request_id"],
                "candidate_id": candidate_id,
                "language": "accepted",
                "instruction_following": "accepted",
                "continuity": "accepted" if case["requires_dialogue"] else "not_applicable",
                "claims": [{"claim_id": "claim-1", "supported": True, "citation_ids": citations}],
            }
        )
    return responses, reviews


def test_harness_contract_pins_inputs_and_freezes_comparable_six_locale_workload() -> None:
    config = _config()

    assert config["contract_id"] == "bpm-grounded-answer-benchmark-harness-0.9.3"
    assert config["backlog_item"] == "BPM093-M6-02"
    assert config["status"] == "accepted-candidate-neutral-harness-contract"
    for entry in config["pins"].values():
        assert hashlib.sha256((ROOT / entry["path"]).read_bytes()).hexdigest() == entry["sha256"]
    assert config["locales"] == ["en", "ru", "de", "zh-CN", "fr", "es-ES"]
    assert config["workload"] == {
        "answer_questions_per_locale": 16,
        "dialogue_answer_cases_per_locale": 4,
        "terminal_cases_per_locale": {"abstain": 4, "clarify": 2, "refuse": 6},
        "total_cases_per_locale": 32,
        "answer_output_tokens_max": 96,
        "evidence_rule": "Every candidate receives byte-identical candidate-neutral request packets built from the same prepared same-locale EvidencePack data and the same locale-native dialogue turns. Expected citations/dispositions are stored only in the scorer oracle, never in model input.",
        "cross_locale_fallback": "forbidden",
    }
    assert config["measurement"]["fixed_generation_settings"] == {
        "temperature": 0.0,
        "top_p": 1.0,
        "top_k": 1,
        "seed": 0,
        "mode": "non-thinking",
        "output_tokens_max": 96,
    }
    assert config["boundaries"]["network_calls_after_install"] == 0
    assert config["boundaries"]["model_download_or_start"] == "absent"


def test_harness_builds_candidate_neutral_workload_and_rejects_unsupported_claims(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    config = _config()
    evidence_path = tmp_path / "prepared-evidence.jsonl"
    workload_root = tmp_path / "workload"
    _write_jsonl(evidence_path, _prepared_evidence(config))

    manifest = runner.build_workload(evidence_path, workload_root)
    candidate_id = manifest["candidate_ids"][0]
    responses, reviews = _responses_and_reviews(workload_root, candidate_id)
    responses_path = tmp_path / "responses.jsonl"
    reviews_path = tmp_path / "reviews.jsonl"
    _write_jsonl(responses_path, responses)
    _write_jsonl(reviews_path, reviews)

    report = runner.score_candidate(workload_root, candidate_id, responses_path, reviews_path)

    assert manifest["locale_case_counts"] == {locale: 32 for locale in config["locales"]}
    assert manifest["ordinary_search_calls"] == manifest["cross_locale_retrieval_calls"] == manifest["network_calls"] == 0
    assert report["status"] == "pass"
    assert report["measurement"]["network_calls"] == 0
    assert all(metrics["grounded_answer_rate"] == 1.0 for metrics in report["per_locale"].values())
    assert all(metrics["terminal_disposition_rate"] == 1.0 for metrics in report["per_locale"].values())
    stdout = capsys.readouterr().out
    assert "en: 8/32 workload packets" in stdout
    assert "zh-CN: 20/20 reviewed answers; 12/12 terminal dispositions" in stdout
    assert "candidate score complete; status=pass" in stdout

    reviews[0]["claims"][0]["supported"] = False
    _write_jsonl(reviews_path, reviews)
    with pytest.raises(runner.HarnessError, match="unsupported claim"):
        runner.score_candidate(workload_root, candidate_id, responses_path, reviews_path)
