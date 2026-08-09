from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
JAVASCRIPT_TEST_ROOT = REPO_ROOT / "tests/javascript"
OWNERSHIP_PATH = JAVASCRIPT_TEST_ROOT / "test-layer-ownership-0.9.4.json"
NODE_WRAPPER = re.compile(
    r"subprocess\.(?:run|check_call|check_output|Popen)\([\s\S]{0,160}?(?:\[\s*)?[\"']node[\"']"
)


def _relative(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def test_native_javascript_tests_have_exactly_one_layer_and_subsystem_owner():
    ownership = json.loads(OWNERSHIP_PATH.read_text(encoding="utf-8"))
    owners = ownership["test_owners"]
    test_paths = sorted(JAVASCRIPT_TEST_ROOT.glob("*/*/*.test.js"))

    assert ownership["backlog_item"] == "BPM094-M8-05"
    assert test_paths
    for path in test_paths:
        relative = _relative(path)
        matches = [owner for owner in owners if relative.startswith(owner["prefix"])]
        assert len(matches) == 1, f"{relative}: expected one native test owner, got {matches}"
        owner = matches[0]
        assert f"/{owner['layer']}/" in f"/{relative}"
        assert f"/{owner['subsystem']}/" in f"/{relative}"

    owned_paths = {_relative(path) for path in test_paths}
    for owner in owners:
        assert any(path.startswith(owner["prefix"]) for path in owned_paths), owner["id"]


def test_native_javascript_support_and_fixtures_are_not_collected_as_tests():
    ownership = json.loads(OWNERSHIP_PATH.read_text(encoding="utf-8"))

    for owner in ownership["support_owners"]:
        owned_files = [
            path
            for path in JAVASCRIPT_TEST_ROOT.rglob("*")
            if path.is_file() and _relative(path).startswith(owner["prefix"])
        ]
        assert owned_files, owner["id"]
        assert all(not path.name.endswith(".test.js") for path in owned_files)


def test_python_tests_do_not_wrap_node_behavior_anymore():
    offenders = []
    for path in sorted((REPO_ROOT / "tests").rglob("*.py")):
        if NODE_WRAPPER.search(path.read_text(encoding="utf-8")):
            offenders.append(_relative(path))

    assert offenders == []
