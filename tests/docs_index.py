import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_INDEX_PATH = REPO_ROOT / "docs" / "docs-index.md"
DOCS_MANIFEST_PATH = REPO_ROOT / "docs" / "docs-manifest.json"

DOCS_INDEX_ROW_RE = re.compile(
    r"^\| \[docs/(?P<path>[^\]]+)\]\((?P<link>[^)]+)\) "
    r"\| (?P<status>active|runbook|audit|backlog|archive) \|",
)


def docs_index_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in DOCS_INDEX_PATH.read_text(encoding="utf-8").splitlines():
        match = DOCS_INDEX_ROW_RE.match(line)
        if match:
            rows.append(match.groupdict())
    return rows


def docs_manifest() -> dict[str, object]:
    return json.loads(DOCS_MANIFEST_PATH.read_text(encoding="utf-8"))


def doc_path_from_index(filename: str, *, status: str | None = None) -> Path:
    matches = [
        row
        for row in docs_index_rows()
        if row["path"] == filename or row["path"].endswith(f"/{filename}")
    ]
    if not matches:
        raise AssertionError(f"{filename!r} is not listed in docs/docs-index.md")
    if len(matches) > 1:
        raise AssertionError(f"{filename!r} has multiple docs/docs-index.md rows")

    row = matches[0]
    if status is not None and row["status"] != status:
        raise AssertionError(
            f"{filename!r} has status {row['status']!r}, expected {status!r}"
        )

    path = REPO_ROOT / "docs" / row["path"]
    if not path.exists():
        raise AssertionError(f"Indexed documentation file does not exist: {path}")
    return path
