import json
from pathlib import Path

DOCS = Path(__file__).parents[2]
ROOT = DOCS.parent
CONTRACT = DOCS / "config/maintained-index-snapshot-contract-0.9.3.json"
INDEX = ROOT / "docs/docs-index.md"
GENERATOR = DOCS / "tools/generate_subsystem_snapshot.py"
SNAPSHOT = DOCS / "PROJECT_SNAPSHOT.generated.md"


def test_maintained_index_snapshot_contract_is_complete():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert contract["backlog_item"] == "BPM093-M12-07"
    source = INDEX.read_text(encoding="utf-8")
    generator = GENERATOR.read_text(encoding="utf-8")
    snapshot = SNAPSHOT.read_text(encoding="utf-8")
    assert "Architecture entry points — documentation architecture maintainers" in snapshot
    assert "Declared source digest:" in snapshot
    for entry in contract["architecture_entry_points"]:
        assert (ROOT / "docs/architecture" / entry).is_file()
        assert entry in source
        assert entry in generator
    assert "ARCHITECTURE_ENTRY_POINTS" in generator
    assert "ENVIRONMENT_REPORT_BOUNDARIES" in generator
