import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.docs_contract


def test_m11_03_intake_is_reviewed_and_non_telemetry():
    c = json.loads(
        (
            Path(__file__).resolve().parents[3]
            / "documentation/config/quality-regression-intake-0.9.3.json"
        ).read_text()
    )
    assert c["backlog_item"] == "BPM093-M11-03"
    assert "No user transcript" in c["rule"]
    assert set(c["required_fixture_fields"]) == {
        "locale",
        "provenance",
        "review_owner",
        "expected_evidence",
        "expected_disposition",
        "regression_command",
    }
