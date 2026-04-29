from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKLOG_PATH = REPO_ROOT / "docs/profile_workspace_split_simplification_backlog_2026-04-21.md"


def test_simplified_wizard_component_contract_is_documented():
    backlog = BACKLOG_PATH.read_text(encoding="utf-8")

    assert "### `WS-D01` Define The Simplified Wizard Component Contract" in backlog
    assert "Status: Done" in backlog
    assert "Simplified wizard component contract:" in backlog
    assert "Every default-visible wizard section should answer one admin question" in backlog
    assert "Title" in backlog
    assert "One-line purpose" in backlog
    assert "Primary choice" in backlog
    assert "Active state" in backlog
    assert "Real warnings" in backlog
    assert "Advanced link" in backlog
    assert "What must leave the default path:" in backlog
    assert "Settings maps and guided coverage maps." in backlog
    assert "`remaining N of M` coverage language." in backlog
    assert "Completion checklist for `WS-D02` through `WS-D13`:" in backlog
