from pathlib import Path

import pytest

pytestmark = pytest.mark.docs_contract


def test_m11_05_runbook_requires_verification_canary_and_rollback():
    text = (
        Path(__file__).resolve().parents[3]
        / "docs/architecture/ai-component-update-runbook-0.9.3.md"
    ).read_text()
    for word in (
        "license",
        "advisories",
        "checksum",
        "canary",
        "rollback",
        "Offline",
        "lexical-search",
    ):
        assert word in text
