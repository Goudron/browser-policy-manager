"""Deterministic source fingerprints and documentation release archives."""

# ruff: noqa: F403, F405
from .catalog import validate_manifest_payloads
from .lifecycle import remove_path, sha256_file
from .shared import *
from .shared import _load_lock, _product_version
from .sources import dita_sources


def tree_hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): sha256_file(path)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def source_hashes() -> dict[str, str]:
    roots = (DOCUMENTATION_ROOT / "src", DOCUMENTATION_ROOT / "assets")
    paths = [
        *(path for root in roots for path in sorted(root.rglob("*")) if path.is_file()),
        TOPIC_SECTION_TAXONOMY,
        TOPIC_SECTION_LABELS,
    ]
    return {
        path.relative_to(DOCUMENTATION_ROOT).as_posix(): (
            hashlib.sha256(path.read_bytes()).hexdigest()
        )
        for path in paths
    }


def _artifact_policy() -> dict[str, Any]:
    try:
        policy = json.loads(ARTIFACT_POLICY.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BuildError(f"cannot read artifact policy: {exc}") from exc
    if policy.get("schema_version") != 1:
        raise BuildError("unsupported artifact policy schema")
    return policy


def _source_fingerprint() -> str:
    inputs = [
        *dita_sources(),
        *sorted((DOCUMENTATION_ROOT / "src/shared/filters").glob("*.ditaval")),
        *sorted(THEME_ROOT.glob("*.css")),
        THEME_ROOT / SEARCH_SCRIPT,
        THEME_ROOT / MODEL_MANAGER_SCRIPT,
        THEME_ROOT / ASSISTANT_RENDERER_SCRIPT,
        THEME_ROOT / ASSISTANT_STATE_MACHINE_SCRIPT,
        THEME_ROOT / ASSISTANT_CONVERSATION_SCRIPT,
        THEME_ROOT / ASSISTANT_TRANSPORT_SCRIPT,
        THEME_ROOT / ASSISTANT_SHELL_SCRIPT,
        DOCUMENTATION_ASSISTANT_COPY,
        PDF_THEME,
        PDF_PRINT_CSS,
        PDF_COVER_LOGO,
        PDF_COVER_BRANDING,
        PDF_UI_FOOTER_TEMPLATE,
        *PDF_UI_FOOTER_CATALOGS,
        PDF_LAYOUT_CONTRACT,
        PDF_GENERATION_CONTRACT,
        MANIFEST_SCHEMA,
        UI_TARGET_SCHEMA,
        NAVIGATION_SCHEMA,
        DOCUMENTATION_ROOT / "config/metadata-vocabulary.json",
        DOCUMENTATION_ROOT / "config/user-guide-map-0.9.0.json",
        SEARCH_CORPUS_CONTRACT,
        SEARCH_NORMALIZATION_ALIASES,
        SEARCH_RANKING_TYPO,
        SEARCH_FACETS_FILTERS,
        SEARCH_DOMAIN_RANKING_FACETS,
        SEARCH_QUALITY_PERFORMANCE,
        SEARCH_INTEGRITY_DRIFT,
        TOPIC_SECTION_TAXONOMY,
        TOPIC_SECTION_LABELS,
        LOCK_PATH,
        REPOSITORY_ROOT / "pyproject.toml",
        REPOSITORY_ROOT / "documentation/buildlib/shared.py",
        REPOSITORY_ROOT / "documentation/buildlib/pdf.py",
        Path(__file__),
    ]
    digest = hashlib.sha256()
    for path in sorted(set(inputs)):
        digest.update(path.relative_to(REPOSITORY_ROOT).as_posix().encode())
        digest.update(b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def _write_integrity(root: Path, policy: dict[str, Any]) -> None:
    lock = _load_lock()
    runtime = policy["current_runtime_contract"]
    integrity = {
        "schema_version": 1,
        "bpm_version": _product_version(),
        "documentation_version": _product_version(),
        "dita_ot_version": lock["components"]["dita_ot"]["version"],
        "locales": list(LOCALES),
        "source_fingerprint": _source_fingerprint(),
        "runtime_ready": runtime["runtime_ready"],
        "runtime_blockers": runtime["required_before_shipping"],
        "files": tree_hashes(root),
    }
    (root / "artifact-integrity.json").write_text(
        json.dumps(integrity, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _tar_filter(info: tarfile.TarInfo) -> tarfile.TarInfo:
    info.uid = 0
    info.gid = 0
    info.uname = ""
    info.gname = ""
    info.mtime = 0
    if info.isdir():
        info.mode = 0o755
    elif info.isfile():
        info.mode = 0o644
    return info


def create_archive(root: Path, archive: Path) -> None:
    with archive.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
            bundle = tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT)
            try:
                paths = [root, *sorted(root.rglob("*"), key=lambda path: path.as_posix().lower())]
                for path in paths:
                    arcname = path.relative_to(root.parent).as_posix()
                    bundle.add(path, arcname=arcname, recursive=False, filter=_tar_filter)
            finally:
                bundle.close()


def verify_archive(archive: Path, policy: dict[str, Any] | None = None) -> str:
    policy = policy or _artifact_policy()
    expected_root = policy["archive"]["root"]
    payloads: dict[str, bytes] = {}
    with tarfile.open(archive, "r:gz") as bundle:
        for member in bundle.getmembers():
            parts = Path(member.name).parts
            if not parts or parts[0] != expected_root or ".." in parts:
                raise BuildError(f"archive member escapes artifact root: {member.name}")
            if member.issym() or member.islnk() or member.isdev():
                raise BuildError(f"special archive member is forbidden: {member.name}")
            if member.isfile():
                stream = bundle.extractfile(member)
                if stream is None:
                    raise BuildError(f"cannot read archive member: {member.name}")
                payloads[Path(*parts[1:]).as_posix()] = stream.read()
    try:
        integrity = json.loads(payloads.pop("artifact-integrity.json").decode("utf-8"))
    except (KeyError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BuildError("archive has no valid artifact-integrity.json") from exc
    if integrity.get("runtime_ready") is not False:
        raise BuildError("artifact runtime status does not match the current blocked contract")
    expected_files = integrity.get("files")
    actual_files = {name: hashlib.sha256(content).hexdigest() for name, content in payloads.items()}
    if expected_files != actual_files:
        raise BuildError("artifact integrity file list or SHA-256 values do not match archive")
    if set(LOCALES) - {Path(name).parts[0] for name in payloads}:
        raise BuildError("artifact does not contain every locale root")
    validate_manifest_payloads(payloads)
    return hashlib.sha256(archive.read_bytes()).hexdigest()


def artifact_paths(policy: dict[str, Any] | None = None) -> tuple[Path, Path]:
    policy = policy or _artifact_policy()
    return (
        REPOSITORY_ROOT / policy["paths"]["release_archive"],
        REPOSITORY_ROOT / policy["paths"]["release_checksum"],
    )


def _remove_path(path: Path) -> None:
    """Compatibility alias for the shared controlled-path cleanup helper."""

    remove_path(path)
