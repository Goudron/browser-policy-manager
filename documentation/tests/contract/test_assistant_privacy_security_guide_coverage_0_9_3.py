import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.docs_contract


def test_m12_03_covers_privacy_without_bypass_guidance():
    c = json.loads(
        (
            Path(__file__).resolve().parents[3]
            / "documentation/config/assistant-privacy-security-guide-coverage-0.9.3.json"
        ).read_text()
    )
    assert (
        c["backlog_item"] == "BPM093-M12-03"
        and len(c["coverage"]) == 7
        and "without publishing" in c["rule"]
    )
