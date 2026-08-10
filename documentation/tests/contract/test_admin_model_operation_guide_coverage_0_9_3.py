import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.docs_contract


def test_m12_02_admin_guide_keeps_local_operation_boundaries():
    c = json.loads(
        (
            Path(__file__).resolve().parents[3]
            / "documentation/config/admin-model-operation-guide-coverage-0.9.3.json"
        ).read_text()
    )
    assert c["backlog_item"] == "BPM093-M12-02" and len(c["coverage"]) == 7
    assert "neither GPU nor cloud" in c["truth"]
