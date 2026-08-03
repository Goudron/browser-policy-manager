from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "documentation/config/embedding-model-benchmark-0.9.3.json"
REMEDIATION_CONFIG_PATH = ROOT / "documentation/config/embedding-model-benchmark-m5-03a-0.9.3.json"
RUNNER_PATH = ROOT / "documentation/tools/run_embedding_model_benchmark_0_9_3.py"
TOOLS_ROOT = ROOT / "documentation/tools"

if str(TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOLS_ROOT))

SPEC = importlib.util.spec_from_file_location("embedding_model_benchmark", RUNNER_PATH)
assert SPEC and SPEC.loader
runner = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = runner
SPEC.loader.exec_module(runner)

pytestmark = pytest.mark.docs_contract


def _config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def _remediation_config() -> dict:
    return json.loads(REMEDIATION_CONFIG_PATH.read_text(encoding="utf-8"))


def test_embedding_benchmark_contract_pins_two_compact_immutable_six_locale_candidates() -> None:
    config = _config()

    assert config["schema_version"] == 1
    assert config["backlog_item"] == "BPM093-M5-03"
    assert config["protocol"]["id"] == "BPM093-M2-02"
    assert config["protocol"]["target_host"]["cpu_model"] == "Intel(R) Core(TM) i5-7200U CPU @ 2.50GHz"
    assert config["inputs"]["top_k"] == 5
    assert config["runtime"]["threads"] == {"intra_op": 2, "inter_op": 1}
    assert config["runtime"]["maximum_sequence_tokens"] == 512
    assert {candidate["id"] for candidate in config["candidates"]} == {
        "multilingual-e5-small-onnx-o4",
        "paraphrase-multilingual-minilm-l12-v2-onnx-quint8-avx2",
    }
    for candidate in config["candidates"]:
        assert len(candidate["revision"]) == 40
        assert candidate["dimension"] == 384
        assert candidate["license"] in {"MIT", "Apache-2.0"}
        assert len(candidate["files"]) == 5
        assert all(len(checksum) == 64 for checksum in candidate["files"].values())


def test_embedding_prefixes_normalization_and_resource_gates_are_explicit() -> None:
    config = _config()
    candidates = {candidate["id"]: candidate for candidate in config["candidates"]}

    assert candidates["multilingual-e5-small-onnx-o4"]["prefixes"] == {
        "query": "query: ",
        "passage": "passage: ",
    }
    assert candidates["paraphrase-multilingual-minilm-l12-v2-onnx-quint8-avx2"]["prefixes"] == {
        "query": "",
        "passage": "",
    }
    assert candidates["paraphrase-multilingual-minilm-l12-v2-onnx-quint8-avx2"]["required_cpu_features"] == ["avx2"]
    assert all("L2 normalization" in candidate["normalization"] for candidate in config["candidates"])
    assert config["acceptance"]["model_and_direct_runtime_disk_gib_max"] == 0.5
    assert config["acceptance"]["peak_process_rss_gib_max"] == 1.5
    assert config["protocol"]["validity"]["swap_must_not_change"] is True
    assert "answer templates" in config["inputs"]["retrieval_query_plan"]
    assert "exact identifiers" in config["inputs"]["retrieval_query_plan"]


def test_remediation_contract_preserves_the_method_and_pins_new_candidates() -> None:
    config = _remediation_config()
    candidates = {candidate["id"]: candidate for candidate in config["candidates"]}

    assert config["backlog_item"] == "BPM093-M5-03A"
    assert config["supersedes_selection_attempt"].endswith("embedding-model-benchmark-0.9.3.json")
    assert config["protocol"]["validity"]["swap_must_not_change"] is True
    assert config["acceptance"]["model_and_direct_runtime_disk_gib_max"] == 0.75
    assert candidates["multilingual-e5-base-onnx-o4"]["dimension"] == 768
    distiluse = candidates["distiluse-base-multilingual-cased-v2-onnx-quint8-avx2"]
    assert distiluse["post_pooling"] == {
        "kind": "dense_tanh_safetensors",
        "artifact": "2_Dense/model.safetensors",
        "weight_key": "linear.weight",
        "bias_key": "linear.bias",
        "in_features": 768,
        "out_features": 512,
    }
    assert len(distiluse["files"]) == 6


def test_topic_deduplication_metrics_and_selection_fail_closed() -> None:
    assert runner._ranked_topic_ids(np.array([0.9, 0.8, 0.7]), [{"topic_id": "a"}, {"topic_id": "a"}, {"topic_id": "b"}], 2) == ["a", "b"]
    config = _config()
    cases = runner._retrieval_cases()
    assert len(cases) == 96
    assert {case.locale for case in cases} == set(runner.LOCALES)
    probe = config["inputs"]["cross_language_probe"]
    assert any(
        case.locale == probe["query_locale"] and case.query_class == probe["query_class"]
        for case in cases
    )
    assert all(any(case.locale == locale and case.query_class == probe["query_class"] for case in cases) for locale in runner.LOCALES)
    assert runner._metrics([1, None]) == {
        "top_1": 0.5,
        "recall_at_5": 0.5,
    }
    report = {
        "validity": {"valid": False, "reasons": ["swap-changed-during-measurement"]},
        "per_locale": {
            locale: {"top_1": 1.0, "recall_at_5": 1.0}
            for locale in runner.LOCALES
        },
        "cross_language": {"recall_at_5": 1.0},
        "resources": {"direct_disk_gib": 0.1, "peak_rss_gib": 0.1},
        "latency": {"p95_ms_max": 1.0},
    }
    assert runner._candidate_status(report, config) == ("fail", ["swap-changed-during-measurement"])


def test_onnx_input_feeds_support_models_with_or_without_token_type_ids() -> None:
    class Encoded:
        ids = [1, 2]
        attention_mask = [1, 1]
        type_ids = [0, 0]

    encoded = [Encoded()]
    required = runner._onnx_feeds(encoded, {"input_ids", "attention_mask"})
    assert set(required) == {"input_ids", "attention_mask"}
    assert runner._onnx_feeds(encoded, {"input_ids", "attention_mask", "token_type_ids"})[
        "token_type_ids"
    ].tolist() == [[0, 0]]
    with pytest.raises(runner.BenchmarkError, match="unsupported ONNX inputs"):
        runner._onnx_feeds(encoded, {"input_ids"})
