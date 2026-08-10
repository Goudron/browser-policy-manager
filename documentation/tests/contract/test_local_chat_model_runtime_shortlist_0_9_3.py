from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "documentation/config/local-chat-model-runtime-shortlist-0.9.3.json"

pytestmark = pytest.mark.docs_contract


def _config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def test_shortlist_pins_the_required_ai_contracts_and_target_host() -> None:
    config = _config()

    assert config["contract_id"] == "bpm-local-chat-model-runtime-shortlist-0.9.3"
    assert config["backlog_item"] == "BPM093-M6-01"
    assert config["status"] == "accepted-benchmark-shortlist-not-selection"
    for entry in config["pins"].values():
        assert hashlib.sha256((ROOT / entry["path"]).read_bytes()).hexdigest() == entry["sha256"]
    assert config["target_host"] == {
        "cpu_model": "Intel(R) Core(TM) i5-7200U CPU @ 2.50GHz",
        "architecture": "x86_64",
        "physical_cores": 2,
        "logical_threads": 4,
        "memory_gib": 7.1,
        "accelerators": "CPU-only; no GPU, NPU, or hosted inference",
        "forbidden_cpu_requirement": "AVX-512",
    }


def test_admitted_runtime_is_immutable_local_and_not_a_public_model_service() -> None:
    runtime = _config()["runtime"]

    assert runtime["id"] == "llama.cpp-b9637-linux-x64-cpu"
    assert runtime["admitted_for_benchmark"] is True
    assert runtime["revision"] == "aedb2a5e9ca3d4064148bbb919e0ddc0c1b70ab3"
    assert runtime["license"]["spdx"] == "MIT"
    assert (
        runtime["artifact"]["sha256"]
        == "a50ee14f021a9d8e92e30f622f7e3be1318ee1125bb9a9ba8d2025388df48743"
    )
    assert runtime["security_boundary"]["allowed_worker_transport"] == [
        "direct child-process pipe",
        "stdio",
    ]
    assert set(runtime["security_boundary"]["forbidden"]) >= {
        "llama-server",
        "TCP listener",
        "HTTP listener",
        "wildcard bind",
        "LAN bind",
        "public model API",
        "tools",
        "plugins",
        "function calling",
    }


def test_each_admitted_model_has_official_immutable_artifact_template_and_six_locale_gate() -> None:
    config = _config()
    expected_locales = ["en", "ru", "de", "zh-CN", "fr", "es-ES"]

    assert [model["id"] for model in config["admitted_models"]] == [
        "qwen3-0.6b-q8_0-official-gguf",
        "qwen3-1.7b-q8_0-official-gguf",
    ]
    for model in config["admitted_models"]:
        assert model["upstream_owner"] == "Qwen"
        assert len(model["source_revision"]) == 40
        assert model["weight_format"] == "GGUF"
        assert model["quantization"] == "Q8_0"
        assert model["license"]["spdx"] == "Apache-2.0"
        assert len(model["artifact"]["sha256"]) == 64
        assert model["artifact"]["byte_count"] > 0
        assert model["context"]["upstream_max_tokens"] == 32768
        assert "Jinja" in model["template_and_reasoning"]["template_source"]
        assert (
            model["template_and_reasoning"]["required_mode"]
            == "non-thinking (/no_think) for BPM answer benchmarking"
        )
        assert model["locale_admission"]["required_locales"] == expected_locales
        assert model["locale_admission"]["quality_status"].startswith("unmeasured")


def test_gated_or_unofficial_gemma_and_conversions_are_not_silently_admitted() -> None:
    config = _config()
    excluded = config["excluded_models"]

    assert excluded == [
        {
            "id": "google-gemma-3-1b-it",
            "upstream_owner": "Google DeepMind",
            "source_repository": "https://huggingface.co/google/gemma-3-1b-it",
            "source_revision": "dcc83ea841ab6100d6b47a070329e1ba4cf78752",
            "weight_format": "Safetensors upstream; no upstream GGUF artifact is admitted",
            "license": "Gemma Terms of Use",
            "terms_source": "https://ai.google.dev/gemma/terms",
            "context_tokens": 32768,
            "locale_claim": (
                "Gemma 3 model card declares multilingual support in over 140 languages."
            ),
            "disposition": "excluded from M6 benchmark shortlist",
            "reason": (
                "The upstream repository is manually gated under Gemma Terms of Use and the task has no accepted upstream GGUF artifact/checksum or redistribution-compliance record. An unofficial conversion is forbidden until a later task supplies separate conversion provenance, artifact hash, terms/redistribution review, and maintainer acceptance."
            ),
        }
    ]
    assert config["artifact_and_resource_rules"]["only_one_chat_model_installed_or_mapped"] is True
    assert config["artifact_and_resource_rules"]["no_silent_download"] is True
    assert config["benchmark_admission"]["required_locales"] == [
        "en",
        "ru",
        "de",
        "zh-CN",
        "fr",
        "es-ES",
    ]
