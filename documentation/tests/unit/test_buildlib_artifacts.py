from __future__ import annotations

import io
import json
import tarfile
from pathlib import Path

import pytest

from documentation.buildlib import artifacts
from documentation.buildlib.shared import BuildError


def _policy(root: str = "bpm-documentation") -> dict[str, object]:
    return {
        "schema_version": 1,
        "archive": {"root": root},
        "paths": {
            "release_archive": "documentation/dist/docs.tar.gz",
            "release_checksum": "documentation/dist/docs.tar.gz.sha256",
        },
        "current_runtime_contract": {
            "runtime_ready": False,
            "required_before_shipping": ["release extraction"],
        },
    }


def _archive(path: Path, members: dict[str, bytes], *, symlink: str | None = None) -> None:
    with tarfile.open(path, "w:gz") as bundle:
        for name, payload in members.items():
            info = tarfile.TarInfo(name)
            info.size = len(payload)
            bundle.addfile(info, io.BytesIO(payload))
        if symlink is not None:
            info = tarfile.TarInfo(symlink)
            info.type = tarfile.SYMTYPE
            info.linkname = "outside"
            bundle.addfile(info)


def test_artifact_policy_rejects_unreadable_or_unsupported_input(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    policy_path = tmp_path / "policy.json"
    monkeypatch.setattr(artifacts, "ARTIFACT_POLICY", policy_path)

    with pytest.raises(BuildError, match="cannot read artifact policy"):
        artifacts._artifact_policy()

    policy_path.write_text("{", encoding="utf-8")
    with pytest.raises(BuildError, match="cannot read artifact policy"):
        artifacts._artifact_policy()

    policy_path.write_text(json.dumps({"schema_version": 2}), encoding="utf-8")
    with pytest.raises(BuildError, match="unsupported artifact policy schema"):
        artifacts._artifact_policy()

    expected = _policy()
    policy_path.write_text(json.dumps(expected), encoding="utf-8")
    assert artifacts._artifact_policy() == expected


def test_integrity_and_paths_use_current_contract_without_product_artifacts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "site"
    root.mkdir()
    (root / "index.html").write_text("site", encoding="utf-8")
    policy = _policy()
    monkeypatch.setattr(
        artifacts, "_load_lock", lambda: {"components": {"dita_ot": {"version": "4.4"}}}
    )
    monkeypatch.setattr(artifacts, "_product_version", lambda: "0.9.4")
    monkeypatch.setattr(artifacts, "_source_fingerprint", lambda: "fingerprint")

    artifacts._write_integrity(root, policy)
    integrity = json.loads((root / "artifact-integrity.json").read_text(encoding="utf-8"))

    assert integrity["bpm_version"] == "0.9.4"
    assert integrity["source_fingerprint"] == "fingerprint"
    assert integrity["files"] == {"index.html": artifacts.sha256_file(root / "index.html")}
    assert artifacts.artifact_paths(policy) == (
        artifacts.REPOSITORY_ROOT / "documentation/dist/docs.tar.gz",
        artifacts.REPOSITORY_ROOT / "documentation/dist/docs.tar.gz.sha256",
    )


def test_source_hashes_are_relative_and_deterministic_for_controlled_inputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    documentation_root = tmp_path / "documentation"
    source = documentation_root / "src/topic.dita"
    asset = documentation_root / "assets/theme.css"
    taxonomy = documentation_root / "config/taxonomy.json"
    labels = documentation_root / "config/labels.json"
    for path, payload in (
        (source, "<topic/>"),
        (asset, "body{}"),
        (taxonomy, "{}"),
        (labels, "{}"),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload, encoding="utf-8")
    monkeypatch.setattr(artifacts, "DOCUMENTATION_ROOT", documentation_root)
    monkeypatch.setattr(artifacts, "TOPIC_SECTION_TAXONOMY", taxonomy)
    monkeypatch.setattr(artifacts, "TOPIC_SECTION_LABELS", labels)

    assert artifacts.source_hashes() == {
        "assets/theme.css": "7c98040a541657584690ae2a1cc3b42a8b53b159cc60c5d3abbfecbaeac6c94a",
        "config/labels.json": "44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a",
        "config/taxonomy.json": "44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a",
        "src/topic.dita": "2fa84835aa1fb80102a121ae3c64b196276ae4235e2693294b70e9142a19cd08",
    }


def test_source_fingerprint_tracks_every_declared_build_input(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = tmp_path / "repository"
    documentation_root = repository / "documentation"
    input_path = repository / "input.txt"
    theme_root = repository / "theme"
    input_path.parent.mkdir(parents=True)
    input_path.write_text("first", encoding="utf-8")
    (repository / "pyproject.toml").write_text("[project]", encoding="utf-8")
    theme_root.mkdir()
    for name in (
        artifacts.SEARCH_SCRIPT,
        artifacts.MODEL_MANAGER_SCRIPT,
        artifacts.ASSISTANT_RENDERER_SCRIPT,
        artifacts.ASSISTANT_STATE_MACHINE_SCRIPT,
        artifacts.ASSISTANT_CONVERSATION_SCRIPT,
        artifacts.ASSISTANT_TRANSPORT_SCRIPT,
        artifacts.ASSISTANT_SHELL_SCRIPT,
    ):
        (theme_root / name).write_text(name, encoding="utf-8")

    monkeypatch.setattr(artifacts, "REPOSITORY_ROOT", repository)
    monkeypatch.setattr(artifacts, "DOCUMENTATION_ROOT", documentation_root)
    monkeypatch.setattr(artifacts, "THEME_ROOT", theme_root)
    monkeypatch.setattr(artifacts, "dita_sources", lambda: [input_path])
    monkeypatch.setattr(artifacts, "__file__", str(input_path))
    for name in (
        "DOCUMENTATION_ASSISTANT_COPY",
        "PDF_THEME",
        "PDF_PRINT_CSS",
        "PDF_COVER_LOGO",
        "PDF_COVER_BRANDING",
        "PDF_UI_FOOTER_TEMPLATE",
        "PDF_LAYOUT_CONTRACT",
        "PDF_GENERATION_CONTRACT",
        "MANIFEST_SCHEMA",
        "UI_TARGET_SCHEMA",
        "NAVIGATION_SCHEMA",
        "SEARCH_CORPUS_CONTRACT",
        "SEARCH_NORMALIZATION_ALIASES",
        "SEARCH_RANKING_TYPO",
        "SEARCH_FACETS_FILTERS",
        "SEARCH_DOMAIN_RANKING_FACETS",
        "SEARCH_QUALITY_PERFORMANCE",
        "SEARCH_INTEGRITY_DRIFT",
        "TOPIC_SECTION_TAXONOMY",
        "TOPIC_SECTION_LABELS",
        "LOCK_PATH",
    ):
        monkeypatch.setattr(artifacts, name, input_path)
    monkeypatch.setattr(
        artifacts,
        "PDF_UI_FOOTER_CATALOGS",
        tuple(input_path for _locale in artifacts.LOCALES),
    )
    metadata = documentation_root / "config/metadata-vocabulary.json"
    metadata.parent.mkdir(parents=True)
    metadata.write_text("metadata", encoding="utf-8")
    (metadata.parent / "user-guide-map-0.9.0.json").write_text("map", encoding="utf-8")
    buildlib = documentation_root / "buildlib"
    buildlib.mkdir()
    (buildlib / "shared.py").write_text("shared owner", encoding="utf-8")
    (buildlib / "pdf.py").write_text("PDF owner", encoding="utf-8")

    first = artifacts._source_fingerprint()
    input_path.write_text("second", encoding="utf-8")

    assert first != artifacts._source_fingerprint()


@pytest.mark.parametrize(
    ("members", "symlink", "diagnostic"),
    [
        ({"outside/file.txt": b"outside"}, None, "archive member escapes artifact root"),
        ({"bpm-documentation/file.txt": b"file"}, None, "archive has no valid artifact-integrity"),
        ({}, "bpm-documentation/link", "special archive member is forbidden"),
    ],
)
def test_archive_verification_rejects_unsafe_or_incomplete_payloads(
    tmp_path: Path,
    members: dict[str, bytes],
    symlink: str | None,
    diagnostic: str,
) -> None:
    archive = tmp_path / "artifact.tar.gz"
    _archive(archive, members, symlink=symlink)

    with pytest.raises(BuildError, match=diagnostic):
        artifacts.verify_archive(archive, _policy())


def test_archive_verification_rejects_wrong_runtime_state_and_hashes(tmp_path: Path) -> None:
    archive = tmp_path / "artifact.tar.gz"
    integrity = {"runtime_ready": True, "files": {}}
    _archive(
        archive,
        {"bpm-documentation/artifact-integrity.json": json.dumps(integrity).encode()},
    )
    with pytest.raises(BuildError, match="runtime status"):
        artifacts.verify_archive(archive, _policy())

    integrity["runtime_ready"] = False
    _archive(
        archive,
        {
            "bpm-documentation/artifact-integrity.json": json.dumps(integrity).encode(),
            "bpm-documentation/en/index.html": b"site",
        },
    )
    with pytest.raises(BuildError, match="integrity file list"):
        artifacts.verify_archive(archive, _policy())


def test_archive_round_trip_is_reproducible_and_validates_manifest_payloads(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "bpm-documentation"
    payloads: dict[str, bytes] = {}
    for locale in artifacts.LOCALES:
        relative = f"{locale}/index.html"
        payload = f"<html lang={locale!r}></html>".encode()
        payloads[relative] = payload
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    integrity = {
        "runtime_ready": False,
        "files": {
            name: artifacts.hashlib.sha256(payload).hexdigest()
            for name, payload in payloads.items()
        },
    }
    (root / "artifact-integrity.json").write_text(json.dumps(integrity), encoding="utf-8")
    first = tmp_path / "first.tar.gz"
    second = tmp_path / "second.tar.gz"
    artifacts.create_archive(root, first)
    artifacts.create_archive(root, second)
    validated: list[dict[str, bytes]] = []
    monkeypatch.setattr(
        artifacts,
        "validate_manifest_payloads",
        lambda archive_payloads: validated.append(archive_payloads),
    )

    digest = artifacts.verify_archive(first, _policy())

    assert first.read_bytes() == second.read_bytes()
    assert digest == artifacts.hashlib.sha256(first.read_bytes()).hexdigest()
    assert validated == [payloads]


def test_archive_verification_rejects_missing_locale_root(tmp_path: Path) -> None:
    archive = tmp_path / "artifact.tar.gz"
    payload = b"site"
    integrity = {
        "runtime_ready": False,
        "files": {"en/index.html": artifacts.hashlib.sha256(payload).hexdigest()},
    }
    _archive(
        archive,
        {
            "bpm-documentation/artifact-integrity.json": json.dumps(integrity).encode(),
            "bpm-documentation/en/index.html": payload,
        },
    )

    with pytest.raises(BuildError, match="does not contain every locale root"):
        artifacts.verify_archive(archive, _policy())


def test_archive_verification_rejects_unreadable_regular_member(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive = tmp_path / "artifact.tar.gz"
    archive.write_bytes(b"placeholder")
    member = tarfile.TarInfo("bpm-documentation/en/index.html")
    member.size = 1

    class UnreadableArchive:
        def __enter__(self) -> UnreadableArchive:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def getmembers(self) -> list[tarfile.TarInfo]:
            return [member]

        def extractfile(self, _member: tarfile.TarInfo) -> None:
            return None

    monkeypatch.setattr(artifacts.tarfile, "open", lambda *_args, **_kwargs: UnreadableArchive())

    with pytest.raises(BuildError, match="cannot read archive member"):
        artifacts.verify_archive(archive, _policy())


def test_tar_metadata_policy_paths_and_cleanup_alias(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    directory = artifacts._tar_filter(tarfile.TarInfo("directory"))
    directory.type = tarfile.DIRTYPE
    assert artifacts._tar_filter(directory).mode == 0o755
    regular = tarfile.TarInfo("file")
    regular.size = 0
    assert artifacts._tar_filter(regular).mode == 0o644
    special = tarfile.TarInfo("link")
    special.type = tarfile.SYMTYPE
    special.mode = 0o777
    assert artifacts._tar_filter(special).mode == 0o777
    for info in (directory, regular, special):
        assert (info.uid, info.gid, info.uname, info.gname, info.mtime) == (0, 0, "", "", 0)

    policy_path = tmp_path / "policy.json"
    policy_path.write_text(json.dumps(_policy()), encoding="utf-8")
    monkeypatch.setattr(artifacts, "ARTIFACT_POLICY", policy_path)
    assert artifacts.artifact_paths() == (
        artifacts.REPOSITORY_ROOT / "documentation/dist/docs.tar.gz",
        artifacts.REPOSITORY_ROOT / "documentation/dist/docs.tar.gz.sha256",
    )
    removed: list[Path] = []
    monkeypatch.setattr(artifacts, "remove_path", removed.append)
    artifacts._remove_path(tmp_path / "candidate")
    assert removed == [tmp_path / "candidate"]
