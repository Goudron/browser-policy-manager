import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.docs_contract


def test_m12_01_requires_six_locale_honest_user_guide_coverage():
    c = json.loads(
        (
            Path(__file__).resolve().parents[3]
            / "documentation/config/user-assistant-guide-coverage-0.9.3.json"
        ).read_text()
    )
    assert c["backlog_item"] == "BPM093-M12-01" and len(c["locales"]) == 6 and len(c["topics"]) == 7
    assert "must not claim" in c["truth"]
