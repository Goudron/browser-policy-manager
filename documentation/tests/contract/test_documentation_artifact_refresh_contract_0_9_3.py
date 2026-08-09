from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
pytestmark = pytest.mark.docs_contract


def test_m11_01_refreshes_only_verified_published_artifacts_atomically() -> None:
    contract = json.loads(
        (
            ROOT / "documentation/config/documentation-artifact-refresh-contract-0.9.3.json"
        ).read_text()
    )
    generation = (
        ROOT / "documentation/tools/generate_chat_rag_exact_generations_0_9_3.py"
    ).read_text()
    assert contract["backlog_item"] == "BPM093-M11-01"
    assert contract["boundaries"]["ordinary_search_depends_on_rag"] is False
    assert "private staging" in contract["promotion"]
    assert "active-pointer" not in generation or "active_pointer" in generation
    assert "os.replace" in generation
