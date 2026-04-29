from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
ALLOWED_PATHS = {
    "alembic/versions/20260330_upgrade_profiles_to_firefox149.py",
    "alembic/versions/20260423_upgrade_profiles_to_firefox150.py",
    "tests/test_migrations.py",
    "tests/test_no_legacy_schema_refs.py",
    ".github/workflows/ci.yml",
}
BANNED_TOKENS = (
    "release-148",
    "release-149",
    "esr-140.8",
    "esr-140.9",
    "firefox-release-148.json",
    "firefox-release-149.json",
    "firefox-esr-140.8.json",
    "firefox-esr-140.9.json",
    "firefox-esr140.json",
    "mozilla-policy-templates-v7.8",
    "mozilla-policy-templates-v7.9",
    "release148",
    "release149",
)


def iter_text_files() -> list[Path]:
    roots = ("app", "tests", "tools", ".github", "README.md")
    files: list[Path] = []
    for root in roots:
        path = REPO_ROOT / root
        if path.is_file():
            files.append(path)
            continue
        files.extend(p for p in path.rglob("*") if p.is_file())
    return files


@pytest.mark.parametrize("token", BANNED_TOKENS)
def test_repository_contains_no_legacy_schema_refs(token: str):
    offenders: list[str] = []

    for path in iter_text_files():
        rel_path = path.relative_to(REPO_ROOT).as_posix()
        if rel_path in ALLOWED_PATHS:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if token in content:
            offenders.append(rel_path)

    assert not offenders, f"Legacy token {token!r} found in: {', '.join(offenders)}"
