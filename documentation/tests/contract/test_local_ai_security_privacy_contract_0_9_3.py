from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
CONTRACT_PATH = ROOT / "documentation/config/local-ai-security-privacy-contract-0.9.3.json"

pytestmark = pytest.mark.docs_contract


def _contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def test_local_ai_security_contract_is_architecture_only() -> None:
    contract = _contract()

    assert contract["schema_version"] == 1
    assert contract["contract_id"] == "bpm-local-ai-security-privacy-0.9.3"
    assert contract["backlog_item"] == "BPM093-M2-05"
    assert contract["target_bpm_version"] == "0.9.3"
    assert contract["status"] == "accepted-architecture-only"
    assert contract["implementation_boundary"] == {
        "enabled_now": False,
        "runtime_routes_added": False,
        "network_access_added": False,
        "model_or_index_added": False,
        "rule": (
            "This contract defines mandatory controls for later tasks; it does not make "
            "an AI path safe or shippable by itself."
        ),
    }


def test_trust_boundaries_and_flow_put_scope_before_retrieval_inference_and_web() -> None:
    contract = _contract()
    boundaries = {boundary["id"] for boundary in contract["trust_boundaries"]}

    assert boundaries == {
        "browser",
        "bpm-ai-controller",
        "pre-inference-scope-gate",
        "local-retrieval",
        "local-inference-worker",
        "verified-artifact-store",
        "conversation-memory",
        "optional-web-adapter",
    }
    flow = contract["mandatory_flow"]
    assert flow.index("pre-inference scope decision") < flow.index("verified local retrieval")
    assert flow.index("pre-inference scope decision") < flow.index(
        "optional consented web-provider call through the isolated adapter"
    )
    assert flow.index("pre-inference scope decision") < flow.index("bounded local inference")
    invariants = " ".join(contract["global_invariants"])
    assert "invoke neither retrieval, inference, nor web access" in invariants
    assert "cannot mutate BPM state" in invariants
    assert "never become executable instructions" in invariants
    assert "Lexical search and /help/ remain available" in invariants


def test_endpoint_worker_path_and_output_boundaries_are_fail_closed() -> None:
    contract = _contract()

    request = contract["request_security"]
    assert request["same_origin_only"] is True
    assert request["inherit_application_wildcard_cors"] is False
    request_rules = " ".join(request["requirements"])
    for requirement in ("No state-changing AI operation uses GET", "CSRF token", "Host and Origin"):
        assert requirement in request_rules

    worker = contract["worker_isolation"]
    assert "TCP listener" in worker["forbidden_transport"]
    assert "HTTP listener" in worker["forbidden_transport"]
    worker_rules = " ".join(worker["requirements"])
    assert "no listening socket" in worker_rules
    assert "No plugin, tool, function-calling" in worker_rules

    path_rules = " ".join(contract["path_and_artifact_security"]["requirements"])
    for requirement in ("opaque manifest IDs", "symlinks", "SHA-256", "atomic promotion"):
        assert requirement in path_rules

    output_rules = " ".join(contract["prompt_and_output_security"]["requirements"])
    assert "prompt-only policy is insufficient" in output_rules
    assert "raw HTML" in output_rules
    assert "textContent-equivalent" in output_rules


def test_privacy_web_resources_and_recovery_are_explicit() -> None:
    contract = _contract()

    resources = contract["resource_limits"]
    assert resources["maximum_active_generations"] == 1
    assert resources["maximum_queued_generations"] == 1
    assert resources["hard_worker_rss_gib"] == 3.5
    assert "circuit breaker" in " ".join(resources["requirements"])

    privacy = contract["privacy_and_retention"]
    assert privacy["local_mode_network_requests_after_install"] == 0
    assert privacy["telemetry_enabled"] is False
    assert privacy["default_conversation_storage"] == "memory-only per browser session"
    privacy_rules = " ".join(privacy["requirements"])
    assert "not localStorage" in privacy_rules
    assert "Crash dumps" in privacy_rules

    web = contract["optional_web_security"]
    assert web["enabled_by_default"] is False
    assert web["provider_selected"] is False
    web_rules = " ".join(web["requirements"])
    for requirement in ("per-query consent", "zero redirects", "loopback", "local documentation precedence"):
        assert requirement in web_rules

    recovery_rules = " ".join(contract["safe_recovery"]["requirements"])
    assert "process tree" in recovery_rules
    assert "last known-good" in recovery_rules
    assert "no worker/listener remains" in recovery_rules


def test_threat_register_covers_acceptance_with_owner_tests_and_fail_state() -> None:
    threats = _contract()["threat_register"]

    assert [threat["id"] for threat in threats] == [f"AI093-T{number:02d}" for number in range(1, 15)]
    threat_text = " ".join(threat["threat"] for threat in threats).lower()
    for required in (
        "ssrf",
        "path traversal",
        "prompt injection",
        "model-server exposure",
        "csrf",
        "xss",
        "resource exhaustion",
        "poisoned",
        "retention",
        "telemetry",
        "supply-chain",
        "recovery",
    ):
        assert required in threat_text
    for threat in threats:
        assert threat["boundaries"]
        assert len(threat["controls"]) >= 4
        assert threat["owner"].startswith("BPM093-M")
        assert len(threat["future_tests"]) >= 2
        assert threat["fail_state"]


def test_security_contract_records_primary_guidance() -> None:
    guidance = _contract()["reviewed_guidance"]

    assert len(guidance) == 5
    assert sum("owasp.org" in source for source in guidance) == 4
    assert any(source.startswith("https://slsa.dev/spec/") for source in guidance)
