"""Navigation, deterministic search, and documentation manifest ownership."""

# ruff: noqa: F403, F405
from dataclasses import dataclass

from .shared import *
from .shared import _NAVIGATION_MODEL_CACHE, _load_lock, _product_version
from .validation import ValidationReporter, ValidationStage


def _map_title(locale: str, filename: str) -> str:
    source = DOCUMENTATION_ROOT / f"src/dita/{locale}/maps/{filename}"
    try:
        root = ET.parse(source).getroot()
    except (OSError, ET.ParseError) as exc:
        raise BuildError(f"cannot read localized map title {source}: {exc}") from exc
    title = root.find("title")
    if title is None or not "".join(title.itertext()).strip():
        raise BuildError(f"localized map title is missing: {source}")
    return " ".join("".join(title.itertext()).split())


def _escape(value: str) -> str:
    return html.escape(value, quote=True)


def _relative_href(from_html: Path, target: Path) -> str:
    return os.path.relpath(target, from_html.parent).replace(os.sep, "/")


def _navigation_topic_order(filename: str) -> list[str]:
    topic_ids: list[str] = []
    for keyref in _guide_topic_keyrefs("en", filename):
        if not keyref.startswith("topic."):
            raise BuildError(f"guide map uses unsupported topic key: {keyref}")
        topic_ids.append(keyref.removeprefix("topic."))
    return topic_ids


def _navigation_section_labels(taxonomy: dict[str, Any]) -> dict[str, dict[str, str]]:
    catalog = _read_json_file(TOPIC_SECTION_LABELS)
    if catalog.get("locales") != list(LOCALES):
        raise BuildError("topic section label catalog must use the exact locale matrix")
    expected = {
        section["label_key"]
        for document in taxonomy["documents"]
        for section in document["sections"]
    }
    labels = catalog.get("labels", {})
    if set(labels) != expected:
        raise BuildError("topic section label catalog must match the taxonomy label keys exactly")
    for document in taxonomy["documents"]:
        for section in document["sections"]:
            label_key = section["label_key"]
            localized = labels[label_key]
            if set(localized) != set(LOCALES):
                raise BuildError(f"topic section label {label_key} must own every locale")
            if any(
                not isinstance(localized[locale], str) or not localized[locale].strip()
                for locale in LOCALES
            ):
                raise BuildError(
                    f"topic section label {label_key} must be non-empty in every locale"
                )
            if localized["en"] != section["canonical_label"]:
                raise BuildError(
                    f"topic section label {label_key} must preserve its canonical English value"
                )
            if any(localized[locale] == localized["en"] for locale in LOCALES if locale != "en"):
                raise BuildError(f"topic section label {label_key} must not fall back to English")
    return labels


def _navigation_sections() -> dict[str, list[dict[str, Any]]]:
    taxonomy = _read_json_file(TOPIC_SECTION_TAXONOMY)
    labels = _navigation_section_labels(taxonomy)
    return {
        document["guide_id"]: [
            {
                **section,
                "labels": labels[section["label_key"]],
                "node_id": f"section:{document['guide_id']}:{section['section_id']}",
            }
            for section in document["sections"]
        ]
        for document in taxonomy["documents"]
    }


def _navigation_model(site_root: Path) -> dict[str, Any]:
    cache_key = str(site_root.resolve())
    cached = _NAVIGATION_MODEL_CACHE.get(cache_key)
    if cached is not None:
        return cached
    model = {
        "topics": _build_topics(site_root),
        "topic_order": {
            filename: _navigation_topic_order(filename)
            for _guide_id, filename, _anchor, _url_root in GUIDE_MAPS
        },
        "sections": _navigation_sections(),
    }
    _NAVIGATION_MODEL_CACHE[cache_key] = model
    return model


def _current_navigation_topic(
    topics: dict[str, dict[str, Any]],
    page: Path,
    site_root: Path,
    locale: str,
) -> tuple[str, str] | None:
    try:
        page_output = page.relative_to(site_root).as_posix()
    except ValueError as exc:
        raise BuildError(f"documentation page is outside site root: {page}") from exc
    guide_ids = {guide_id for guide_id, *_rest in GUIDE_MAPS}
    for topic_id, topic in topics.items():
        if topic_id in guide_ids:
            continue
        if topic["output"].get(locale) == page_output:
            return topic["guide_id"], topic_id
    return None


def _locale_navigation_href(output: str, locale: str) -> str:
    prefix = f"{locale}/"
    if not output.startswith(prefix):
        raise BuildError(f"navigation output is outside locale root: {output}")
    return output.removeprefix(prefix)


def _navigation_topic_node(
    topics: dict[str, dict[str, Any]], topic_id: str, locale: str
) -> dict[str, Any]:
    topic = topics[topic_id]
    return {
        "node_id": topic_id,
        "node_type": "topic",
        "label": topic["title"][locale],
        "href": _locale_navigation_href(topic["output"][locale], locale),
        "anchor": None,
        "label_key": None,
        "children": [],
    }


def _navigation_payload(site_root: Path, locale: str) -> dict[str, Any]:
    model = _navigation_model(site_root)
    topics = model["topics"]
    guide_ids = {guide_id for guide_id, *_rest in GUIDE_MAPS}
    guide_nodes = []
    for guide_id, filename, anchor, _url_root in GUIDE_MAPS:
        guide = topics[guide_id]
        sections = model["sections"].get(guide_id, [])
        if sections:
            children = [
                {
                    "node_id": section["node_id"],
                    "node_type": "section",
                    "label": section["labels"][locale],
                    "href": None,
                    "anchor": None,
                    "label_key": section["label_key"],
                    "children": [
                        _navigation_topic_node(topics, topic_id, locale)
                        for topic_id in section["topics"]
                    ],
                }
                for section in sections
            ]
        else:
            children = [
                _navigation_topic_node(topics, topic_id, locale)
                for topic_id in model["topic_order"][filename]
                if topic_id not in guide_ids
            ]
        guide_nodes.append(
            {
                "node_id": guide_id,
                "node_type": "guide",
                "label": guide["title"][locale],
                "href": f"{_locale_navigation_href(guide['output'][locale], locale)}#{anchor}",
                "anchor": anchor,
                "label_key": None,
                "children": children,
            }
        )
    root = {
        "node_id": "documentation-root",
        "node_type": "root",
        "label": SHELL_LABELS[locale]["navigation_root"],
        "href": "index.html",
        "anchor": None,
        "label_key": "navigation.root",
        "children": guide_nodes,
    }

    def count_nodes(node: dict[str, Any]) -> int:
        return 1 + sum(count_nodes(child) for child in node["children"])

    return {
        "$schema": "../schemas/product-documentation-navigation-v1.schema.json",
        "schema_version": 1,
        "documentation_version": _product_version(),
        "locale": locale,
        "node_count": count_nodes(root),
        "root": root,
    }


def generate_navigation_files(site_root: Path) -> None:
    for locale in LOCALES:
        payload = _navigation_payload(site_root, locale)
        _validate_schema(payload, NAVIGATION_SCHEMA)
        _write_json(site_root / locale / "navigation.json", payload)


def _manifest_navigation_root(manifest: dict[str, Any], locale: str) -> dict[str, Any]:
    topics = manifest["topics"]
    sections_by_guide = _navigation_sections()
    guide_ids = {guide_id for guide_id, *_rest in GUIDE_MAPS}

    def topic_node(topic_id: str) -> dict[str, Any]:
        topic = topics[topic_id]
        return {
            "node_id": topic_id,
            "node_type": "topic",
            "label": topic["title"][locale],
            "href": _locale_navigation_href(topic["output"][locale], locale),
            "anchor": None,
            "label_key": None,
            "children": [],
        }

    guide_nodes = []
    for guide_id, filename, anchor, _url_root in GUIDE_MAPS:
        guide = manifest["guides"][guide_id]
        sections = sections_by_guide.get(guide_id, [])
        if sections:
            children = [
                {
                    "node_id": section["node_id"],
                    "node_type": "section",
                    "label": section["labels"][locale],
                    "href": None,
                    "anchor": None,
                    "label_key": section["label_key"],
                    "children": [topic_node(topic_id) for topic_id in section["topics"]],
                }
                for section in sections
            ]
        else:
            children = [
                topic_node(topic_id)
                for topic_id in _navigation_topic_order(filename)
                if topic_id not in guide_ids
            ]
        home_topic = topics[guide["home_topic_id"]]
        guide_nodes.append(
            {
                "node_id": guide_id,
                "node_type": "guide",
                "label": guide["title"][locale],
                "href": f"{_locale_navigation_href(home_topic['output'][locale], locale)}#{anchor}",
                "anchor": anchor,
                "label_key": None,
                "children": children,
            }
        )
    return {
        "node_id": "documentation-root",
        "node_type": "root",
        "label": SHELL_LABELS[locale]["navigation_root"],
        "href": "index.html",
        "anchor": None,
        "label_key": "navigation.root",
        "children": guide_nodes,
    }


def _validate_navigation_manifest_alignment(
    locale: str, navigation_payload: dict[str, Any], manifest: dict[str, Any]
) -> None:
    if navigation_payload.get("locale") != locale:
        raise BuildError(f"navigation locale mismatch for {locale}")
    artifact = manifest.get("artifact")
    if not isinstance(artifact, dict):
        raise BuildError("manifest artifact metadata is missing")
    bpm_version = artifact.get("bpm_version")
    documentation_version = artifact.get("documentation_version")
    if (
        not isinstance(bpm_version, str)
        or documentation_version != bpm_version
        or navigation_payload.get("documentation_version") != bpm_version
    ):
        raise BuildError(f"navigation version diverges from BPM artifact metadata for {locale}")
    expected_root = _manifest_navigation_root(manifest, locale)
    if navigation_payload.get("root") != expected_root:
        raise BuildError(f"navigation source diverges from manifest authority for {locale}")

    def count_nodes(node: dict[str, Any]) -> int:
        return 1 + sum(count_nodes(child) for child in node["children"])

    expected_count = count_nodes(expected_root)
    if navigation_payload.get("node_count") != expected_count:
        raise BuildError(f"navigation node count diverges from manifest authority for {locale}")


def _validate_navigation_artifact_record(
    locale: str,
    record: dict[str, Any],
    payload: bytes,
    manifest: dict[str, Any],
    *,
    context: str,
) -> dict[str, Any]:
    if _payload_sha256(payload) != record["sha256"]:
        raise BuildError(f"{context} navigation SHA-256 mismatch for {locale}")
    navigation_payload = _read_json_bytes(payload, record["path"])
    _validate_schema(navigation_payload, NAVIGATION_SCHEMA)
    if record["format_version"] != navigation_payload["schema_version"]:
        raise BuildError(f"{context} navigation format version mismatch for {locale}")
    if record["node_count"] != navigation_payload["node_count"]:
        raise BuildError(f"{context} navigation node count mismatch for {locale}")
    _validate_navigation_manifest_alignment(locale, navigation_payload, manifest)
    return navigation_payload


def _navigation_host(site_root: Path, page: Path, locale: str) -> str:
    labels = SHELL_LABELS[locale]
    current = _current_navigation_topic(
        _navigation_model(site_root)["topics"], page, site_root, locale
    )
    current_node_id = current[1] if current else "documentation-root"
    navigation_href = _relative_href(page, site_root / locale / "navigation.json")
    root_href = _relative_href(page, site_root / locale / "index.html")
    return f"""            <div class="bpm-docs-tree-host" data-docs-tree-host aria-busy="true" data-navigation-href="{_escape(navigation_href)}" data-navigation-locale="{_escape(locale)}" data-navigation-version="{_escape(_product_version())}" data-current-tree-node="{_escape(current_node_id)}" data-tree-storage-key="bpm-docs-tree:{_escape(locale)}:{_escape(_product_version())}" data-label-tree="{_escape(labels["navigation_tree_label"])}" data-label-expand="{_escape(labels["navigation_expand"])}" data-label-collapse="{_escape(labels["navigation_collapse"])}" data-label-current="{_escape(labels["navigation_current"])}" data-label-parent="{_escape(labels["navigation_parent"])}" data-label-back-to-root="{_escape(labels["navigation_back_to_root"])}" data-label-loading="{_escape(labels["navigation_loading"])}" data-label-unavailable="{_escape(labels["navigation_unavailable"])}" data-root-href="{_escape(root_href)}">
               <p class="bpm-docs-tree-status" role="status" aria-live="polite" data-docs-tree-status>{_escape(labels["navigation_loading"])}</p>
               <noscript><p class="bpm-docs-tree-status"><a href="{_escape(root_href)}">{_escape(labels["navigation_back_to_root"])}</a></p></noscript>
            </div>"""


def _navigation_breadcrumbs(site_root: Path, page: Path, locale: str) -> str:
    labels = SHELL_LABELS[locale]
    model = _navigation_model(site_root)
    topics = model["topics"]
    current = _current_navigation_topic(topics, page, site_root, locale)
    root_href = _relative_href(page, site_root / locale / "index.html")
    if not current:
        return f'            <li aria-current="page">{_escape(labels["navigation_root"])}</li>'
    guide_id, topic_id = current
    guide = topics[guide_id]
    topic = topics[topic_id]
    guide_anchor = next(
        anchor
        for candidate_guide_id, _filename, anchor, _url_root in GUIDE_MAPS
        if candidate_guide_id == guide_id
    )
    guide_href = f"{root_href}#{guide_anchor}"
    return "\n".join(
        [
            f'            <li><a href="{_escape(root_href)}">{_escape(labels["navigation_root"])}</a></li>',
            f'            <li><a href="{_escape(guide_href)}">{_escape(guide["title"][locale])}</a></li>',
            f'            <li aria-current="page">{_escape(topic["title"][locale])}</li>',
        ]
    )


def _guide_titles(filename: str) -> dict[str, str]:
    return {locale: _map_title(locale, filename) for locale in LOCALES}


def _source_revision() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "--verify", "HEAD"],
        cwd=REPOSITORY_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    revision = completed.stdout.strip()
    if completed.returncode or not re.fullmatch(r"[a-f0-9]{40}", revision):
        raise BuildError("cannot resolve 40-character source revision for documentation manifest")
    return revision


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _payload_sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _schema(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BuildError(f"cannot read documentation JSON schema {path}: {exc}") from exc


def _validate_schema(instance: dict[str, Any], schema_path: Path) -> None:
    try:
        jsonschema.Draft202012Validator(_schema(schema_path)).validate(instance)
    except jsonschema.ValidationError as exc:
        location = "/".join(str(part) for part in exc.absolute_path) or "<root>"
        raise BuildError(
            f"schema validation failed for {schema_path.name} at {location}: {exc.message}"
        ) from exc


def _read_json_file(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BuildError(f"cannot read documentation JSON {path}: {exc}") from exc


def _guide_topic_id(guide_id: str) -> str:
    return guide_id


def _guide_source_inventory(filename: str) -> str:
    return f"documentation/src/dita/en/maps/{filename}"


def _localized_map_keydefs(locale: str) -> dict[str, Path]:
    key_map = DOCUMENTATION_ROOT / f"src/dita/{locale}/maps/keys.ditamap"
    try:
        root = ET.parse(key_map).getroot()
    except (OSError, ET.ParseError) as exc:
        raise BuildError(f"cannot read localized key map {key_map}: {exc}") from exc
    keydefs: dict[str, Path] = {}
    for keydef in root.findall("keydef"):
        key = keydef.attrib.get("keys")
        href = keydef.attrib.get("href")
        if key and href:
            keydefs[key] = (key_map.parent / href).resolve()
    return keydefs


def _topicrefs(root: ET.Element) -> list[str]:
    keyrefs: list[str] = []
    for element in root.iter():
        if element.tag == "topicref":
            keyref = element.attrib.get("keyref")
            if keyref:
                keyrefs.append(keyref)
    return keyrefs


def _guide_topic_keyrefs(locale: str, filename: str) -> list[str]:
    source = DOCUMENTATION_ROOT / f"src/dita/{locale}/maps/{filename}"
    try:
        root = ET.parse(source).getroot()
    except (OSError, ET.ParseError) as exc:
        raise BuildError(f"cannot read localized guide map {source}: {exc}") from exc
    return _topicrefs(root)


def _localized_topic_roots(
    key: str, hrefs_by_locale: dict[str, dict[str, Path]]
) -> dict[str, ET.Element]:
    roots = {}
    for locale in LOCALES:
        try:
            path = hrefs_by_locale[locale][key]
        except KeyError as exc:
            raise BuildError(f"missing localized key {key!r} for {locale}") from exc
        try:
            roots[locale] = ET.parse(path).getroot()
        except (OSError, ET.ParseError) as exc:
            raise BuildError(f"cannot read localized topic {path}: {exc}") from exc
    return roots


def _element_text(element: ET.Element | None) -> str:
    if element is None:
        return ""
    return " ".join("".join(element.itertext()).split())


def _tag_name(element: ET.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def _unique_non_empty(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        normalized = " ".join(value.split())
        if normalized and normalized not in seen:
            unique.append(normalized)
            seen.add(normalized)
    return unique


def _search_normalization_aliases() -> dict[str, Any]:
    return _read_json_file(SEARCH_NORMALIZATION_ALIASES)


def _search_ranking_typo() -> dict[str, Any]:
    return _read_json_file(SEARCH_RANKING_TYPO)


def _search_facets_filters() -> dict[str, Any]:
    config = _read_json_file(SEARCH_FACETS_FILTERS)
    bpm_version = config.get("facet_fields", {}).get("bpm_version", {})
    if bpm_version.get("values") != [PRODUCT_VERSION_FACET_PLACEHOLDER]:
        raise BuildError("search BPM-version facet must derive from the product version")
    bpm_version["values"] = [_product_version()]
    return config


def _search_domain_ranking_facets() -> dict[str, Any]:
    config = _read_json_file(SEARCH_DOMAIN_RANKING_FACETS)
    if config.get("contract_id") != "bpm-doc-search-domain-ranking-facets-0.9.3":
        raise BuildError("unsupported search domain ranking/facets contract")
    return config


def _localized_search_facet_fields(
    locale: str,
    config: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    field_labels = SEARCH_FILTER_FIELD_LABELS[locale]
    value_labels = SEARCH_FILTER_VALUE_LABELS[locale]
    localized: dict[str, dict[str, Any]] = {}
    for field, definition in config["facet_fields"].items():
        field_value_labels = value_labels.get(field, {})
        localized[field] = {
            **definition,
            "label": field_labels[field],
            "value_labels": {
                str(value): field_value_labels.get(str(value), str(value))
                for value in definition["values"]
                if value is not None
            },
        }
    return localized


def _search_quality_performance() -> dict[str, Any]:
    return _read_json_file(SEARCH_QUALITY_PERFORMANCE)


def _search_integrity_drift() -> dict[str, Any]:
    return _read_json_file(SEARCH_INTEGRITY_DRIFT)


def _is_latin(character: str) -> bool:
    return "LATIN" in unicodedata.name(character, "")


def _strip_latin_diacritics(value: str) -> str:
    stripped: list[str] = []
    last_base_was_latin = False
    for character in unicodedata.normalize("NFKD", value):
        if unicodedata.combining(character):
            if not last_base_was_latin:
                stripped.append(character)
            continue
        stripped.append(character)
        last_base_was_latin = _is_latin(character)
    return unicodedata.normalize("NFC", "".join(stripped))


def _is_cjk(character: str) -> bool:
    codepoint = ord(character)
    return (
        0x3400 <= codepoint <= 0x4DBF
        or 0x4E00 <= codepoint <= 0x9FFF
        or 0xF900 <= codepoint <= 0xFAFF
    )


def _cjk_expansions(token: str) -> list[str]:
    cjk_run = "".join(character for character in token if _is_cjk(character))
    if not cjk_run:
        return []
    expansions = [cjk_run]
    expansions.extend(cjk_run[index : index + 1] for index in range(len(cjk_run)))
    expansions.extend(cjk_run[index : index + 2] for index in range(len(cjk_run) - 1))
    return expansions


def _normalize_search_text(
    locale: str, text: str, config: dict[str, Any] | None = None
) -> list[str]:
    if locale not in LOCALES:
        raise BuildError(f"unsupported search locale: {locale}")
    rules = (config or _search_normalization_aliases())["normalization"]
    normalized = unicodedata.normalize(rules["unicode_form"], text).casefold()
    if rules["strip_diacritics"]:
        normalized = _strip_latin_diacritics(normalized)
    tokens: list[str] = []
    compound_parts: list[str] = []
    for match in SEARCH_TOKEN_PATTERN.finditer(normalized):
        token = match.group(0).strip(".,;!?()[]{}<>\"'")
        if not token:
            continue
        tokens.append(token)
        tokens.extend(_cjk_expansions(token))
        if token.isalnum() and not any(_is_cjk(character) for character in token):
            compound_parts.append(token)
    tokens.extend(
        f"{left}-{right}" for left, right in zip(compound_parts, compound_parts[1:], strict=False)
    )
    return _unique_non_empty(tokens)


def _normalize_search_values(
    locale: str,
    values: list[str],
    config: dict[str, Any],
) -> list[str]:
    tokens: list[str] = []
    for value in values:
        tokens.extend(_normalize_search_text(locale, value, config))
    return _unique_non_empty(tokens)


def _alias_terms_for_locale(alias_group: dict[str, Any], locale: str) -> list[str]:
    return [
        *alias_group["terms"][locale],
        *alias_group.get("technical_identifiers", []),
    ]


def _search_alias_groups_for_document(
    locale: str,
    topic_id: str,
    identifiers: set[str],
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    matched = []
    for alias_group in config["alias_groups"]:
        target_topics = set(alias_group.get("target_topic_ids", []))
        target_ids = set(alias_group.get("target_ids", []))
        technical_identifiers = set(alias_group.get("technical_identifiers", []))
        if topic_id in target_topics or identifiers & (target_ids | technical_identifiers):
            match_sources = []
            if topic_id in target_topics:
                match_sources.append("target_topic")
            if identifiers & target_ids:
                match_sources.append("target_id")
            if identifiers & technical_identifiers:
                match_sources.append("technical_identifier")
            matched.append(
                {
                    "alias_id": alias_group["alias_id"],
                    "match_sources": match_sources,
                    "terms": _alias_terms_for_locale(alias_group, locale),
                }
            )
    return matched


def _resolve_search_query_aliases(
    locale: str,
    query: str,
    config: dict[str, Any] | None = None,
) -> list[str]:
    alias_config = config or _search_normalization_aliases()
    query_tokens = set(_normalize_search_text(locale, query, alias_config))
    matched_aliases: list[str] = []
    for alias_group in alias_config["alias_groups"]:
        for term in _alias_terms_for_locale(alias_group, locale):
            term_tokens = set(_normalize_search_text(locale, term, alias_config))
            if term_tokens and term_tokens <= query_tokens:
                matched_aliases.append(alias_group["alias_id"])
                break
    return sorted(set(matched_aliases))


def _query_fixtures_for_locale(locale: str, config: dict[str, Any]) -> list[dict[str, Any]]:
    return [fixture for fixture in config["query_fixtures"] if fixture["locale"] == locale]


def _ranking_fixtures_for_locale(locale: str, config: dict[str, Any]) -> list[dict[str, Any]]:
    return [fixture for fixture in config["ranking_fixtures"] if fixture["locale"] == locale]


def _max_typo_distance(token: str, ranking_config: dict[str, Any]) -> int:
    tolerance = ranking_config["typo_tolerance"]
    length = len(token)
    if length < tolerance["min_token_length"] or length > tolerance["max_token_length"]:
        return 0
    for rule in tolerance["max_distance_by_length"]:
        if rule["min_length"] <= length <= rule["max_length"]:
            return rule["max_distance"]
    return 0


def _is_typo_excluded(token: str, ranking_config: dict[str, Any]) -> bool:
    return any(
        re.fullmatch(pattern, token, flags=re.IGNORECASE)
        for pattern in ranking_config["typo_tolerance"]["excluded_token_patterns"]
    )


def _bounded_levenshtein(left: str, right: str, limit: int) -> int | None:
    if abs(len(left) - len(right)) > limit:
        return None
    previous = list(range(len(right) + 1))
    for left_index, left_character in enumerate(left, start=1):
        current = [left_index]
        row_min = current[0]
        for right_index, right_character in enumerate(right, start=1):
            substitution = previous[right_index - 1] + (left_character != right_character)
            insertion = current[right_index - 1] + 1
            deletion = previous[right_index] + 1
            value = min(substitution, insertion, deletion)
            current.append(value)
            row_min = min(row_min, value)
        if row_min > limit:
            return None
        previous = current
    distance = previous[-1]
    return distance if distance <= limit else None


def _bounded_typo_matches(
    query_tokens: list[str],
    document: dict[str, Any],
    ranking_config: dict[str, Any],
) -> list[dict[str, Any]]:
    fields = document["normalized"]["fields"]
    exact_pool = {token for field_tokens in fields.values() for token in field_tokens}
    matches: list[dict[str, Any]] = []
    for query_token in query_tokens:
        if query_token in exact_pool or _is_typo_excluded(query_token, ranking_config):
            continue
        limit = _max_typo_distance(query_token, ranking_config)
        if not limit:
            continue
        best: dict[str, Any] | None = None
        for field in ranking_config["typo_tolerance"]["fields"]:
            for candidate in fields.get(field, []):
                if candidate == query_token or _is_typo_excluded(candidate, ranking_config):
                    continue
                distance = _bounded_levenshtein(query_token, candidate, limit)
                if distance is None:
                    continue
                match = {
                    "query_token": query_token,
                    "matched_token": candidate,
                    "field": field,
                    "distance": distance,
                }
                if best is None or (distance, field, candidate) < (
                    best["distance"],
                    best["field"],
                    best["matched_token"],
                ):
                    best = match
        if best is not None:
            matches.append(best)
    return matches


def _score_search_document(
    locale: str,
    query: str,
    document: dict[str, Any],
    alias_config: dict[str, Any] | None = None,
    ranking_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalizer = alias_config or _search_normalization_aliases()
    ranking = ranking_config or _search_ranking_typo()
    weights = ranking["weights"]
    query_tokens = _normalize_search_text(locale, query, normalizer)
    query_token_set = set(query_tokens)
    normalized_fields = document["normalized"]["fields"]
    query_alias_ids = set(_resolve_search_query_aliases(locale, query, normalizer))
    document_alias_ids = set(document["normalized"]["alias_ids"])
    unmatched_technical_identifier = any(
        _is_typo_excluded(token, ranking) and token not in normalized_fields["identifiers"]
        for token in query_tokens
    )
    if unmatched_technical_identifier:
        return {
            "score": 0,
            "score_breakdown": {
                "exact_identifier": 0,
                "title": 0,
                "alias": 0,
                "heading": 0,
                "body": 0,
                "bounded_typo": 0,
                "recency": 0,
            },
            "matched_fields": [],
            "matches": {},
        }

    meaningful_query_tokens = {
        token for token in query_token_set if len(token) > 1 or not _is_cjk(token)
    }
    exact_identifier_matches = sorted(
        meaningful_query_tokens & set(normalized_fields["identifiers"])
    )
    title_matches = sorted(meaningful_query_tokens & set(normalized_fields["title"]))
    alias_token_matches = sorted(meaningful_query_tokens & set(normalized_fields["aliases"]))
    alias_id_matches = sorted(query_alias_ids & document_alias_ids)
    direct_alias_matches = sorted(
        alias_id
        for alias_id in alias_id_matches
        if "target_topic" in document["normalized"].get("alias_match_sources", {}).get(alias_id, [])
    )
    heading_matches = sorted(meaningful_query_tokens & set(normalized_fields["headings"]))
    body_matches = sorted(meaningful_query_tokens & set(normalized_fields["body"]))
    typo_matches = _bounded_typo_matches(query_tokens, document, ranking)

    components = {
        "exact_identifier": len(exact_identifier_matches) * weights["exact_identifier"],
        "title": len(title_matches) * weights["title"],
        "alias": (
            (len(alias_token_matches) + len(alias_id_matches) + len(direct_alias_matches))
            * weights["alias"]
        ),
        "heading": len(heading_matches) * weights["heading"],
        "body": len(body_matches) * weights["body"],
        "bounded_typo": len(typo_matches) * weights["bounded_typo"],
        "recency": weights["recency"],
    }
    score = sum(components.values())
    return {
        "score": score,
        "score_breakdown": components,
        "matched_fields": [
            field
            for field in ("exact_identifier", "title", "alias", "heading", "body", "bounded_typo")
            if components[field] > 0
        ],
        "matches": {
            "exact_identifier": exact_identifier_matches,
            "title": title_matches,
            "alias": sorted({*alias_token_matches, *alias_id_matches, *direct_alias_matches}),
            "heading": heading_matches,
            "body": body_matches,
            "bounded_typo": typo_matches,
        },
    }


def _rank_search_documents(
    locale: str,
    query: str,
    documents: list[dict[str, Any]],
    alias_config: dict[str, Any] | None = None,
    ranking_config: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    ranking = ranking_config or _search_ranking_typo()
    scored = []
    for document in documents:
        score = _score_search_document(locale, query, document, alias_config, ranking)
        if score["score"] > 0:
            scored.append({**score, "document": document})
    return sorted(
        scored,
        key=lambda result: (
            -result["score"],
            -result["score_breakdown"]["exact_identifier"],
            -result["score_breakdown"]["title"],
            -result["score_breakdown"]["alias"],
            result["document"]["guide_id"],
            result["document"]["topic_id"],
        ),
    )


def _ranking_fixture_results(
    locale: str,
    documents: list[dict[str, Any]],
    alias_config: dict[str, Any],
    ranking_config: dict[str, Any],
) -> list[dict[str, Any]]:
    results = []
    for fixture in _ranking_fixtures_for_locale(locale, ranking_config):
        ranked = _rank_search_documents(
            locale, fixture["query"], documents, alias_config, ranking_config
        )
        top = ranked[0] if ranked else None
        results.append(
            {
                "fixture_id": fixture["fixture_id"],
                "query": fixture["query"],
                "expected_top_topic_id": fixture["expected_top_topic_id"],
                "top_topic_id": top["document"]["topic_id"] if top else None,
                "score": top["score"] if top else 0,
                "score_breakdown": top["score_breakdown"] if top else {},
                "matched_fields": top["matched_fields"] if top else [],
            }
        )
    return results


def _topic_kind(root: ET.Element) -> str:
    if root.tag in {"concept", "task", "reference"}:
        return root.tag
    if root.tag == "troubleshooting":
        return "troubleshooting"
    raise BuildError(f"unsupported publishable DITA topic type: {root.tag}")


def _topic_anchor_titles(roots: dict[str, ET.Element]) -> dict[str, dict[str, Any]]:
    anchor_ids: set[str] = set()
    titles_by_locale: dict[str, dict[str, str]] = {}
    for locale, root in roots.items():
        titles_by_locale[locale] = {}
        for element in root.iter():
            anchor_id = element.attrib.get("id")
            if not anchor_id or not re.fullmatch(r"a-[a-z0-9]+(?:-[a-z0-9]+)*", anchor_id):
                continue
            title = _element_text(element.find("title"))
            anchor_ids.add(anchor_id)
            titles_by_locale[locale][anchor_id] = title or anchor_id

    anchors = {}
    for anchor_id in sorted(anchor_ids):
        anchors[anchor_id] = {
            "title": {
                locale: titles_by_locale[locale].get(anchor_id, anchor_id) for locale in LOCALES
            },
            "aliases": [],
        }
    return anchors


def _topic_shortdesc(root: ET.Element | None) -> str:
    if root is None:
        return ""
    for child in root:
        if _tag_name(child) == "shortdesc":
            return _element_text(child)
    return ""


def _topic_headings(root: ET.Element | None, root_title: str) -> list[str]:
    if root is None:
        return []
    return _unique_non_empty(
        [
            _element_text(element)
            for element in root.iter()
            if _tag_name(element) == "title" and _element_text(element) != root_title
        ]
    )


def _topic_keywords(root: ET.Element | None) -> list[str]:
    if root is None:
        return []
    return _unique_non_empty(
        [
            _element_text(element)
            for element in root.iter()
            if _tag_name(element) in {"keyword", "indexterm"}
        ]
    )


def _topic_body(root: ET.Element | None, fallback: str) -> str:
    if root is None:
        return fallback
    return _element_text(root)


def _target_identifiers_by_topic(target_map: dict[str, Any]) -> dict[str, dict[str, list[str]]]:
    by_topic: dict[str, dict[str, list[str]]] = {}
    field_by_kind = {
        "policy": "policy_ids",
        "cis": "cis_recommendation_ids",
        "api-operation": "api_operation_ids",
        "capability": "capability_ids",
        "topic": "target_topic_ids",
    }
    for target_id, target in sorted(target_map["targets"].items()):
        topic_id = target["topic_id"]
        kind = target["kind"]
        topic_identifiers = by_topic.setdefault(
            topic_id,
            {
                "target_ids": [],
                "target_topic_ids": [],
                "policy_ids": [],
                "cis_recommendation_ids": [],
                "api_operation_ids": [],
                "capability_ids": [],
            },
        )
        topic_identifiers["target_ids"].append(target_id)
        field = field_by_kind.get(kind)
        if field:
            topic_identifiers[field].append(target["source_id"])
    return {
        topic_id: {field: sorted(set(values)) for field, values in identifiers.items()}
        for topic_id, identifiers in by_topic.items()
    }


def _api_operation_area(operation_id: str) -> str:
    if operation_id.startswith("API-SVC-"):
        return "service"
    if operation_id.startswith("API-HEALTH-"):
        return "health"
    if operation_id.startswith("API-PROFILE-"):
        return "profiles"
    if operation_id.startswith("API-VAL-"):
        return "validation"
    if operation_id.startswith("API-FF-"):
        return "import-export"
    if operation_id.startswith("WEB-"):
        return "ui"
    raise BuildError(f"cannot derive API documentation area from operation ID: {operation_id}")


def _policy_facet_metadata() -> dict[str, dict[str, list[str]]]:
    inventory = _read_json_file(FIREFOX_POLICY_INVENTORY)
    index = _read_json_file(FIREFOX_POLICY_INDEX)
    metadata: dict[str, dict[str, set[str]]] = {}
    for policy in index["policies"]:
        policy_id = policy["policy_id"]
        fields = metadata.setdefault(
            policy_id, {"firefox_channel": set(), "policy_category": set()}
        )
        channel_support = policy.get("channel_support", {})
        fields["firefox_channel"].update(channel_support.get("supported_channels", []))

    for policy in inventory["policies"]:
        policy_id = policy["policy_id"]
        fields = metadata.setdefault(
            policy_id, {"firefox_channel": set(), "policy_category": set()}
        )
        for channel_id, channel in policy.get("channels", {}).items():
            fields["firefox_channel"].add(channel_id)
            ui = channel.get("ui", {})
            if ui.get("section"):
                fields["policy_category"].add(ui["section"])
            fields["policy_category"].update(channel.get("categories", []))

    return {
        policy_id: {field: sorted(values) for field, values in fields.items()}
        for policy_id, fields in metadata.items()
    }


def _cis_facet_metadata() -> dict[str, dict[str, list[str]]]:
    inventory = _read_json_file(CIS_INVENTORY)
    index = _read_json_file(CIS_RECOMMENDATION_INDEX)
    metadata: dict[str, dict[str, set[str]]] = {}
    for topic in index["topics"]:
        recommendation_id = topic["recommendation_id"]
        fields = metadata.setdefault(
            recommendation_id, {"cis_level": set(), "cis_control_state": set()}
        )
        if topic.get("level"):
            fields["cis_level"].add(f"level-{topic['level']}")
        if topic.get("mapping_status"):
            fields["cis_control_state"].add(topic["mapping_status"])

    for record in index.get("provenance_only_records", []):
        recommendation_id = record["recommendation_id"]
        fields = metadata.setdefault(
            recommendation_id, {"cis_level": set(), "cis_control_state": set()}
        )
        if record.get("level"):
            fields["cis_level"].add(f"level-{record['level']}")
        fields["cis_control_state"].add("provenance-only")

    for recommendation in inventory["recommendations"]:
        recommendation_id = recommendation["recommendation_id"]
        fields = metadata.setdefault(
            recommendation_id, {"cis_level": set(), "cis_control_state": set()}
        )
        if recommendation.get("level"):
            fields["cis_level"].add(f"level-{recommendation['level']}")
        if recommendation.get("mapping_status"):
            fields["cis_control_state"].add(recommendation["mapping_status"])
        if recommendation.get("assessment") == "manual":
            fields["cis_control_state"].add("manual-review")

    return {
        recommendation_id: {field: sorted(values) for field, values in fields.items()}
        for recommendation_id, fields in metadata.items()
    }


def _facet_values_from_config(config: dict[str, Any], field: str) -> set[str]:
    return {value for value in config["facet_fields"][field]["values"] if value is not None}


def _target_facets_by_topic(
    target_map: dict[str, Any], config: dict[str, Any]
) -> dict[str, dict[str, list[str]]]:
    policy_metadata = _policy_facet_metadata()
    cis_metadata = _cis_facet_metadata()
    allowed_values = {
        field: _facet_values_from_config(config, field) for field in config["facet_fields"]
    }
    by_topic: dict[str, dict[str, set[str]]] = {}
    for target in target_map["targets"].values():
        topic_id = target["topic_id"]
        fields = by_topic.setdefault(
            topic_id,
            {
                "firefox_channel": set(),
                "policy_category": set(),
                "cis_level": set(),
                "cis_control_state": set(),
                "api_area": set(),
            },
        )
        kind = target["kind"]
        source_id = target["source_id"]
        if kind == "policy":
            policy_fields = policy_metadata.get(source_id, {})
            fields["firefox_channel"].update(policy_fields.get("firefox_channel", []))
            fields["policy_category"].update(policy_fields.get("policy_category", []))
        elif kind == "cis":
            cis_fields = cis_metadata.get(source_id, {})
            fields["cis_level"].update(cis_fields.get("cis_level", []))
            fields["cis_control_state"].update(cis_fields.get("cis_control_state", []))
        elif kind == "api-operation":
            fields["api_area"].add(_api_operation_area(source_id))

    clean: dict[str, dict[str, list[str]]] = {}
    for topic_id, fields in by_topic.items():
        clean[topic_id] = {}
        for field, values in fields.items():
            unknown = values - allowed_values[field]
            if unknown:
                raise BuildError(
                    f"search facet values are not declared for {topic_id}/{field}: {sorted(unknown)}"
                )
            clean[topic_id][field] = sorted(values)
    return clean


def _document_filter_facets(document: dict[str, Any]) -> dict[str, list[str]]:
    filter_facets = document.get("filter_facets", {})
    if isinstance(filter_facets, dict):
        return {
            field: sorted(str(value) for value in values)
            for field, values in filter_facets.items()
            if isinstance(values, list)
        }
    facets = document.get("facets", {})
    values: dict[str, list[str]] = {}
    for field, value in facets.items():
        if value is None:
            values[field] = []
        elif isinstance(value, list):
            values[field] = sorted(str(item) for item in value)
        else:
            values[field] = [str(value)]
    return values


def _facet_counts(
    documents: list[dict[str, Any]], config: dict[str, Any]
) -> dict[str, dict[str, int]]:
    counts = {
        field: {str(value): 0 for value in definition["values"] if value is not None}
        for field, definition in config["facet_fields"].items()
    }
    for document in documents:
        filter_facets = _document_filter_facets(document)
        for field in counts:
            for value in set(filter_facets.get(field, [])):
                if value in counts[field]:
                    counts[field][value] += 1
    return counts


def _filter_search_documents(
    documents: list[dict[str, Any]],
    filters: dict[str, list[str]],
) -> list[dict[str, Any]]:
    active_filters = {field: set(values) for field, values in filters.items() if values}
    if not active_filters:
        return documents
    filtered = []
    for document in documents:
        filter_facets = _document_filter_facets(document)
        if all(
            set(filter_facets.get(field, [])) & values for field, values in active_filters.items()
        ):
            filtered.append(document)
    return filtered


def _filter_url_query(filters: dict[str, list[str]], config: dict[str, Any]) -> str:
    parameters = config["url_state"]["parameters"]
    pairs: list[tuple[str, str]] = []
    for field in sorted(filters):
        parameter = parameters[field]
        for value in sorted(filters[field]):
            pairs.append((parameter, value))
    return urllib.parse.urlencode(pairs)


def _filter_fixture_results(
    locale: str,
    documents: list[dict[str, Any]],
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    results = []
    for fixture in config["filter_fixtures"]:
        if fixture["locale"] != locale:
            continue
        filters = {field: sorted(values) for field, values in fixture["filters"].items()}
        filtered = _filter_search_documents(documents, filters)
        results.append(
            {
                "fixture_id": fixture["fixture_id"],
                "locale": locale,
                "filters": filters,
                "url_query": _filter_url_query(filters, config),
                "result_count": len(filtered),
                "result_topic_ids": [document["topic_id"] for document in filtered],
                "empty_result_message": (
                    config["empty_result"]["messages"][locale] if not filtered else None
                ),
            }
        )
    return results


def _quality_fixtures_for_locale(locale: str, config: dict[str, Any]) -> list[dict[str, Any]]:
    return [fixture for fixture in config["quality_fixtures"] if fixture["locale"] == locale]


def _quality_fixture_results(
    locale: str,
    documents: list[dict[str, Any]],
    alias_config: dict[str, Any],
    ranking_config: dict[str, Any],
    quality_config: dict[str, Any],
) -> list[dict[str, Any]]:
    visible_limit = quality_config["performance_budget"]["max_visible_results_per_query"]
    results = []
    for fixture in _quality_fixtures_for_locale(locale, quality_config):
        filters = {field: sorted(values) for field, values in fixture.get("filters", {}).items()}
        filtered_documents = _filter_search_documents(documents, filters)
        ranked = _rank_search_documents(
            locale,
            fixture["query"],
            filtered_documents,
            alias_config,
            ranking_config,
        )
        visible_ranked = ranked[:visible_limit]
        top = ranked[0] if ranked else None
        required_component = fixture.get("required_score_component")
        results.append(
            {
                "fixture_id": fixture["fixture_id"],
                "locale": locale,
                "category": fixture["category"],
                "query": fixture["query"],
                "filters": filters,
                "expected_top_topic_id": fixture.get("expected_top_topic_id"),
                "top_topic_id": top["document"]["topic_id"] if top else None,
                "expected_count": fixture.get("expected_count"),
                "result_count": len(ranked),
                "visible_result_count": len(visible_ranked),
                "top_topic_ids": [result["document"]["topic_id"] for result in visible_ranked[:5]],
                "required_score_component": required_component,
                "required_score_component_value": (
                    top["score_breakdown"].get(required_component, 0)
                    if top and required_component
                    else 0
                ),
                "top_score": top["score"] if top else 0,
                "top_score_breakdown": top["score_breakdown"] if top else {},
                "matched_fields": top["matched_fields"] if top else [],
            }
        )
    return results


def _quality_performance_report(
    documents: list[dict[str, Any]],
    fixture_results: list[dict[str, Any]],
    quality_config: dict[str, Any],
) -> dict[str, Any]:
    budget = quality_config["performance_budget"]
    return {
        "latency_budget_proxy": budget["latency_budget_proxy"],
        "document_count": len(documents),
        "quality_fixture_count": len(fixture_results),
        "deterministic_scan_units": len(documents) * len(fixture_results),
        "max_visible_results_per_query": budget["max_visible_results_per_query"],
        "max_observed_visible_results": max(
            (result["visible_result_count"] for result in fixture_results),
            default=0,
        ),
        "budget": budget,
    }


def _validate_quality_fixture_coverage(config: dict[str, Any]) -> None:
    coverage = config["coverage_requirements"]
    if coverage["locales"] != list(LOCALES):
        raise BuildError("search quality fixture locale matrix mismatch")
    categories = set(coverage["categories"])
    fixture_categories = {fixture["category"] for fixture in config["quality_fixtures"]}
    if not categories <= fixture_categories:
        raise BuildError("search quality fixture categories are incomplete")
    common_categories = categories - {"cjk"}
    cjk_required_locales = set(coverage["cjk_required_locales"])
    for locale in LOCALES:
        locale_categories = {
            fixture["category"]
            for fixture in config["quality_fixtures"]
            if fixture["locale"] == locale
        }
        if (
            len(_quality_fixtures_for_locale(locale, config))
            < coverage["minimum_locale_fixture_count"]
        ):
            raise BuildError(f"search quality fixture count is too low for {locale}")
        if not common_categories <= locale_categories:
            raise BuildError(f"search quality fixture categories are incomplete for {locale}")
        if locale in cjk_required_locales and "cjk" not in locale_categories:
            raise BuildError(f"search quality CJK fixture is missing for {locale}")


def _duplicates(values: list[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return sorted(duplicates)


def _contains_control_character(value: str) -> bool:
    return any(ord(character) < 32 and character not in "\n\r\t" for character in value)


def _snippet_source(document: dict[str, Any], config: dict[str, Any]) -> str:
    searchable = document.get("searchable", {})
    for field in config["snippet_integrity"]["source_fields"]:
        value = searchable.get(field, "")
        if isinstance(value, list):
            value = " ".join(str(item) for item in value)
        value = str(value)
        if value.strip():
            return value
    return ""


def _inventory_gap_report(
    expected_source_ids: set[str],
    target_source_ids: set[str],
) -> dict[str, Any]:
    return {
        "inventory_count": len(expected_source_ids),
        "target_count": len(target_source_ids),
        "missing_source_ids": sorted(expected_source_ids - target_source_ids),
        "extra_source_ids": sorted(target_source_ids - expected_source_ids),
    }


def _search_integrity_report(
    locale: str,
    documents: list[dict[str, Any]],
    topics: dict[str, dict[str, Any]],
    target_map: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    topic_ids = set(topics)
    document_topic_ids = {str(document.get("topic_id", "")) for document in documents}
    document_ids = [str(document.get("document_id", "")) for document in documents]

    wrong_locale_document_ids: list[str] = []
    wrong_url_document_ids: list[str] = []
    wrong_output_document_ids: list[str] = []
    broken_snippet_document_ids: list[str] = []
    control_character_document_ids: list[str] = []
    for document in documents:
        document_id = str(document.get("document_id", ""))
        topic_id = document.get("topic_id")
        topic = topics.get(str(topic_id), {})
        expected_output = topic.get("output", {}).get(locale)
        if document.get("locale") != locale:
            wrong_locale_document_ids.append(document_id)
        if not str(document.get("url", "")).startswith(f"/help/{locale}/"):
            wrong_url_document_ids.append(document_id)
        if expected_output and document.get("source", {}).get("output_path") != expected_output:
            wrong_output_document_ids.append(document_id)
        snippet_source = _snippet_source(document, config)
        if not snippet_source:
            broken_snippet_document_ids.append(document_id)
        searchable_values = [
            value
            for value in document.get("searchable", {}).values()
            for value in (value if isinstance(value, list) else [value])
        ]
        if any(
            _contains_control_character(str(value))
            for value in [snippet_source, *searchable_values]
        ):
            control_character_document_ids.append(document_id)

    stale_target_anchors = []
    target_topic_mismatches = []
    for target_id, target in sorted(target_map["targets"].items()):
        topic_id = target["topic_id"]
        topic = topics.get(topic_id)
        if topic is None:
            target_topic_mismatches.append(target_id)
            continue
        anchor_id = target.get("anchor_id")
        if anchor_id and anchor_id not in topic["anchors"]:
            stale_target_anchors.append(
                {
                    "target_id": target_id,
                    "topic_id": topic_id,
                    "anchor_id": anchor_id,
                }
            )

    source_ids_by_kind: dict[str, set[str]] = {
        "policy": set(),
        "cis": set(),
        "api-operation": set(),
    }
    for target in target_map["targets"].values():
        kind = target["kind"]
        if kind in source_ids_by_kind:
            source_ids_by_kind[kind].add(target["source_id"])

    inventory_gap_integrity = {
        "firefox_policy": _inventory_gap_report(_policy_ids(), source_ids_by_kind["policy"]),
        "cis": _inventory_gap_report(_cis_recommendation_ids(), source_ids_by_kind["cis"]),
        "api": _inventory_gap_report(
            set(_api_operation_topic_ids()), source_ids_by_kind["api-operation"]
        ),
    }

    document_integrity = {
        "missing_topic_ids": sorted(topic_ids - document_topic_ids),
        "extra_topic_ids": sorted(document_topic_ids - topic_ids),
        "duplicate_document_ids": _duplicates(document_ids),
        "wrong_locale_document_ids": sorted(wrong_locale_document_ids),
        "wrong_url_document_ids": sorted(wrong_url_document_ids),
        "wrong_output_document_ids": sorted(wrong_output_document_ids),
    }
    anchor_integrity = {
        "stale_target_anchors": stale_target_anchors,
        "target_topic_mismatches": sorted(target_topic_mismatches),
    }
    snippet_integrity = {
        "broken_snippet_document_ids": sorted(broken_snippet_document_ids),
        "control_character_document_ids": sorted(control_character_document_ids),
        "max_snippet_characters": config["snippet_integrity"]["max_characters"],
        "source_fields": config["snippet_integrity"]["source_fields"],
    }

    failure_count = (
        sum(len(values) for values in document_integrity.values())
        + len(anchor_integrity["stale_target_anchors"])
        + len(anchor_integrity["target_topic_mismatches"])
        + len(snippet_integrity["broken_snippet_document_ids"])
        + len(snippet_integrity["control_character_document_ids"])
        + sum(
            len(report["missing_source_ids"]) + len(report["extra_source_ids"])
            for report in inventory_gap_integrity.values()
        )
    )

    return {
        "schema_version": config["schema_version"],
        "contract_id": config["contract_id"],
        "locale": locale,
        "status": "pass" if failure_count == 0 else "fail",
        "failure_count": failure_count,
        "check_categories": config["check_categories"],
        "counts": {
            "manifest_topics": len(topics),
            "search_documents": len(documents),
            "target_map_targets": len(target_map["targets"]),
            "firefox_policy_inventory": len(_policy_ids()),
            "cis_inventory": len(_cis_recommendation_ids()),
            "api_inventory": len(_api_operation_topic_ids()),
        },
        "document_integrity": document_integrity,
        "anchor_integrity": anchor_integrity,
        "snippet_integrity": snippet_integrity,
        "inventory_gap_integrity": inventory_gap_integrity,
    }


def _topic_search_document(
    locale: str,
    topic_id: str,
    topic: dict[str, Any],
    identifiers_by_topic: dict[str, dict[str, list[str]]],
    facets_by_topic: dict[str, dict[str, list[str]]],
    source_revision: str,
    alias_config: dict[str, Any],
    product_version: str,
) -> dict[str, Any]:
    root = topic.get("_roots", {}).get(locale)
    title = topic["title"][locale]
    output_path = topic["output"][locale]
    identifier_groups = identifiers_by_topic.get(topic_id, {})
    anchor_ids = sorted(topic["anchors"])
    identifiers = sorted(
        {
            topic_id,
            topic["guide_id"],
            topic["dita_key"],
            *anchor_ids,
            *identifier_groups.get("target_ids", []),
            *identifier_groups.get("target_topic_ids", []),
            *identifier_groups.get("policy_ids", []),
            *identifier_groups.get("cis_recommendation_ids", []),
            *identifier_groups.get("api_operation_ids", []),
            *identifier_groups.get("capability_ids", []),
        }
    )
    identifier_set = set(identifiers)
    document_alias_groups = _search_alias_groups_for_document(
        locale,
        topic_id,
        identifier_set,
        alias_config,
    )
    aliases = sorted(
        {alias for anchor in topic["anchors"].values() for alias in anchor.get("aliases", [])}
        | {alias for alias_group in document_alias_groups for alias in alias_group["terms"]}
    )
    searchable = {
        "title": title,
        "shortdesc": _topic_shortdesc(root),
        "headings": (
            _topic_headings(root, title)
            or [topic["anchors"][anchor_id]["title"][locale] for anchor_id in anchor_ids]
        ),
        "body": _topic_body(root, title),
        "keywords": _topic_keywords(root),
        "identifiers": identifiers,
        "aliases": aliases,
    }
    normalized_fields = {
        field: _normalize_search_values(
            locale,
            value if isinstance(value, list) else [value],
            alias_config,
        )
        for field, value in searchable.items()
    }
    target_facets = facets_by_topic.get(topic_id, {})
    filter_facets = {
        "locale": [locale],
        "guide_id": [topic["guide_id"]],
        "topic_kind": [topic["kind"]],
        "firefox_channel": target_facets.get("firefox_channel", []),
        "policy_category": target_facets.get("policy_category", []),
        "cis_level": target_facets.get("cis_level", []),
        "cis_control_state": target_facets.get("cis_control_state", []),
        "api_area": target_facets.get("api_area", []),
        "bpm_version": [product_version],
    }
    return {
        "document_id": f"{locale}:{topic_id}",
        "locale": locale,
        "guide_id": topic["guide_id"],
        "topic_id": topic_id,
        "topic_kind": topic["kind"],
        "url": f"/help/{output_path}",
        "source": {
            "topic_id": topic_id,
            "anchor_id": None,
            "dita_key": topic["dita_key"],
            "source_slug": topic["source_slug"],
            "output_path": output_path,
        },
        "searchable": searchable,
        "normalized": {
            "alias_ids": sorted({group["alias_id"] for group in document_alias_groups}),
            "alias_match_sources": {
                group["alias_id"]: group["match_sources"] for group in document_alias_groups
            },
            "fields": normalized_fields,
        },
        "identifier_groups": identifier_groups,
        "facets": {
            "locale": locale,
            "guide_id": topic["guide_id"],
            "topic_kind": topic["kind"],
            "firefox_channel": filter_facets["firefox_channel"] or None,
            "policy_category": filter_facets["policy_category"] or None,
            "cis_level": filter_facets["cis_level"] or None,
            "cis_control_state": filter_facets["cis_control_state"] or None,
            "api_area": filter_facets["api_area"] or None,
            "bpm_version": product_version,
        },
        "filter_facets": filter_facets,
        "versions": {
            "bpm_version": product_version,
            "documentation_version": product_version,
            "source_revision": source_revision,
        },
    }


def _search_document(
    locale: str,
    topics: dict[str, dict[str, Any]],
    target_map: dict[str, Any],
) -> dict[str, Any]:
    contract = _read_json_file(SEARCH_CORPUS_CONTRACT)
    alias_config = _search_normalization_aliases()
    ranking_config = _search_ranking_typo()
    facets_config = _search_facets_filters()
    domain_ranking_config = _search_domain_ranking_facets()
    quality_config = _search_quality_performance()
    integrity_config = _search_integrity_drift()
    _validate_quality_fixture_coverage(quality_config)
    identifiers_by_topic = _target_identifiers_by_topic(target_map)
    facets_by_topic = _target_facets_by_topic(target_map, facets_config)
    source_revision = _source_revision()
    product_version = _product_version()
    documents = [
        _topic_search_document(
            locale,
            topic_id,
            topic,
            identifiers_by_topic,
            facets_by_topic,
            source_revision,
            alias_config,
            product_version,
        )
        for topic_id, topic in sorted(topics.items())
    ]
    locale_fixtures = _query_fixtures_for_locale(locale, alias_config)
    ranking_fixture_results = _ranking_fixture_results(
        locale,
        documents,
        alias_config,
        ranking_config,
    )
    filter_fixture_results = _filter_fixture_results(locale, documents, facets_config)
    quality_fixture_results = _quality_fixture_results(
        locale,
        documents,
        alias_config,
        ranking_config,
        quality_config,
    )
    integrity_report = _search_integrity_report(
        locale,
        documents,
        topics,
        target_map,
        integrity_config,
    )
    return {
        "schema_version": 1,
        "contract_id": contract["contract_id"],
        "contract_schema_version": contract["schema_version"],
        "normalization_contract_id": alias_config["contract_id"],
        "normalization_schema_version": alias_config["schema_version"],
        "ranking_contract_id": ranking_config["contract_id"],
        "ranking_schema_version": ranking_config["schema_version"],
        "facets_contract_id": facets_config["contract_id"],
        "facets_schema_version": facets_config["schema_version"],
        "domain_ranking_contract_id": domain_ranking_config["contract_id"],
        "domain_ranking_schema_version": domain_ranking_config["schema_version"],
        "quality_contract_id": quality_config["contract_id"],
        "quality_schema_version": quality_config["schema_version"],
        "integrity_contract_id": integrity_config["contract_id"],
        "integrity_schema_version": integrity_config["schema_version"],
        "result_schema_version": contract["result_schema"]["schema_version"],
        "target_bpm_version": product_version,
        "locale": locale,
        "format_version": 1,
        "generated_by": "documentation/tools/build_docs.py",
        "status": "ready",
        "index_kind": "dita-document-corpus-v1",
        "search_mode": contract["search_mode"],
        "non_ai_boundary": contract["non_ai_boundary"]["mode"],
        "allowlisted_cross_locale_fields": ["identifiers"],
        "normalization": {
            **alias_config["normalization"],
            "alias_groups": [
                {
                    "alias_id": alias_group["alias_id"],
                    "terms": _alias_terms_for_locale(alias_group, locale),
                }
                for alias_group in alias_config["alias_groups"]
            ],
            "alias_group_count": len(alias_config["alias_groups"]),
            "query_fixture_count": len(locale_fixtures),
        },
        "ranking": {
            "ranking_order": ranking_config["ranking_order"],
            "weights": ranking_config["weights"],
            "typo_tolerance": ranking_config["typo_tolerance"],
            "tie_breakers": ranking_config["tie_breakers"],
            "ranking_fixture_count": len(_ranking_fixtures_for_locale(locale, ranking_config)),
        },
        "filtering": {
            "facet_fields": _localized_search_facet_fields(locale, facets_config),
            "composition": facets_config["filter_contract"]["composition"],
            "url_state": facets_config["url_state"],
            "empty_result": facets_config["empty_result"]["messages"][locale],
            "filter_fixture_count": len(
                [
                    fixture
                    for fixture in facets_config["filter_fixtures"]
                    if fixture["locale"] == locale
                ]
            ),
        },
        "domain_ranking": {
            "preserved_sources": domain_ranking_config["ranking"]["preserved_sources"],
            "evidence_fields": domain_ranking_config["ranking"]["evidence_fields"],
            "preserved_facets": domain_ranking_config["facets"]["preserved_fields"],
            "maximum_evidence_rows": domain_ranking_config["adapter_projection"][
                "maximum_evidence_rows"
            ],
        },
        "quality": {
            "categories": quality_config["coverage_requirements"]["categories"],
            "fixture_count": len(_quality_fixtures_for_locale(locale, quality_config)),
            "thresholds": quality_config["quality_thresholds"],
        },
        "performance_report": _quality_performance_report(
            documents,
            quality_fixture_results,
            quality_config,
        ),
        "integrity_report": integrity_report,
        "facet_counts": _facet_counts(documents, facets_config),
        "query_fixtures": locale_fixtures,
        "ranking_fixture_results": ranking_fixture_results,
        "filter_fixture_results": filter_fixture_results,
        "quality_fixture_results": quality_fixture_results,
        "document_required_fields": contract["document_schema"]["required_fields"],
        "searchable_fields": [field["field"] for field in contract["corpus"]["searchable_fields"]],
        "result_required_fields": contract["result_schema"]["required_fields"],
        "documents": documents,
    }


def _policy_ids() -> set[str]:
    index = _read_json_file(FIREFOX_POLICY_INDEX)
    return {policy["policy_id"] for policy in index["policies"]}


def _managed_preference_ids() -> set[str]:
    inventory = _read_json_file(FIREFOX_POLICY_INVENTORY)
    return {preference["preference_id"] for preference in inventory["managed_preferences"]}


def _all_settings_help_target_contract() -> dict[str, Any]:
    contract = _read_json_file(ALL_SETTINGS_HELP_TARGET_MAP)
    if contract.get("schema_version") != 1:
        raise BuildError("unsupported All Settings help target map contract schema")
    if contract.get("target_bpm_version") != _product_version():
        raise BuildError("All Settings help target map contract has the wrong BPM version")
    return contract


def _validate_all_settings_help_target_coverage(targets: dict[str, dict[str, Any]]) -> None:
    expected_policy_targets = {f"policy:{policy_id}" for policy_id in _policy_ids()}
    expected_preference_targets = {
        f"known-preference:{preference_id}" for preference_id in _managed_preference_ids()
    }
    actual_policy_targets = {target_id for target_id in targets if target_id.startswith("policy:")}
    actual_preference_targets = {
        target_id for target_id in targets if target_id.startswith("known-preference:")
    }
    for kind, expected, actual in (
        ("policy", expected_policy_targets, actual_policy_targets),
        ("known preference", expected_preference_targets, actual_preference_targets),
    ):
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        if missing:
            raise BuildError(f"All Settings help target map is missing {kind} targets: {missing}")
        if extra:
            raise BuildError(f"All Settings help target map has unknown {kind} targets: {extra}")


def _cis_recommendation_ids() -> set[str]:
    index = _read_json_file(CIS_RECOMMENDATION_INDEX)
    topic_ids = {topic["recommendation_id"] for topic in index["topics"]}
    provenance_only_ids = {
        record["recommendation_id"] for record in index["provenance_only_records"]
    }
    return topic_ids | provenance_only_ids


def _api_operation_topic_ids() -> dict[str, str]:
    text = API_INVENTORY.read_text(encoding="utf-8")
    operations: dict[str, str] = {}
    for line in text.splitlines():
        if not line.startswith("| `API-"):
            continue
        parts = [part.strip() for part in line.strip("|").split("|")]
        if len(parts) >= 8:
            operations[parts[0].strip("`")] = parts[7].strip("`")
    return operations


def _capability_topic_ids() -> dict[str, str]:
    text = CAPABILITY_INVENTORY.read_text(encoding="utf-8")
    capabilities: dict[str, str] = {}
    for line in text.splitlines():
        if not line.startswith("| `CAP-"):
            continue
        parts = [part.strip() for part in line.strip("|").split("|")]
        if len(parts) >= 5:
            capabilities[parts[0].strip("`")] = parts[3].strip("`")
    return capabilities


def _policy_context_assignments(context: dict[str, Any] | None = None) -> dict[str, dict[str, Any]]:
    context = context or _read_json_file(FIREFOX_POLICY_CONTEXT_TARGETS)
    if context.get("schema_version") != 1:
        raise BuildError("unsupported Firefox policy context target schema")
    known_policy_ids = _policy_ids()
    known_api_operation_ids = set(_api_operation_topic_ids())
    known_capability_topics = set(_capability_topic_ids().values())
    assignments: dict[str, dict[str, Any]] = {}
    context_targets = [context["default_policy_target"], *context["family_targets"]]
    for target in context_targets:
        if target["topic_id"] not in known_capability_topics and not target["topic_id"].startswith(
            "fx-"
        ):
            raise BuildError(f"policy context references unknown user topic: {target['topic_id']}")
        validation_topic_id = target.get("validation_topic_id")
        if validation_topic_id and validation_topic_id not in known_capability_topics:
            raise BuildError(
                f"policy context references unknown validation topic: {validation_topic_id}"
            )
        for task_topic_id in target.get("user_task_topic_ids", []):
            if task_topic_id not in known_capability_topics:
                raise BuildError(
                    f"policy context references unknown user task topic: {task_topic_id}"
                )
        for operation_id in target.get("api_operation_ids", []):
            if operation_id not in known_api_operation_ids:
                raise BuildError(f"policy context references unknown API operation: {operation_id}")

    for family in context["family_targets"]:
        family_policy_ids = family.get("policy_ids", [])
        if not family_policy_ids:
            raise BuildError(f"policy context family has no policy IDs: {family.get('family_id')}")
        for policy_id in family_policy_ids:
            if policy_id not in known_policy_ids:
                raise BuildError(f"policy context references unknown policy: {policy_id}")
            if policy_id in assignments:
                raise BuildError(f"policy context assigns policy more than once: {policy_id}")
            assignments[policy_id] = family
        for related_policy_id in family.get("related_policy_ids", []):
            if related_policy_id not in known_policy_ids:
                raise BuildError(
                    f"policy context references unknown related policy: {related_policy_id}"
                )
    return assignments


def _target(
    topic_id: str, kind: str, source_id: str, source_inventory: str, anchor_id: str | None = None
) -> dict[str, Any]:
    target = {
        "kind": kind,
        "source_id": source_id,
        "source_inventory": source_inventory,
        "topic_id": topic_id,
    }
    if anchor_id:
        target["anchor_id"] = anchor_id
    return target


def _build_target_map(topics: dict[str, dict[str, Any]]) -> dict[str, Any]:
    targets = {}
    policy_context = _read_json_file(FIREFOX_POLICY_CONTEXT_TARGETS)
    help_target_contract = _all_settings_help_target_contract()
    policy_assignments = _policy_context_assignments(policy_context)
    default_policy_target = policy_context["default_policy_target"]

    for topic_id in sorted(topics):
        targets[f"topic:{topic_id}"] = _target(
            topic_id,
            "topic",
            topic_id,
            "documentation/src/dita",
        )

    for guide_id, filename, anchor, _url_root in GUIDE_MAPS:
        topic_id = _guide_topic_id(guide_id)
        if topic_id not in topics:
            raise BuildError(f"cannot create target for missing guide topic: {topic_id}")
        targets[f"topic:{topic_id}"] = _target(
            topic_id,
            "topic",
            topic_id,
            _guide_source_inventory(filename),
            anchor,
        )

    for policy_id in sorted(_policy_ids()):
        assignment = policy_assignments.get(policy_id, default_policy_target)
        targets[f"policy:{policy_id}"] = _target(
            assignment["topic_id"],
            "policy",
            policy_id,
            "documentation/config/firefox-policy-context-targets-0.9.0.json",
            assignment["anchor_id"],
        )

    preference_target = help_target_contract["known_preference_targets"]
    for preference_id in sorted(_managed_preference_ids()):
        targets[f"known-preference:{preference_id}"] = _target(
            preference_target["topic_id"],
            "known-preference",
            preference_id,
            help_target_contract["source_inventory"],
            preference_target["anchor_id"],
        )

    for recommendation_id in sorted(_cis_recommendation_ids()):
        targets[f"cis:{recommendation_id}"] = _target(
            "cis-settings-guide",
            "cis",
            recommendation_id,
            "docs/architecture/cis-documentation-inventory-0.9.0.json",
            "a-cis-settings-guide",
        )

    for operation_id, planned_topic_id in sorted(_api_operation_topic_ids().items()):
        if planned_topic_id not in topics:
            raise BuildError(
                "API operation target is missing its Administrator Guide topic: "
                f"{operation_id} -> {planned_topic_id}"
            )
        targets[f"api-operation:{operation_id}"] = _target(
            planned_topic_id,
            "api-operation",
            operation_id,
            "docs/architecture/api-documentation-inventory-0.9.0.md",
        )

    for capability_id, topic_id in sorted(_capability_topic_ids().items()):
        targets[f"capability:{capability_id}"] = _target(
            topic_id,
            "capability",
            capability_id,
            "docs/architecture/product-user-capability-inventory-0.9.0.md",
        )

    _validate_all_settings_help_target_coverage(targets)
    return {
        "$schema": "schemas/product-documentation-ui-target-map-v1.schema.json",
        "schema_version": 1,
        "manifest_schema_version": 1,
        "bpm_version": _product_version(),
        "locales": list(LOCALES),
        "targets": targets,
    }


def _build_topics(site_root: Path) -> dict[str, dict[str, Any]]:
    topics: dict[str, dict[str, Any]] = {}
    hrefs_by_locale = {locale: _localized_map_keydefs(locale) for locale in LOCALES}
    for guide_id, filename, anchor, url_root in GUIDE_MAPS:
        title = _guide_titles(filename)
        topic_id = _guide_topic_id(guide_id)
        output = {}
        for locale in LOCALES:
            page = site_root / locale / "index.html"
            if not page.is_file():
                raise BuildError(f"missing guide landing output for {locale}: {page}")
            output[locale] = page.relative_to(site_root).as_posix()
        topics[topic_id] = {
            "guide_id": guide_id,
            "dita_key": f"topic.{topic_id}",
            "source_slug": guide_id,
            "url_path": "home",
            "kind": "landing",
            "title": title,
            "anchors": {
                anchor: {
                    "title": title,
                    "aliases": [],
                }
            },
            "output": output,
            "_url_root": url_root,
        }

        keyrefs = _guide_topic_keyrefs("en", filename)
        for keyref in keyrefs:
            if not keyref.startswith("topic."):
                raise BuildError(f"guide map uses unsupported topic key: {keyref}")
            child_topic_id = keyref.removeprefix("topic.")
            if child_topic_id in topics:
                raise BuildError(f"topic is present in more than one guide map: {child_topic_id}")
            roots = _localized_topic_roots(keyref, hrefs_by_locale)
            child_output = {}
            for locale in LOCALES:
                topic_path = hrefs_by_locale[locale][keyref]
                output_path = site_root / locale / topic_path.parent.name / f"{child_topic_id}.html"
                if not output_path.is_file():
                    raise BuildError(
                        f"missing topic output for {locale}/{child_topic_id}: {output_path}"
                    )
                child_output[locale] = output_path.relative_to(site_root).as_posix()
            topics[child_topic_id] = {
                "guide_id": guide_id,
                "dita_key": keyref,
                "source_slug": child_topic_id,
                "url_path": child_topic_id,
                "kind": _topic_kind(roots["en"]),
                "title": {
                    locale: _element_text(root.find("title")) for locale, root in roots.items()
                },
                "anchors": _topic_anchor_titles(roots),
                "output": child_output,
                "_url_root": url_root,
                "_roots": roots,
                "_source_paths": {locale: hrefs_by_locale[locale][keyref] for locale in LOCALES},
            }
    return topics


def _build_guides(topics: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    guides = {}
    for guide_id, filename, _anchor, url_root in GUIDE_MAPS:
        topic_id = _guide_topic_id(guide_id)
        if topic_id not in topics:
            raise BuildError(f"guide home topic is missing: {topic_id}")
        guides[guide_id] = {
            "url_root": url_root,
            "home_topic_id": topic_id,
            "title": _guide_titles(filename),
        }
    return guides


def _manifest_build_id(site_root: Path) -> str:
    excluded = {"manifest.json", "artifact-integrity.json"}
    digest = hashlib.sha256()
    for path in sorted(path for path in site_root.rglob("*") if path.is_file()):
        relative = path.relative_to(site_root).as_posix()
        if relative in excluded:
            continue
        digest.update(relative.encode())
        digest.update(b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def generate_manifest_files(site_root: Path) -> None:
    topics_with_private = _build_topics(site_root)
    topics = {
        topic_id: {key: value for key, value in topic.items() if not key.startswith("_")}
        for topic_id, topic in topics_with_private.items()
    }
    target_map = _build_target_map(topics)
    _validate_schema(target_map, UI_TARGET_SCHEMA)
    _write_json(site_root / "ui-target-map.json", target_map)

    navigation = {}
    for locale in LOCALES:
        navigation_path = site_root / locale / "navigation.json"
        if not navigation_path.is_file():
            raise BuildError(f"generated navigation source is missing for {locale}")
        navigation_payload = json.loads(navigation_path.read_text(encoding="utf-8"))
        _validate_schema(navigation_payload, NAVIGATION_SCHEMA)
        if navigation_payload != _navigation_payload(site_root, locale):
            raise BuildError(
                f"generated navigation source diverges from manifest topics for {locale}"
            )
        navigation[locale] = {
            "path": navigation_path.relative_to(site_root).as_posix(),
            "sha256": _file_sha256(navigation_path),
            "format_version": 1,
            "node_count": navigation_payload["node_count"],
        }

    search = {}
    for locale in LOCALES:
        search_payload = _search_document(locale, topics_with_private, target_map)
        search_path = site_root / "search" / locale / "index.json"
        _write_json(search_path, search_payload)
        search[locale] = {
            "path": search_path.relative_to(site_root).as_posix(),
            "sha256": _file_sha256(search_path),
            "format_version": 1,
            "document_count": len(search_payload["documents"]),
        }

    manifest = {
        "$schema": "schemas/product-documentation-manifest-v1.schema.json",
        "schema_version": 1,
        "artifact": {
            "bpm_version": _product_version(),
            "documentation_version": _product_version(),
            "build_id": _manifest_build_id(site_root),
            "source_revision": _source_revision(),
            "dita_ot_version": _load_lock()["components"]["dita_ot"]["version"],
        },
        "locales": list(LOCALES),
        "default_locale": "en",
        "guides": _build_guides(topics),
        "topics": topics,
        "assets": {},
        "navigation": navigation,
        "search": search,
        "aliases": {},
        "tombstones": {},
        "ui_target_map": {
            "path": "ui-target-map.json",
            "sha256": _file_sha256(site_root / "ui-target-map.json"),
            "schema_version": 1,
        },
    }
    _validate_schema(manifest, MANIFEST_SCHEMA)
    _write_json(site_root / "manifest.json", manifest)
    validate_manifest_files(site_root)


def _read_json_bytes(payload: bytes, name: str) -> dict[str, Any]:
    try:
        return json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BuildError(f"cannot parse generated JSON {name}: {exc}") from exc


def _safe_artifact_path(root: Path, relative: str) -> Path:
    parsed = urllib.parse.urlsplit(relative)
    if parsed.scheme or parsed.netloc or relative.startswith("/") or "\\" in relative:
        raise BuildError(f"artifact path is not relative and local: {relative}")
    candidate = (root / urllib.parse.unquote(parsed.path)).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise BuildError(f"artifact path escapes root: {relative}") from exc
    return candidate


def _target_source_authorities(manifest: dict[str, Any]) -> dict[str, tuple[set[str], str]]:
    """Return target kinds, authoritative source IDs, and stable failure nouns."""

    return {
        "topic": (set(manifest["topics"]), "topic"),
        "policy": (_policy_ids(), "policy"),
        "known-preference": (_managed_preference_ids(), "known-preference"),
        "cis": (_cis_recommendation_ids(), "CIS recommendation"),
        "api-operation": (set(_api_operation_topic_ids()), "API operation"),
        "capability": (set(_capability_topic_ids()), "capability"),
    }


def _validate_target_map_semantics(target_map: dict[str, Any], manifest: dict[str, Any]) -> None:
    reporter = ValidationReporter(BuildError, artifact="ui-target-map.json")
    topics = manifest["topics"]
    authorities = _target_source_authorities(manifest)
    for target_id, target in target_map["targets"].items():
        expected_key = f"{target['kind']}:{target['source_id']}"
        reporter.require(
            ValidationStage.TARGET_MAP,
            target_id == expected_key,
            f"target key does not match kind/source_id: {target_id}",
        )
        source_id = target["source_id"]
        kind = target["kind"]
        reporter.require(
            ValidationStage.TARGET_MAP,
            kind in authorities,
            f"target has unsupported kind: {target_id}",
        )
        assert isinstance(kind, str)
        allowed_ids, source_noun = authorities[kind]
        reporter.require(
            ValidationStage.TARGET_MAP,
            source_id in allowed_ids,
            f"target references unknown {source_noun} source: {target_id}",
        )
        topic_id = target["topic_id"]
        reporter.require(
            ValidationStage.TARGET_MAP,
            topic_id in topics,
            f"target references unknown topic: {target_id}",
        )
        assert isinstance(topic_id, str)
        anchor_id = target.get("anchor_id")
        reporter.require(
            ValidationStage.TARGET_MAP,
            not anchor_id or anchor_id in topics[topic_id]["anchors"],
            f"target references unknown anchor: {target_id} -> {anchor_id}",
        )


def _validate_manifest_matrix_stage(
    manifest: dict[str, Any], target_map: dict[str, Any], reporter: ValidationReporter
) -> None:
    reporter.require(
        ValidationStage.MANIFEST_MATRIX,
        manifest["locales"] == list(LOCALES) and target_map["locales"] == list(LOCALES),
        "manifest and target map must use the exact locale matrix",
    )
    reporter.require(
        ValidationStage.MANIFEST_MATRIX,
        target_map["manifest_schema_version"] == manifest["schema_version"],
        "target map schema version does not match manifest schema version",
    )


def _validate_manifest_guides_stage(manifest: dict[str, Any], reporter: ValidationReporter) -> None:
    topics = manifest["topics"]
    for guide_id, guide in manifest["guides"].items():
        home_topic_id = guide["home_topic_id"]
        reporter.require(
            ValidationStage.MANIFEST_GUIDES,
            home_topic_id in topics,
            f"guide {guide_id} references missing home topic {home_topic_id}",
        )
        assert isinstance(home_topic_id, str)
        reporter.require(
            ValidationStage.MANIFEST_GUIDES,
            topics[home_topic_id]["guide_id"] == guide_id,
            f"guide {guide_id} home topic is owned by another guide",
        )


def _validate_manifest_topics_stage(manifest: dict[str, Any], reporter: ValidationReporter) -> None:
    seen_paths: set[str] = set()
    seen_slugs: set[str] = set()
    for topic_id, topic in manifest["topics"].items():
        reporter.require(
            ValidationStage.MANIFEST_TOPICS,
            topic["dita_key"] == f"topic.{topic_id}",
            f"topic {topic_id} has inconsistent DITA key",
        )
        slug_key = topic["source_slug"].casefold()
        reporter.require(
            ValidationStage.MANIFEST_TOPICS,
            slug_key not in seen_slugs,
            f"duplicate topic source slug after case-folding: {topic['source_slug']}",
        )
        seen_slugs.add(slug_key)
        guide_root = manifest["guides"][topic["guide_id"]]["url_root"]
        public_path = f"{guide_root}/{topic['url_path']}".casefold()
        reporter.require(
            ValidationStage.MANIFEST_TOPICS,
            public_path not in seen_paths,
            f"duplicate topic public path: {public_path}",
        )
        seen_paths.add(public_path)
        for locale in LOCALES:
            reporter.require(
                ValidationStage.MANIFEST_TOPICS,
                locale in topic["title"] and locale in topic["output"],
                f"topic {topic_id} lacks locale data for {locale}",
            )


def _validate_manifest_semantics(manifest: dict[str, Any], target_map: dict[str, Any]) -> None:
    reporter = ValidationReporter(BuildError, artifact="manifest.json")
    _validate_manifest_matrix_stage(manifest, target_map, reporter)
    _validate_manifest_guides_stage(manifest, reporter)
    _validate_manifest_topics_stage(manifest, reporter)
    _validate_target_map_semantics(target_map, manifest)


@dataclass(frozen=True)
class _SearchValidationContext:
    locale: str
    payload: dict[str, Any]
    manifest: dict[str, Any]
    target_map: dict[str, Any]
    contract: dict[str, Any]
    aliases: dict[str, Any]
    ranking: dict[str, Any]
    facets: dict[str, Any]
    domain_ranking: dict[str, Any]
    quality: dict[str, Any]
    integrity: dict[str, Any]


def _search_validation_context(
    locale: str,
    payload: dict[str, Any],
    manifest: dict[str, Any],
    target_map: dict[str, Any],
) -> _SearchValidationContext:
    quality = _search_quality_performance()
    _validate_quality_fixture_coverage(quality)
    return _SearchValidationContext(
        locale=locale,
        payload=payload,
        manifest=manifest,
        target_map=target_map,
        contract=_read_json_file(SEARCH_CORPUS_CONTRACT),
        aliases=_search_normalization_aliases(),
        ranking=_search_ranking_typo(),
        facets=_search_facets_filters(),
        domain_ranking=_search_domain_ranking_facets(),
        quality=quality,
        integrity=_search_integrity_drift(),
    )


def _validate_search_contract_stage(
    context: _SearchValidationContext, reporter: ValidationReporter
) -> None:
    payload = context.payload
    expected = (
        ("contract_id", context.contract["contract_id"], "search index contract mismatch"),
        (
            "normalization_contract_id",
            context.aliases["contract_id"],
            "search index normalization contract mismatch",
        ),
        (
            "normalization_schema_version",
            context.aliases["schema_version"],
            "search index normalization schema mismatch",
        ),
        (
            "ranking_contract_id",
            context.ranking["contract_id"],
            "search index ranking contract mismatch",
        ),
        (
            "ranking_schema_version",
            context.ranking["schema_version"],
            "search index ranking schema mismatch",
        ),
        (
            "facets_contract_id",
            context.facets["contract_id"],
            "search index facets contract mismatch",
        ),
        (
            "facets_schema_version",
            context.facets["schema_version"],
            "search index facets schema mismatch",
        ),
        (
            "domain_ranking_contract_id",
            context.domain_ranking["contract_id"],
            "search index domain ranking contract mismatch",
        ),
        (
            "domain_ranking_schema_version",
            context.domain_ranking["schema_version"],
            "search index domain ranking schema mismatch",
        ),
        (
            "quality_contract_id",
            context.quality["contract_id"],
            "search index quality contract mismatch",
        ),
        (
            "quality_schema_version",
            context.quality["schema_version"],
            "search index quality schema mismatch",
        ),
        (
            "integrity_contract_id",
            context.integrity["contract_id"],
            "search index integrity contract mismatch",
        ),
        (
            "integrity_schema_version",
            context.integrity["schema_version"],
            "search index integrity schema mismatch",
        ),
        ("status", "ready", "search index is not ready"),
        ("locale", context.locale, "search index locale mismatch"),
        ("search_mode", "deterministic-local-static", "search index mode mismatch"),
        (
            "non_ai_boundary",
            "no-ai-no-rag-no-embeddings-no-generative-answers",
            "search index non-AI boundary mismatch",
        ),
        (
            "allowlisted_cross_locale_fields",
            ["identifiers"],
            "search index cross-locale allowlist mismatch",
        ),
    )
    for field, value, message in expected:
        reporter.require(
            ValidationStage.SEARCH_CONTRACT,
            payload.get(field) == value,
            f"{message} for {context.locale}",
        )


def _validate_search_fixtures_stage(
    context: _SearchValidationContext, reporter: ValidationReporter
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    locale, payload, aliases, ranking, facets, quality = (
        context.locale,
        context.payload,
        context.aliases,
        context.ranking,
        context.facets,
        context.quality,
    )
    expected_fixtures = _query_fixtures_for_locale(locale, aliases)
    reporter.require(
        ValidationStage.SEARCH_FIXTURES,
        payload.get("query_fixtures") == expected_fixtures,
        f"search index query fixtures mismatch for {locale}",
    )
    normalization = payload.get("normalization", {})
    browser_aliases = [
        {"alias_id": group["alias_id"], "terms": _alias_terms_for_locale(group, locale)}
        for group in aliases["alias_groups"]
    ]
    expected_normalization = (
        ("alias_groups", browser_aliases, "search index browser alias groups mismatch"),
        (
            "alias_group_count",
            len(aliases["alias_groups"]),
            "search index alias group count mismatch",
        ),
        (
            "query_fixture_count",
            len(expected_fixtures),
            "search index query fixture count mismatch",
        ),
    )
    for field, value, message in expected_normalization:
        reporter.require(
            ValidationStage.SEARCH_FIXTURES,
            normalization.get(field) == value,
            f"{message} for {locale}",
        )
    expected_ranking_fixtures = _ranking_fixtures_for_locale(locale, ranking)
    ranking_payload = payload.get("ranking", {})
    for field, value, message in (
        ("ranking_order", ranking["ranking_order"], "search index ranking order mismatch"),
        ("weights", ranking["weights"], "search index ranking weights mismatch"),
        ("typo_tolerance", ranking["typo_tolerance"], "search index typo tolerance mismatch"),
        (
            "ranking_fixture_count",
            len(expected_ranking_fixtures),
            "search index ranking fixture count mismatch",
        ),
    ):
        reporter.require(
            ValidationStage.SEARCH_FIXTURES,
            ranking_payload.get(field) == value,
            f"{message} for {locale}",
        )
    expected_filter_fixtures = [
        item for item in facets["filter_fixtures"] if item["locale"] == locale
    ]
    filtering = payload.get("filtering", {})
    for field, value, message in (
        (
            "facet_fields",
            _localized_search_facet_fields(locale, facets),
            "search index facet fields mismatch",
        ),
        (
            "composition",
            facets["filter_contract"]["composition"],
            "search index filter composition mismatch",
        ),
        ("url_state", facets["url_state"], "search index filter URL state mismatch"),
        (
            "empty_result",
            facets["empty_result"]["messages"][locale],
            "search index empty result message mismatch",
        ),
        (
            "filter_fixture_count",
            len(expected_filter_fixtures),
            "search index filter fixture count mismatch",
        ),
    ):
        reporter.require(
            ValidationStage.SEARCH_FIXTURES,
            filtering.get(field) == value,
            f"{message} for {locale}",
        )
    expected_quality_fixtures = _quality_fixtures_for_locale(locale, quality)
    quality_payload = payload.get("quality", {})
    for field, value, message in (
        (
            "categories",
            quality["coverage_requirements"]["categories"],
            "search index quality categories mismatch",
        ),
        (
            "fixture_count",
            len(expected_quality_fixtures),
            "search index quality fixture count mismatch",
        ),
        ("thresholds", quality["quality_thresholds"], "search index quality thresholds mismatch"),
    ):
        reporter.require(
            ValidationStage.SEARCH_FIXTURES,
            quality_payload.get(field) == value,
            f"{message} for {locale}",
        )
    for fixture in expected_fixtures:
        tokens = _normalize_search_text(locale, fixture["query"], aliases)
        reporter.require(
            ValidationStage.SEARCH_FIXTURES,
            set(fixture["expected_tokens"]) <= set(tokens),
            f"search fixture expected tokens are not resolved: {fixture['fixture_id']}",
        )
        resolved = set(_resolve_search_query_aliases(locale, fixture["query"], aliases))
        reporter.require(
            ValidationStage.SEARCH_FIXTURES,
            set(fixture["expected_alias_ids"]) <= resolved,
            f"search fixture expected aliases are not resolved: {fixture['fixture_id']}",
        )
    return (
        expected_fixtures,
        expected_ranking_fixtures,
        expected_filter_fixtures,
        expected_quality_fixtures,
    )


def _validate_search_document_stage(
    context: _SearchValidationContext, reporter: ValidationReporter
) -> list[dict[str, Any]]:
    locale, payload, manifest, aliases, facets = (
        context.locale,
        context.payload,
        context.manifest,
        context.aliases,
        context.facets,
    )
    documents = payload.get("documents")
    reporter.require(
        ValidationStage.SEARCH_DOCUMENTS,
        isinstance(documents, list) and len(documents) == len(manifest["topics"]),
        f"search index document count mismatch for {locale}",
    )
    assert isinstance(documents, list)
    document_ids: set[str] = set()
    required_searchable = set(context.contract["document_schema"]["searchable"]["required_fields"])
    required_facets = set(context.contract["document_schema"]["facets"]["required_fields"])
    known_alias_ids = {group["alias_id"] for group in aliases["alias_groups"]}
    for document in documents:
        topic_id = document.get("topic_id")
        reporter.require(
            ValidationStage.SEARCH_DOCUMENTS,
            topic_id in manifest["topics"],
            f"search index references unknown topic for {locale}: {topic_id}",
        )
        assert isinstance(topic_id, str)
        topic = manifest["topics"][topic_id]
        expected_output, expected_url = topic["output"][locale], f"/help/{topic['output'][locale]}"
        document_id = document.get("document_id")
        reporter.require(
            ValidationStage.SEARCH_DOCUMENTS,
            document_id not in document_ids,
            f"duplicate search document ID for {locale}: {document_id}",
        )
        assert isinstance(document_id, str)
        document_ids.add(document_id)
        reporter.require(
            ValidationStage.SEARCH_DOCUMENTS,
            document_id == f"{locale}:{topic_id}" and document.get("locale") == locale,
            f"search document identity mismatch for {locale}/{topic_id}",
        )
        reporter.require(
            ValidationStage.SEARCH_DOCUMENTS,
            document.get("guide_id") == topic["guide_id"]
            and document.get("topic_kind") == topic["kind"],
            f"search document manifest metadata mismatch for {locale}/{topic_id}",
        )
        reporter.require(
            ValidationStage.SEARCH_DOCUMENTS,
            document.get("url") == expected_url and expected_url.startswith(f"/help/{locale}/"),
            f"search document URL mismatch for {locale}/{topic_id}",
        )
        source = document.get("source", {})
        reporter.require(
            ValidationStage.SEARCH_DOCUMENTS,
            source.get("topic_id") == topic_id and source.get("output_path") == expected_output,
            f"search document source mismatch for {locale}/{topic_id}",
        )
        searchable = document.get("searchable", {})
        reporter.require(
            ValidationStage.SEARCH_DOCUMENTS,
            set(searchable) == required_searchable,
            f"search document searchable fields mismatch for {locale}/{topic_id}",
        )
        reporter.require(
            ValidationStage.SEARCH_DOCUMENTS,
            isinstance(searchable.get("title"), str) and bool(searchable["title"]),
            f"search document title is missing for {locale}/{topic_id}",
        )
        reporter.require(
            ValidationStage.SEARCH_DOCUMENTS,
            isinstance(searchable.get("body"), str) and bool(searchable["body"]),
            f"search document body is missing for {locale}/{topic_id}",
        )
        for field in ("headings", "keywords", "identifiers", "aliases"):
            reporter.require(
                ValidationStage.SEARCH_DOCUMENTS,
                isinstance(searchable.get(field), list),
                f"search document {field} is not a list for {locale}/{topic_id}",
            )
        reporter.require(
            ValidationStage.SEARCH_DOCUMENTS,
            topic_id in searchable["identifiers"]
            and topic["guide_id"] in searchable["identifiers"],
            f"search document identifiers are incomplete for {locale}/{topic_id}",
        )
        normalized = document.get("normalized", {})
        normalized_fields, alias_ids = normalized.get("fields", {}), normalized.get("alias_ids", [])
        reporter.require(
            ValidationStage.SEARCH_DOCUMENTS,
            set(normalized_fields) == required_searchable,
            f"search document normalized fields mismatch for {locale}/{topic_id}",
        )
        reporter.require(
            ValidationStage.SEARCH_DOCUMENTS,
            "tokens" not in normalized,
            f"search document has obsolete normalized tokens for {locale}/{topic_id}",
        )
        reporter.require(
            ValidationStage.SEARCH_DOCUMENTS,
            set(alias_ids) <= known_alias_ids,
            f"search document aliases reference unknown group for {locale}/{topic_id}",
        )
        document_facets = document.get("facets", {})
        reporter.require(
            ValidationStage.SEARCH_DOCUMENTS,
            set(document_facets) == required_facets,
            f"search document facets mismatch for {locale}/{topic_id}",
        )
        reporter.require(
            ValidationStage.SEARCH_DOCUMENTS,
            document_facets["locale"] == locale
            and document_facets["guide_id"] == topic["guide_id"],
            f"search document facet values mismatch for {locale}/{topic_id}",
        )
        filter_facets = document.get("filter_facets", {})
        reporter.require(
            ValidationStage.SEARCH_DOCUMENTS,
            set(filter_facets) == set(facets["facet_fields"]),
            f"search document filter facets mismatch for {locale}/{topic_id}",
        )
        for field, values in filter_facets.items():
            reporter.require(
                ValidationStage.SEARCH_DOCUMENTS,
                isinstance(values, list),
                f"search document filter facet is not a list for {locale}/{topic_id}/{field}",
            )
            unknown_values = set(values) - _facet_values_from_config(facets, field)
            reporter.require(
                ValidationStage.SEARCH_DOCUMENTS,
                not unknown_values,
                f"search document filter facet has undeclared values for {locale}/{topic_id}/{field}: {sorted(unknown_values)}",
            )
        reporter.require(
            ValidationStage.SEARCH_DOCUMENTS,
            filter_facets["locale"] == [locale]
            and filter_facets["guide_id"] == [topic["guide_id"]],
            f"search document filter identity facets mismatch for {locale}/{topic_id}",
        )
    return documents


def _validate_search_projections_stage(
    context: _SearchValidationContext,
    reporter: ValidationReporter,
    documents: list[dict[str, Any]],
) -> None:
    payload, locale, domain = context.payload, context.locale, context.domain_ranking
    reporter.require(
        ValidationStage.SEARCH_PROJECTIONS,
        payload.get("facet_counts") == _facet_counts(documents, context.facets),
        f"search index facet counts mismatch for {locale}",
    )
    expected_domain = {
        "preserved_sources": domain["ranking"]["preserved_sources"],
        "evidence_fields": domain["ranking"]["evidence_fields"],
        "preserved_facets": domain["facets"]["preserved_fields"],
        "maximum_evidence_rows": domain["adapter_projection"]["maximum_evidence_rows"],
    }
    reporter.require(
        ValidationStage.SEARCH_PROJECTIONS,
        payload.get("domain_ranking") == expected_domain,
        f"search index domain ranking projection mismatch for {locale}",
    )
    integrity = _search_integrity_report(
        locale, documents, context.manifest["topics"], context.target_map, context.integrity
    )
    reporter.require(
        ValidationStage.SEARCH_PROJECTIONS,
        payload.get("integrity_report") == integrity,
        f"search index integrity report mismatch for {locale}",
    )
    reporter.require(
        ValidationStage.SEARCH_PROJECTIONS,
        integrity["status"] == "pass" and integrity["failure_count"] == 0,
        f"search index integrity drift detected for {locale}",
    )


def _validate_search_ranking_stage(
    context: _SearchValidationContext,
    reporter: ValidationReporter,
    documents: list[dict[str, Any]],
    fixtures: list[dict[str, Any]],
) -> None:
    expected = _ranking_fixture_results(context.locale, documents, context.aliases, context.ranking)
    reporter.require(
        ValidationStage.SEARCH_RANKING,
        context.payload.get("ranking_fixture_results") == expected,
        f"search index ranking fixture results mismatch for {context.locale}",
    )
    by_id = {result["fixture_id"]: result for result in expected}
    for fixture in fixtures:
        result = by_id.get(fixture["fixture_id"])
        reporter.require(
            ValidationStage.SEARCH_RANKING,
            result is not None,
            f"missing ranking fixture result: {fixture['fixture_id']}",
        )
        assert result is not None
        reporter.require(
            ValidationStage.SEARCH_RANKING,
            result["top_topic_id"] == fixture["expected_top_topic_id"],
            f"ranking fixture top result mismatch: {fixture['fixture_id']}",
        )
        component = fixture["required_score_component"]
        reporter.require(
            ValidationStage.SEARCH_RANKING,
            result["score_breakdown"].get(component, 0) > 0,
            f"ranking fixture component missing: {fixture['fixture_id']}/{component}",
        )


def _validate_search_filter_stage(
    context: _SearchValidationContext,
    reporter: ValidationReporter,
    documents: list[dict[str, Any]],
    fixtures: list[dict[str, Any]],
) -> None:
    expected = _filter_fixture_results(context.locale, documents, context.facets)
    reporter.require(
        ValidationStage.SEARCH_FILTERS,
        context.payload.get("filter_fixture_results") == expected,
        f"search index filter fixture results mismatch for {context.locale}",
    )
    by_id = {result["fixture_id"]: result for result in expected}
    for fixture in fixtures:
        result = by_id.get(fixture["fixture_id"])
        reporter.require(
            ValidationStage.SEARCH_FILTERS,
            result is not None,
            f"missing filter fixture result: {fixture['fixture_id']}",
        )
        assert result is not None
        if "expected_count" in fixture:
            reporter.require(
                ValidationStage.SEARCH_FILTERS,
                result["result_count"] == fixture["expected_count"],
                f"filter fixture count mismatch: {fixture['fixture_id']}",
            )
        reporter.require(
            ValidationStage.SEARCH_FILTERS,
            result["result_count"] >= fixture.get("expected_min_count", 0),
            f"filter fixture minimum count mismatch: {fixture['fixture_id']}",
        )
        reporter.require(
            ValidationStage.SEARCH_FILTERS,
            set(fixture.get("must_include_topic_ids", [])) <= set(result["result_topic_ids"]),
            f"filter fixture missing expected topics: {fixture['fixture_id']}",
        )
        if fixture.get("expected_empty"):
            reporter.require(
                ValidationStage.SEARCH_FILTERS,
                result["result_count"] == 0 and bool(result["empty_result_message"]),
                f"filter fixture empty-result recovery mismatch: {fixture['fixture_id']}",
            )
        if fixture["filters"]:
            reporter.require(
                ValidationStage.SEARCH_FILTERS,
                bool(result["url_query"]),
                f"filter fixture URL state is missing: {fixture['fixture_id']}",
            )


def _validate_search_quality_stage(
    context: _SearchValidationContext,
    reporter: ValidationReporter,
    documents: list[dict[str, Any]],
    fixtures: list[dict[str, Any]],
) -> None:
    expected = _quality_fixture_results(
        context.locale, documents, context.aliases, context.ranking, context.quality
    )
    reporter.require(
        ValidationStage.SEARCH_QUALITY,
        context.payload.get("quality_fixture_results") == expected,
        f"search index quality fixture results mismatch for {context.locale}",
    )
    by_id = {result["fixture_id"]: result for result in expected}
    for fixture in fixtures:
        result = by_id.get(fixture["fixture_id"])
        reporter.require(
            ValidationStage.SEARCH_QUALITY,
            result is not None,
            f"missing quality fixture result: {fixture['fixture_id']}",
        )
        assert result is not None
        if "expected_count" in fixture:
            reporter.require(
                ValidationStage.SEARCH_QUALITY,
                result["result_count"] == fixture["expected_count"],
                f"quality fixture count mismatch: {fixture['fixture_id']}",
            )
        if fixture.get("expected_top_topic_id"):
            reporter.require(
                ValidationStage.SEARCH_QUALITY,
                result["top_topic_id"] == fixture["expected_top_topic_id"],
                f"quality fixture top result mismatch: {fixture['fixture_id']}",
            )
        component = fixture.get("required_score_component")
        if component:
            reporter.require(
                ValidationStage.SEARCH_QUALITY,
                result["required_score_component_value"] > 0,
                f"quality fixture score component missing: {fixture['fixture_id']}/{component}",
            )
        reporter.require(
            ValidationStage.SEARCH_QUALITY,
            result["visible_result_count"]
            <= context.quality["performance_budget"]["max_visible_results_per_query"],
            f"quality fixture visible result budget exceeded: {fixture['fixture_id']}",
        )
    performance = _quality_performance_report(documents, expected, context.quality)
    reporter.require(
        ValidationStage.SEARCH_BUDGETS,
        context.payload.get("performance_report") == performance,
        f"search index performance report mismatch for {context.locale}",
    )
    budget = context.quality["performance_budget"]
    reporter.require(
        ValidationStage.SEARCH_BUDGETS,
        performance["document_count"] <= budget["max_documents_per_locale"],
        f"search index document performance budget exceeded for {context.locale}",
    )
    reporter.require(
        ValidationStage.SEARCH_BUDGETS,
        performance["quality_fixture_count"] <= budget["max_quality_fixtures_per_locale"],
        f"search index quality fixture budget exceeded for {context.locale}",
    )
    reporter.require(
        ValidationStage.SEARCH_BUDGETS,
        performance["deterministic_scan_units"]
        <= budget["max_deterministic_scan_units_per_locale"],
        f"search index deterministic scan budget exceeded for {context.locale}",
    )


def _validate_search_index_semantics(
    locale: str,
    search_payload: dict[str, Any],
    manifest: dict[str, Any],
    target_map: dict[str, Any],
) -> None:
    """Validate one index through small typed, fail-closed semantic stages."""

    reporter = ValidationReporter(
        BuildError,
        artifact=f"search/{locale}/index.json",
        locale=locale,
    )
    context = reporter.stage(
        ValidationStage.SEARCH_CONTRACT,
        lambda: _search_validation_context(locale, search_payload, manifest, target_map),
    )
    reporter.stage(
        ValidationStage.SEARCH_CONTRACT,
        lambda: _validate_search_contract_stage(context, reporter),
    )
    query_fixtures, ranking_fixtures, filter_fixtures, quality_fixtures = reporter.stage(
        ValidationStage.SEARCH_FIXTURES,
        lambda: _validate_search_fixtures_stage(context, reporter),
    )
    documents = reporter.stage(
        ValidationStage.SEARCH_DOCUMENTS,
        lambda: _validate_search_document_stage(context, reporter),
    )
    reporter.stage(
        ValidationStage.SEARCH_PROJECTIONS,
        lambda: _validate_search_projections_stage(context, reporter, documents),
    )
    reporter.stage(
        ValidationStage.SEARCH_RANKING,
        lambda: _validate_search_ranking_stage(context, reporter, documents, ranking_fixtures),
    )
    reporter.stage(
        ValidationStage.SEARCH_FILTERS,
        lambda: _validate_search_filter_stage(context, reporter, documents, filter_fixtures),
    )
    reporter.stage(
        ValidationStage.SEARCH_QUALITY,
        lambda: _validate_search_quality_stage(context, reporter, documents, quality_fixtures),
    )
    del query_fixtures
    return


def validate_manifest_files(site_root: Path) -> None:
    manifest_path = site_root / "manifest.json"
    target_map_path = site_root / "ui-target-map.json"
    if not manifest_path.is_file() or not target_map_path.is_file():
        raise BuildError("manifest.json or ui-target-map.json is missing")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    target_map = json.loads(target_map_path.read_text(encoding="utf-8"))
    _validate_schema(target_map, UI_TARGET_SCHEMA)
    _validate_schema(manifest, MANIFEST_SCHEMA)
    _validate_manifest_semantics(manifest, target_map)
    if _file_sha256(target_map_path) != manifest["ui_target_map"]["sha256"]:
        raise BuildError("ui-target-map.json SHA-256 does not match manifest")
    quality_config = _search_quality_performance()
    for locale, navigation in manifest["navigation"].items():
        navigation_path = _safe_artifact_path(site_root, navigation["path"])
        if not navigation_path.is_file():
            raise BuildError(
                f"manifest navigation source is missing for {locale}: {navigation['path']}"
            )
        navigation_payload = _validate_navigation_artifact_record(
            locale,
            navigation,
            navigation_path.read_bytes(),
            manifest,
            context="manifest",
        )
        if navigation_payload != _navigation_payload(site_root, locale):
            raise BuildError(f"manifest navigation source diverges for {locale}")
    max_search_index_bytes = quality_config["performance_budget"]["max_index_bytes_per_locale"]
    for locale, search in manifest["search"].items():
        search_path = _safe_artifact_path(site_root, search["path"])
        if not search_path.is_file():
            raise BuildError(f"manifest search file is missing for {locale}: {search['path']}")
        if search_path.stat().st_size > max_search_index_bytes:
            raise BuildError(f"manifest search index size budget exceeded for {locale}")
        if _file_sha256(search_path) != search["sha256"]:
            raise BuildError(f"manifest search SHA-256 mismatch for {locale}")
        search_payload = json.loads(search_path.read_text(encoding="utf-8"))
        if search["document_count"] != len(search_payload.get("documents", [])):
            raise BuildError(f"manifest search document count mismatch for {locale}")
        _validate_search_index_semantics(locale, search_payload, manifest, target_map)
    for topic_id, topic in manifest["topics"].items():
        for locale, output in topic["output"].items():
            output_path = _safe_artifact_path(site_root, output)
            if not output_path.is_file():
                raise BuildError(f"manifest topic output is missing for {topic_id}/{locale}")


def validate_manifest_payloads(payloads: dict[str, bytes]) -> None:
    try:
        manifest = _read_json_bytes(payloads["manifest.json"], "manifest.json")
        target_map = _read_json_bytes(payloads["ui-target-map.json"], "ui-target-map.json")
    except KeyError as exc:
        raise BuildError("manifest.json or ui-target-map.json is missing from artifact") from exc
    _validate_schema(target_map, UI_TARGET_SCHEMA)
    _validate_schema(manifest, MANIFEST_SCHEMA)
    _validate_manifest_semantics(manifest, target_map)
    if _payload_sha256(payloads["ui-target-map.json"]) != manifest["ui_target_map"]["sha256"]:
        raise BuildError("archived ui-target-map.json SHA-256 does not match manifest")
    quality_config = _search_quality_performance()
    for locale, navigation in manifest["navigation"].items():
        path = navigation["path"]
        if path not in payloads:
            raise BuildError(f"archived navigation source is missing for {locale}: {path}")
        _validate_navigation_artifact_record(
            locale,
            navigation,
            payloads[path],
            manifest,
            context="archived",
        )
    max_search_index_bytes = quality_config["performance_budget"]["max_index_bytes_per_locale"]
    for locale, search in manifest["search"].items():
        path = search["path"]
        if path not in payloads:
            raise BuildError(f"archived search file is missing for {locale}: {path}")
        if len(payloads[path]) > max_search_index_bytes:
            raise BuildError(f"archived search index size budget exceeded for {locale}")
        if _payload_sha256(payloads[path]) != search["sha256"]:
            raise BuildError(f"archived search SHA-256 mismatch for {locale}")
        search_payload = _read_json_bytes(payloads[path], path)
        if search["document_count"] != len(search_payload.get("documents", [])):
            raise BuildError(f"archived search document count mismatch for {locale}")
        _validate_search_index_semantics(locale, search_payload, manifest, target_map)
    for topic_id, topic in manifest["topics"].items():
        for locale, output in topic["output"].items():
            if output not in payloads:
                raise BuildError(f"archived topic output is missing for {topic_id}/{locale}")
