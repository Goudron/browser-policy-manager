import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.docs_contract


def test_m11_04_keeps_adapter_out_of_v093_without_full_evidence():
    c = json.loads(
        (
            Path(__file__).resolve().parents[3]
            / "documentation/config/adapter-governance-0.9.3.json"
        ).read_text()
    )
    assert c["backlog_item"] == "BPM093-M11-04" and c["v093_requires_adapter"] is False
    assert (
        "forbidden" in c["data"]
        and "six-locale" in c["release"]
        and "No adapter ships" in c["shipping"]
    )
