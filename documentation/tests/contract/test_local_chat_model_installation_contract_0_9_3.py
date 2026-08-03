from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from app.ai import model_installation

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "documentation/config/local-chat-model-installation-contract-0.9.3.json"
MAKEFILE_PATH = ROOT / "Makefile"

pytestmark = pytest.mark.docs_contract


def _contract() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def test_m6_05_contract_and_implementation_pin_one_selected_artifact() -> None:
    contract = _contract()
    artifact = contract["selected_artifact"]

    assert contract["backlog_item"] == "BPM093-M6-05"
    assert contract["status"] == "implemented"
    runtime_pin = contract["pins"]["runtime_decision"]
    assert (
        hashlib.sha256((ROOT / runtime_pin["path"]).read_bytes()).hexdigest()
        == runtime_pin["sha256"]
    )
    assert artifact == {
        "model_id": model_installation.MODEL_ID,
        "upstream": model_installation.ARTIFACT_UPSTREAM,
        "source_revision": "23749fefcc72300e3a2ad315e1317431b06b590a",
        "source": model_installation.ARTIFACT_SOURCE,
        "filename": model_installation.ARTIFACT_FILENAME,
        "sha256": model_installation.ARTIFACT_SHA256,
        "byte_count": model_installation.ARTIFACT_BYTES,
        "license": model_installation.ARTIFACT_LICENSE,
        "target_architectures": ["x86_64"],
    }


def test_m6_05_contract_requires_explicit_localized_consent_and_safe_lifecycle() -> None:
    contract = _contract()

    consent = contract["consent_and_disclosure"]
    assert consent["locales"] == list(model_installation.ACTIVE_CATALOG_LOCALES)
    assert set(model_installation.DISCLOSURES) == set(consent["locales"])
    assert set(consent["required_fields"]) <= set(
        model_installation.ModelInstaller(Path("data")).disclosure("en")
    )
    assert set(consent["no_implicit_actions"]) >= {"application startup", "chat request"}

    storage = contract["storage_and_integrity"]
    assert "atomic promotion" in " ".join(storage["file_rules"])
    assert "symlinks are refused" in storage["removal"]
    assert "fails closed" in storage["corruption"]
    assert contract["network_and_runtime_boundary"]["offline_operations"] == [
        "describe",
        "verify",
        "install-local",
        "remove",
    ]
    assert "direct regular non-symlink" in storage["offline_local_install"]
    assert "worker" in contract["network_and_runtime_boundary"]["not_implemented"]


def test_m6_05_development_bootstrap_is_explicit_idempotent_and_persistent() -> None:
    contract = _contract()
    makefile = MAKEFILE_PATH.read_text(encoding="utf-8")

    handoff = contract["development_handoff"]
    assert handoff["make_target"] == "make ai-model-install-dev"
    assert "explicit maintainer consent" in handoff["consent_boundary"]
    assert "never removed" in handoff["persistence"]
    assert "dev: docs-install-dev ai-model-install-dev" in makefile
    assert "ai-model-install-dev:" in makefile
    assert "install --locale $(AI_MODEL_LOCALE) --confirm" in makefile
    assert "except data/ai" in makefile
