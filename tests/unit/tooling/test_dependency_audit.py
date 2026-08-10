from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools import dependency_audit


def _write_suppressions(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_checked_in_suppression_policy_is_empty_and_valid() -> None:
    assert dependency_audit.load_suppressions(dependency_audit.DEFAULT_SUPPRESSIONS) == ()


def test_python_suppression_requires_advisory_rationale_owner_and_expiry(tmp_path: Path) -> None:
    suppressions = tmp_path / "suppressions.json"
    _write_suppressions(
        suppressions,
        {
            "version": 1,
            "python": [{"advisory": "PYSEC-1", "rationale": "temporary"}],
            "npm": [],
        },
    )

    with pytest.raises(dependency_audit.SuppressionError, match="advisory.*expires_on"):
        dependency_audit.load_suppressions(suppressions)


def test_expired_python_suppression_is_rejected(tmp_path: Path) -> None:
    suppressions = tmp_path / "suppressions.json"
    _write_suppressions(
        suppressions,
        {
            "version": 1,
            "python": [
                {
                    "advisory": "PYSEC-1",
                    "rationale": "temporary",
                    "owner": "release",
                    "expires_on": "2000-01-01",
                }
            ],
            "npm": [],
        },
    )

    with pytest.raises(dependency_audit.SuppressionError, match="expired"):
        dependency_audit.load_suppressions(suppressions)


def test_npm_suppressions_are_rejected_instead_of_hiding_lockfile_advisories(
    tmp_path: Path,
) -> None:
    suppressions = tmp_path / "suppressions.json"
    _write_suppressions(
        suppressions,
        {
            "version": 1,
            "python": [],
            "npm": [{"advisory": "GHSA-example"}],
        },
    )

    with pytest.raises(dependency_audit.SuppressionError, match="npm audit"):
        dependency_audit.load_suppressions(suppressions)


def test_runner_uses_venv_console_scripts_without_resolving_python_symlink() -> None:
    source = (dependency_audit.REPO_ROOT / "tools" / "dependency_audit.py").read_text(
        encoding="utf-8"
    )

    assert "TOOL_BIN_DIR = Path(sys.executable).parent" in source
    assert '"--package-lock-only"' in source
    assert '"--output-reproducible"' in source
    assert '"--no-deps"' in source
