from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from app.ai import local_inference_worker as worker
from app.ai import runtime_installation as runtime

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "documentation/config/local-chat-worker-contract-0.9.3.json"

pytestmark = pytest.mark.docs_contract


def _contract() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def test_m6_06_pins_verified_stdio_only_runtime_model_and_limits() -> None:
    contract = _contract()

    assert contract["backlog_item"] == "BPM093-M6-06"
    assert contract["status"] == "implemented-no-browser-route"
    for pin in contract["pins"].values():
        assert hashlib.sha256((ROOT / pin["path"]).read_bytes()).hexdigest() == pin["sha256"]
    runtime_contract = contract["runtime"]
    assert runtime_contract["id"] == runtime.RUNTIME_ID
    assert runtime_contract["archive_sha256"] == runtime.RUNTIME_ARCHIVE_SHA256
    assert runtime_contract["archive_byte_count"] == runtime.RUNTIME_ARCHIVE_BYTES
    assert set(runtime_contract["forbidden"]) >= {"llama-server", "TCP listener", "HTTP listener"}
    assert contract["model"]["id"] == "qwen3-0.6b-q8_0-official-gguf"
    assert contract["inference_profile"]["output_tokens_max"] == worker.MAX_OUTPUT_TOKENS
    assert contract["inference_profile"]["context_tokens"] == worker.CONTEXT_TOKENS
    assert contract["inference_profile"]["threads"] == worker.THREADS
    assert "--grammar" in contract["inference_profile"]["required_flags"]
    assert "--no-show-timings" in contract["inference_profile"]["required_flags"]
    assert "syntax, not facts" in contract["inference_profile"]["structured_output"]


def test_m6_06_preserves_fail_closed_and_persistent_dev_boundaries() -> None:
    contract = _contract()

    lifecycle = contract["resource_and_lifecycle"]
    assert lifecycle["disabled_by_default"] is True
    assert "lexical search" in lifecycle["failure"]
    assert "never returns prompts" in lifecycle["diagnostics"]
    assert lifecycle["input_limits"] == {
        "max_input_bytes": worker.MAX_INPUT_BYTES,
        "max_question_characters": worker.MAX_QUESTION_CHARACTERS,
        "max_evidence_characters": worker.MAX_EVIDENCE_CHARACTERS,
        "max_dialogue_turns": worker.MAX_DIALOGUE_TURNS,
    }
    assert lifecycle["rss_ceiling_bytes"] == worker.MAX_WORKER_AND_RETRIEVAL_RSS_BYTES
    assert contract["development_handoff"]["make_target"] == "make ai-runtime-install-dev"
    assert "preserved by clean-local-artifacts" in contract["development_handoff"]["persistence"]
    assert contract["implementation_boundary"]["not_implemented"] == [
        "FastAPI assistant routes",
        "browser controls",
        "scope gate",
        "retrieval invocation",
        "citation validation",
        "conversation persistence",
        "web search",
    ]
