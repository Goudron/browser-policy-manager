import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.docs_contract


def test_m11_06_maps_each_change_class_to_required_gates():
    c = json.loads(
        (
            Path(__file__).resolve().parents[3]
            / "documentation/config/maintenance-drift-gates-0.9.3.json"
        ).read_text()
    )
    assert c["backlog_item"] == "BPM093-M11-06" and len(c["matrix"]) == 5
    assert "ordinary deterministic search remains independent" in c["rule"]
