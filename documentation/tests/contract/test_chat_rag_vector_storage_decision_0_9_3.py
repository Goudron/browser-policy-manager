from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "documentation/config/chat-rag-vector-storage-decision-0.9.3.json"
RUNNER_PATH = ROOT / "documentation/tools/run_chat_rag_vector_storage_benchmark_0_9_3.py"

SPEC = importlib.util.spec_from_file_location("chat_rag_vector_storage_benchmark", RUNNER_PATH)
assert SPEC and SPEC.loader
runner = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = runner
SPEC.loader.exec_module(runner)

pytestmark = pytest.mark.docs_contract


def _config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_storage_decision_selects_exact_locale_private_f32_without_changing_ordinary_search() -> (
    None
):
    config = _config()

    assert config["backlog_item"] == "BPM093-M5-04"
    assert config["status"] == "accepted-for-implementation"
    assert config["selected_backend"]["id"] == "normalized-exact-f32-matrix-v1"
    assert config["embedding_decision"]["sha256"] == _sha256(
        ROOT / config["embedding_decision"]["path"]
    )
    assert config["embedding_decision"]["dimension"] == 768
    assert "active locale only" in config["selected_backend"]["algorithm"]
    assert config["acceptance"]["ordinary_search_dependency"] == "forbidden"
    assert "Offline generation may use swap" in config["acceptance"]["resource_policy"]


def test_storage_decision_has_a_pinned_rejected_sqlite_vec_candidate_and_fail_closed_recovery() -> (
    None
):
    config = _config()

    candidate = config["rejected_candidates"][0]
    assert candidate["id"] == "sqlite-vec-0.1.10-alpha.4"
    assert len(candidate["observed_package"]["wheel_sha256"]) == 64
    assert len(candidate["observed_package"]["linux_x86_64_extension_sha256"]) == 64
    assert "pre-v1" in candidate["rejection_reason"]
    assert "atomically promote" in config["selected_backend"]["promotion_and_recovery"]
    assert "abstains" in config["selected_backend"]["promotion_and_recovery"]


def test_exact_scan_returns_deterministic_descending_top_k_without_cross_locale_input() -> None:
    matrix = np.array([[1.0, 0.0], [0.9, 0.1], [0.5, 0.5], [-1.0, 0.0]], dtype=np.float32)
    query = np.array([1.0, 0.0], dtype=np.float32)

    assert runner._exact_top_k(matrix, query, 3) == [0, 1, 2]
    assert runner._p95_ms([1] * 30) == 0.000001
    with pytest.raises(runner.BenchmarkError, match="expected 30"):
        runner._p95_ms([1])
