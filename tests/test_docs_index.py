from tests.docs_index import DOCS_INDEX_PATH, REPO_ROOT, docs_index_rows, docs_manifest

VALID_STATUSES = {"active", "runbook", "audit", "backlog", "archive"}


def _maintained_docs_files() -> set[str]:
    docs_root = REPO_ROOT / "docs"
    paths: set[str] = set()
    for path in docs_root.rglob("*"):
        if not path.is_file():
            continue
        if "screenshots" in path.relative_to(docs_root).parts:
            continue
        paths.add(path.relative_to(docs_root).as_posix())
    return paths


def test_docs_index_lists_every_maintained_docs_file_once():
    indexed_paths = [row["path"] for row in docs_index_rows()]

    assert sorted(indexed_paths) == sorted(_maintained_docs_files())
    assert len(indexed_paths) == len(set(indexed_paths))


def test_docs_index_rows_use_known_statuses_and_existing_links():
    for row in docs_index_rows():
        assert row["status"] in VALID_STATUSES
        assert (REPO_ROOT / "docs" / row["path"]).exists()
        assert (DOCS_INDEX_PATH.parent / row["link"]).resolve() == (
            REPO_ROOT / "docs" / row["path"]
        ).resolve()


def test_archived_q2_docs_are_reached_through_index_statuses():
    archived_paths = [
        row["path"]
        for row in docs_index_rows()
        if row["path"].startswith("archive/2026-q2/")
    ]

    assert archived_paths
    for row in docs_index_rows():
        if row["path"].startswith("archive/2026-q2/"):
            assert row["status"] in {"audit", "backlog", "archive"}


def test_docs_manifest_finished_backlog_sources_are_indexed():
    indexed_paths = {row["path"] for row in docs_index_rows()}
    manifest = docs_manifest()

    assert manifest["schema_version"] == 1
    for item in manifest["finished_backlog_items"]:
        assert item["status"] == "done"
        assert item["source_doc"] in indexed_paths
        assert (REPO_ROOT / "docs" / item["source_doc"]).exists()
