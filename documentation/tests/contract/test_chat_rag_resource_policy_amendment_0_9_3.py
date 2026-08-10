from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
AMENDMENT_PATH = ROOT / "documentation/config/chat-rag-resource-policy-amendment-0.9.3.json"

pytestmark = pytest.mark.docs_contract


def test_resource_policy_allows_swap_for_offline_embedding_but_not_model_training() -> None:
    amendment = json.loads(AMENDMENT_PATH.read_text(encoding="utf-8"))

    assert amendment["status"] == "accepted"
    assert "never fine-tuned" in amendment["scope"]["model_training"]
    assert "operating-system swap" in amendment["scope"]["offline_index_build"]
    assert (
        amendment["resource_policy"]["index_build_threads"] == "all available logical CPU threads"
    )
    assert amendment["resource_policy"]["index_build_swap"] == "permitted"


def test_resource_policy_retains_interactive_limits_and_removes_only_no_swap_blocker() -> None:
    amendment = json.loads(AMENDMENT_PATH.read_text(encoding="utf-8"))

    assert amendment["resource_policy"]["interactive_chat_retrieval_p95_ms_max"] == 2000
    assert amendment["resource_policy"]["interactive_peak_rss_gib_max"] == 1.5
    assert amendment["resource_policy"]["ordinary_search_dependency"] == "forbidden"
    assert "Retired as a no-swap release blocker" in amendment["release_effect"]["M5_03D"]
    assert amendment["release_effect"]["M4"] == "Unchanged and independent."
