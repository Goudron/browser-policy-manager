"""Build publication, dev-site installation, and archive commands."""

# ruff: noqa: F403, F405
from .artifacts import (
    _artifact_policy,
    _source_fingerprint,
    _write_integrity,
    artifact_paths,
    create_archive,
    tree_hashes,
    verify_archive,
)
from .catalog import validate_manifest_files
from .lifecycle import (
    Progress,
    StagedDirectory,
    atomic_promote,
    atomic_promote_many,
    tracked_operation,
)
from .pdf import build_tree
from .shared import *
from .shared import _product_version
from .sources import validate_sources


def publish() -> None:
    BUILD_ROOT.mkdir(parents=True, exist_ok=True)
    with StagedDirectory(BUILD_ROOT, "site-build") as staging:
        candidate = staging.candidate("site")
        destination = BUILD_ROOT / "site"
        progress = Progress("Documentation site publication", 3)
        with tracked_operation(progress):
            progress.phase("validate sources")
            validate_sources()
            progress.complete_unit("source validation")
            progress.phase("build verified site candidate")
            build_tree(candidate)
            progress.complete_unit("site candidate")
            progress.phase("validate and atomically promote site")
            atomic_promote(candidate, destination, validate=validate_manifest_files)
            progress.complete_unit("site promotion")
    print(f"Published documentation to {destination.relative_to(REPOSITORY_ROOT)}", flush=True)


def _dev_site_is_current(source_fingerprint: str) -> bool:
    if not DEV_SITE_ROOT.is_dir() or not DEV_SITE_METADATA.is_file():
        return False
    try:
        metadata = json.loads(DEV_SITE_METADATA.read_text(encoding="utf-8"))
    except OSError, json.JSONDecodeError:
        return False
    if metadata.get("source_fingerprint") != source_fingerprint:
        return False
    try:
        validate_manifest_files(DEV_SITE_ROOT)
    except BuildError:
        return False
    return True


def _promote_dev_site(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with StagedDirectory(destination.parent, f"{destination.name}-install") as staging:
        candidate = staging.candidate(destination.name)
        shutil.copytree(source, candidate)
        atomic_promote(candidate, destination, validate=validate_manifest_files)


def install_dev_site() -> None:
    """Install the locally built documentation site into the BPM dev runtime path."""

    source_fingerprint = _source_fingerprint()
    if _dev_site_is_current(source_fingerprint):
        print(
            f"Installed dev documentation is current at {DEV_SITE_ROOT.relative_to(REPOSITORY_ROOT)}",
            flush=True,
        )
        return

    progress = Progress("Documentation dev-site installation", 2)
    with tracked_operation(progress):
        progress.phase("build publishable site")
        publish()
        progress.complete_unit("publishable site")
        progress.phase("validate and atomically install dev site")
        source = BUILD_ROOT / "site"
        _promote_dev_site(source, DEV_SITE_ROOT)
        metadata = {
            "schema_version": 1,
            "bpm_version": _product_version(),
            "source_fingerprint": source_fingerprint,
            "source_site": source.relative_to(REPOSITORY_ROOT).as_posix(),
            "installed_site": DEV_SITE_ROOT.relative_to(REPOSITORY_ROOT).as_posix(),
        }
        DEV_SITE_METADATA.write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        progress.complete_unit("dev site")
    print(
        f"Installed dev documentation to {DEV_SITE_ROOT.relative_to(REPOSITORY_ROOT)}",
        flush=True,
    )


def validate_build() -> None:
    BUILD_ROOT.mkdir(parents=True, exist_ok=True)
    with StagedDirectory(BUILD_ROOT, "validation") as staging:
        candidate = staging.candidate("site")
        progress = Progress("Documentation validation", 2)
        with tracked_operation(progress):
            progress.phase("validate sources")
            validate_sources()
            progress.complete_unit("source validation")
            progress.phase("build and validate candidate")
            build_tree(candidate)
            progress.complete_unit("candidate")
    print("DITA, metadata, source links, and generated links are valid.", flush=True)


def reproducibility_check() -> None:
    BUILD_ROOT.mkdir(parents=True, exist_ok=True)
    with StagedDirectory(BUILD_ROOT, "reproducibility") as staging:
        root = staging.path
        assert root is not None
        first = root / "first"
        second = root / "second"
        progress = Progress("Documentation reproducibility", 3)
        with tracked_operation(progress):
            progress.phase("validate sources")
            validate_sources()
            progress.complete_unit("source validation")
            progress.phase("build first independent site")
            build_tree(first)
            progress.complete_unit("first site")
            progress.phase("build second independent site")
            build_tree(second)
            progress.complete_unit("second site")
            progress.phase("compare verified SHA-256 file trees")
            first_hashes = tree_hashes(first)
            second_hashes = tree_hashes(second)
            if first_hashes != second_hashes:
                differing = sorted(
                    path
                    for path in set(first_hashes) | set(second_hashes)
                    if first_hashes.get(path) != second_hashes.get(path)
                )
                raise BuildError("non-deterministic publishable files:\n" + "\n".join(differing))
    print(f"Reproducibility check passed for {len(first_hashes)} files.", flush=True)


def package() -> None:
    policy = _artifact_policy()
    archive, checksum_file = artifact_paths(policy)
    DIST_ROOT.mkdir(parents=True, exist_ok=True)
    with StagedDirectory(DIST_ROOT, "documentation-package") as staging:
        progress = Progress("Documentation package", 4)
        with tracked_operation(progress):
            progress.phase("validate sources")
            validate_sources()
            progress.complete_unit("source validation")
            root = staging.candidate(policy["archive"]["root"])
            progress.phase("build artifact tree")
            build_tree(root)
            progress.complete_unit("artifact tree")
            licenses = root / "licenses"
            licenses.mkdir()
            shutil.copyfile(REPOSITORY_ROOT / "LICENSE", licenses / "BPM-MPL-2.0.txt")
            shutil.copyfile(
                DOCUMENTATION_ROOT / "config/THIRD_PARTY_NOTICES.md",
                licenses / "THIRD_PARTY_NOTICES.md",
            )
            _write_integrity(root, policy)
            candidate = staging.candidate(archive.name)
            progress.phase("create and verify archive SHA-256")
            create_archive(root, candidate)
            digest = verify_archive(candidate, policy)
            progress.complete_unit("archive")
            candidate_checksum = staging.candidate(checksum_file.name)
            candidate_checksum.write_text(f"{digest}  {archive.name}\n", encoding="ascii")
            progress.phase("atomically promote verified archive and checksum")
            atomic_promote_many(((candidate, archive), (candidate_checksum, checksum_file)))
            progress.complete_unit("archive and checksum")
    print(f"Packaged documentation candidate: {archive.relative_to(REPOSITORY_ROOT)}", flush=True)


def verify_package() -> None:
    policy = _artifact_policy()
    archive, checksum_file = artifact_paths(policy)
    if not archive.is_file() or not checksum_file.is_file():
        raise BuildError("documentation package or checksum is absent; run make docs-package")
    digest = verify_archive(archive, policy)
    expected_checksum = f"{digest}  {archive.name}\n"
    if checksum_file.read_text(encoding="ascii") != expected_checksum:
        raise BuildError("documentation package checksum file does not match archive")
    print(f"Verified documentation package SHA-256: {digest}", flush=True)
