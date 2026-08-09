from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
MAP_PATH = REPO_ROOT / "docs" / "architecture" / "current-system-map.md"
CONTRACT_PATTERN = re.compile(r"```json system-map-contract\n(?P<contract>.*?)\n```", re.DOTALL)


def _contract() -> dict[str, object]:
    map_text = MAP_PATH.read_text(encoding="utf-8")
    match = CONTRACT_PATTERN.search(map_text)
    assert match, "current-system-map.md must contain its bounded JSON drift contract"
    return json.loads(match.group("contract"))


def test_system_map_contract_references_existing_owned_paths_and_commands():
    contract = _contract()
    assert contract["version"] == "0.9.4"

    paths = contract["paths"]
    assert isinstance(paths, list)
    for relative_path in paths:
        assert isinstance(relative_path, str)
        assert (REPO_ROOT / relative_path).exists(), relative_path

    makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    commands = contract["commands"]
    assert isinstance(commands, list)
    for command in commands:
        assert isinstance(command, str)
        target = command.removeprefix("make ")
        assert re.search(rf"^{re.escape(target)}:", makefile, re.MULTILINE), command


def test_system_map_keeps_release_docs_and_incubation_boundaries_explicit():
    map_text = MAP_PATH.read_text(encoding="utf-8")

    for required_text in (
        "Release Application",
        "Documentation And Optional AI Are Separate Contours",
        "Machine-Checked Drift Contract",
        "must not become a transitive dependency of `app.main`",
        "vendored boundaries. Do not use them for broad context",
    ):
        assert required_text in map_text

    contract = _contract()
    excluded_boundaries = contract["excluded_boundaries"]
    assert isinstance(excluded_boundaries, list)
    assert "app/static/vendor/" in excluded_boundaries
    assert "app/compliance/firefox/cis/generated/" in excluded_boundaries
