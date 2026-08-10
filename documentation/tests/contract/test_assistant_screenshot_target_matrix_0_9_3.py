import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.docs_contract


def test_m12_04_targets_are_six_locale_manifest_backed():
    c = json.loads(
        (
            Path(__file__).resolve().parents[3]
            / "documentation/config/assistant-screenshot-target-matrix-0.9.3.json"
        ).read_text()
    )
    assert (
        c["backlog_item"] == "BPM093-M12-04"
        and len(c["locales"]) == 6
        and "Never edit generated output" in c["rules"]
    )
