from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "documentation/config/documentation-assistant-api-delivery-contract-0.9.3.json"


def test_m12a_01_records_the_release_training_notice_without_runtime_assembly() -> None:
    contract = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

    assert contract["backlog_item"] == "BPM093-M12A-01"
    assert contract["status"] == "implemented-release-training-notice"
    for pin in contract["pins"].values():
        assert hashlib.sha256((ROOT / pin["path"]).read_bytes()).hexdigest() == pin["sha256"]
    assert contract["transport"]["same_origin_routes"] == [
        "GET /api/documentation-assistant/status",
        "POST /api/documentation-assistant/chat",
        "GET /api/documentation-assistant/chat/{request_id}/stream",
        "POST /api/documentation-assistant/chat/{request_id}/cancel",
        "DELETE /api/documentation-assistant/conversation",
        "GET /api/documentation-assistant/chat/{request_id}/sources/{source_id}",
    ]
    assert contract["safety"] == {
        "default_service": "localized_training_notice",
        "worker_started_on_status_page_load_or_failed_admission": False,
        "ordinary_search_changed": False,
        "web_network_calls": 0,
        "source_access": "The 0.9.3 training notice exposes no sources, citations, retrieval artifacts or source handles.",
    }
    assert contract["deferred_release_assembly"] == {
        "local_model_training_and_rag": "post-0.9.3",
        "generated_answers_and_citations": "post-0.9.3",
        "external_evidence": "outside-0.9.3",
    }
    assert "documentation_assistant.router" in (ROOT / "app/main.py").read_text(encoding="utf-8")
