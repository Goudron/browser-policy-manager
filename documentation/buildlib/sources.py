"""DITA source validation and focused documentation checks."""

# ruff: noqa: F403, F405
from .shared import *


def dita_sources() -> list[Path]:
    roots = (
        DOCUMENTATION_ROOT / "src/dita",
        DOCUMENTATION_ROOT / "src/shared",
        DOCUMENTATION_ROOT / "src/generated/firefox",
        DOCUMENTATION_ROOT / "src/generated/cis",
    )
    return sorted(
        path for root in roots for path in root.rglob("*") if path.suffix in SOURCE_SUFFIXES
    )


def _source_target(source: Path, href: str) -> tuple[Path, str]:
    parsed = urllib.parse.urlsplit(href)
    if parsed.scheme or parsed.netloc:
        if parsed.scheme != "https":
            raise BuildError(f"{source}: forbidden link scheme in {href!r}")
        return source, ""
    target = source if not parsed.path else (source.parent / urllib.parse.unquote(parsed.path))
    resolved = target.resolve()
    try:
        resolved.relative_to(DOCUMENTATION_ROOT.resolve())
    except ValueError as exc:
        raise BuildError(f"{source}: link escapes documentation workspace: {href!r}") from exc
    return resolved, urllib.parse.unquote(parsed.fragment)


def _xml_ids(path: Path, cache: dict[Path, set[str]]) -> set[str]:
    if path not in cache:
        try:
            root = ET.parse(path).getroot()
        except (OSError, ET.ParseError) as exc:
            raise BuildError(f"invalid DITA XML {path}: {exc}") from exc
        cache[path] = {element.attrib["id"] for element in root.iter() if "id" in element.attrib}
    return cache[path]


def validate_source_links() -> None:
    sources = dita_sources()
    if not sources:
        raise BuildError("no DITA source files found")
    parsed: dict[Path, ET.Element] = {}
    keys: set[str] = set()
    for source in sources:
        try:
            root = ET.parse(source).getroot()
        except (OSError, ET.ParseError) as exc:
            raise BuildError(f"invalid DITA XML {source}: {exc}") from exc
        parsed[source] = root
        for element in root.iter():
            keys.update(element.attrib.get("keys", "").split())

    id_cache: dict[Path, set[str]] = {}
    errors: list[str] = []
    for source, root in parsed.items():
        for element in root.iter():
            for keyref_attribute in ("keyref", "conkeyref"):
                keyref = element.attrib.get(keyref_attribute)
                if keyref and keyref.split("/", 1)[0] not in keys:
                    errors.append(f"{source}: unknown {keyref_attribute} {keyref!r}")
            href = element.attrib.get("href")
            if not href:
                continue
            try:
                target, fragment = _source_target(source, href)
            except BuildError as exc:
                errors.append(str(exc))
                continue
            if target == source and urllib.parse.urlsplit(href).scheme:
                continue
            if not target.is_file():
                errors.append(f"{source}: missing local target {href!r}")
                continue
            if fragment:
                anchor = fragment.split("/", 1)[-1]
                if anchor not in _xml_ids(target, id_cache):
                    errors.append(f"{source}: missing DITA fragment {fragment!r} in {target}")
    if errors:
        raise BuildError("source link validation failed:\n" + "\n".join(errors))


def _source_keys_from_text(sources: list[Path]) -> set[str]:
    keys: set[str] = set()
    key_attribute = re.compile(r"""\bkeys\s*=\s*(['"])(.*?)\1""", flags=re.DOTALL)
    for source in sources:
        try:
            text = source.read_text(encoding="utf-8")
        except OSError:
            continue
        for _quote, value in key_attribute.findall(text):
            keys.update(value.split())
    return keys


def validate_focused_source_links(focused_sources: list[Path]) -> None:
    sources = [source for source in focused_sources if source.suffix in SOURCE_SUFFIXES]
    if not sources:
        return
    keys = _source_keys_from_text(dita_sources())
    id_cache: dict[Path, set[str]] = {}
    errors: list[str] = []
    for source in sources:
        if not source.is_file():
            errors.append(f"{source}: changed DITA source is missing")
            continue
        try:
            root = ET.parse(source).getroot()
        except (OSError, ET.ParseError) as exc:
            errors.append(f"invalid DITA XML {source}: {exc}")
            continue
        for element in root.iter():
            for keyref_attribute in ("keyref", "conkeyref"):
                keyref = element.attrib.get(keyref_attribute)
                if keyref and keyref.split("/", 1)[0] not in keys:
                    errors.append(f"{source}: unknown {keyref_attribute} {keyref!r}")
            href = element.attrib.get("href")
            if not href:
                continue
            try:
                target, fragment = _source_target(source, href)
            except BuildError as exc:
                errors.append(str(exc))
                continue
            if target == source and urllib.parse.urlsplit(href).scheme:
                continue
            if not target.is_file():
                errors.append(f"{source}: missing local target {href!r}")
                continue
            if fragment:
                anchor = fragment.split("/", 1)[-1]
                if anchor not in _xml_ids(target, id_cache):
                    errors.append(f"{source}: missing DITA fragment {fragment!r} in {target}")
    if errors:
        raise BuildError("focused source link validation failed:\n" + "\n".join(errors))


def _resolve_changed_path(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = REPOSITORY_ROOT / path
    resolved = path.resolve()
    try:
        resolved.relative_to(REPOSITORY_ROOT.resolve())
    except ValueError as exc:
        raise BuildError(f"changed path is outside repository: {value}") from exc
    return resolved


def _git_changed_paths() -> list[Path]:
    paths: list[Path] = []
    commands = (
        [
            "git",
            "diff",
            "--name-only",
            "--diff-filter=ACMRTUXB",
            "--",
            "documentation",
            "docs/architecture",
        ],
        [
            "git",
            "ls-files",
            "--others",
            "--exclude-standard",
            "--",
            "documentation",
            "docs/architecture",
        ],
    )
    for command in commands:
        completed = subprocess.run(
            command,
            cwd=REPOSITORY_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode:
            raise BuildError((completed.stdout + "\n" + completed.stderr).strip())
        paths.extend(
            _resolve_changed_path(line) for line in completed.stdout.splitlines() if line.strip()
        )
    return sorted(set(paths))


def _changed_paths(arguments: list[str]) -> list[Path]:
    if arguments:
        return sorted({_resolve_changed_path(argument) for argument in arguments})
    return _git_changed_paths()


def _relative_repo_path(path: Path) -> str:
    return path.relative_to(REPOSITORY_ROOT).as_posix()


def _fast_scope(path: Path) -> dict[str, Any] | None:
    if path == REPOSITORY_ROOT / "README.md":
        return {
            "kind": "readme",
            "locales": set(),
            "guide_roots": set(),
            "search_indexes": set(),
            "path": "README.md",
        }
    try:
        relative = path.relative_to(DOCUMENTATION_ROOT)
    except ValueError:
        try:
            architecture_relative = path.relative_to(REPOSITORY_ROOT / "docs/architecture")
        except ValueError:
            return None
        return {
            "kind": "architecture-contract",
            "locales": set(LOCALES),
            "guide_roots": set(),
            "search_indexes": set(),
            "path": architecture_relative.as_posix(),
        }
    parts = relative.parts
    if not parts:
        return None
    if parts[:2] == ("src", "dita") and len(parts) >= 4 and parts[2] in LOCALES:
        guide_root = ""
        if parts[3] == "maps":
            guide_root = GUIDE_OUTPUT_ROOT_BY_MAP.get(path.name, "")
        else:
            guide_root = GUIDE_OUTPUT_ROOT_BY_SOURCE_DIR.get(parts[3], "user")
        return {
            "kind": "dita",
            "locales": {parts[2]},
            "guide_roots": {guide_root} if guide_root else set(),
            "search_indexes": {parts[2]},
            "path": relative.as_posix(),
        }
    if parts[:2] == ("src", "shared"):
        return {
            "kind": "shared-source",
            "locales": set(LOCALES),
            "guide_roots": {url_root for *_prefix, url_root in GUIDE_MAPS},
            "search_indexes": set(LOCALES),
            "path": relative.as_posix(),
        }
    if parts[:2] == ("src", "generated"):
        guide_root = {"firefox": "firefox", "cis": "cis"}.get(
            parts[2] if len(parts) > 2 else "", ""
        )
        return {
            "kind": "generated-source",
            "locales": set(LOCALES),
            "guide_roots": {guide_root} if guide_root else set(),
            "search_indexes": set(LOCALES),
            "path": relative.as_posix(),
        }
    if parts[:2] == ("assets", "theme"):
        return {
            "kind": "theme-asset",
            "locales": set(LOCALES),
            "guide_roots": set(),
            "search_indexes": set(),
            "path": relative.as_posix(),
        }
    if parts[:2] == ("assets", "screenshots") and len(parts) >= 3 and parts[2] in LOCALES:
        return {
            "kind": "screenshot-asset",
            "locales": {parts[2]},
            "guide_roots": set(),
            "search_indexes": {parts[2]},
            "path": relative.as_posix(),
        }
    if parts[0] == "config" and path.name.startswith("search-") and path.suffix == ".json":
        return {
            "kind": "search-config",
            "locales": set(LOCALES),
            "guide_roots": set(),
            "search_indexes": set(LOCALES),
            "path": relative.as_posix(),
        }
    if parts[0] in {"config", "fixtures", "runbooks", "tests"}:
        return {
            "kind": f"{parts[0]}-input",
            "locales": set(),
            "guide_roots": set(),
            "search_indexes": set(),
            "path": relative.as_posix(),
        }
    return None


def _topic_id(path: Path) -> str | None:
    if path.suffix not in SOURCE_SUFFIXES or not path.is_file():
        return None
    try:
        root = ET.parse(path).getroot()
    except OSError, ET.ParseError:
        return None
    return root.attrib.get("id")


def _source_line_hint(path: Path, topic_id: str | None = None) -> int | None:
    if not path.is_file():
        return None
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError, UnicodeDecodeError:
        return None
    patterns = [f'id="{topic_id}"', f"id='{topic_id}'"] if topic_id else []
    patterns.extend(["<topic", "<map", "<section"])
    for index, line in enumerate(lines, start=1):
        if any(pattern in line for pattern in patterns):
            return index
    return 1 if lines else None


def _first_fixture_entry(path: Path, collection: str) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError, json.JSONDecodeError:
        return None
    entries = payload.get(collection)
    if isinstance(entries, list) and entries and isinstance(entries[0], dict):
        return entries[0]
    return None


def _diagnostic_context(path: Path) -> dict[str, Any]:
    scope = _fast_scope(path) or {
        "kind": "unknown",
        "locales": set(),
        "guide_roots": set(),
        "search_indexes": set(),
    }
    locales = sorted(scope["locales"])
    guide_roots = sorted(scope["guide_roots"])
    topic_id = _topic_id(path)
    locale = locales[0] if locales else None
    guide = guide_roots[0] if guide_roots else None
    target_url = (
        f"/help/{locale}/{guide}/{topic_id}.html" if locale and guide and topic_id else None
    )
    search_hint = _first_fixture_entry(SEARCH_STATE_FIXTURE, "queries")
    screenshot_hint = _first_fixture_entry(SCREENSHOT_STATE_FIXTURE, "capture_matrix")
    return {
        "source_path": _relative_repo_path(path),
        "failure_domain": scope["kind"],
        "topic_id": topic_id,
        "locale": locale,
        "guide": guide,
        "source_line": _source_line_hint(path, topic_id),
        "target_url": target_url,
        "query": search_hint.get("query") if search_hint else None,
        "query_fixture_id": search_hint.get("id") if search_hint else None,
        "screenshot_state": screenshot_hint.get("id") if screenshot_hint else None,
        "focused_rerun": f"make docs-fast-check DOCS_CHANGED={_relative_repo_path(path)}",
    }


def _diagnostic_payload(error: BaseException, changed_arguments: list[str]) -> dict[str, Any]:
    resolved_paths: list[Path] = []
    for argument in changed_arguments:
        try:
            resolved_paths.append(_resolve_changed_path(argument))
        except BuildError:
            continue
    contexts = [_diagnostic_context(path) for path in resolved_paths]
    focused_rerun = (
        "make docs-fast-check"
        if not changed_arguments
        else 'make docs-fast-check DOCS_CHANGED="' + " ".join(changed_arguments) + '"'
    )
    return {
        "schema_version": 1,
        "backlog_item": "BPM090-M11-06",
        "target_bpm_version": "0.9.1",
        "status": "failed",
        "error_summary": str(error).splitlines()[0],
        "focused_rerun": focused_rerun,
        "contexts": contexts,
        "debug_artifacts_root": "documentation/reports/diagnostics/",
        "retention": "ignored local/CI diagnostics; do not commit generated reports",
    }


def write_failure_diagnostic(error: BaseException, changed_arguments: list[str]) -> Path:
    payload = _diagnostic_payload(error, changed_arguments)
    digest = hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()[:12]
    DIAGNOSTICS_ROOT.mkdir(parents=True, exist_ok=True)
    path = DIAGNOSTICS_ROOT / f"diagnostic-{digest}.json"
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def _affected_output_paths(scopes: list[dict[str, Any]], dita_paths: list[Path]) -> list[str]:
    outputs: set[str] = set()
    topic_ids = {path: _topic_id(path) for path in dita_paths}
    for path, topic_id in topic_ids.items():
        scope = _fast_scope(path)
        if not scope:
            continue
        for locale in scope["locales"]:
            if topic_id:
                guide_roots = scope["guide_roots"] or {"index"}
                for guide_root in guide_roots:
                    if guide_root == "index":
                        outputs.add(f"documentation/build/site/{locale}/index.html")
                    else:
                        outputs.add(
                            f"documentation/build/site/{locale}/{guide_root}/{topic_id}.html"
                        )
            for search_locale in scope["search_indexes"]:
                outputs.add(f"documentation/build/site/search/{search_locale}/index.json")
    for scope in scopes:
        for locale in scope["locales"]:
            for guide_root in scope["guide_roots"]:
                outputs.add(f"documentation/build/site/{locale}/{guide_root}/")
            for search_locale in scope["search_indexes"]:
                outputs.add(f"documentation/build/site/search/{search_locale}/index.json")
    return sorted(outputs)


def _validate_changed_inputs(paths: list[Path]) -> None:
    errors: list[str] = []
    for path in paths:
        scope = _fast_scope(path)
        if scope is None:
            continue
        if not path.exists():
            errors.append(f"{_relative_repo_path(path)}: changed documentation input is missing")
            continue
        if path.is_file() and path.stat().st_size == 0:
            errors.append(f"{_relative_repo_path(path)}: changed documentation input is empty")
            continue
        if path.suffix == ".json":
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                errors.append(f"{_relative_repo_path(path)}: invalid JSON: {exc}")
    if errors:
        raise BuildError("focused input validation failed:\n" + "\n".join(errors))


def _structural_signature(root: ET.Element) -> dict[str, Any]:
    """Keep locale contracts meaningful without treating inline-markup choice as prose drift."""
    return {
        "root": (root.tag, root.get("id")),
        "ids": sorted(element.get("id") for element in root.iter() if element.get("id")),
        "sections": [element.get("id") for element in root.iter("section")],
        "steps": len(list(root.iter("step"))),
        "warnings": len(list(root.iter("note"))),
        "examples": sorted(
            element.get("id") for element in root.iter("example") if element.get("id")
        ),
        "codeblocks": sorted(element.get("outputclass", "") for element in root.iter("codeblock")),
        "figures": sorted(element.get("id") for element in root.iter("fig") if element.get("id")),
        "related_keyrefs": sorted(
            element.get("keyref") for element in root.iter("link") if element.get("keyref")
        ),
    }


def _validate_localized_shape(paths: list[Path]) -> None:
    errors: list[str] = []
    dita_root = DOCUMENTATION_ROOT / "src/dita"
    for path in paths:
        try:
            relative = path.relative_to(dita_root)
        except ValueError:
            continue
        if (
            len(relative.parts) < 2
            or relative.parts[0] == "en"
            or path.suffix not in SOURCE_SUFFIXES
        ):
            continue
        english_peer = dita_root / "en" / Path(*relative.parts[1:])
        if not english_peer.is_file():
            errors.append(
                f"{_relative_repo_path(path)}: missing English peer for localized shape check"
            )
            continue
        try:
            localized = ET.parse(path).getroot()
            english = ET.parse(english_peer).getroot()
        except (OSError, ET.ParseError) as exc:
            errors.append(f"{_relative_repo_path(path)}: cannot compare localized shape: {exc}")
            continue
        if _structural_signature(localized) != _structural_signature(english):
            errors.append(
                f"{_relative_repo_path(path)}: localized structural shape differs from "
                f"{_relative_repo_path(english_peer)}"
            )
    if errors:
        raise BuildError("focused localization shape validation failed:\n" + "\n".join(errors))


def _validate_semantic_markup(paths: list[Path]) -> None:
    """Check semantic UI, warnings, figures, and full Firefox documents in changed source only."""
    errors: list[str] = []
    excluded_ui_ancestors = {"title", "navtitle", "alt", "figdesc", "codeph", "filepath", "apiname"}
    for path in paths:
        if path.suffix not in SOURCE_SUFFIXES:
            continue
        try:
            root = ET.parse(path).getroot()
        except OSError, ET.ParseError:
            continue  # XML parsing is reported by validate_focused_source_links.
        parents = {child: parent for parent in root.iter() for child in parent}
        for control in root.findall(".//uicontrol"):
            if not "".join(control.itertext()).strip():
                errors.append(f"{_relative_repo_path(path)}: empty uicontrol markup")
            ancestor = parents.get(control)
            while ancestor is not None:
                if ancestor.tag in excluded_ui_ancestors:
                    errors.append(
                        f"{_relative_repo_path(path)}: uicontrol is nested in {ancestor.tag}"
                    )
                ancestor = parents.get(ancestor)
        for note in root.findall(".//note"):
            if note.get("type") != "warning" or not "".join(note.itertext()).strip():
                errors.append(
                    f"{_relative_repo_path(path)}: admonition must be a non-empty warning note"
                )
        for figure in root.findall(".//fig"):
            image = figure.find("image")
            title = figure.find("title")
            if not figure.get("id") or title is None or not "".join(title.itertext()).strip():
                errors.append(f"{_relative_repo_path(path)}: figure requires an id and title")
            if (
                image is None
                or not image.get("keyref")
                or not "".join(image.findtext("alt", default="")).strip()
            ):
                errors.append(
                    f"{_relative_repo_path(path)}: figure requires a keyed image and localized alt text"
                )
        if path.name.endswith("policies-json.dita"):
            documents: list[dict[str, Any]] = []
            for block in root.iter("codeblock"):
                if block.get("outputclass") != "language-json":
                    continue
                try:
                    documents.append(json.loads(block.text or ""))
                except json.JSONDecodeError as exc:
                    errors.append(f"{_relative_repo_path(path)}: invalid JSON codeblock: {exc}")
            if not any(
                set(document) == {"policies"} and isinstance(document["policies"], dict)
                for document in documents
            ):
                errors.append(
                    f"{_relative_repo_path(path)}: policies.json topic requires a complete top-level policies document"
                )
    if errors:
        raise BuildError("focused semantic source validation failed:\n" + "\n".join(errors))


def _validate_readme_policies(paths: list[Path]) -> None:
    if REPOSITORY_ROOT / "README.md" not in paths:
        return
    readme = (REPOSITORY_ROOT / "README.md").read_text(encoding="utf-8")
    blocks = re.findall(r"```json\n(.*?)\n```", readme, re.DOTALL)
    try:
        documents = [json.loads(block) for block in blocks]
    except json.JSONDecodeError as exc:
        raise BuildError(f"README.md: invalid JSON codeblock: {exc}") from exc
    if not any(
        set(document) == {"policies"} and isinstance(document["policies"], dict)
        for document in documents
    ):
        raise BuildError("README.md: requires a complete top-level Firefox policies document")


def _validate_registered_fixtures(paths: list[Path]) -> None:
    fixture_paths = {path for path in paths if path.is_relative_to(DOCUMENTATION_ROOT / "fixtures")}
    if not fixture_paths:
        return
    catalog = json.loads(FIXTURE_CATALOG.read_text(encoding="utf-8"))
    registered = {
        REPOSITORY_ROOT / item["path"]
        for item in catalog["fixtures"]
        if isinstance(item, dict) and isinstance(item.get("path"), str)
    }
    errors: list[str] = []
    for path in fixture_paths & registered:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("schema_version") != 1 or payload.get("synthetic") is not True:
            errors.append(
                f"{_relative_repo_path(path)}: registered fixture must be schema v1 and synthetic"
            )
    if errors:
        raise BuildError("focused fixture validation failed:\n" + "\n".join(errors))


def fast_check(changed_arguments: list[str] | None = None, *, emit: bool = True) -> dict[str, Any]:
    changed = _changed_paths(changed_arguments or [])
    scoped = [(path, _fast_scope(path)) for path in changed]
    relevant = [(path, scope) for path, scope in scoped if scope is not None]
    if not relevant:
        report = {
            "changed": [_relative_repo_path(path) for path in changed],
            "checked": [],
            "locales": [],
            "guide_roots": [],
            "search_indexes": [],
            "affected_outputs": [],
            "checked_guards": [],
            "skipped_release_only_checks": [
                "six-locale DITA validation and editorial sign-off",
                "binary PDF build, verification, and delivery",
                "reproducibility, package verification, snapshot, and install handoff",
            ],
            "recommended_next_checks": ["make docs-release-handoff"],
        }
        if emit:
            print("Documentation fast check: no changed documentation inputs detected.", flush=True)
            print(
                "Escalate to authoritative release handoff: make docs-release-handoff", flush=True
            )
        return report

    paths = [path for path, _scope in relevant]
    _validate_changed_inputs(paths)
    focused_dita = [path for path in paths if path.suffix in SOURCE_SUFFIXES]
    validate_focused_source_links(focused_dita)
    _validate_localized_shape(focused_dita)
    _validate_semantic_markup(focused_dita)
    _validate_readme_policies(paths)
    _validate_registered_fixtures(paths)
    scopes = [scope for _path, scope in relevant if scope is not None]
    locales = sorted({locale for scope in scopes for locale in scope["locales"]})
    guide_roots = sorted({guide_root for scope in scopes for guide_root in scope["guide_roots"]})
    search_indexes = sorted({locale for scope in scopes for locale in scope["search_indexes"]})
    affected_outputs = _affected_output_paths(scopes, focused_dita)
    checked_guards = ["schema and direct links", "semantic UI/admonition and figures"]
    if any(
        path.suffix in SOURCE_SUFFIXES
        and path.is_relative_to(DOCUMENTATION_ROOT / "src/dita")
        and path.relative_to(DOCUMENTATION_ROOT / "src/dita").parts[0] != "en"
        for path in paths
    ):
        checked_guards.append("localized structural shape when a locale topic changed")
    if any(path.name.endswith("policies-json.dita") or path.name == "README.md" for path in paths):
        checked_guards.append("complete Firefox policies.json document shape")
    if any(path.is_relative_to(DOCUMENTATION_ROOT / "fixtures") for path in paths):
        checked_guards.append("affected registered fixture shape")
    skipped_release_only_checks = [
        "six-locale DITA validation and editorial sign-off",
        "full locale parity, manifest, search, API-example, and portal contract suites",
        "binary PDF build, verification, and delivery",
        "reproducibility, package verification, documentation snapshot, and install handoff",
    ]
    recommended_next_checks = ["make docs-release-handoff"]
    report = {
        "changed": [_relative_repo_path(path) for path in changed],
        "checked": [_relative_repo_path(path) for path in paths],
        "locales": locales,
        "guide_roots": guide_roots,
        "search_indexes": search_indexes,
        "affected_outputs": affected_outputs,
        "checked_guards": checked_guards,
        "skipped_release_only_checks": skipped_release_only_checks,
        "recommended_next_checks": recommended_next_checks,
    }
    if emit:
        print(f"Documentation fast check: {len(paths)} changed documentation input(s).", flush=True)
        print("Checked inputs:", flush=True)
        for path in report["checked"]:
            print(f"  {path}", flush=True)
        print(f"Affected locales: {', '.join(locales) if locales else 'none'}", flush=True)
        print(
            f"Affected guide roots: {', '.join(guide_roots) if guide_roots else 'none'}", flush=True
        )
        print(
            f"Affected search indexes: {', '.join(search_indexes) if search_indexes else 'none'}",
            flush=True,
        )
        print(f"Selected scope: {', '.join(report['checked'])}", flush=True)
        print("Fast guards run:", flush=True)
        for guard in checked_guards:
            print(f"  {guard}", flush=True)
        if affected_outputs:
            print("Expected outputs touched by a full docs build:", flush=True)
            for output in affected_outputs[:30]:
                print(f"  {output}", flush=True)
            if len(affected_outputs) > 30:
                print(f"  ... {len(affected_outputs) - 30} more", flush=True)
        print("Skipped release-only checks (intentional):", flush=True)
        for check in skipped_release_only_checks:
            print(f"  {check}", flush=True)
        print("Fast check passed; this is not a release gate.", flush=True)
        print("Escalate to authoritative release handoff: make docs-release-handoff", flush=True)
    return report


def _metadata_validation() -> None:
    validator = DOCUMENTATION_ROOT / "tools/validate_metadata.py"
    completed = subprocess.run(
        [sys.executable, str(validator)], text=True, capture_output=True, check=False
    )
    if completed.returncode:
        raise BuildError((completed.stdout + "\n" + completed.stderr).strip())


def validate_sources() -> None:
    _metadata_validation()
    validate_source_links()
