#!/usr/bin/env python3
"""Validate and reproducibly publish the six-locale BPM DITA documentation."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unicodedata
import urllib.parse
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import jsonschema

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DOCUMENTATION_ROOT = REPOSITORY_ROOT / "documentation"
LOCK_PATH = DOCUMENTATION_ROOT / "config/toolchain-lock.json"
BUILD_ROOT = DOCUMENTATION_ROOT / "build"
DIST_ROOT = DOCUMENTATION_ROOT / "dist"
REPORTS_ROOT = DOCUMENTATION_ROOT / "reports"
DIAGNOSTICS_ROOT = REPORTS_ROOT / "diagnostics"
DEV_SITE_ROOT = REPOSITORY_ROOT / "app/documentation/site"
DEV_SITE_METADATA = REPOSITORY_ROOT / "app/documentation/.site-dev-install.json"
ARTIFACT_POLICY = DOCUMENTATION_ROOT / "config/artifact-policy.json"
FIREFOX_POLICY_CONTEXT_TARGETS = DOCUMENTATION_ROOT / "config/firefox-policy-context-targets-0.9.0.json"
FIREFOX_POLICY_INDEX = DOCUMENTATION_ROOT / "src/generated/firefox/firefox-policy-skeletons-0.9.0.json"
CIS_RECOMMENDATION_INDEX = DOCUMENTATION_ROOT / "src/generated/cis/cis-recommendation-skeletons-0.9.0.json"
SEARCH_CORPUS_CONTRACT = DOCUMENTATION_ROOT / "config/search-corpus-and-results-0.9.0.json"
SEARCH_NORMALIZATION_ALIASES = DOCUMENTATION_ROOT / "config/search-normalization-aliases-0.9.0.json"
SEARCH_RANKING_TYPO = DOCUMENTATION_ROOT / "config/search-ranking-typo-0.9.0.json"
SEARCH_FACETS_FILTERS = DOCUMENTATION_ROOT / "config/search-facets-filters-0.9.0.json"
SEARCH_QUALITY_PERFORMANCE = DOCUMENTATION_ROOT / "config/search-quality-performance-0.9.0.json"
SEARCH_INTEGRITY_DRIFT = DOCUMENTATION_ROOT / "config/search-integrity-drift-0.9.0.json"
FIXTURE_CATALOG = DOCUMENTATION_ROOT / "fixtures/fixture-catalog-0.9.0.json"
SEARCH_STATE_FIXTURE = DOCUMENTATION_ROOT / "fixtures/search-states/search-query-states-0.9.0.json"
SCREENSHOT_STATE_FIXTURE = DOCUMENTATION_ROOT / "fixtures/screenshot-states/screenshot-states-0.9.0.json"
FIREFOX_POLICY_INVENTORY = REPOSITORY_ROOT / "docs/architecture/firefox-policy-documentation-inventory-0.9.0.json"
CIS_INVENTORY = REPOSITORY_ROOT / "docs/architecture/cis-documentation-inventory-0.9.0.json"
API_INVENTORY = REPOSITORY_ROOT / "docs/architecture/api-documentation-inventory-0.9.0.md"
CAPABILITY_INVENTORY = REPOSITORY_ROOT / "docs/architecture/product-user-capability-inventory-0.9.0.md"
MANIFEST_SCHEMA = (
    REPOSITORY_ROOT
    / "docs/architecture/schemas/product-documentation-manifest-v1.schema.json"
)
UI_TARGET_SCHEMA = (
    REPOSITORY_ROOT
    / "docs/architecture/schemas/product-documentation-ui-target-map-v1.schema.json"
)
LOCALES = ("en", "ru", "de", "zh-CN", "fr", "es-ES")
SOURCE_SUFFIXES = {".dita", ".ditamap"}
LINK_ATTRIBUTES = {"href", "src"}
THEME_ROOT = DOCUMENTATION_ROOT / "assets/theme"
THEME_FILES = ("bpm-docs.css", "bpm-docs-print.css")
SEARCH_SCRIPT = "bpm-docs-search.js"
SEARCH_TOKEN_PATTERN = re.compile(
    r"/[^\s\"'<>]+|[^\W_]+(?:[-._:/][^\W_]+)+|[^\W_]+",
    flags=re.UNICODE,
)
GUIDE_MAPS = (
    ("user-guide", "user-guide.ditamap", "a-user-guide", "user"),
    ("firefox-policy-guide", "firefox-policy-guide.ditamap", "a-firefox-policy-guide", "firefox"),
    ("cis-settings-guide", "cis-settings-guide.ditamap", "a-cis-settings-guide", "cis"),
    ("api-integration-guide", "api-integration-guide.ditamap", "a-api-integration-guide", "api"),
    ("administrator-guide", "administrator-guide.ditamap", "a-administrator-guide", "admin"),
)
GUIDE_OUTPUT_ROOT_BY_MAP = {filename: url_root for _guide_id, filename, _anchor, url_root in GUIDE_MAPS}
GUIDE_OUTPUT_ROOT_BY_SOURCE_DIR = {
    "api": "api",
    "admin": "admin",
    "cis": "cis",
    "firefox": "firefox",
    "json": "user",
    "user": "user",
}
SHELL_LABELS = {
    "en": {
        "skip": "Skip to content",
        "guides": "Guides",
        "locales": "Languages",
        "breadcrumbs": "Breadcrumbs",
        "home": "Documentation home",
        "version": "BPM 0.9.0 · Documentation 0.9.0",
        "status": "Runtime package pending manifest, search, and UI target metadata.",
        "search": "Search documentation",
        "search_query": "Search query",
        "search_placeholder": "Search topics, policies, CIS IDs, or API operations",
        "search_submit": "Search",
        "search_clear": "Clear",
        "search_help": "Search uses this locale’s static offline index. No AI, telemetry, or network search is used.",
        "search_filters": "Filters",
        "search_results": "Search results",
        "search_loading": "Loading the local search index…",
        "search_ready": "Enter a query or choose filters to search this documentation.",
        "search_no_results": "No documentation pages match the query and selected filters.",
        "search_unavailable": "Search is unavailable because the local index could not be loaded.",
        "search_result_singular": "1 result",
        "search_result_plural": "results",
    },
    "ru": {
        "skip": "Перейти к содержимому",
        "guides": "Руководства",
        "locales": "Языки",
        "breadcrumbs": "Навигационная цепочка",
        "home": "Главная страница документации",
        "version": "BPM 0.9.0 · Документация 0.9.0",
        "status": "Пакет для runtime ожидает манифест, поиск и метаданные UI-целей.",
        "search": "Поиск по документации",
        "search_query": "Поисковый запрос",
        "search_placeholder": "Ищите разделы, политики, CIS ID или операции API",
        "search_submit": "Найти",
        "search_clear": "Сбросить",
        "search_help": "Поиск использует статический офлайн-индекс текущей локали. ИИ, телеметрия и сетевой поиск не используются.",
        "search_filters": "Фильтры",
        "search_results": "Результаты поиска",
        "search_loading": "Загружается локальный поисковый индекс…",
        "search_ready": "Введите запрос или выберите фильтры для поиска в документации.",
        "search_no_results": "Нет страниц документации, соответствующих запросу и выбранным фильтрам.",
        "search_unavailable": "Поиск недоступен: локальный индекс не удалось загрузить.",
        "search_result_singular": "1 результат",
        "search_result_plural": "результатов",
    },
    "de": {
        "skip": "Zum Inhalt springen",
        "guides": "Handbücher",
        "locales": "Sprachen",
        "breadcrumbs": "Breadcrumbs",
        "home": "Startseite der Dokumentation",
        "version": "BPM 0.9.0 · Dokumentation 0.9.0",
        "status": "Das Runtime-Paket wartet auf Manifest, Suche und UI-Zielmetadaten.",
        "search": "Dokumentation durchsuchen",
        "search_query": "Suchanfrage",
        "search_placeholder": "Themen, Richtlinien, CIS-IDs oder API-Vorgänge suchen",
        "search_submit": "Suchen",
        "search_clear": "Zurücksetzen",
        "search_help": "Die Suche verwendet den statischen Offline-Index dieser Sprache. Keine KI, Telemetrie oder Netzwerksuche wird verwendet.",
        "search_filters": "Filter",
        "search_results": "Suchergebnisse",
        "search_loading": "Lokaler Suchindex wird geladen…",
        "search_ready": "Geben Sie eine Anfrage ein oder wählen Sie Filter, um diese Dokumentation zu durchsuchen.",
        "search_no_results": "Keine Dokumentationsseiten entsprechen der Anfrage und den ausgewählten Filtern.",
        "search_unavailable": "Die Suche ist nicht verfügbar, weil der lokale Index nicht geladen werden konnte.",
        "search_result_singular": "1 Ergebnis",
        "search_result_plural": "Ergebnisse",
    },
    "zh-CN": {
        "skip": "跳到内容",
        "guides": "指南",
        "locales": "语言",
        "breadcrumbs": "面包屑导航",
        "home": "文档主页",
        "version": "BPM 0.9.0 · 文档 0.9.0",
        "status": "运行时包仍需清单、搜索和 UI 目标元数据。",
        "search": "搜索文档",
        "search_query": "搜索查询",
        "search_placeholder": "搜索主题、策略、CIS ID 或 API 操作",
        "search_submit": "搜索",
        "search_clear": "清除",
        "search_help": "搜索使用当前语言的静态离线索引。不使用 AI、遥测或网络搜索。",
        "search_filters": "筛选条件",
        "search_results": "搜索结果",
        "search_loading": "正在加载本地搜索索引…",
        "search_ready": "输入查询或选择筛选条件以搜索此文档。",
        "search_no_results": "没有文档页面符合该查询和所选筛选条件。",
        "search_unavailable": "搜索不可用，因为无法加载本地索引。",
        "search_result_singular": "1 个结果",
        "search_result_plural": "个结果",
    },
    "fr": {
        "skip": "Aller au contenu",
        "guides": "Guides",
        "locales": "Langues",
        "breadcrumbs": "Fil d’Ariane",
        "home": "Accueil de la documentation",
        "version": "BPM 0.9.0 · Documentation 0.9.0",
        "status": "Le paquet d’exécution attend le manifeste, la recherche et les métadonnées des cibles UI.",
        "search": "Rechercher dans la documentation",
        "search_query": "Requête de recherche",
        "search_placeholder": "Rechercher des rubriques, politiques, ID CIS ou opérations API",
        "search_submit": "Rechercher",
        "search_clear": "Effacer",
        "search_help": "La recherche utilise l’index statique hors ligne de cette langue. Aucune IA, télémétrie ni recherche réseau n’est utilisée.",
        "search_filters": "Filtres",
        "search_results": "Résultats de recherche",
        "search_loading": "Chargement de l’index de recherche local…",
        "search_ready": "Saisissez une requête ou choisissez des filtres pour rechercher dans cette documentation.",
        "search_no_results": "Aucune page de documentation ne correspond à la requête et aux filtres sélectionnés.",
        "search_unavailable": "La recherche est indisponible car l’index local n’a pas pu être chargé.",
        "search_result_singular": "1 résultat",
        "search_result_plural": "résultats",
    },
    "es-ES": {
        "skip": "Ir al contenido",
        "guides": "Guías",
        "locales": "Idiomas",
        "breadcrumbs": "Ruta de navegación",
        "home": "Inicio de la documentación",
        "version": "BPM 0.9.0 · Documentación 0.9.0",
        "status": "El paquete de runtime espera el manifiesto, la búsqueda y los metadatos de objetivos de UI.",
        "search": "Buscar en la documentación",
        "search_query": "Consulta de búsqueda",
        "search_placeholder": "Buscar temas, políticas, ID de CIS u operaciones de API",
        "search_submit": "Buscar",
        "search_clear": "Borrar",
        "search_help": "La búsqueda usa el índice estático sin conexión de este idioma. No se usa IA, telemetría ni búsqueda de red.",
        "search_filters": "Filtros",
        "search_results": "Resultados de búsqueda",
        "search_loading": "Cargando el índice de búsqueda local…",
        "search_ready": "Escriba una consulta o elija filtros para buscar en esta documentación.",
        "search_no_results": "Ninguna página de documentación coincide con la consulta y los filtros seleccionados.",
        "search_unavailable": "La búsqueda no está disponible porque no se pudo cargar el índice local.",
        "search_result_singular": "1 resultado",
        "search_result_plural": "resultados",
    },
}


class BuildError(RuntimeError):
    """A documentation validation or publishing failure."""


def _load_lock() -> dict[str, Any]:
    try:
        return json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BuildError(f"cannot read toolchain lock: {exc}") from exc


def toolchain() -> tuple[Path, Path]:
    lock = _load_lock()
    cache = REPOSITORY_ROOT / lock["cache_directory"]
    dita = cache / "installs" / f"dita-ot-{lock['components']['dita_ot']['version']}" / "bin/dita"
    java = (
        cache
        / "installs"
        / f"temurin-jre-{lock['components']['java']['version']}"
        / "bin/java"
    )
    for executable in (dita, java):
        if not executable.is_file() or not os.access(executable, os.X_OK):
            raise BuildError(
                f"locked toolchain executable is missing: {executable}; run make setup-docs-toolchain"
            )
    return dita, java.parent.parent


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
        ["git", "diff", "--name-only", "--", "documentation", "docs/architecture"],
        ["git", "ls-files", "--others", "--exclude-standard", "--", "documentation", "docs/architecture"],
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
            _resolve_changed_path(line)
            for line in completed.stdout.splitlines()
            if line.strip()
        )
    return sorted(set(paths))


def _changed_paths(arguments: list[str]) -> list[Path]:
    if arguments:
        return sorted({_resolve_changed_path(argument) for argument in arguments})
    return _git_changed_paths()


def _relative_repo_path(path: Path) -> str:
    return path.relative_to(REPOSITORY_ROOT).as_posix()


def _fast_scope(path: Path) -> dict[str, Any] | None:
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
        guide_root = {"firefox": "firefox", "cis": "cis"}.get(parts[2] if len(parts) > 2 else "", "")
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
    if parts[0] in {"config", "runbooks", "tests"}:
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
    except (OSError, ET.ParseError):
        return None
    return root.attrib.get("id")


def _source_line_hint(path: Path, topic_id: str | None = None) -> int | None:
    if not path.is_file():
        return None
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
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
    except (OSError, json.JSONDecodeError):
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
    target_url = f"/help/{locale}/{guide}/{topic_id}.html" if locale and guide and topic_id else None
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
        else "make docs-fast-check DOCS_CHANGED=\"" + " ".join(changed_arguments) + "\""
    )
    return {
        "schema_version": 1,
        "backlog_item": "BPM090-M11-06",
        "target_bpm_version": "0.9.0",
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
                        outputs.add(f"documentation/build/site/{locale}/{guide_root}/{topic_id}.html")
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
            "recommended_next_checks": ["make test-docs-contract"],
        }
        if emit:
            print("Documentation fast check: no changed documentation inputs detected.", flush=True)
            print("Recommended next check: make test-docs-contract", flush=True)
        return report

    paths = [path for path, _scope in relevant]
    _validate_changed_inputs(paths)
    focused_dita = [path for path in paths if path.suffix in SOURCE_SUFFIXES]
    validate_focused_source_links(focused_dita)
    scopes = [scope for _path, scope in relevant if scope is not None]
    locales = sorted({locale for scope in scopes for locale in scope["locales"]})
    guide_roots = sorted({guide_root for scope in scopes for guide_root in scope["guide_roots"]})
    search_indexes = sorted({locale for scope in scopes for locale in scope["search_indexes"]})
    affected_outputs = _affected_output_paths(scopes, focused_dita)
    recommended_next_checks = [
        "make test-docs-contract",
        "make docs-validate",
    ]
    report = {
        "changed": [_relative_repo_path(path) for path in changed],
        "checked": [_relative_repo_path(path) for path in paths],
        "locales": locales,
        "guide_roots": guide_roots,
        "search_indexes": search_indexes,
        "affected_outputs": affected_outputs,
        "recommended_next_checks": recommended_next_checks,
    }
    if emit:
        print(f"Documentation fast check: {len(paths)} changed documentation input(s).", flush=True)
        print("Checked inputs:", flush=True)
        for path in report["checked"]:
            print(f"  {path}", flush=True)
        print(f"Affected locales: {', '.join(locales) if locales else 'none'}", flush=True)
        print(f"Affected guide roots: {', '.join(guide_roots) if guide_roots else 'none'}", flush=True)
        print(
            f"Affected search indexes: {', '.join(search_indexes) if search_indexes else 'none'}",
            flush=True,
        )
        if affected_outputs:
            print("Expected outputs touched by a full docs build:", flush=True)
            for output in affected_outputs[:30]:
                print(f"  {output}", flush=True)
            if len(affected_outputs) > 30:
                print(f"  ... {len(affected_outputs) - 30} more", flush=True)
        print("Fast check passed. Full deterministic gate remains: make docs-validate.", flush=True)
    return report


class _HTMLLinks(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.links: list[str] = []
        self.tags: list[str] = []
        self.h1_count = 0
        self.html_lang = ""
        self.main_count = 0
        self.body_classes: set[str] = set()
        self.nav_labels: set[str] = set()
        self.forbidden: list[str] = []
        self._script_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        self.tags.append(tag)
        attributes = {name.lower(): value or "" for name, value in attrs}
        if tag == "html":
            self.html_lang = attributes.get("lang", "")
        if tag == "h1":
            self.h1_count += 1
        if tag == "main" and attributes.get("id") == "main-content":
            self.main_count += 1
        if tag == "body":
            self.body_classes.update(attributes.get("class", "").split())
        if tag == "nav" and attributes.get("aria-label"):
            self.nav_labels.add(attributes["aria-label"])
        if tag == "script":
            self._script_depth += 1
            if set(attributes) != {"src", "defer"} or not attributes.get("src"):
                self.forbidden.append("forbidden script element")
        elif tag in {"style", "iframe", "frame", "object", "embed", "applet", "form"}:
            self.forbidden.append(f"forbidden element <{tag}>")
        for name, value in attrs:
            if value is None:
                continue
            name = name.lower()
            if name == "style" or name.startswith("on"):
                self.forbidden.append(f"forbidden attribute {name!r}")
            if name == "id":
                if value in self.ids:
                    raise BuildError(f"duplicate generated HTML id: {value}")
                self.ids.add(value)
            elif name in LINK_ATTRIBUTES:
                self.links.append(value)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "script" and self._script_depth:
            self._script_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._script_depth and data.strip():
            self.forbidden.append("forbidden inline script content")


def _html_document(path: Path, cache: dict[Path, _HTMLLinks]) -> _HTMLLinks:
    if path not in cache:
        parser = _HTMLLinks()
        try:
            parser.feed(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError) as exc:
            raise BuildError(f"cannot parse generated HTML {path}: {exc}") from exc
        cache[path] = parser
    return cache[path]


def validate_output(root: Path) -> None:
    html_files = sorted(root.rglob("*.html"))
    if len(html_files) < len(LOCALES):
        raise BuildError("generated site does not contain an HTML entry point for every locale")
    cache: dict[Path, _HTMLLinks] = {}
    errors: list[str] = []
    workspace_bytes = str(REPOSITORY_ROOT).encode()
    for artifact in sorted(path for path in root.rglob("*") if path.is_file()):
        if workspace_bytes in artifact.read_bytes():
            errors.append(f"generated artifact leaks absolute workspace path: {artifact}")
    for page in html_files:
        locale = page.relative_to(root).parts[0]
        document = _html_document(page, cache)
        if locale in LOCALES:
            if document.html_lang != locale:
                errors.append(f"{page}: html lang must be {locale!r}")
            if document.h1_count != 1:
                errors.append(f"{page}: generated page must contain exactly one h1")
            if document.main_count != 1:
                errors.append(f"{page}: generated page must contain one main#main-content landmark")
            if "bpm-docs-shell" not in document.body_classes:
                errors.append(f"{page}: portal shell class is missing")
            if len(document.nav_labels) < 3:
                errors.append(f"{page}: portal shell must expose distinct navigation labels")
        errors.extend(f"{page}: {issue}" for issue in document.forbidden)
        for link in document.links:
            parsed = urllib.parse.urlsplit(link)
            if parsed.scheme:
                if parsed.scheme != "https":
                    errors.append(f"{page}: forbidden generated link scheme in {link!r}")
                continue
            if parsed.netloc or parsed.path.startswith("/"):
                errors.append(f"{page}: generated link must be relative: {link!r}")
                continue
            target = page if not parsed.path else (page.parent / urllib.parse.unquote(parsed.path))
            if target.is_dir():
                target /= "index.html"
            if not target.is_file():
                errors.append(f"{page}: missing generated target {link!r}")
                continue
            if parsed.fragment and target.suffix == ".html":
                if urllib.parse.unquote(parsed.fragment) not in _html_document(target, cache).ids:
                    errors.append(f"{page}: missing generated fragment in {link!r}")
    if errors:
        raise BuildError("generated link validation failed:\n" + "\n".join(errors))


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


def _normalize_locale_root_links(site_root: Path) -> None:
    for locale in LOCALES:
        locale_root = site_root / locale
        for page in sorted(locale_root.rglob("*.html")):
            content = page.read_text(encoding="utf-8")

            def replace_link(
                match: re.Match[str],
                *,
                page: Path = page,
                locale_root: Path = locale_root,
            ) -> str:
                attribute = match.group("attribute")
                quote = match.group("quote")
                value = match.group("value")
                parsed = urllib.parse.urlsplit(value)
                if parsed.scheme or parsed.netloc or not parsed.path.startswith("../"):
                    return match.group(0)
                current_target = page.parent / urllib.parse.unquote(parsed.path)
                stripped_path = parsed.path.removeprefix("../")
                locale_target = locale_root / urllib.parse.unquote(stripped_path)
                if current_target.is_file() or not locale_target.is_file():
                    return match.group(0)
                normalized = urllib.parse.urlunsplit(
                    ("", "", _relative_href(page, locale_target), parsed.query, parsed.fragment)
                )
                return f"{attribute}={quote}{_escape(normalized)}{quote}"

            updated = re.sub(
                r'(?P<attribute>href|src)=(?P<quote>["\'])(?P<value>.*?)(?P=quote)',
                replace_link,
                content,
                flags=re.IGNORECASE,
            )
            if updated != content:
                page.write_text(updated, encoding="utf-8")


def _body_with_shell_class(body_tag: str) -> str:
    class_match = re.search(r'\sclass=(["\'])(.*?)\1', body_tag, flags=re.IGNORECASE)
    if class_match:
        classes = class_match.group(2).split()
        if "bpm-docs-shell" not in classes:
            classes.append("bpm-docs-shell")
        start, end = class_match.span(2)
        return body_tag[:start] + " ".join(classes) + body_tag[end:]
    return body_tag[:-1] + ' class="bpm-docs-shell">'


def _html_with_locale(content: str, locale: str) -> str:
    html_match = re.search(r"<html\b[^>]*>", content, flags=re.IGNORECASE)
    if not html_match:
        raise BuildError("generated page lacks an html root element")
    html_tag = html_match.group(0)
    lang_match = re.search(r'\slang=(["\'])(.*?)\1', html_tag, flags=re.IGNORECASE)
    if lang_match:
        start, end = lang_match.span(2)
        html_tag = html_tag[:start] + locale + html_tag[end:]
    else:
        html_tag = html_tag[:-1] + f' lang="{locale}">'
    return content[: html_match.start()] + html_tag + content[html_match.end() :]


def _locale_peer(site_root: Path, page: Path, source_locale: str, target_locale: str) -> Path:
    try:
        locale_relative = page.relative_to(site_root / source_locale)
    except ValueError as exc:
        raise BuildError(f"generated page is outside its locale root: {page}") from exc
    peer = site_root / target_locale / locale_relative
    return peer if peer.is_file() else site_root / target_locale / "index.html"


def _portal_shell(site_root: Path, page: Path, locale: str, body_inner: str) -> str:
    labels = SHELL_LABELS[locale]
    portal_title = _map_title(locale, "portal.ditamap")
    guide_items = [
        (_map_title(locale, filename), anchor) for _guide, filename, anchor, _root in GUIDE_MAPS
    ]
    guide_links = "\n".join(
        f'               <li><a href="#{anchor}">{_escape(title)}</a></li>'
        for title, anchor in guide_items
    )
    guide_sidebar = "\n".join(
        f'            <li id="{anchor}"><a href="#{anchor}">{_escape(title)}</a></li>'
        for title, anchor in guide_items
    )
    locale_links = "\n".join(
        "               <li>"
        f'<a href="{_escape(_relative_href(page, _locale_peer(site_root, page, locale, peer)))}"'
        f' hreflang="{peer}" lang="{peer}"'
        f'{" aria-current=\"true\"" if peer == locale else ""}>{peer}</a>'
        "</li>"
        for peer in LOCALES
    )
    search_index_href = _relative_href(page, site_root / "search" / locale / "index.json")
    search_shell = f"""            <section class="bpm-docs-search" role="search" aria-labelledby="bpm-docs-search-heading" data-search-locale="{_escape(locale)}" data-search-index-href="{_escape(search_index_href)}" data-label-loading="{_escape(labels["search_loading"])}" data-label-ready="{_escape(labels["search_ready"])}" data-label-no-results="{_escape(labels["search_no_results"])}" data-label-unavailable="{_escape(labels["search_unavailable"])}" data-label-result-singular="{_escape(labels["search_result_singular"])}" data-label-result-plural="{_escape(labels["search_result_plural"])}">
               <h2 id="bpm-docs-search-heading">{_escape(labels["search"])}</h2>
               <div class="bpm-docs-search-form">
                  <label for="bpm-docs-search-query">{_escape(labels["search_query"])}</label>
                  <div class="bpm-docs-search-row">
                     <input id="bpm-docs-search-query" class="bpm-docs-search-input" name="q" type="search" inputmode="search" maxlength="256" autocomplete="off" placeholder="{_escape(labels["search_placeholder"])}">
                     <button class="bpm-docs-search-submit" type="button" data-search-submit>{_escape(labels["search_submit"])}</button>
                     <button class="bpm-docs-search-clear" type="button" data-search-clear>{_escape(labels["search_clear"])}</button>
                  </div>
               </div>
               <p class="bpm-docs-search-help" id="bpm-docs-search-help">{_escape(labels["search_help"])}</p>
               <details class="bpm-docs-search-filters">
                  <summary>{_escape(labels["search_filters"])}</summary>
                  <div class="bpm-docs-search-filter-grid" data-search-filters></div>
               </details>
               <p class="bpm-docs-search-status" role="status" aria-live="polite" data-search-status>{_escape(labels["search_loading"])}</p>
               <section class="bpm-docs-search-results" aria-labelledby="bpm-docs-search-results-heading">
                  <h3 id="bpm-docs-search-results-heading">{_escape(labels["search_results"])}</h3>
                  <ol class="bpm-docs-search-result-list" data-search-results></ol>
               </section>
            </section>"""
    return f"""      <a class="bpm-docs-skip-link" href="#main-content">{_escape(labels["skip"])}</a>
      <header class="bpm-docs-header">
         <div class="bpm-docs-brand">
            <p class="bpm-docs-brand-kicker">Browser Policy Manager</p>
            <p class="bpm-docs-brand-title">{_escape(portal_title)}</p>
            <p class="bpm-docs-version">{_escape(labels["version"])}</p>
         </div>
         <div class="bpm-docs-header-nav">
            <nav aria-label="{_escape(labels["guides"])}">
               <ul>
{guide_links}
               </ul>
            </nav>
            <nav aria-label="{_escape(labels["locales"])}">
               <ul>
{locale_links}
               </ul>
            </nav>
         </div>
      </header>
      <nav class="bpm-docs-breadcrumbs" aria-label="{_escape(labels["breadcrumbs"])}">
         <ol>
            <li><a href="{_escape(_relative_href(page, site_root / locale / "index.html"))}">{_escape(labels["home"])}</a></li>
            <li aria-current="page">{_escape(portal_title)}</li>
         </ol>
      </nav>
      <div class="bpm-docs-content-grid">
         <aside class="bpm-docs-sidebar" aria-labelledby="bpm-docs-guides-heading">
            <h2 id="bpm-docs-guides-heading">{_escape(labels["guides"])}</h2>
            <ol class="bpm-docs-guide-list">
{guide_sidebar}
            </ol>
         </aside>
         <main id="main-content" class="bpm-docs-main" tabindex="-1">
{search_shell}
{body_inner.rstrip()}
         </main>
      </div>
      <footer class="bpm-docs-footer">
         <p>{_escape(labels["status"])}</p>
      </footer>
"""


def _install_theme_assets(locale_root: Path) -> None:
    assets_root = locale_root / "assets"
    assets_root.mkdir(parents=True, exist_ok=True)
    for filename in THEME_FILES:
        source = THEME_ROOT / filename
        if not source.is_file():
            raise BuildError(f"missing portal theme asset: {source}")
        shutil.copyfile(source, assets_root / filename)
    script = THEME_ROOT / SEARCH_SCRIPT
    if not script.is_file():
        raise BuildError(f"missing portal search asset: {script}")
    shutil.copyfile(script, assets_root / SEARCH_SCRIPT)


def _apply_portal_shell_to_page(site_root: Path, page: Path, locale: str) -> None:
    content = _html_with_locale(page.read_text(encoding="utf-8"), locale)
    head_end = re.search(r"</head\s*>", content, flags=re.IGNORECASE)
    body_start = re.search(r"<body\b[^>]*>", content, flags=re.IGNORECASE)
    body_end = re.search(r"</body\s*>", content, flags=re.IGNORECASE)
    if not head_end or not body_start or not body_end:
        raise BuildError(f"generated page lacks head/body shell anchors: {page}")
    css_links = (
        f'      <link rel="stylesheet" type="text/css" href="'
        f'{_escape(_relative_href(page, site_root / locale / "assets" / THEME_FILES[0]))}">\n'
        f'      <link rel="stylesheet" type="text/css" media="print" href="'
        f'{_escape(_relative_href(page, site_root / locale / "assets" / THEME_FILES[1]))}">\n'
        f'      <script src="{_escape(_relative_href(page, site_root / locale / "assets" / SEARCH_SCRIPT))}" defer></script>\n'
    )
    before_head_close = content[: head_end.start()]
    after_head_close = content[head_end.start() : body_start.start()]
    body_tag = _body_with_shell_class(body_start.group(0))
    body_inner = content[body_start.end() : body_end.start()]
    shell = _portal_shell(site_root, page, locale, body_inner)
    updated = (
        before_head_close
        + css_links
        + after_head_close
        + body_tag
        + "\n"
        + shell
        + content[body_end.start() :]
    )
    page.write_text(updated, encoding="utf-8")


def apply_portal_shell(site_root: Path) -> None:
    for locale in LOCALES:
        locale_root = site_root / locale
        if not locale_root.is_dir():
            raise BuildError(f"generated locale root is missing: {locale_root}")
        _install_theme_assets(locale_root)
    for locale in LOCALES:
        for page in sorted((site_root / locale).rglob("*.html")):
            _apply_portal_shell_to_page(site_root, page, locale)


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
        raise BuildError(f"schema validation failed for {schema_path.name} at {location}: {exc.message}") from exc


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


def _localized_topic_roots(key: str, hrefs_by_locale: dict[str, dict[str, Path]]) -> dict[str, ET.Element]:
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
    return _read_json_file(SEARCH_FACETS_FILTERS)


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


def _normalize_search_text(locale: str, text: str, config: dict[str, Any] | None = None) -> list[str]:
    if locale not in LOCALES:
        raise BuildError(f"unsupported search locale: {locale}")
    rules = (config or _search_normalization_aliases())["normalization"]
    normalized = unicodedata.normalize(rules["unicode_form"], text).casefold()
    if rules["strip_diacritics"]:
        normalized = _strip_latin_diacritics(normalized)
    tokens: list[str] = []
    for match in SEARCH_TOKEN_PATTERN.finditer(normalized):
        token = match.group(0).strip(".,;!?()[]{}<>\"'")
        if not token:
            continue
        tokens.append(token)
        tokens.extend(_cjk_expansions(token))
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
    return [
        fixture
        for fixture in config["query_fixtures"]
        if fixture["locale"] == locale
    ]


def _ranking_fixtures_for_locale(locale: str, config: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        fixture
        for fixture in config["ranking_fixtures"]
        if fixture["locale"] == locale
    ]


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
    exact_pool = {
        token
        for field_tokens in fields.values()
        for token in field_tokens
    }
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

    exact_identifier_matches = sorted(query_token_set & set(normalized_fields["identifiers"]))
    title_matches = sorted(query_token_set & set(normalized_fields["title"]))
    alias_token_matches = sorted(query_token_set & set(normalized_fields["aliases"]))
    alias_id_matches = sorted(query_alias_ids & document_alias_ids)
    direct_alias_matches = sorted(
        alias_id
        for alias_id in alias_id_matches
        if "target_topic" in document["normalized"].get("alias_match_sources", {}).get(alias_id, [])
    )
    heading_matches = sorted(query_token_set & set(normalized_fields["headings"]))
    body_matches = sorted(query_token_set & set(normalized_fields["body"]))
    typo_matches = _bounded_typo_matches(query_tokens, document, ranking)

    components = {
        "exact_identifier": len(exact_identifier_matches) * weights["exact_identifier"],
        "title": len(title_matches) * weights["title"],
        "alias": (len(alias_token_matches) + len(alias_id_matches) + len(direct_alias_matches)) * weights["alias"],
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
        ranked = _rank_search_documents(locale, fixture["query"], documents, alias_config, ranking_config)
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
                locale: titles_by_locale[locale].get(anchor_id, anchor_id)
                for locale in LOCALES
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
        topic_id: {
            field: sorted(set(values))
            for field, values in identifiers.items()
        }
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
        fields = metadata.setdefault(policy_id, {"firefox_channel": set(), "policy_category": set()})
        channel_support = policy.get("channel_support", {})
        fields["firefox_channel"].update(channel_support.get("supported_channels", []))

    for policy in inventory["policies"]:
        policy_id = policy["policy_id"]
        fields = metadata.setdefault(policy_id, {"firefox_channel": set(), "policy_category": set()})
        for channel_id, channel in policy.get("channels", {}).items():
            fields["firefox_channel"].add(channel_id)
            ui = channel.get("ui", {})
            if ui.get("section"):
                fields["policy_category"].add(ui["section"])
            fields["policy_category"].update(channel.get("categories", []))

    return {
        policy_id: {
            field: sorted(values)
            for field, values in fields.items()
        }
        for policy_id, fields in metadata.items()
    }


def _cis_facet_metadata() -> dict[str, dict[str, list[str]]]:
    inventory = _read_json_file(CIS_INVENTORY)
    index = _read_json_file(CIS_RECOMMENDATION_INDEX)
    metadata: dict[str, dict[str, set[str]]] = {}
    for topic in index["topics"]:
        recommendation_id = topic["recommendation_id"]
        fields = metadata.setdefault(recommendation_id, {"cis_level": set(), "cis_control_state": set()})
        if topic.get("level"):
            fields["cis_level"].add(f"level-{topic['level']}")
        if topic.get("mapping_status"):
            fields["cis_control_state"].add(topic["mapping_status"])

    for record in index.get("provenance_only_records", []):
        recommendation_id = record["recommendation_id"]
        fields = metadata.setdefault(recommendation_id, {"cis_level": set(), "cis_control_state": set()})
        if record.get("level"):
            fields["cis_level"].add(f"level-{record['level']}")
        fields["cis_control_state"].add("provenance-only")

    for recommendation in inventory["recommendations"]:
        recommendation_id = recommendation["recommendation_id"]
        fields = metadata.setdefault(recommendation_id, {"cis_level": set(), "cis_control_state": set()})
        if recommendation.get("level"):
            fields["cis_level"].add(f"level-{recommendation['level']}")
        if recommendation.get("mapping_status"):
            fields["cis_control_state"].add(recommendation["mapping_status"])
        if recommendation.get("assessment") == "manual":
            fields["cis_control_state"].add("manual-review")

    return {
        recommendation_id: {
            field: sorted(values)
            for field, values in fields.items()
        }
        for recommendation_id, fields in metadata.items()
    }


def _facet_values_from_config(config: dict[str, Any], field: str) -> set[str]:
    return {
        value
        for value in config["facet_fields"][field]["values"]
        if value is not None
    }


def _target_facets_by_topic(target_map: dict[str, Any], config: dict[str, Any]) -> dict[str, dict[str, list[str]]]:
    policy_metadata = _policy_facet_metadata()
    cis_metadata = _cis_facet_metadata()
    allowed_values = {
        field: _facet_values_from_config(config, field)
        for field in config["facet_fields"]
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


def _facet_counts(documents: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, dict[str, int]]:
    counts = {
        field: {
            str(value): 0
            for value in definition["values"]
            if value is not None
        }
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
    active_filters = {
        field: set(values)
        for field, values in filters.items()
        if values
    }
    if not active_filters:
        return documents
    filtered = []
    for document in documents:
        filter_facets = _document_filter_facets(document)
        if all(set(filter_facets.get(field, [])) & values for field, values in active_filters.items()):
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
        filters = {
            field: sorted(values)
            for field, values in fixture["filters"].items()
        }
        filtered = _filter_search_documents(documents, filters)
        results.append(
            {
                "fixture_id": fixture["fixture_id"],
                "locale": locale,
                "filters": filters,
                "url_query": _filter_url_query(filters, config),
                "result_count": len(filtered),
                "result_topic_ids": [document["topic_id"] for document in filtered],
                "empty_result_message": config["empty_result"]["messages"][locale]
                if not filtered
                else None,
            }
        )
    return results


def _quality_fixtures_for_locale(locale: str, config: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        fixture
        for fixture in config["quality_fixtures"]
        if fixture["locale"] == locale
    ]


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
        filters = {
            field: sorted(values)
            for field, values in fixture.get("filters", {}).items()
        }
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
                "top_topic_ids": [
                    result["document"]["topic_id"]
                    for result in visible_ranked[:5]
                ],
                "required_score_component": required_component,
                "required_score_component_value": top["score_breakdown"].get(required_component, 0)
                if top and required_component
                else 0,
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
        if len(_quality_fixtures_for_locale(locale, config)) < coverage["minimum_locale_fixture_count"]:
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
        if any(_contains_control_character(str(value)) for value in [snippet_source, *searchable_values]):
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
        "api": _inventory_gap_report(set(_api_operation_topic_ids()), source_ids_by_kind["api-operation"]),
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
        {
            alias
            for anchor in topic["anchors"].values()
            for alias in anchor.get("aliases", [])
        }
        | {
            alias
            for alias_group in document_alias_groups
            for alias in alias_group["terms"]
        }
    )
    searchable = {
        "title": title,
        "shortdesc": _topic_shortdesc(root),
        "headings": _topic_headings(root, title) or [
            topic["anchors"][anchor_id]["title"][locale]
            for anchor_id in anchor_ids
        ],
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
        "bpm_version": ["0.9.0"],
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
                group["alias_id"]: group["match_sources"]
                for group in document_alias_groups
            },
            "fields": normalized_fields,
            "tokens": _unique_non_empty(
                [
                    token
                    for field_tokens in normalized_fields.values()
                    for token in field_tokens
                ]
            ),
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
            "bpm_version": "0.9.0",
        },
        "filter_facets": filter_facets,
        "versions": {
            "bpm_version": "0.9.0",
            "documentation_version": "0.9.0",
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
    quality_config = _search_quality_performance()
    integrity_config = _search_integrity_drift()
    _validate_quality_fixture_coverage(quality_config)
    identifiers_by_topic = _target_identifiers_by_topic(target_map)
    facets_by_topic = _target_facets_by_topic(target_map, facets_config)
    source_revision = _source_revision()
    documents = [
        _topic_search_document(
            locale,
            topic_id,
            topic,
            identifiers_by_topic,
            facets_by_topic,
            source_revision,
            alias_config,
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
        "quality_contract_id": quality_config["contract_id"],
        "quality_schema_version": quality_config["schema_version"],
        "integrity_contract_id": integrity_config["contract_id"],
        "integrity_schema_version": integrity_config["schema_version"],
        "result_schema_version": contract["result_schema"]["schema_version"],
        "target_bpm_version": contract["target_bpm_version"],
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
            "facet_fields": facets_config["facet_fields"],
            "composition": facets_config["filter_contract"]["composition"],
            "url_state": facets_config["url_state"],
            "empty_result": facets_config["empty_result"]["messages"][locale],
            "filter_fixture_count": len(
                [fixture for fixture in facets_config["filter_fixtures"] if fixture["locale"] == locale]
            ),
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
        "searchable_fields": [
            field["field"]
            for field in contract["corpus"]["searchable_fields"]
        ],
        "result_required_fields": contract["result_schema"]["required_fields"],
        "documents": documents,
    }


def _policy_ids() -> set[str]:
    index = _read_json_file(FIREFOX_POLICY_INDEX)
    return {policy["policy_id"] for policy in index["policies"]}


def _managed_preference_ids() -> set[str]:
    inventory = _read_json_file(FIREFOX_POLICY_INVENTORY)
    return {preference["preference_id"] for preference in inventory["managed_preferences"]}


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
        if target["topic_id"] not in known_capability_topics and not target["topic_id"].startswith("fx-"):
            raise BuildError(f"policy context references unknown user topic: {target['topic_id']}")
        validation_topic_id = target.get("validation_topic_id")
        if validation_topic_id and validation_topic_id not in known_capability_topics:
            raise BuildError(f"policy context references unknown validation topic: {validation_topic_id}")
        for task_topic_id in target.get("user_task_topic_ids", []):
            if task_topic_id not in known_capability_topics:
                raise BuildError(f"policy context references unknown user task topic: {task_topic_id}")
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
                raise BuildError(f"policy context references unknown related policy: {related_policy_id}")
    return assignments


def _target(topic_id: str, kind: str, source_id: str, source_inventory: str, anchor_id: str | None = None) -> dict[str, Any]:
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

    for recommendation_id in sorted(_cis_recommendation_ids()):
        targets[f"cis:{recommendation_id}"] = _target(
            "cis-settings-guide",
            "cis",
            recommendation_id,
            "docs/architecture/cis-documentation-inventory-0.9.0.json",
            "a-cis-settings-guide",
        )

    for operation_id, planned_topic_id in sorted(_api_operation_topic_ids().items()):
        topic_id = planned_topic_id if planned_topic_id in topics else "api-integration-guide"
        anchor_id = None if planned_topic_id in topics else "a-api-integration-guide"
        targets[f"api-operation:{operation_id}"] = _target(
            topic_id,
            "api-operation",
            operation_id,
            "docs/architecture/api-documentation-inventory-0.9.0.md",
            anchor_id,
        )

    for capability_id, topic_id in sorted(_capability_topic_ids().items()):
        targets[f"capability:{capability_id}"] = _target(
            topic_id,
            "capability",
            capability_id,
            "docs/architecture/product-user-capability-inventory-0.9.0.md",
        )

    return {
        "$schema": "schemas/product-documentation-ui-target-map-v1.schema.json",
        "schema_version": 1,
        "manifest_schema_version": 1,
        "bpm_version": "0.9.0",
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
                    raise BuildError(f"missing topic output for {locale}/{child_topic_id}: {output_path}")
                child_output[locale] = output_path.relative_to(site_root).as_posix()
            topics[child_topic_id] = {
                "guide_id": guide_id,
                "dita_key": keyref,
                "source_slug": child_topic_id,
                "url_path": child_topic_id,
                "kind": _topic_kind(roots["en"]),
                "title": {
                    locale: _element_text(root.find("title"))
                    for locale, root in roots.items()
                },
                "anchors": _topic_anchor_titles(roots),
                "output": child_output,
                "_url_root": url_root,
                "_roots": roots,
                "_source_paths": {
                    locale: hrefs_by_locale[locale][keyref]
                    for locale in LOCALES
                },
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
            "bpm_version": "0.9.0",
            "documentation_version": "0.9.0",
            "build_id": _manifest_build_id(site_root),
            "source_revision": _source_revision(),
            "dita_ot_version": _load_lock()["components"]["dita_ot"]["version"],
        },
        "locales": list(LOCALES),
        "default_locale": "en",
        "guides": _build_guides(topics),
        "topics": topics,
        "assets": {},
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


def _validate_target_map_semantics(target_map: dict[str, Any], manifest: dict[str, Any]) -> None:
    topics = manifest["topics"]
    policy_ids = _policy_ids()
    preference_ids = _managed_preference_ids()
    cis_recommendation_ids = _cis_recommendation_ids()
    api_operation_ids = set(_api_operation_topic_ids())
    capability_ids = set(_capability_topic_ids())
    for target_id, target in target_map["targets"].items():
        expected_key = f"{target['kind']}:{target['source_id']}"
        if target_id != expected_key:
            raise BuildError(f"target key does not match kind/source_id: {target_id}")
        source_id = target["source_id"]
        if target["kind"] == "topic" and source_id not in topics:
            raise BuildError(f"target references unknown topic source: {target_id}")
        if target["kind"] == "policy" and source_id not in policy_ids:
            raise BuildError(f"target references unknown policy source: {target_id}")
        if target["kind"] == "known-preference" and source_id not in preference_ids:
            raise BuildError(f"target references unknown known-preference source: {target_id}")
        if target["kind"] == "cis" and source_id not in cis_recommendation_ids:
            raise BuildError(f"target references unknown CIS recommendation source: {target_id}")
        if target["kind"] == "api-operation" and source_id not in api_operation_ids:
            raise BuildError(f"target references unknown API operation source: {target_id}")
        if target["kind"] == "capability" and source_id not in capability_ids:
            raise BuildError(f"target references unknown capability source: {target_id}")
        topic_id = target["topic_id"]
        if topic_id not in topics:
            raise BuildError(f"target references unknown topic: {target_id}")
        anchor_id = target.get("anchor_id")
        if anchor_id and anchor_id not in topics[topic_id]["anchors"]:
            raise BuildError(f"target references unknown anchor: {target_id} -> {anchor_id}")


def _validate_manifest_semantics(manifest: dict[str, Any], target_map: dict[str, Any]) -> None:
    if manifest["locales"] != list(LOCALES) or target_map["locales"] != list(LOCALES):
        raise BuildError("manifest and target map must use the exact locale matrix")
    if target_map["manifest_schema_version"] != manifest["schema_version"]:
        raise BuildError("target map schema version does not match manifest schema version")
    topics = manifest["topics"]
    for guide_id, guide in manifest["guides"].items():
        home_topic_id = guide["home_topic_id"]
        if home_topic_id not in topics:
            raise BuildError(f"guide {guide_id} references missing home topic {home_topic_id}")
        if topics[home_topic_id]["guide_id"] != guide_id:
            raise BuildError(f"guide {guide_id} home topic is owned by another guide")
    seen_paths: set[str] = set()
    seen_slugs: set[str] = set()
    for topic_id, topic in topics.items():
        if topic["dita_key"] != f"topic.{topic_id}":
            raise BuildError(f"topic {topic_id} has inconsistent DITA key")
        slug_key = topic["source_slug"].casefold()
        if slug_key in seen_slugs:
            raise BuildError(f"duplicate topic source slug after case-folding: {topic['source_slug']}")
        seen_slugs.add(slug_key)
        guide_root = manifest["guides"][topic["guide_id"]]["url_root"]
        public_path = f"{guide_root}/{topic['url_path']}".casefold()
        if public_path in seen_paths:
            raise BuildError(f"duplicate topic public path: {public_path}")
        seen_paths.add(public_path)
        for locale in LOCALES:
            if locale not in topic["title"] or locale not in topic["output"]:
                raise BuildError(f"topic {topic_id} lacks locale data for {locale}")
    _validate_target_map_semantics(target_map, manifest)


def _validate_search_index_semantics(
    locale: str,
    search_payload: dict[str, Any],
    manifest: dict[str, Any],
    target_map: dict[str, Any],
) -> None:
    contract = _read_json_file(SEARCH_CORPUS_CONTRACT)
    alias_config = _search_normalization_aliases()
    ranking_config = _search_ranking_typo()
    facets_config = _search_facets_filters()
    quality_config = _search_quality_performance()
    integrity_config = _search_integrity_drift()
    _validate_quality_fixture_coverage(quality_config)
    if search_payload.get("contract_id") != contract["contract_id"]:
        raise BuildError(f"search index contract mismatch for {locale}")
    if search_payload.get("normalization_contract_id") != alias_config["contract_id"]:
        raise BuildError(f"search index normalization contract mismatch for {locale}")
    if search_payload.get("normalization_schema_version") != alias_config["schema_version"]:
        raise BuildError(f"search index normalization schema mismatch for {locale}")
    if search_payload.get("ranking_contract_id") != ranking_config["contract_id"]:
        raise BuildError(f"search index ranking contract mismatch for {locale}")
    if search_payload.get("ranking_schema_version") != ranking_config["schema_version"]:
        raise BuildError(f"search index ranking schema mismatch for {locale}")
    if search_payload.get("facets_contract_id") != facets_config["contract_id"]:
        raise BuildError(f"search index facets contract mismatch for {locale}")
    if search_payload.get("facets_schema_version") != facets_config["schema_version"]:
        raise BuildError(f"search index facets schema mismatch for {locale}")
    if search_payload.get("quality_contract_id") != quality_config["contract_id"]:
        raise BuildError(f"search index quality contract mismatch for {locale}")
    if search_payload.get("quality_schema_version") != quality_config["schema_version"]:
        raise BuildError(f"search index quality schema mismatch for {locale}")
    if search_payload.get("integrity_contract_id") != integrity_config["contract_id"]:
        raise BuildError(f"search index integrity contract mismatch for {locale}")
    if search_payload.get("integrity_schema_version") != integrity_config["schema_version"]:
        raise BuildError(f"search index integrity schema mismatch for {locale}")
    if search_payload.get("status") != "ready":
        raise BuildError(f"search index is not ready for {locale}")
    if search_payload.get("locale") != locale:
        raise BuildError(f"search index locale mismatch for {locale}")
    if search_payload.get("search_mode") != "deterministic-local-static":
        raise BuildError(f"search index mode mismatch for {locale}")
    if search_payload.get("non_ai_boundary") != "no-ai-no-rag-no-embeddings-no-generative-answers":
        raise BuildError(f"search index non-AI boundary mismatch for {locale}")
    if search_payload.get("allowlisted_cross_locale_fields") != ["identifiers"]:
        raise BuildError(f"search index cross-locale allowlist mismatch for {locale}")

    fixtures = search_payload.get("query_fixtures")
    expected_fixtures = _query_fixtures_for_locale(locale, alias_config)
    if fixtures != expected_fixtures:
        raise BuildError(f"search index query fixtures mismatch for {locale}")
    normalization = search_payload.get("normalization", {})
    if normalization.get("alias_group_count") != len(alias_config["alias_groups"]):
        raise BuildError(f"search index alias group count mismatch for {locale}")
    if normalization.get("query_fixture_count") != len(expected_fixtures):
        raise BuildError(f"search index query fixture count mismatch for {locale}")
    ranking = search_payload.get("ranking", {})
    expected_ranking_fixtures = _ranking_fixtures_for_locale(locale, ranking_config)
    if ranking.get("ranking_order") != ranking_config["ranking_order"]:
        raise BuildError(f"search index ranking order mismatch for {locale}")
    if ranking.get("weights") != ranking_config["weights"]:
        raise BuildError(f"search index ranking weights mismatch for {locale}")
    if ranking.get("typo_tolerance") != ranking_config["typo_tolerance"]:
        raise BuildError(f"search index typo tolerance mismatch for {locale}")
    if ranking.get("ranking_fixture_count") != len(expected_ranking_fixtures):
        raise BuildError(f"search index ranking fixture count mismatch for {locale}")
    filtering = search_payload.get("filtering", {})
    expected_filter_fixtures = [
        fixture
        for fixture in facets_config["filter_fixtures"]
        if fixture["locale"] == locale
    ]
    if filtering.get("facet_fields") != facets_config["facet_fields"]:
        raise BuildError(f"search index facet fields mismatch for {locale}")
    if filtering.get("composition") != facets_config["filter_contract"]["composition"]:
        raise BuildError(f"search index filter composition mismatch for {locale}")
    if filtering.get("url_state") != facets_config["url_state"]:
        raise BuildError(f"search index filter URL state mismatch for {locale}")
    if filtering.get("empty_result") != facets_config["empty_result"]["messages"][locale]:
        raise BuildError(f"search index empty result message mismatch for {locale}")
    if filtering.get("filter_fixture_count") != len(expected_filter_fixtures):
        raise BuildError(f"search index filter fixture count mismatch for {locale}")
    quality = search_payload.get("quality", {})
    expected_quality_fixtures = _quality_fixtures_for_locale(locale, quality_config)
    if quality.get("categories") != quality_config["coverage_requirements"]["categories"]:
        raise BuildError(f"search index quality categories mismatch for {locale}")
    if quality.get("fixture_count") != len(expected_quality_fixtures):
        raise BuildError(f"search index quality fixture count mismatch for {locale}")
    if quality.get("thresholds") != quality_config["quality_thresholds"]:
        raise BuildError(f"search index quality thresholds mismatch for {locale}")
    for fixture in expected_fixtures:
        query_tokens = _normalize_search_text(locale, fixture["query"], alias_config)
        if not set(fixture["expected_tokens"]) <= set(query_tokens):
            raise BuildError(f"search fixture expected tokens are not resolved: {fixture['fixture_id']}")
        resolved_aliases = set(_resolve_search_query_aliases(locale, fixture["query"], alias_config))
        if not set(fixture["expected_alias_ids"]) <= resolved_aliases:
            raise BuildError(f"search fixture expected aliases are not resolved: {fixture['fixture_id']}")

    documents = search_payload.get("documents")
    if not isinstance(documents, list) or len(documents) != len(manifest["topics"]):
        raise BuildError(f"search index document count mismatch for {locale}")

    document_ids: set[str] = set()
    required_searchable = set(contract["document_schema"]["searchable"]["required_fields"])
    required_facets = set(contract["document_schema"]["facets"]["required_fields"])
    known_alias_ids = {alias_group["alias_id"] for alias_group in alias_config["alias_groups"]}
    for document in documents:
        topic_id = document.get("topic_id")
        if topic_id not in manifest["topics"]:
            raise BuildError(f"search index references unknown topic for {locale}: {topic_id}")
        topic = manifest["topics"][topic_id]
        expected_output = topic["output"][locale]
        expected_url = f"/help/{expected_output}"
        document_id = document.get("document_id")
        if document_id in document_ids:
            raise BuildError(f"duplicate search document ID for {locale}: {document_id}")
        document_ids.add(document_id)
        if document_id != f"{locale}:{topic_id}" or document.get("locale") != locale:
            raise BuildError(f"search document identity mismatch for {locale}/{topic_id}")
        if document.get("guide_id") != topic["guide_id"] or document.get("topic_kind") != topic["kind"]:
            raise BuildError(f"search document manifest metadata mismatch for {locale}/{topic_id}")
        if document.get("url") != expected_url or not expected_url.startswith(f"/help/{locale}/"):
            raise BuildError(f"search document URL mismatch for {locale}/{topic_id}")

        source = document.get("source", {})
        if source.get("topic_id") != topic_id or source.get("output_path") != expected_output:
            raise BuildError(f"search document source mismatch for {locale}/{topic_id}")
        searchable = document.get("searchable", {})
        if set(searchable) != required_searchable:
            raise BuildError(f"search document searchable fields mismatch for {locale}/{topic_id}")
        if not isinstance(searchable.get("title"), str) or not searchable["title"]:
            raise BuildError(f"search document title is missing for {locale}/{topic_id}")
        if not isinstance(searchable.get("body"), str) or not searchable["body"]:
            raise BuildError(f"search document body is missing for {locale}/{topic_id}")
        for field in ("headings", "keywords", "identifiers", "aliases"):
            if not isinstance(searchable.get(field), list):
                raise BuildError(f"search document {field} is not a list for {locale}/{topic_id}")
        if topic_id not in searchable["identifiers"] or topic["guide_id"] not in searchable["identifiers"]:
            raise BuildError(f"search document identifiers are incomplete for {locale}/{topic_id}")
        normalized = document.get("normalized", {})
        normalized_fields = normalized.get("fields", {})
        normalized_tokens = normalized.get("tokens", [])
        alias_ids = normalized.get("alias_ids", [])
        if set(normalized_fields) != required_searchable:
            raise BuildError(f"search document normalized fields mismatch for {locale}/{topic_id}")
        if not isinstance(normalized_tokens, list) or not normalized_tokens:
            raise BuildError(f"search document normalized tokens are missing for {locale}/{topic_id}")
        if not set(alias_ids) <= known_alias_ids:
            raise BuildError(f"search document aliases reference unknown group for {locale}/{topic_id}")

        facets = document.get("facets", {})
        if set(facets) != required_facets:
            raise BuildError(f"search document facets mismatch for {locale}/{topic_id}")
        if facets["locale"] != locale or facets["guide_id"] != topic["guide_id"]:
            raise BuildError(f"search document facet values mismatch for {locale}/{topic_id}")
        filter_facets = document.get("filter_facets", {})
        if set(filter_facets) != set(facets_config["facet_fields"]):
            raise BuildError(f"search document filter facets mismatch for {locale}/{topic_id}")
        for field, values in filter_facets.items():
            if not isinstance(values, list):
                raise BuildError(f"search document filter facet is not a list for {locale}/{topic_id}/{field}")
            allowed_values = _facet_values_from_config(facets_config, field)
            unknown_values = set(values) - allowed_values
            if unknown_values:
                raise BuildError(
                    f"search document filter facet has undeclared values for {locale}/{topic_id}/{field}: "
                    f"{sorted(unknown_values)}"
                )
        if filter_facets["locale"] != [locale] or filter_facets["guide_id"] != [topic["guide_id"]]:
            raise BuildError(f"search document filter identity facets mismatch for {locale}/{topic_id}")

    if search_payload.get("facet_counts") != _facet_counts(documents, facets_config):
        raise BuildError(f"search index facet counts mismatch for {locale}")

    expected_integrity_report = _search_integrity_report(
        locale,
        documents,
        manifest["topics"],
        target_map,
        integrity_config,
    )
    if search_payload.get("integrity_report") != expected_integrity_report:
        raise BuildError(f"search index integrity report mismatch for {locale}")
    if expected_integrity_report["status"] != "pass" or expected_integrity_report["failure_count"] != 0:
        raise BuildError(f"search index integrity drift detected for {locale}")

    expected_results = _ranking_fixture_results(
        locale,
        documents,
        alias_config,
        ranking_config,
    )
    if search_payload.get("ranking_fixture_results") != expected_results:
        raise BuildError(f"search index ranking fixture results mismatch for {locale}")
    result_by_id = {result["fixture_id"]: result for result in expected_results}
    for fixture in expected_ranking_fixtures:
        result = result_by_id.get(fixture["fixture_id"])
        if result is None:
            raise BuildError(f"missing ranking fixture result: {fixture['fixture_id']}")
        if result["top_topic_id"] != fixture["expected_top_topic_id"]:
            raise BuildError(f"ranking fixture top result mismatch: {fixture['fixture_id']}")
        component = fixture["required_score_component"]
        if result["score_breakdown"].get(component, 0) <= 0:
            raise BuildError(f"ranking fixture component missing: {fixture['fixture_id']}/{component}")

    expected_filter_results = _filter_fixture_results(locale, documents, facets_config)
    if search_payload.get("filter_fixture_results") != expected_filter_results:
        raise BuildError(f"search index filter fixture results mismatch for {locale}")
    filter_results_by_id = {
        result["fixture_id"]: result
        for result in expected_filter_results
    }
    for fixture in expected_filter_fixtures:
        result = filter_results_by_id.get(fixture["fixture_id"])
        if result is None:
            raise BuildError(f"missing filter fixture result: {fixture['fixture_id']}")
        if "expected_count" in fixture and result["result_count"] != fixture["expected_count"]:
            raise BuildError(f"filter fixture count mismatch: {fixture['fixture_id']}")
        if result["result_count"] < fixture.get("expected_min_count", 0):
            raise BuildError(f"filter fixture minimum count mismatch: {fixture['fixture_id']}")
        if not set(fixture.get("must_include_topic_ids", [])) <= set(result["result_topic_ids"]):
            raise BuildError(f"filter fixture missing expected topics: {fixture['fixture_id']}")
        if fixture.get("expected_empty") and (
            result["result_count"] != 0 or not result["empty_result_message"]
        ):
            raise BuildError(f"filter fixture empty-result recovery mismatch: {fixture['fixture_id']}")
        if fixture["filters"] and not result["url_query"]:
            raise BuildError(f"filter fixture URL state is missing: {fixture['fixture_id']}")

    expected_quality_results = _quality_fixture_results(
        locale,
        documents,
        alias_config,
        ranking_config,
        quality_config,
    )
    if search_payload.get("quality_fixture_results") != expected_quality_results:
        raise BuildError(f"search index quality fixture results mismatch for {locale}")
    quality_results_by_id = {
        result["fixture_id"]: result
        for result in expected_quality_results
    }
    for fixture in expected_quality_fixtures:
        result = quality_results_by_id.get(fixture["fixture_id"])
        if result is None:
            raise BuildError(f"missing quality fixture result: {fixture['fixture_id']}")
        if "expected_count" in fixture and result["result_count"] != fixture["expected_count"]:
            raise BuildError(f"quality fixture count mismatch: {fixture['fixture_id']}")
        if fixture.get("expected_top_topic_id") and result["top_topic_id"] != fixture["expected_top_topic_id"]:
            raise BuildError(f"quality fixture top result mismatch: {fixture['fixture_id']}")
        component = fixture.get("required_score_component")
        if component and result["required_score_component_value"] <= 0:
            raise BuildError(f"quality fixture score component missing: {fixture['fixture_id']}/{component}")
        if result["visible_result_count"] > quality_config["performance_budget"]["max_visible_results_per_query"]:
            raise BuildError(f"quality fixture visible result budget exceeded: {fixture['fixture_id']}")

    expected_performance = _quality_performance_report(documents, expected_quality_results, quality_config)
    if search_payload.get("performance_report") != expected_performance:
        raise BuildError(f"search index performance report mismatch for {locale}")
    budget = quality_config["performance_budget"]
    if expected_performance["document_count"] > budget["max_documents_per_locale"]:
        raise BuildError(f"search index document performance budget exceeded for {locale}")
    if expected_performance["quality_fixture_count"] > budget["max_quality_fixtures_per_locale"]:
        raise BuildError(f"search index quality fixture budget exceeded for {locale}")
    if expected_performance["deterministic_scan_units"] > budget["max_deterministic_scan_units_per_locale"]:
        raise BuildError(f"search index deterministic scan budget exceeded for {locale}")


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


def _run(command: list[str], env: dict[str, str]) -> None:
    completed = subprocess.run(command, env=env, text=True, capture_output=True, check=False)
    if completed.returncode:
        output = (completed.stdout + "\n" + completed.stderr).strip()
        raise BuildError(f"DITA command failed ({' '.join(command)}):\n{output[-12000:]}")


def build_tree(destination: Path) -> None:
    dita, java_home = toolchain()
    source_before = source_hashes()
    destination.mkdir(parents=True, exist_ok=False)
    temp_root = destination.parent / f".{destination.name}-dita-temp"
    temp_root.mkdir(parents=True, exist_ok=False)
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
    try:
        for locale in LOCALES:
            maintained_source = DOCUMENTATION_ROOT / f"src/dita/{locale}/maps/portal.ditamap"
            if not maintained_source.is_file():
                raise BuildError(f"missing locale portal map: {maintained_source}")
            locale_workspace = temp_root / locale
            input_root = locale_workspace / "input"
            shutil.copytree(DOCUMENTATION_ROOT / "src", input_root / "src")
            shutil.copytree(DOCUMENTATION_ROOT / "assets", input_root / "assets")
            source = input_root / f"src/dita/{locale}/maps/portal.ditamap"
            print(f"DITA publish: {locale}", flush=True)
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
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)
    if source_hashes() != source_before:
        raise BuildError("DITA transform mutated maintained documentation source or assets")
    _normalize_locale_root_links(destination)
    apply_portal_shell(destination)
    generate_manifest_files(destination)
    validate_output(destination)


def tree_hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def source_hashes() -> dict[str, str]:
    roots = (DOCUMENTATION_ROOT / "src", DOCUMENTATION_ROOT / "assets")
    return {
        path.relative_to(DOCUMENTATION_ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for root in roots
        for path in sorted(root.rglob("*"))
        if path.is_file()
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
        MANIFEST_SCHEMA,
        UI_TARGET_SCHEMA,
        DOCUMENTATION_ROOT / "config/metadata-vocabulary.json",
        DOCUMENTATION_ROOT / "config/user-guide-map-0.9.0.json",
        LOCK_PATH,
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
        "bpm_version": policy["target_bpm_version"],
        "documentation_version": policy["target_bpm_version"],
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
            with tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as bundle:
                paths = [root, *sorted(root.rglob("*"), key=lambda path: path.as_posix().lower())]
                for path in paths:
                    arcname = path.relative_to(root.parent).as_posix()
                    bundle.add(path, arcname=arcname, recursive=False, filter=_tar_filter)


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


def publish() -> None:
    validate_sources()
    BUILD_ROOT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".publish-", dir=BUILD_ROOT) as temporary:
        candidate = Path(temporary) / "site"
        build_tree(candidate)
        destination = BUILD_ROOT / "site"
        previous = BUILD_ROOT / ".site-previous"
        shutil.rmtree(previous, ignore_errors=True)
        if destination.exists():
            destination.replace(previous)
        try:
            candidate.replace(destination)
        except OSError:
            if previous.exists():
                previous.replace(destination)
            raise
        shutil.rmtree(previous, ignore_errors=True)
    print(f"Published documentation to {destination.relative_to(REPOSITORY_ROOT)}", flush=True)


def _remove_path(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink(missing_ok=True)


def _dev_site_is_current(source_fingerprint: str) -> bool:
    if not DEV_SITE_ROOT.is_dir() or not DEV_SITE_METADATA.is_file():
        return False
    try:
        metadata = json.loads(DEV_SITE_METADATA.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
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
    candidate = destination.parent / f".{destination.name}-candidate"
    previous = destination.parent / f".{destination.name}-previous"
    _remove_path(candidate)
    _remove_path(previous)
    shutil.copytree(source, candidate)
    validate_manifest_files(candidate)
    if destination.exists():
        destination.replace(previous)
    try:
        candidate.replace(destination)
    except OSError:
        if previous.exists():
            previous.replace(destination)
        raise
    finally:
        _remove_path(candidate)
        _remove_path(previous)


def install_dev_site() -> None:
    """Install the locally built documentation site into the BPM dev runtime path."""

    source_fingerprint = _source_fingerprint()
    if _dev_site_is_current(source_fingerprint):
        print(
            f"Installed dev documentation is current at {DEV_SITE_ROOT.relative_to(REPOSITORY_ROOT)}",
            flush=True,
        )
        return

    publish()
    source = BUILD_ROOT / "site"
    _promote_dev_site(source, DEV_SITE_ROOT)
    metadata = {
        "schema_version": 1,
        "bpm_version": _artifact_policy()["target_bpm_version"],
        "source_fingerprint": source_fingerprint,
        "source_site": source.relative_to(REPOSITORY_ROOT).as_posix(),
        "installed_site": DEV_SITE_ROOT.relative_to(REPOSITORY_ROOT).as_posix(),
    }
    DEV_SITE_METADATA.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        f"Installed dev documentation to {DEV_SITE_ROOT.relative_to(REPOSITORY_ROOT)}",
        flush=True,
    )


def validate_build() -> None:
    validate_sources()
    BUILD_ROOT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".validate-", dir=BUILD_ROOT) as temporary:
        build_tree(Path(temporary) / "site")
    print("DITA, metadata, source links, and generated links are valid.", flush=True)


def reproducibility_check() -> None:
    validate_sources()
    BUILD_ROOT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".reproducibility-", dir=BUILD_ROOT) as temporary:
        root = Path(temporary)
        first = root / "first"
        second = root / "second"
        build_tree(first)
        build_tree(second)
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
    archive.unlink(missing_ok=True)
    checksum_file.unlink(missing_ok=True)
    try:
        validate_sources()
        with tempfile.TemporaryDirectory(prefix=".package-", dir=DIST_ROOT) as temporary:
            staging = Path(temporary)
            root = staging / policy["archive"]["root"]
            build_tree(root)
            licenses = root / "licenses"
            licenses.mkdir()
            shutil.copyfile(REPOSITORY_ROOT / "LICENSE", licenses / "BPM-MPL-2.0.txt")
            shutil.copyfile(
                DOCUMENTATION_ROOT / "config/THIRD_PARTY_NOTICES.md",
                licenses / "THIRD_PARTY_NOTICES.md",
            )
            _write_integrity(root, policy)
            candidate = staging / archive.name
            create_archive(root, candidate)
            digest = verify_archive(candidate, policy)
            candidate_checksum = staging / checksum_file.name
            candidate_checksum.write_text(f"{digest}  {archive.name}\n", encoding="ascii")
            candidate.replace(archive)
            candidate_checksum.replace(checksum_file)
    except Exception:
        archive.unlink(missing_ok=True)
        checksum_file.unlink(missing_ok=True)
        raise
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=(
            "validate",
            "build",
            "install-dev",
            "fast-check",
            "reproducibility",
            "package",
            "package-verify",
        ),
    )
    parser.add_argument("paths", nargs="*", help="changed documentation paths for fast-check")
    args = parser.parse_args()
    try:
        {
            "validate": validate_build,
            "build": publish,
            "install-dev": install_dev_site,
            "fast-check": lambda: fast_check(args.paths),
            "reproducibility": reproducibility_check,
            "package": package,
            "package-verify": verify_package,
        }[args.command]()
    except (BuildError, OSError) as exc:
        print(f"documentation build failed: {exc}", file=sys.stderr)
        if args.command == "fast-check":
            diagnostic = write_failure_diagnostic(exc, args.paths)
            print(
                f"diagnostic artifact: {diagnostic.relative_to(REPOSITORY_ROOT)}",
                file=sys.stderr,
            )
            print(
                f"focused rerun: {_diagnostic_payload(exc, args.paths)['focused_rerun']}",
                file=sys.stderr,
            )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
