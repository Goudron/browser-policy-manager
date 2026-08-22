"""Deterministic PDF guide generation and verification."""

# ruff: noqa: F403, F405
from collections.abc import Callable

from .artifacts import _source_fingerprint, source_hashes, tree_hashes
from .catalog import (
    _file_sha256,
    _read_json_file,
    _source_revision,
    _write_json,
    generate_manifest_files,
)
from .lifecycle import Progress, StagedDirectory, atomic_promote, remove_path, tracked_operation
from .portal import (
    _normalize_locale_root_links,
    _normalize_screenshot_links,
    _remove_dita_transient_screenshot_copies,
    apply_portal_shell,
    validate_output,
)
from .shared import *
from .shared import _load_lock, _product_version
from .sources import validate_sources

PDF_FIGURE_CAPTION_PREFIXES = {
    "en": "Figure",
    "ru": "Рис.",
    "de": "Abbildung",
    "zh-CN": "图",
    "fr": "Figure",
    "es-ES": "Figura",
}
PDF_USER_GUIDE_FIGURE_COUNT = 11
PDF_CACHE_SCHEMA_VERSION = 1
PDF_CACHE_MANIFEST = "cache-entry.json"
PDF_A4_WIDTH_POINTS = 595.276
PDF_A4_HEIGHT_POINTS = 841.89
PDF_PAGE_NUMBER_FONT_SIZE = 9
PDF_PAGE_NUMBER_BASELINE = 22.677
PDF_HELVETICA_DIGIT_WIDTH = 556


def _run(command: list[str], env: dict[str, str]) -> None:
    completed = subprocess.run(command, env=env, text=True, capture_output=True, check=False)
    if completed.returncode:
        output = (completed.stdout + "\n" + completed.stderr).strip()
        raise BuildError(f"DITA command failed ({' '.join(command)}):\n{output[-12000:]}")


def _dita_environment(java_home: Path) -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "JAVA_HOME": str(java_home),
            "PATH": f"{java_home / 'bin'}:{env.get('PATH', '')}",
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            "TZ": "UTC",
            "SOURCE_DATE_EPOCH": "0",
        }
    )
    return env


def _run_pdf(command: list[str], env: dict[str, str]) -> None:
    """Run DITA PDF conversion and fail on errors emitted with a zero exit code."""

    completed = subprocess.run(command, env=env, text=True, capture_output=True, check=False)
    output = (completed.stdout + "\n" + completed.stderr).strip()
    has_transform_error = "[DOTJ088E]" in output or "BUILD FAILED" in output
    if completed.returncode or has_transform_error:
        raise BuildError(f"DITA PDF command failed ({' '.join(command)}):\n{output[-12000:]}")


def build_tree(destination: Path) -> None:
    dita, java_home = toolchain()
    source_before = source_hashes()
    destination.mkdir(parents=True, exist_ok=False)
    temp_root = destination.parent / f".{destination.name}-dita-temp"
    temp_root.mkdir(parents=True, exist_ok=False)
    env = _dita_environment(java_home)
    progress = Progress("Documentation site build", len(LOCALES))
    try:
        with tracked_operation(progress):
            progress.phase("prepare DITA workspaces")
            for locale in LOCALES:
                maintained_source = DOCUMENTATION_ROOT / f"src/dita/{locale}/maps/portal.ditamap"
                if not maintained_source.is_file():
                    raise BuildError(f"missing locale portal map: {maintained_source}")
                locale_workspace = temp_root / locale
                input_root = locale_workspace / "input"
                shutil.copytree(DOCUMENTATION_ROOT / "src", input_root / "src")
                shutil.copytree(DOCUMENTATION_ROOT / "assets", input_root / "assets")
                source = input_root / f"src/dita/{locale}/maps/portal.ditamap"
                progress.phase(f"DITA HTML5 {locale}")
                _run(
                    [
                        str(dita),
                        "--input",
                        str(source),
                        "--format",
                        "html5",
                        "--output",
                        str(destination / locale),
                        "--temp",
                        str(locale_workspace / "work"),
                    ],
                    env,
                )
                progress.complete_unit(f"DITA HTML5 {locale}")
            progress.phase("assemble portal metadata")
            _normalize_locale_root_links(destination)
            _remove_dita_transient_screenshot_copies(destination)
            apply_portal_shell(destination)
            _normalize_screenshot_links(destination)
            generate_manifest_files(destination)
            validate_output(destination)
            if source_hashes() != source_before:
                raise BuildError("DITA transform mutated maintained documentation source or assets")
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


def _pdf_layout() -> dict[str, Any]:
    layout = _read_json_file(PDF_LAYOUT_CONTRACT)
    if layout.get("schema_version") != 1:
        raise BuildError("unsupported future PDF delivery layout schema")
    if layout.get("target_bpm_version") != _product_version():
        raise BuildError("future PDF delivery layout version does not match BPM version")
    if layout.get("locales") != list(LOCALES):
        raise BuildError("future PDF delivery layout locales do not match the BPM locale matrix")
    guides = layout.get("guides")
    if not isinstance(guides, list) or [guide.get("id") for guide in guides] != [
        guide_id for guide_id, _map_name in PDF_GUIDE_MAPS
    ]:
        raise BuildError("future PDF delivery layout guide order is invalid")
    for guide in guides:
        filename = guide.get("filename")
        if (
            not isinstance(filename, str)
            or "{locale}" not in filename
            or "{bpm_version}" not in filename
        ):
            raise BuildError("future PDF delivery layout guide filename is invalid")
    return layout


def _pdf_generation_policy() -> dict[str, Any]:
    policy = _read_json_file(PDF_GENERATION_CONTRACT)
    if policy.get("schema_version") != 1 or policy.get("backlog_item") != "BPM093-M14-08":
        raise BuildError("unsupported PDF generation contract")
    if policy.get("candidate_root") != "documentation/build/pdf":
        raise BuildError("PDF generation contract candidate root is invalid")
    if policy.get("candidate_path_layout") != "{locale}/{filename}":
        raise BuildError("PDF generation contract candidate path layout is invalid")
    if policy.get("dita_format") != "html5":
        raise BuildError("PDF generation contract DITA format is invalid")
    if policy.get("pdf_renderer") != "chromium":
        raise BuildError("PDF generation contract renderer is invalid")
    if policy.get("page_number_overlay_renderer") != "native-pdf":
        raise BuildError("PDF page-number overlay renderer is invalid")
    if not isinstance(policy.get("ui_footer_year"), int) or policy["ui_footer_year"] < 2025:
        raise BuildError("PDF generation contract UI footer year is invalid")
    expected_maps = [map_name for _guide_id, map_name in PDF_GUIDE_MAPS]
    if policy.get("source_maps") != expected_maps:
        raise BuildError("PDF generation contract source maps are invalid")
    cache = policy.get("development_cache")
    if not isinstance(cache, dict) or cache != {
        "schema_version": PDF_CACHE_SCHEMA_VERSION,
        "root": "documentation/.cache/pdf-pipeline",
        "unit": "locale-guide",
        "layers": ["dita-html5", "verified-pdf"],
        "hash_algorithm": "sha256",
        "reuse": "verified-only",
        "invalid_entry": "quarantine-and-rebuild",
        "promotion": "staged-and-atomic",
    }:
        raise BuildError("PDF generation contract development cache is invalid")
    parallelism = policy.get("parallelism")
    if not isinstance(parallelism, dict) or parallelism.get("max_workers") != 1:
        raise BuildError("PDF generation contract parallelism boundary is invalid")
    return policy


def _pdf_cache_root(policy: dict[str, Any]) -> Path:
    """Resolve the contract-pinned ignored cache without accepting an arbitrary path."""

    configured = policy["development_cache"]["root"]
    if configured != "documentation/.cache/pdf-pipeline":
        raise BuildError("PDF cache root is outside the maintained ignored boundary")
    return REPOSITORY_ROOT / configured


def _pdf_input_name(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(REPOSITORY_ROOT.resolve()).as_posix()
    except ValueError:
        return resolved.as_posix()


def _pdf_file_hashes(paths: list[Path] | tuple[Path, ...]) -> dict[str, str]:
    result: dict[str, str] = {}
    for path in sorted(set(paths)):
        if not path.is_file() or path.is_symlink():
            raise BuildError(f"PDF cache input is missing or unsafe: {path}")
        result[_pdf_input_name(path)] = _file_sha256(path)
    return result


def _pdf_cache_fingerprint(inputs: dict[str, Any]) -> str:
    payload = json.dumps(
        inputs,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _pdf_local_dependency(source: Path, reference: str) -> Path | None:
    parsed = urllib.parse.urlparse(reference.split("#", 1)[0])
    if parsed.scheme or parsed.netloc or not parsed.path:
        return None
    relative = Path(urllib.parse.unquote(parsed.path))
    if relative.is_absolute():
        raise BuildError(f"PDF source dependency is absolute in {source}: {reference!r}")
    target = (source.parent / relative).resolve()
    try:
        target.relative_to(REPOSITORY_ROOT.resolve())
    except ValueError as exc:
        raise BuildError(f"PDF source dependency leaves the repository: {reference!r}") from exc
    return target if target.is_file() and not target.is_symlink() else None


def _pdf_pair_source_hashes(locale: str, map_name: str) -> dict[str, str]:
    """Hash the transitive source and locale-asset closure for one printable map.

    The locale keys map is a registry shared by all guides.  Hashing the whole
    registry would invalidate an unrelated guide whenever one unused key is
    added, so the cache records only key definitions reached from this map and
    its topic closure, plus the language-neutral keys-map context.
    """

    map_path = DOCUMENTATION_ROOT / f"src/dita/{locale}/maps/{map_name}"
    keys_path = map_path.parent / "keys.ditamap"
    try:
        keys_root = ET.parse(keys_path).getroot()
    except (OSError, ET.ParseError) as exc:
        raise BuildError(f"cannot read PDF cache keys for {locale}/{map_name}: {exc}") from exc

    keydefs: dict[str, ET.Element] = {}
    for keydef in keys_root.findall(".//keydef"):
        for key in keydef.get("keys", "").split():
            keydefs[key] = keydef
    context = ET.Element(keys_root.tag, keys_root.attrib)
    for child in keys_root:
        if child.tag != "keydef":
            context.append(child)

    records: dict[str, str] = {
        f"keys-context:{_pdf_input_name(keys_path)}": (
            hashlib.sha256(ET.tostring(context, encoding="utf-8")).hexdigest()
        )
    }
    pending = [map_path]
    for child in context:
        reference = child.get("href")
        if reference:
            target = _pdf_local_dependency(keys_path, reference)
            if target is not None:
                pending.append(target)
    visited: set[Path] = set()
    used_keys: set[str] = set()
    while pending:
        source = pending.pop().resolve()
        if source in visited:
            continue
        if not source.is_file() or source.is_symlink():
            raise BuildError(f"PDF pair source is missing or unsafe: {source}")
        visited.add(source)
        records[_pdf_input_name(source)] = _file_sha256(source)
        if source.suffix.lower() not in {".dita", ".ditamap", ".xml"}:
            continue
        try:
            root = ET.parse(source).getroot()
        except ET.ParseError as exc:
            raise BuildError(f"cannot parse PDF pair source {source}: {exc}") from exc
        for element in root.iter():
            keyref = element.get("keyref") or element.get("conkeyref")
            if keyref:
                key = keyref.split("/", 1)[0]
                if key not in used_keys:
                    used_keys.add(key)
                    keydef = keydefs.get(key)
                    if keydef is None:
                        records[f"external-keyref:{key}"] = hashlib.sha256(
                            key.encode("utf-8")
                        ).hexdigest()
                    else:
                        records[f"keydef:{key}"] = hashlib.sha256(
                            ET.tostring(keydef, encoding="utf-8")
                        ).hexdigest()
                        href = keydef.get("href")
                        if href:
                            target = _pdf_local_dependency(keys_path, href)
                            if target is not None:
                                pending.append(target)
            for attribute in ("href", "conref"):
                reference = element.get(attribute)
                if not reference:
                    continue
                target = _pdf_local_dependency(source, reference)
                if target is None or target == keys_path.resolve():
                    continue
                pending.append(target)

    return dict(sorted(records.items()))


def _pdf_toolchain_identity(dita: Path, java_home: Path) -> dict[str, Any]:
    lock = _load_lock()
    java = java_home / "bin/java"
    return {
        "lock": _pdf_file_hashes((LOCK_PATH,)),
        "versions": {
            "dita_ot": lock["components"]["dita_ot"]["version"],
            "java": lock["components"]["java"]["version"],
        },
        "executables": _pdf_file_hashes((dita, java)),
    }


def _pdf_executable_identity(executable: str, version_args: tuple[str, ...]) -> dict[str, str]:
    completed = subprocess.run(
        [executable, *version_args],
        text=True,
        capture_output=True,
        check=False,
    )
    output = (completed.stdout + "\n" + completed.stderr).strip()
    if completed.returncode or not output:
        raise BuildError(f"cannot identify PDF tool {executable}: {output[-2000:]}")
    return {"path": str(Path(executable).resolve()), "version": output.splitlines()[0]}


def _pdf_runtime_identity() -> dict[str, dict[str, str]]:
    chromium = _chromium_pdf_renderer()
    qpdf = shutil.which("qpdf")
    pdftotext = shutil.which("pdftotext")
    if qpdf is None or pdftotext is None:
        raise BuildError("qpdf and pdftotext are required for verified PDF caching")
    return {
        "chromium": _pdf_executable_identity(chromium, ("--version",)),
        "qpdf": _pdf_executable_identity(qpdf, ("--version",)),
        "pdftotext": _pdf_executable_identity(pdftotext, ("-v",)),
    }


def _pdf_pair_html_inputs(
    *,
    locale: str,
    guide_id: str,
    map_name: str,
    policy: dict[str, Any],
    toolchain_identity: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": PDF_CACHE_SCHEMA_VERSION,
        "kind": "dita-html5",
        "locale": locale,
        "guide": guide_id,
        "format": policy["dita_format"],
        "environment": policy["determinism"]["environment"],
        "sources": _pdf_pair_source_hashes(locale, map_name),
        "toolchain": toolchain_identity,
        "generator": _pdf_file_hashes((Path(__file__),)),
    }


def _pdf_pair_pdf_inputs(
    *,
    locale: str,
    guide_id: str,
    html_fingerprint: str,
    policy: dict[str, Any],
    runtime_identity: dict[str, dict[str, str]],
) -> dict[str, Any]:
    return {
        "schema_version": PDF_CACHE_SCHEMA_VERSION,
        "kind": "verified-pdf",
        "locale": locale,
        "guide": guide_id,
        "html_fingerprint": html_fingerprint,
        "footer_year": policy["ui_footer_year"],
        "print_inputs": _pdf_file_hashes(
            (
                PDF_PRINT_CSS,
                PDF_COVER_LOGO,
                PDF_UI_FOOTER_TEMPLATE,
                REPOSITORY_ROOT / f"app/i18n/{locale}.json",
                PDF_LAYOUT_CONTRACT,
                PDF_GENERATION_CONTRACT,
                Path(__file__),
            )
        ),
        "runtime": runtime_identity,
    }


def _validate_pdf_cache_payload_tree(
    payload: Path,
    files: dict[str, str],
    validate_payload: Callable[[Path], None],
) -> None:
    if not payload.is_dir() or payload.is_symlink():
        raise BuildError(f"PDF cache payload is missing or unsafe: {payload}")
    unsafe = [path for path in payload.rglob("*") if path.is_symlink()]
    if unsafe:
        raise BuildError(f"PDF cache payload contains a symbolic link: {unsafe[0]}")
    if tree_hashes(payload) != files:
        raise BuildError("PDF cache payload SHA-256 values do not match its manifest")
    validate_payload(payload)


def _validate_pdf_cache_entry(
    entry: Path,
    *,
    kind: str,
    fingerprint: str,
    inputs: dict[str, Any],
    validate_payload: Callable[[Path], None],
) -> None:
    if not entry.is_dir() or entry.is_symlink():
        raise BuildError(f"PDF cache entry is missing or unsafe: {entry}")
    manifest = _read_json_file(entry / PDF_CACHE_MANIFEST)
    if (
        manifest.get("schema_version") != PDF_CACHE_SCHEMA_VERSION
        or manifest.get("kind") != kind
        or manifest.get("fingerprint") != fingerprint
        or manifest.get("inputs") != inputs
        or not isinstance(manifest.get("files"), dict)
    ):
        raise BuildError("PDF cache entry manifest does not match its declared inputs")
    expected_files = {PDF_CACHE_MANIFEST, *(f"payload/{path}" for path in manifest["files"])}
    actual_files = {
        path.relative_to(entry).as_posix()
        for path in entry.rglob("*")
        if path.is_file() and not path.is_symlink()
    }
    if actual_files != expected_files:
        raise BuildError("PDF cache entry contains an unexpected file set")
    _validate_pdf_cache_payload_tree(
        entry / "payload",
        manifest["files"],
        validate_payload,
    )


def _quarantine_pdf_cache_entry(cache_root: Path, entry: Path, reason: BaseException) -> None:
    if not entry.exists():
        return
    quarantine = cache_root / ".quarantine"
    quarantine.mkdir(parents=True, exist_ok=True)
    destination = quarantine / f"{entry.parent.name}-{entry.name}-{time.time_ns()}"
    entry.replace(destination)
    summary = str(reason).splitlines()[0][:300]
    print(
        f"PDF cache: state=quarantined; entry={entry.parent.name}/{entry.name}; reason={summary}",
        flush=True,
    )


def _reuse_pdf_cache_entry(
    cache_root: Path,
    *,
    kind: str,
    fingerprint: str,
    inputs: dict[str, Any],
    destination: Path,
    validate_payload: Callable[[Path], None],
) -> bool:
    entry = cache_root / kind / fingerprint
    if not entry.exists():
        print(f"PDF cache: state=miss; kind={kind}; key={fingerprint[:12]}", flush=True)
        return False
    try:
        _validate_pdf_cache_entry(
            entry,
            kind=kind,
            fingerprint=fingerprint,
            inputs=inputs,
            validate_payload=validate_payload,
        )
        shutil.copytree(entry / "payload", destination)
        _validate_pdf_cache_payload_tree(
            destination,
            tree_hashes(entry / "payload"),
            validate_payload,
        )
    except (BuildError, OSError, ValueError) as exc:
        remove_path(destination)
        _quarantine_pdf_cache_entry(cache_root, entry, exc)
        print(
            f"PDF cache: state=miss; kind={kind}; key={fingerprint[:12]}; reason=invalid",
            flush=True,
        )
        return False
    print(f"PDF cache: state=reused; kind={kind}; key={fingerprint[:12]}", flush=True)
    return True


def _store_pdf_cache_entry(
    cache_root: Path,
    *,
    kind: str,
    fingerprint: str,
    inputs: dict[str, Any],
    payload: Path,
    validate_payload: Callable[[Path], None],
) -> None:
    files = tree_hashes(payload)
    _validate_pdf_cache_payload_tree(payload, files, validate_payload)
    entry = cache_root / kind / fingerprint
    if entry.exists():
        try:
            _validate_pdf_cache_entry(
                entry,
                kind=kind,
                fingerprint=fingerprint,
                inputs=inputs,
                validate_payload=validate_payload,
            )
        except (BuildError, OSError, ValueError) as exc:
            _quarantine_pdf_cache_entry(cache_root, entry, exc)
        else:
            print(
                f"PDF cache: state=verified-existing; kind={kind}; key={fingerprint[:12]}",
                flush=True,
            )
            return
    cache_root.mkdir(parents=True, exist_ok=True)
    with StagedDirectory(cache_root, f"pdf-cache-{kind}") as staging:
        candidate = staging.candidate("entry")
        shutil.copytree(payload, candidate / "payload")
        _write_json(
            candidate / PDF_CACHE_MANIFEST,
            {
                "schema_version": PDF_CACHE_SCHEMA_VERSION,
                "kind": kind,
                "fingerprint": fingerprint,
                "inputs": inputs,
                "files": files,
            },
        )
        atomic_promote(
            candidate,
            entry,
            validate=lambda path: _validate_pdf_cache_entry(
                path,
                kind=kind,
                fingerprint=fingerprint,
                inputs=inputs,
                validate_payload=validate_payload,
            ),
        )
    print(f"PDF cache: state=stored; kind={kind}; key={fingerprint[:12]}", flush=True)


def _pdf_guide_filename(layout: dict[str, Any], guide_id: str, locale: str) -> str:
    guides = {guide["id"]: guide for guide in layout["guides"]}
    try:
        filename = guides[guide_id]["filename"].format(
            locale=locale, bpm_version=_product_version()
        )
    except (KeyError, AttributeError) as exc:
        raise BuildError(f"cannot format PDF filename for {guide_id}/{locale}") from exc
    if Path(filename).name != filename or not filename.endswith(".pdf"):
        raise BuildError(f"unsafe PDF filename for {guide_id}/{locale}: {filename!r}")
    return filename


def _expected_pdf_paths(layout: dict[str, Any]) -> set[str]:
    return {
        (Path(locale) / _pdf_guide_filename(layout, guide_id, locale)).as_posix()
        for locale in LOCALES
        for guide_id, _map_name in PDF_GUIDE_MAPS
    }


def _normalize_pdf_metadata(path: Path) -> None:
    """Remove renderer wall-clock metadata and canonically rewrite the PDF."""

    payload = path.read_bytes()

    def normalize_creation_date(match: re.Match[bytes]) -> bytes:
        fixed_date = (
            PDF_FIXED_UTC_CREATION_DATE
            if match.group(2).endswith(b"Z")
            else PDF_FIXED_CREATION_DATE
        )
        if len(match.group(2)) != len(fixed_date):
            raise BuildError(f"unsupported PDF creation-date format in {path}")
        return match.group(1) + fixed_date + match.group(3)

    payload, creation_dates = PDF_CREATION_DATE_PATTERN.subn(normalize_creation_date, payload)
    payload, modification_dates = PDF_MODIFICATION_DATE_PATTERN.subn(
        normalize_creation_date, payload
    )
    payload, document_ids = PDF_DOCUMENT_ID_PATTERN.subn(
        b"/ID [<" + PDF_FIXED_DOCUMENT_ID + b"> <" + PDF_FIXED_DOCUMENT_ID + b">]",
        payload,
    )
    if creation_dates != 1 or modification_dates not in {0, 1} or document_ids not in {0, 1}:
        raise BuildError(
            f"cannot deterministically normalize PDF metadata for {path}: "
            f"creation_dates={creation_dates}, modification_dates={modification_dates}, "
            f"document_ids={document_ids}"
        )
    path.write_bytes(payload)
    _canonicalize_pdf(path)


def _canonicalize_pdf(path: Path) -> None:
    qpdf = shutil.which("qpdf")
    if qpdf is None:
        raise BuildError("qpdf is required for deterministic PDF generation; install qpdf")
    qdf_path = path.with_name(f".{path.stem}.qdf.pdf")
    canonical_path = path.with_name(f".{path.stem}.canonical.pdf")
    try:
        _run_pdf_tool(
            [qpdf, "--qdf", "--object-streams=disable", str(path), str(qdf_path)],
            "expand PDF metadata",
        )
        qdf_payload = qdf_path.read_bytes()

        def normalize_xmp_timestamp(match: re.Match[bytes]) -> bytes:
            fixed_timestamp = (
                PDF_FIXED_UTC_XMP_TIMESTAMP
                if match.group(2).endswith(b"Z")
                else PDF_FIXED_XMP_TIMESTAMP
            )
            if len(match.group(2)) != len(fixed_timestamp):
                raise BuildError(f"unsupported PDF XMP timestamp format in {path}")
            return match.group(1) + fixed_timestamp + match.group(3)

        qdf_payload, xmp_timestamps = PDF_XMP_TIMESTAMP_PATTERN.subn(
            normalize_xmp_timestamp, qdf_payload
        )
        if xmp_timestamps not in {0, 3}:
            raise BuildError(
                f"cannot deterministically normalize PDF XMP metadata for {path}: "
                f"timestamps={xmp_timestamps}"
            )
        qdf_path.write_bytes(qdf_payload)
        _run_pdf_tool(
            [
                qpdf,
                "--static-id",
                "--object-streams=generate",
                "--recompress-flate",
                "--compression-level=9",
                str(qdf_path),
                str(canonical_path),
            ],
            "canonicalize PDF",
        )
        canonical_path.replace(path)
        # qpdf writes a new trailer ID while canonicalizing.  Replacing it after
        # that rewrite keeps the byte-level reproducibility promise without
        # changing any cross-reference offsets: the replacement is the same
        # fixed-width value.
        canonical_payload = path.read_bytes()
        canonical_payload, canonical_document_ids = PDF_DOCUMENT_ID_PATTERN.subn(
            b"/ID [<" + PDF_FIXED_DOCUMENT_ID + b"> <" + PDF_FIXED_DOCUMENT_ID + b">]",
            canonical_payload,
        )
        if canonical_document_ids != 1:
            raise BuildError(
                f"cannot deterministically normalize canonical PDF ID for {path}: "
                f"document_ids={canonical_document_ids}"
            )
        path.write_bytes(canonical_payload)
    finally:
        qdf_path.unlink(missing_ok=True)
        canonical_path.unlink(missing_ok=True)


def _run_pdf_tool(command: list[str], operation: str) -> None:
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    if completed.returncode:
        output = (completed.stdout + "\n" + completed.stderr).strip()
        raise BuildError(f"cannot {operation} ({' '.join(command)}):\n{output[-12000:]}")


def _qpdf_json(path: Path) -> dict[str, Any]:
    """Return qpdf's structural JSON for one generated PDF."""

    qpdf = shutil.which("qpdf")
    if qpdf is None:
        raise BuildError("qpdf is required for PDF navigation verification; install qpdf")
    completed = subprocess.run(
        [qpdf, "--json", str(path)], text=True, capture_output=True, check=False
    )
    if completed.returncode:
        output = (completed.stdout + "\n" + completed.stderr).strip()
        raise BuildError(f"cannot inspect PDF navigation for {path}:\n{output[-12000:]}")
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise BuildError(f"qpdf returned invalid navigation JSON for {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise BuildError(f"qpdf returned an invalid navigation model for {path}")
    return payload


def _pdf_navigation_model(path: Path) -> tuple[int, dict[str, int], set[str]]:
    """Return page count, named-destination pages, and linked destinations."""

    payload = _qpdf_json(path)
    pages = payload.get("pages")
    object_groups = payload.get("qpdf")
    if not isinstance(pages, list) or not isinstance(object_groups, list) or len(object_groups) < 2:
        raise BuildError(f"qpdf navigation model is incomplete for {path}")
    page_numbers: dict[str, int] = {}
    for page in pages:
        if not isinstance(page, dict):
            raise BuildError(f"qpdf page model is invalid for {path}")
        page_object = page.get("object")
        page_number = page.get("pageposfrom1")
        if not isinstance(page_object, str) or not isinstance(page_number, int):
            raise BuildError(f"qpdf page position is invalid for {path}")
        page_numbers[page_object] = page_number

    objects = object_groups[1]
    if not isinstance(objects, dict):
        raise BuildError(f"qpdf object model is invalid for {path}")
    catalog: dict[str, Any] | None = None
    for entry in objects.values():
        if not isinstance(entry, dict):
            continue
        value = entry.get("value")
        if isinstance(value, dict) and value.get("/Type") == "/Catalog":
            catalog = value
            break
    if catalog is None or not isinstance(catalog.get("/Dests"), str):
        raise BuildError(f"PDF has no named-destination catalog: {path}")
    destinations_entry = objects.get(f"obj:{catalog['/Dests']}")
    if not isinstance(destinations_entry, dict) or not isinstance(
        destinations_entry.get("value"), dict
    ):
        raise BuildError(f"PDF named-destination catalog is invalid: {path}")
    destinations: dict[str, int] = {}
    for encoded_name, target in destinations_entry["value"].items():
        if (
            not isinstance(encoded_name, str)
            or not encoded_name.startswith("/")
            or not isinstance(target, list)
            or not target
            or not isinstance(target[0], str)
            or target[0] not in page_numbers
        ):
            raise BuildError(f"PDF named destination is invalid in {path}: {encoded_name!r}")
        destinations[encoded_name[1:]] = page_numbers[target[0]]

    linked_destinations: set[str] = set()
    for entry in objects.values():
        if not isinstance(entry, dict):
            continue
        value = entry.get("value")
        if not isinstance(value, dict) or value.get("/Subtype") != "/Link":
            continue
        destination = value.get("/Dest")
        if isinstance(destination, str) and destination.startswith("/"):
            linked_destinations.add(destination[1:])
    return len(pages), destinations, linked_destinations


def _pdf_navigation_model_without_destinations(path: Path) -> tuple[int, dict[str, int], set[str]]:
    """Return only a page count for a deliberately link-free overlay PDF."""

    payload = _qpdf_json(path)
    pages = payload.get("pages")
    if not isinstance(pages, list) or not pages:
        raise BuildError(f"qpdf page model is incomplete for {path}")
    return len(pages), {}, set()


def _pdf_footer_text(locale: str, *, current_year: int | None = None) -> str:
    """Assemble exactly the visible copyright string rendered by the BPM UI footer."""

    template = PDF_UI_FOOTER_TEMPLATE.read_text(encoding="utf-8")
    ordered_tokens = (
        "©",
        "footer_year_range",
        'tr("profiles.footer_owner")',
        'tr("profiles.footer_license_prefix")',
        'tr("profiles.footer_license_label")',
    )
    positions = [template.find(token) for token in ordered_tokens]
    if any(position < 0 for position in positions) or positions != sorted(positions):
        raise BuildError("BPM UI footer template no longer matches the PDF footer contract")
    catalog_path = REPOSITORY_ROOT / f"app/i18n/{locale}.json"
    catalog = _read_json_file(catalog_path)
    try:
        owner = catalog["profiles.footer_owner"]
        license_prefix = catalog["profiles.footer_license_prefix"]
        license_label = catalog["profiles.footer_license_label"]
    except KeyError as exc:
        raise BuildError(f"BPM UI footer catalog is incomplete for {locale}: {exc}") from exc
    if not all(
        isinstance(value, str) and value for value in (owner, license_prefix, license_label)
    ):
        raise BuildError(f"BPM UI footer catalog values are invalid for {locale}")
    year = time.gmtime().tm_year if current_year is None else current_year
    year_range = "2025" if year <= 2025 else f"2025-{year}"
    return f"© {year_range} • {owner} • {license_prefix} {license_label}"


def _pdf_keydefs(keys_path: Path) -> dict[str, str]:
    """Return local DITA map keys needed to assemble a print-only guide HTML file."""

    try:
        root = ET.parse(keys_path).getroot()
    except ET.ParseError as exc:
        raise BuildError(f"cannot parse PDF keys map {keys_path}: {exc}") from exc
    keydefs: dict[str, str] = {}
    for keydef in root.findall(".//keydef"):
        href = keydef.get("href")
        for key in keydef.get("keys", "").split():
            if href:
                keydefs[key] = href
    return keydefs


def _pdf_html_path_for_topic(map_path: Path, href: str) -> Path:
    """Resolve a local DITA topic href to its DITA-OT HTML5 output path."""

    topic_href = urllib.parse.unquote(href.split("#", 1)[0])
    if not topic_href:
        raise BuildError(f"PDF topic reference has no local target: {map_path}")
    locale_root = map_path.parents[1]
    target = (map_path.parent / topic_href).resolve()
    try:
        return target.relative_to(locale_root).with_suffix(".html")
    except ValueError as exc:
        raise BuildError(f"PDF topic target leaves locale source root: {href!r}") from exc


def _pdf_print_navigation(map_path: Path) -> tuple[str, list[tuple[str, list[Path]]]]:
    """Read the reviewed map order so the PDF has the same logical hierarchy as the web guide."""

    try:
        root = ET.parse(map_path).getroot()
    except ET.ParseError as exc:
        raise BuildError(f"cannot parse PDF source map {map_path}: {exc}") from exc
    title = " ".join(root.findtext("title", default="").split())
    if not title:
        raise BuildError(f"PDF source map has no title: {map_path}")
    keydefs = _pdf_keydefs(map_path.parent / "keys.ditamap")

    def topic_path(topicref: ET.Element) -> Path:
        href = topicref.get("href") or keydefs.get(topicref.get("keyref", ""))
        if href is None:
            raise BuildError(
                f"PDF topic reference cannot resolve keyref {topicref.get('keyref')!r} in {map_path}"
            )
        return _pdf_html_path_for_topic(map_path, href)

    sections: list[tuple[str, list[Path]]] = []
    direct_topics: list[Path] = []
    for child in root:
        if child.tag == "topichead":
            heading = " ".join(child.findtext("./topicmeta/navtitle", default="").split())
            if not heading:
                raise BuildError(f"PDF topic section has no navigation title: {map_path}")
            topics = [topic_path(topicref) for topicref in child.findall("./topicref")]
            if not topics:
                raise BuildError(f"PDF topic section has no topics: {heading!r} in {map_path}")
            sections.append((heading, topics))
        elif child.tag == "topicref":
            direct_topics.append(topic_path(child))
    if direct_topics:
        sections.insert(0, ("", direct_topics))
    if not sections:
        raise BuildError(f"PDF source map has no printable topics: {map_path}")
    return title, sections


def _pdf_article_from_html(path: Path) -> str:
    """Keep DITA-OT semantic HTML while dropping portal-only related-topic navigation."""

    try:
        rendered = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise BuildError(f"cannot read generated PDF topic HTML {path}: {exc}") from exc
    match = re.search(r"(<article\b.*?</article>)", rendered, flags=re.DOTALL)
    if match is None:
        raise BuildError(f"generated PDF topic has no article element: {path}")
    article = re.sub(
        r"<nav\b(?=[^>]*\brelated-links\b)[^>]*>.*?</nav>",
        "",
        match.group(1),
        flags=re.DOTALL,
    )
    # DITA-OT can resolve an intra-guide xref to the temporary output directory
    # when Chromium prints this combined HTML file. It has no stable PDF target;
    # omit local topic links while preserving external reader links.
    return re.sub(
        r"\s+href=(['\"])(?:file:.*?)?[^/'\"]+\.html(?:#[^'\"]*)?\1",
        "",
        article,
        flags=re.IGNORECASE,
    )


def _pdf_article_with_destination(article: str, destination_id: str) -> str:
    """Replace only an article's temporary DITA id, preserving all semantic attributes."""

    def replace(match: re.Match[str]) -> str:
        attributes = re.sub(r"\s+id=(['\"]).*?\1", "", match.group(1))
        return f'<article id="{destination_id}"{attributes}>'

    rendered, substitutions = re.subn(
        r"<article\b([^>]*)>", replace, article, count=1, flags=re.DOTALL
    )
    if substitutions != 1:
        raise BuildError("generated PDF topic article cannot receive a destination")
    return rendered


def _number_pdf_figure_captions(article: str, *, locale: str, first_number: int) -> tuple[str, int]:
    """Continue DITA topic-local figure labels through the assembled PDF guide."""

    if locale not in PDF_FIGURE_CAPTION_PREFIXES:
        raise BuildError(f"PDF figure-caption locale is unsupported: {locale}")
    next_number = first_number
    label_pattern = re.compile(
        r'(?P<open><span class="fig--title-label">)' r"(?P<label>[^<]+?)" r"(?P<close></span>)"
    )

    def replace(match: re.Match[str]) -> str:
        nonlocal next_number
        expected_prefix = PDF_FIGURE_CAPTION_PREFIXES[locale]
        label = html.unescape(match.group("label"))
        expected_label = re.fullmatch(rf"{re.escape(expected_prefix)}\s+\d+\.\s*", label)
        if expected_label is None:
            raise BuildError(
                f"generated PDF figure caption has an unexpected label for {locale}: {label!r}"
            )
        numbered = f"{expected_prefix} {next_number}. "
        next_number += 1
        return match.group("open") + html.escape(numbered) + match.group("close")

    return label_pattern.sub(replace, article), next_number


def _generated_pdf_topic_html(output_root: Path, topic_html: Path) -> Path | None:
    """Find one map topic in DITA-OT output, accepting its locale prefix.

    DITA-OT normally preserves the locale-relative path, but it can prepend the
    locale directory for a key-resolved map topic.  The basename and trailing
    locale-relative path remain stable, which is sufficient to select the
    generated article without deriving an invalid web-link path.
    """

    expected = output_root / topic_html
    if expected.is_file():
        return expected
    trailing_parts = topic_html.parts
    matches = [
        candidate
        for candidate in output_root.rglob(topic_html.name)
        if candidate.is_file() and candidate.parts[-len(trailing_parts) :] == trailing_parts
    ]
    if len(matches) == 1:
        return matches[0]
    return None


def _wait_for_pdf_topic_html(
    *,
    locale: str,
    guide_id: str,
    map_path: Path,
    output_root: Path,
    timeout_seconds: float = 120.0,
) -> None:
    """Wait until DITA-OT has materialized every map topic HTML file.

    Some DITA-OT runs return control slightly before every topic file is visible
    on disk.  The PDF printer must consume one complete map transformation, not
    launch independent topic transformations that could diverge from map output.
    """

    _title, sections = _pdf_print_navigation(map_path)
    expected = [topic_html for _section_title, topics in sections for topic_html in topics]
    deadline = time.monotonic() + timeout_seconds
    reported_pending = False
    while True:
        pending = [
            topic_html
            for topic_html in expected
            if _generated_pdf_topic_html(output_root, topic_html) is None
        ]
        if not pending:
            return
        if not reported_pending:
            print(
                f"PDF source wait: {locale}/{guide_id} ({len(pending)} topic HTML pending)",
                flush=True,
            )
            reported_pending = True
        if time.monotonic() >= deadline:
            samples = ", ".join(topic_html.as_posix() for topic_html in pending[:5])
            raise BuildError(
                f"DITA HTML5 output did not become ready for {locale}/{guide_id}: {samples}"
            )
        time.sleep(0.25)


def _write_pdf_print_guide(
    *,
    locale: str,
    guide_id: str,
    map_path: Path,
    output_root: Path,
    total_pages: int | None = None,
    destination_pages: dict[str, int] | None = None,
    footer_year: int | None = None,
) -> Path:
    """Compose one A4-ready guide from DITA HTML5 topic output in reviewed map order."""

    title, sections = _pdf_print_navigation(map_path)
    guide_directory = output_root / ("user" if guide_id == "user-guide" else "admin")
    guide_directory.mkdir(parents=True, exist_ok=True)
    print_path = guide_directory / f".{guide_id}-print.html"
    toc: list[str] = []
    content: list[str] = []
    topic_number = 0
    figure_number = 1
    for section_number, (section_title, topics) in enumerate(sections, start=1):
        if section_title:
            section_id = f"bpm-section-{section_number:03d}"
            rendered_section_id = _pdf_rendered_destination_id(section_id, destination_pages)
            toc.append(
                '<h2 class="bpm-pdf-toc__entry bpm-pdf-toc__section">'
                f'<a href="#{rendered_section_id}"><span class="bpm-pdf-toc__label">'
                f"{html.escape(section_title)}</span>"
                f'<span class="bpm-pdf-toc__page">{_pdf_toc_page(section_id, destination_pages)}</span>'
                "</a></h2>"
            )
            content.append(
                '<section class="bpm-pdf-section">'
                f'<h2 id="{rendered_section_id}">{html.escape(section_title)}</h2>'
            )
        toc.append("<ul>")
        for topic in topics:
            topic_number += 1
            topic_id = f"bpm-topic-{topic_number:04d}"
            rendered_topic_id = _pdf_rendered_destination_id(topic_id, destination_pages)
            topic_path = _generated_pdf_topic_html(output_root, topic)
            if topic_path is None:
                raise BuildError(f"generated PDF topic is missing: {output_root / topic}")
            article = _pdf_article_from_html(topic_path)
            article, figure_number = _number_pdf_figure_captions(
                article, locale=locale, first_number=figure_number
            )
            topic_title_match = re.search(r"<h1\b[^>]*>(.*?)</h1>", article, flags=re.DOTALL)
            if topic_title_match is None:
                raise BuildError(f"generated PDF topic has no title: {topic_path}")
            topic_title = re.sub(r"<[^>]+>", "", topic_title_match.group(1)).strip()
            toc.append(
                '<li class="bpm-pdf-toc__entry"><a '
                f'href="#{rendered_topic_id}"><span class="bpm-pdf-toc__label">'
                f"{html.escape(topic_title)}</span>"
                f'<span class="bpm-pdf-toc__page">{_pdf_toc_page(topic_id, destination_pages)}</span>'
                "</a></li>"
            )
            article = _pdf_article_with_destination(article, rendered_topic_id)
            content.append(article)
        toc.append("</ul>")
        if section_title:
            content.append("</section>")
    if guide_id == "user-guide" and figure_number != PDF_USER_GUIDE_FIGURE_COUNT + 1:
        raise BuildError(
            f"PDF User Guide figure count is invalid for {locale}: {figure_number - 1}"
        )
    version = _product_version()
    page_count = "—" if total_pages is None else str(total_pages)
    print_path.write_text(
        "<!doctype html>\n"
        f'<html lang="{html.escape(locale)}"><head><meta charset="utf-8">'
        f"<title>{html.escape(title)}</title>"
        '<link rel="stylesheet" href="../bpm-guide-print.css"></head><body>'
        '<section class="bpm-pdf-cover">'
        '<div class="bpm-pdf-cover__main">'
        '<img class="bpm-pdf-cover__logo" src="../assets/branding/bpm-logo.png" alt="">'
        f"<h1>{html.escape(title)}</h1>"
        f'<p class="bpm-pdf-cover__product">Browser Policy Manager {html.escape(version)}</p>'
        f'<p class="bpm-pdf-cover__pages">{html.escape(_pdf_page_count_label(locale, page_count))}</p>'
        "</div>"
        f'<p class="bpm-pdf-cover__copyright">{html.escape(_pdf_footer_text(locale, current_year=footer_year))}</p>'
        "</section>"
        f'<nav class="bpm-pdf-toc"><h1>{html.escape(_pdf_contents_title(locale))}</h1>'
        + "".join(toc)
        + "</nav>"
        + "".join(content)
        + "</body></html>\n",
        encoding="utf-8",
    )
    return print_path


def _pdf_rendered_destination_id(
    destination_id: str, destination_pages: dict[str, int] | None
) -> str:
    if destination_pages is None:
        return destination_id
    page = destination_pages.get(destination_id)
    if not isinstance(page, int) or page < 1:
        raise BuildError(f"PDF draft has no valid page for destination {destination_id!r}")
    return f"{destination_id}-p{page:04d}"


def _pdf_toc_page(destination_id: str, destination_pages: dict[str, int] | None) -> str:
    if destination_pages is None:
        return "—"
    return str(destination_pages[destination_id])


def _expected_pdf_destination_ids(map_path: Path) -> set[str]:
    _title, sections = _pdf_print_navigation(map_path)
    destination_ids: set[str] = set()
    topic_number = 0
    for section_number, (section_title, topics) in enumerate(sections, start=1):
        if section_title:
            destination_ids.add(f"bpm-section-{section_number:03d}")
        for _topic in topics:
            topic_number += 1
            destination_ids.add(f"bpm-topic-{topic_number:04d}")
    return destination_ids


def _pdf_page_count_label(locale: str, page_count: str) -> str:
    return {
        "en": f"Pages: {page_count}",
        "ru": f"Количество страниц: {page_count}",
        "de": f"Seiten: {page_count}",
        "zh-CN": f"页数：{page_count}",
        "fr": f"Nombre de pages : {page_count}",
        "es-ES": f"Número de páginas: {page_count}",
    }[locale]


def _pdf_contents_title(locale: str) -> str:
    return {
        "en": "Contents",
        "ru": "Содержание",
        "de": "Inhalt",
        "zh-CN": "目录",
        "fr": "Sommaire",
        "es-ES": "Contenido",
    }[locale]


def _chromium_pdf_renderer() -> str:
    for executable in ("chromium", "chromium-browser", "google-chrome"):
        resolved = shutil.which(executable)
        if resolved:
            return resolved
    raise BuildError(
        "Chromium is required for Unicode-safe PDF generation; install the chromium executable"
    )


def _render_pdf_with_chromium(source: Path, target: Path, env: dict[str, str]) -> None:
    renderer = _chromium_pdf_renderer()
    completed = subprocess.run(
        [
            renderer,
            "--headless",
            "--no-sandbox",
            "--disable-gpu",
            "--disable-background-networking",
            "--disable-component-update",
            "--disable-sync",
            "--no-first-run",
            "--no-pdf-header-footer",
            f"--print-to-pdf={target}",
            source.resolve().as_uri(),
        ],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        output = (completed.stdout + "\n" + completed.stderr).strip()
        raise BuildError(f"Chromium PDF rendering failed for {source}:\n{output[-12000:]}")
    _validate_pdf_file(target)


def _write_pdf_page_number_overlay(output_root: Path, total_pages: int) -> Path:
    """Write one deterministic A4 PDF overlay per page, leaving the title blank.

    Chromium remains responsible for the two HTML/CSS passes that establish
    pagination and linked contents. This overlay contains ASCII digits only,
    so a small native PDF avoids a third browser launch for every guide.
    """

    if total_pages < 2:
        raise BuildError("a BPM PDF guide must have a title page and at least one content page")
    overlay_path = output_root / ".bpm-page-number-overlay.pdf"
    page_object_numbers = [4 + 2 * index for index in range(total_pages)]
    content_object_numbers = [number + 1 for number in page_object_numbers]
    objects: dict[int, bytes] = {
        1: b"<< /Type /Catalog /Pages 2 0 R >>",
        2: (
            b"<< /Type /Pages /Kids ["
            + b" ".join(f"{number} 0 R".encode("ascii") for number in page_object_numbers)
            + f"] /Count {total_pages} >>".encode("ascii")
        ),
        3: b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    }
    for page_number, (page_object, content_object) in enumerate(
        zip(page_object_numbers, content_object_numbers, strict=True),
        start=1,
    ):
        objects[page_object] = (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 "
            + f"{PDF_A4_WIDTH_POINTS:.3f} {PDF_A4_HEIGHT_POINTS:.3f}".encode("ascii")
            + b"] /Resources << /Font << /F1 3 0 R >> >> /Contents "
            + f"{content_object} 0 R >>".encode("ascii")
        )
        if page_number == 1:
            content = b""
        else:
            text = str(page_number)
            text_width = len(text) * PDF_HELVETICA_DIGIT_WIDTH / 1000 * PDF_PAGE_NUMBER_FONT_SIZE
            x_position = (PDF_A4_WIDTH_POINTS - text_width) / 2
            content = (
                b"q\n0.2 0.254902 0.333333 rg\nBT\n/F1 "
                + str(PDF_PAGE_NUMBER_FONT_SIZE).encode("ascii")
                + b" Tf\n1 0 0 1 "
                + f"{x_position:.3f} {PDF_PAGE_NUMBER_BASELINE:.3f}".encode("ascii")
                + b" Tm\n("
                + text.encode("ascii")
                + b") Tj\nET\nQ\n"
            )
        objects[content_object] = (
            f"<< /Length {len(content)} >>\nstream\n".encode("ascii") + content + b"endstream"
        )

    payload = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for object_number in range(1, max(objects) + 1):
        offsets.append(len(payload))
        payload.extend(f"{object_number} 0 obj\n".encode("ascii"))
        payload.extend(objects[object_number])
        payload.extend(b"\nendobj\n")
    xref_offset = len(payload)
    payload.extend(f"xref\n0 {len(offsets)}\n".encode("ascii"))
    payload.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        payload.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    payload.extend(
        f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode(
            "ascii"
        )
    )
    overlay_path.write_bytes(payload)
    if not payload.startswith(b"%PDF-") or not payload.endswith(b"%%EOF\n"):
        raise BuildError("generated PDF page-number overlay is incomplete")
    return overlay_path


def _overlay_pdf_page_numbers(target: Path, overlay: Path) -> None:
    qpdf = shutil.which("qpdf")
    if qpdf is None:
        raise BuildError("qpdf is required for PDF page-number overlays; install qpdf")
    overlaid = target.with_name(f".{target.stem}.numbered.pdf")
    try:
        _run_pdf_tool(
            [qpdf, str(target), "--overlay", str(overlay), "--", str(overlaid)],
            "overlay PDF page numbers",
        )
        overlaid.replace(target)
    finally:
        overlaid.unlink(missing_ok=True)
    _validate_pdf_file(target)


def _pdf_bbox_pages(path: Path) -> list[ET.Element]:
    pdftotext = shutil.which("pdftotext")
    if pdftotext is None:
        raise BuildError(
            "pdftotext is required for printed PDF verification; install poppler-utils"
        )
    completed = subprocess.run(
        [pdftotext, "-bbox-layout", str(path), "-"],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        output = (completed.stdout + "\n" + completed.stderr).strip()
        raise BuildError(f"cannot extract positioned PDF text from {path}:\n{output[-12000:]}")
    try:
        root = ET.fromstring(completed.stdout)
    except ET.ParseError as exc:
        raise BuildError(f"pdftotext returned invalid positioned text for {path}: {exc}") from exc
    pages = [element for element in root.iter() if element.tag.rsplit("}", 1)[-1] == "page"]
    if not pages:
        raise BuildError(f"pdftotext found no pages in {path}")
    return pages


def _pdf_page_words(page: ET.Element) -> list[ET.Element]:
    return [element for element in page.iter() if element.tag.rsplit("}", 1)[-1] == "word"]


def _pdf_positioned_line_text(line: ET.Element) -> str:
    """Recreate visible line spacing without inserting spaces inside CJK labels."""

    words = _pdf_page_words(line)
    if not words:
        return ""
    parts = [words[0].text or ""]
    previous_x_max = float(words[0].get("xMax", "0"))
    for word in words[1:]:
        current_x_min = float(word.get("xMin", "0"))
        if current_x_min - previous_x_max > 0.5:
            parts.append(" ")
        parts.append(word.text or "")
        previous_x_max = float(word.get("xMax", "0"))
    return "".join(parts)


def _pdf_figure_caption_numbers(pages: list[ET.Element], locale: str) -> list[int]:
    """Read User Guide figure labels from positioned PDF text in printed order."""

    try:
        prefix = PDF_FIGURE_CAPTION_PREFIXES[locale]
    except KeyError as exc:
        raise BuildError(f"PDF figure-caption locale is unsupported: {locale}") from exc
    caption_pattern = re.compile(rf"{re.escape(prefix)}\s+(\d+)\.")
    text = "\n".join(
        _pdf_positioned_line_text(line)
        for page in pages
        for line in page.iter()
        if line.tag.rsplit("}", 1)[-1] == "line"
    )
    return [int(number) for number in caption_pattern.findall(text)]


def _validate_pdf_print_contract(
    path: Path,
    *,
    locale: str,
    guide_id: str,
    expected_destination_ids: set[str],
    footer_year: int,
) -> None:
    """Verify M11-05 title, page-number, contents-link, and destination guarantees."""

    page_count, destinations, linked_destinations = _pdf_navigation_model(path)
    destination_pattern = re.compile(r"^(bpm-(?:section|topic)-\d+)-p(\d{4})$")
    destination_bases: set[str] = set()
    for destination, actual_page in destinations.items():
        match = destination_pattern.fullmatch(destination)
        if match is None:
            raise BuildError(f"unexpected PDF destination {destination!r} in {path}")
        destination_bases.add(match.group(1))
        if int(match.group(2)) != actual_page:
            raise BuildError(
                f"PDF contents page does not match destination for {destination!r} in {path}"
            )
        if destination not in linked_destinations:
            raise BuildError(
                f"PDF contents destination is not clickable: {destination!r} in {path}"
            )
    if destination_bases != expected_destination_ids:
        missing = sorted(expected_destination_ids - destination_bases)
        unexpected = sorted(destination_bases - expected_destination_ids)
        raise BuildError(
            f"PDF contents destination set is invalid for {path}: "
            f"missing={missing}, unexpected={unexpected}"
        )

    pages = _pdf_bbox_pages(path)
    if len(pages) != page_count:
        raise BuildError(f"positioned PDF page count does not match qpdf for {path}")
    expected_figures = (
        list(range(1, PDF_USER_GUIDE_FIGURE_COUNT + 1)) if guide_id == "user-guide" else []
    )
    actual_figures = _pdf_figure_caption_numbers(pages, locale)
    if actual_figures != expected_figures:
        raise BuildError(
            f"PDF figure-caption sequence is invalid for {locale}/{guide_id}: "
            f"expected={expected_figures}, actual={actual_figures}"
        )
    title_page = pages[0]
    title_height = float(title_page.get("height", "0"))
    title_lines: list[tuple[str, float]] = []
    for element in title_page.iter():
        if element.tag.rsplit("}", 1)[-1] != "line":
            continue
        title_lines.append((_pdf_positioned_line_text(element), float(element.get("yMin", "0"))))
    footer_text = _pdf_footer_text(locale, current_year=footer_year)
    if not any(text == footer_text and y_min > title_height - 100 for text, y_min in title_lines):
        raise BuildError(f"PDF title-page copyright is missing or not bottom-aligned in {path}")
    page_count_label = _pdf_page_count_label(locale, str(page_count))
    if not any(text == page_count_label for text, _y_min in title_lines):
        raise BuildError(f"PDF title-page page count is missing or incorrect in {path}")

    for page_number, page in enumerate(pages, start=1):
        width = float(page.get("width", "0"))
        height = float(page.get("height", "0"))
        footer_words = [
            word
            for word in _pdf_page_words(page)
            if (word.text or "") == str(page_number)
            and float(word.get("yMin", "0")) > height - 40
            and abs((float(word.get("xMin", "0")) + float(word.get("xMax", "0"))) / 2 - width / 2)
            < 1.0
        ]
        if page_number == 1 and footer_words:
            raise BuildError(f"PDF title page must not have a printed page number: {path}")
        if page_number > 1 and len(footer_words) != 1:
            raise BuildError(
                f"PDF page {page_number} has no single centered footer page number: {path}"
            )


def _validate_pdf_file(path: Path) -> None:
    if not path.is_file() or path.is_symlink():
        raise BuildError(f"generated PDF is missing or unsafe: {path}")
    payload = path.read_bytes()
    if len(payload) < 1024 or not payload.startswith(b"%PDF-") or b"%%EOF" not in payload[-2048:]:
        raise BuildError(f"generated file is not a complete PDF: {path}")


def _pdf_build_manifest(
    layout: dict[str, Any], policy: dict[str, Any], root: Path
) -> dict[str, Any]:
    files = {path: _file_sha256(root / path) for path in sorted(_expected_pdf_paths(layout))}
    lock = _load_lock()
    return {
        "schema_version": 1,
        "contract_id": policy["contract_id"],
        "backlog_item": policy["backlog_item"],
        "bpm_version": _product_version(),
        "source_revision": _source_revision(),
        "source_fingerprint": _source_fingerprint(),
        "dita_ot_version": lock["components"]["dita_ot"]["version"],
        "ui_footer_year": policy["ui_footer_year"],
        "files": files,
    }


def validate_pdf_tree(root: Path) -> None:
    layout = _pdf_layout()
    policy = _pdf_generation_policy()
    if not root.is_dir() or root.is_symlink():
        raise BuildError(f"PDF candidate root is missing or unsafe: {root}")
    expected_pdf_paths = _expected_pdf_paths(layout)
    expected_files = expected_pdf_paths | {PDF_BUILD_MANIFEST}
    actual_files = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and not path.is_symlink()
    }
    unsafe_paths = [path for path in root.rglob("*") if path.is_symlink()]
    if unsafe_paths:
        raise BuildError(f"PDF candidate contains a symbolic link: {unsafe_paths[0]}")
    if actual_files != expected_files:
        missing = sorted(expected_files - actual_files)
        unexpected = sorted(actual_files - expected_files)
        raise BuildError(
            "PDF candidate file set does not match the contract: "
            f"missing={missing}, unexpected={unexpected}"
        )
    manifest = _read_json_file(root / PDF_BUILD_MANIFEST)
    if (
        manifest.get("schema_version") != 1
        or manifest.get("contract_id") != policy["contract_id"]
        or manifest.get("backlog_item") != policy["backlog_item"]
        or manifest.get("bpm_version") != _product_version()
        or manifest.get("source_fingerprint") != _source_fingerprint()
        or manifest.get("ui_footer_year") != policy["ui_footer_year"]
    ):
        raise BuildError("PDF candidate manifest does not match the current generation contract")
    for locale in LOCALES:
        for guide_id, map_name in PDF_GUIDE_MAPS:
            path = root / locale / _pdf_guide_filename(layout, guide_id, locale)
            _validate_pdf_file(path)
            _validate_pdf_print_contract(
                path,
                locale=locale,
                guide_id=guide_id,
                expected_destination_ids=_expected_pdf_destination_ids(
                    DOCUMENTATION_ROOT / f"src/dita/{locale}/maps/{map_name}"
                ),
                footer_year=policy["ui_footer_year"],
            )
    expected_hashes = {path: _file_sha256(root / path) for path in sorted(expected_pdf_paths)}
    if manifest.get("files") != expected_hashes:
        raise BuildError("PDF candidate manifest SHA-256 values do not match generated PDFs")


def build_pdf_tree(destination: Path, *, use_cache: bool = True) -> None:
    """Generate every locale-guide pair, reusing only verified development cache entries."""

    layout = _pdf_layout()
    policy = _pdf_generation_policy()
    for required_asset in (PDF_PRINT_CSS, PDF_COVER_LOGO):
        if not required_asset.is_file():
            raise BuildError(f"PDF asset is missing: {required_asset}")
    validate_sources()
    dita, java_home = toolchain()
    source_before = source_hashes()
    cache_root = _pdf_cache_root(policy)
    toolchain_identity = _pdf_toolchain_identity(dita, java_home) if use_cache else {}
    runtime_identity = _pdf_runtime_identity() if use_cache else {}
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.mkdir(parents=True, exist_ok=False)
    temp_root = destination.parent / f".{destination.name}-dita-temp"
    temp_root.mkdir(parents=True, exist_ok=False)
    env = _dita_environment(java_home)
    total = len(LOCALES) * len(PDF_GUIDE_MAPS) * 2
    progress = Progress("PDF candidate build", total)
    try:
        with tracked_operation(progress):
            progress.phase("prepare DITA workspaces")
            for locale in LOCALES:
                locale_workspace = temp_root / locale
                input_root = locale_workspace / "input"
                input_prepared = False
                for guide_id, map_name in PDF_GUIDE_MAPS:
                    maintained_source = DOCUMENTATION_ROOT / f"src/dita/{locale}/maps/{map_name}"
                    if not maintained_source.is_file():
                        raise BuildError(f"missing PDF source map: {maintained_source}")
                    expected_destinations = _expected_pdf_destination_ids(maintained_source)
                    output = locale_workspace / "output" / guide_id
                    target = destination / locale / _pdf_guide_filename(layout, guide_id, locale)
                    target.parent.mkdir(parents=True, exist_ok=True)

                    html_inputs: dict[str, Any] = {}
                    pdf_inputs: dict[str, Any] = {}
                    html_fingerprint = ""
                    pdf_fingerprint = ""
                    pdf_payload = locale_workspace / "cache-pdf" / guide_id

                    def validate_html_payload(
                        payload: Path,
                        *,
                        pair_locale: str = locale,
                        pair_guide: str = guide_id,
                        pair_map: Path = maintained_source,
                    ) -> None:
                        _wait_for_pdf_topic_html(
                            locale=pair_locale,
                            guide_id=pair_guide,
                            map_path=pair_map,
                            output_root=payload,
                        )

                    def validate_pdf_payload(
                        payload: Path,
                        *,
                        pair_locale: str = locale,
                        pair_guide: str = guide_id,
                        pair_destinations: set[str] = expected_destinations,
                    ) -> None:
                        if {
                            path.relative_to(payload).as_posix()
                            for path in payload.rglob("*")
                            if path.is_file() and not path.is_symlink()
                        } != {"guide.pdf"}:
                            raise BuildError("verified PDF cache payload has an invalid file set")
                        cached_pdf = payload / "guide.pdf"
                        _validate_pdf_file(cached_pdf)
                        _validate_pdf_print_contract(
                            cached_pdf,
                            locale=pair_locale,
                            guide_id=pair_guide,
                            expected_destination_ids=pair_destinations,
                            footer_year=policy["ui_footer_year"],
                        )

                    if use_cache:
                        html_inputs = _pdf_pair_html_inputs(
                            locale=locale,
                            guide_id=guide_id,
                            map_name=map_name,
                            policy=policy,
                            toolchain_identity=toolchain_identity,
                        )
                        html_fingerprint = _pdf_cache_fingerprint(html_inputs)
                        pdf_inputs = _pdf_pair_pdf_inputs(
                            locale=locale,
                            guide_id=guide_id,
                            html_fingerprint=html_fingerprint,
                            policy=policy,
                            runtime_identity=runtime_identity,
                        )
                        pdf_fingerprint = _pdf_cache_fingerprint(pdf_inputs)
                        progress.phase(f"{locale}/{guide_id} verified PDF cache lookup")
                        if _reuse_pdf_cache_entry(
                            cache_root,
                            kind="verified-pdf",
                            fingerprint=pdf_fingerprint,
                            inputs=pdf_inputs,
                            destination=pdf_payload,
                            validate_payload=validate_pdf_payload,
                        ):
                            shutil.copyfile(pdf_payload / "guide.pdf", target)
                            validate_pdf_payload(pdf_payload)
                            progress.complete_unit(f"{locale}/{guide_id} DITA HTML5 cache=reused")
                            progress.complete_unit(f"{locale}/{guide_id} Chromium PDF cache=reused")
                            continue

                    html_reused = False
                    if use_cache:
                        progress.phase(f"{locale}/{guide_id} DITA HTML5 cache lookup")
                        html_reused = _reuse_pdf_cache_entry(
                            cache_root,
                            kind="dita-html5",
                            fingerprint=html_fingerprint,
                            inputs=html_inputs,
                            destination=output,
                            validate_payload=validate_html_payload,
                        )
                    if html_reused:
                        progress.complete_unit(f"{locale}/{guide_id} DITA HTML5 cache=reused")
                        source = maintained_source
                    else:
                        if not input_prepared:
                            shutil.copytree(DOCUMENTATION_ROOT / "src", input_root / "src")
                            shutil.copytree(DOCUMENTATION_ROOT / "assets", input_root / "assets")
                            input_prepared = True
                        source = input_root / f"src/dita/{locale}/maps/{map_name}"
                        if not source.is_file():
                            raise BuildError(f"missing isolated PDF source map: {source}")
                        progress.phase(f"{locale}/{guide_id} DITA HTML5")
                        _run_pdf(
                            [
                                str(dita),
                                "--input",
                                str(source),
                                "--format",
                                policy["dita_format"],
                                "--output",
                                str(output),
                                "--temp",
                                str(locale_workspace / "work" / guide_id),
                            ],
                            env,
                        )
                        _wait_for_pdf_topic_html(
                            locale=locale,
                            guide_id=guide_id,
                            map_path=source,
                            output_root=output,
                        )
                        if use_cache:
                            if (
                                _pdf_pair_html_inputs(
                                    locale=locale,
                                    guide_id=guide_id,
                                    map_name=map_name,
                                    policy=policy,
                                    toolchain_identity=toolchain_identity,
                                )
                                != html_inputs
                            ):
                                raise BuildError(
                                    f"PDF HTML inputs changed during {locale}/{guide_id}"
                                )
                            _store_pdf_cache_entry(
                                cache_root,
                                kind="dita-html5",
                                fingerprint=html_fingerprint,
                                inputs=html_inputs,
                                payload=output,
                                validate_payload=validate_html_payload,
                            )
                        cache_state = "rebuilt" if use_cache else "bypassed"
                        progress.complete_unit(
                            f"{locale}/{guide_id} DITA HTML5 cache={cache_state}"
                        )

                    if input_prepared:
                        css = input_root / "assets/pdf/bpm-guide-print.css"
                        logo = input_root / "assets/branding/bpm-logo.png"
                    else:
                        css = PDF_PRINT_CSS
                        logo = PDF_COVER_LOGO
                    if not css.is_file() or not logo.is_file():
                        raise BuildError("isolated PDF print assets are missing")
                    shutil.copyfile(css, output / "bpm-guide-print.css")
                    logo_destination = output / "assets/branding/bpm-logo.png"
                    logo_destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(logo, logo_destination)
                    print_source = _write_pdf_print_guide(
                        locale=locale,
                        guide_id=guide_id,
                        map_path=maintained_source,
                        output_root=output,
                        footer_year=policy["ui_footer_year"],
                    )
                    progress.phase(f"{locale}/{guide_id} Chromium PDF")
                    draft = output / f".{guide_id}-pagination-draft.pdf"
                    _render_pdf_with_chromium(print_source, draft, env)
                    draft_page_count, draft_destinations, draft_links = _pdf_navigation_model(draft)
                    if set(draft_destinations) != expected_destinations:
                        raise BuildError(
                            f"PDF draft destination set is invalid for {locale}/{guide_id}"
                        )
                    if not expected_destinations <= draft_links:
                        raise BuildError(
                            f"PDF draft contents links are incomplete for {locale}/{guide_id}"
                        )
                    print_source = _write_pdf_print_guide(
                        locale=locale,
                        guide_id=guide_id,
                        map_path=maintained_source,
                        output_root=output,
                        total_pages=draft_page_count,
                        destination_pages=draft_destinations,
                        footer_year=policy["ui_footer_year"],
                    )
                    _render_pdf_with_chromium(print_source, target, env)
                    final_page_count, _final_destinations, _final_links = _pdf_navigation_model(
                        target
                    )
                    if final_page_count != draft_page_count:
                        raise BuildError(
                            f"PDF pagination changed between passes for {locale}/{guide_id}: "
                            f"draft={draft_page_count}, final={final_page_count}"
                        )
                    overlay_pdf = _write_pdf_page_number_overlay(output, final_page_count)
                    overlay_page_count, _overlay_destinations, _overlay_links = (
                        _pdf_navigation_model_without_destinations(overlay_pdf)
                    )
                    if overlay_page_count != final_page_count:
                        raise BuildError(
                            f"PDF page-number overlay count is invalid for {locale}/{guide_id}"
                        )
                    _overlay_pdf_page_numbers(target, overlay_pdf)
                    _normalize_pdf_metadata(target)
                    _validate_pdf_file(target)
                    _validate_pdf_print_contract(
                        target,
                        locale=locale,
                        guide_id=guide_id,
                        expected_destination_ids=expected_destinations,
                        footer_year=policy["ui_footer_year"],
                    )
                    if use_cache:
                        if (
                            _pdf_pair_pdf_inputs(
                                locale=locale,
                                guide_id=guide_id,
                                html_fingerprint=html_fingerprint,
                                policy=policy,
                                runtime_identity=runtime_identity,
                            )
                            != pdf_inputs
                        ):
                            raise BuildError(
                                f"PDF render inputs changed during {locale}/{guide_id}"
                            )
                        cache_candidate = locale_workspace / "cache-store-pdf" / guide_id
                        cache_candidate.mkdir(parents=True, exist_ok=False)
                        shutil.copyfile(target, cache_candidate / "guide.pdf")
                        _store_pdf_cache_entry(
                            cache_root,
                            kind="verified-pdf",
                            fingerprint=pdf_fingerprint,
                            inputs=pdf_inputs,
                            payload=cache_candidate,
                            validate_payload=validate_pdf_payload,
                        )
                    cache_state = "rebuilt" if use_cache else "bypassed"
                    progress.complete_unit(f"{locale}/{guide_id} Chromium PDF cache={cache_state}")
            progress.phase("write and verify manifest")
            _write_json(
                destination / PDF_BUILD_MANIFEST, _pdf_build_manifest(layout, policy, destination)
            )
            validate_pdf_tree(destination)
            if source_hashes() != source_before:
                raise BuildError(
                    "DITA PDF transform mutated maintained documentation source or assets"
                )
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


def publish_pdfs() -> None:
    BUILD_ROOT.mkdir(parents=True, exist_ok=True)
    with StagedDirectory(BUILD_ROOT, "pdf-build") as staging:
        candidate = staging.candidate("pdf")
        progress = Progress("PDF candidate publication", 2)
        with tracked_operation(progress):
            progress.phase("build verified PDF candidate")
            build_pdf_tree(candidate)
            progress.complete_unit("PDF candidate")
            progress.phase("atomically promote PDF candidate")
            atomic_promote(candidate, PDF_BUILD_ROOT, validate=validate_pdf_tree)
            progress.complete_unit("PDF candidate promotion")
    print(f"Published PDF candidate to {PDF_BUILD_ROOT.relative_to(REPOSITORY_ROOT)}", flush=True)


def verify_pdfs() -> None:
    validate_pdf_tree(PDF_BUILD_ROOT)
    print(f"Verified PDF candidate: {PDF_BUILD_ROOT.relative_to(REPOSITORY_ROOT)}", flush=True)


def pdf_reproducibility_check() -> None:
    BUILD_ROOT.mkdir(parents=True, exist_ok=True)
    with StagedDirectory(BUILD_ROOT, "pdf-reproducibility") as staging:
        candidate = staging.candidate("candidate")
        progress = Progress("PDF reproducibility", 2)
        with tracked_operation(progress):
            progress.phase("verify published PDF candidate")
            validate_pdf_tree(PDF_BUILD_ROOT)
            published_hashes = tree_hashes(PDF_BUILD_ROOT)
            progress.complete_unit("published candidate")
            progress.phase("build and compare independent PDF candidate")
            build_pdf_tree(candidate, use_cache=False)
            candidate_hashes = tree_hashes(candidate)
            if published_hashes != candidate_hashes:
                differing = sorted(
                    path
                    for path in set(published_hashes) | set(candidate_hashes)
                    if published_hashes.get(path) != candidate_hashes.get(path)
                )
                raise BuildError("non-deterministic PDF files:\n" + "\n".join(differing))
            progress.complete_unit("independent candidate")
    print(f"PDF reproducibility check passed for {len(published_hashes)} files.", flush=True)
