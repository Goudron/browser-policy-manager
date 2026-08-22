"""Runtime resolver for packaged product-documentation manifest targets."""

from __future__ import annotations

import hashlib
import json
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

from app.core.config import get_settings
from app.core.locales import ACTIVE_CATALOG_LOCALES

SUPPORTED_DOCUMENTATION_MANIFEST_SCHEMA_VERSION: Final[int] = 1
SUPPORTED_DOCUMENTATION_UI_TARGET_MAP_SCHEMA_VERSION: Final[int] = 1
DOCUMENTATION_HOME_TARGET_ID: Final[str] = "topic:user-guide"
DOCUMENTATION_CONTEXTUAL_HELP_TARGET_IDS: Final[dict[str, str]] = {
    "library": "topic:ug-task-use-profile-library",
    "compare": "topic:ug-task-compare-profiles",
    "guided": "topic:ug-task-use-guided-editor",
    "settings": "topic:ug-task-use-all-settings",
    "json": "topic:ug-task-use-json-editor",
}
DOCUMENTATION_DEEP_HELP_TARGET_IDS: Final[dict[str, str]] = {
    "preparation-create": "topic:ug-task-create-first-profile",
    "preparation-duplicate": "topic:ug-task-duplicate-profile",
    "guided-urls-sites-navigation": "policy:Homepage",
    "guided-certificates-trust": "policy:Certificates",
    "guided-extensions": "policy:ExtensionSettings",
    "policy-ai-controls": "policy:AIControls",
    "policy-visual-search-enabled": "policy:VisualSearchEnabled",
    "cis-baseline-selection": "cis:1.1.1.1",
    "validation": "topic:ug-task-validate-profile",
    "import-firefox-policies": "topic:ug-task-import-policies-json",
    "export-firefox-policies": "topic:ug-task-export-policies-json",
}
DOCUMENTATION_LOCALES: Final[tuple[str, ...]] = tuple(ACTIVE_CATALOG_LOCALES)


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _load_json_object(path: Path) -> dict[str, Any]:
    value = json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=_reject_duplicate_pairs,
    )
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} must be a JSON object")
    return value


def _safe_artifact_path(raw_path: str) -> Path | None:
    decoded = urllib.parse.unquote(raw_path).replace("\\", "/")
    if "\x00" in decoded or decoded.startswith("/"):
        return None
    parts = [part for part in decoded.split("/") if part not in {"", "."}]
    if not parts or any(part == ".." for part in parts):
        return None
    return Path(*parts)


def _resolve_artifact_file(site_root: Path, raw_path: str) -> Path | None:
    safe_path = _safe_artifact_path(raw_path)
    if safe_path is None:
        return None
    root = site_root.resolve()
    candidate = (root / safe_path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    return candidate if candidate.is_file() else None


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _manifest_bpm_version(manifest: dict[str, Any]) -> str | None:
    artifact = manifest.get("artifact")
    if not isinstance(artifact, dict):
        return None
    version = artifact.get("bpm_version")
    return version if isinstance(version, str) and version else None


@dataclass(frozen=True)
class DocumentationCatalog:
    """Validated documentation manifest plus UI target map."""

    site_root: Path
    manifest: dict[str, Any]
    target_map: dict[str, Any]
    locales: tuple[str, ...]
    default_locale: str

    def resolve_target_url(self, target_id: str, locale: str) -> str | None:
        active_locale = locale if locale in self.locales else self.default_locale
        targets = self.target_map.get("targets")
        topics = self.manifest.get("topics")
        if not isinstance(targets, dict) or not isinstance(topics, dict):
            return None

        target = targets.get(target_id)
        if not isinstance(target, dict):
            return None

        topic_id = target.get("topic_id")
        if not isinstance(topic_id, str):
            return None
        topic = topics.get(topic_id)
        if not isinstance(topic, dict):
            return None

        anchor_id = target.get("anchor_id")
        if anchor_id is not None:
            anchors = topic.get("anchors")
            if (
                not isinstance(anchor_id, str)
                or not isinstance(anchors, dict)
                or anchor_id not in anchors
            ):
                return None

        outputs = topic.get("output")
        if not isinstance(outputs, dict):
            return None
        output = outputs.get(active_locale)
        if not isinstance(output, str):
            return None

        if _resolve_artifact_file(self.site_root, output) is None:
            return None

        fragment = f"#{urllib.parse.quote(anchor_id, safe='-._~')}" if anchor_id else ""
        return f"/help/{output}{fragment}"

    def locale_urls_for_target(self, target_id: str) -> dict[str, str] | None:
        urls: dict[str, str] = {}
        for locale in self.locales:
            url = self.resolve_target_url(target_id, locale)
            if url is None:
                return None
            urls[locale] = url
        return urls


def _validate_manifest_identity(manifest: dict[str, Any]) -> tuple[str, ...]:
    if manifest.get("schema_version") != SUPPORTED_DOCUMENTATION_MANIFEST_SCHEMA_VERSION:
        raise ValueError("unsupported documentation manifest schema version")

    locales = manifest.get("locales")
    if (
        not isinstance(locales, list)
        or not all(isinstance(locale, str) for locale in locales)
        or tuple(locales) != DOCUMENTATION_LOCALES
    ):
        raise ValueError("documentation manifest locale matrix mismatch")

    default_locale = manifest.get("default_locale")
    if default_locale not in DOCUMENTATION_LOCALES:
        raise ValueError("documentation manifest default locale mismatch")

    bpm_version = _manifest_bpm_version(manifest)
    if bpm_version != get_settings().APP_VERSION:
        raise ValueError("documentation manifest BPM version mismatch")
    artifact = manifest.get("artifact")
    if not isinstance(artifact, dict) or artifact.get("documentation_version") != bpm_version:
        raise ValueError("documentation manifest compatibility version mismatch")

    return tuple(locales)


def _load_validated_target_map(site_root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    ui_target_map = manifest.get("ui_target_map")
    if not isinstance(ui_target_map, dict):
        raise ValueError("documentation manifest target-map metadata is missing")

    target_map_path = ui_target_map.get("path")
    if not isinstance(target_map_path, str):
        raise ValueError("documentation target-map path is missing")
    target_map_file = _resolve_artifact_file(site_root, target_map_path)
    if target_map_file is None:
        raise ValueError("documentation target-map file is missing")

    expected_sha256 = ui_target_map.get("sha256")
    if not isinstance(expected_sha256, str) or _sha256(target_map_file) != expected_sha256:
        raise ValueError("documentation target-map digest mismatch")

    target_map = _load_json_object(target_map_file)
    if target_map.get("schema_version") != SUPPORTED_DOCUMENTATION_UI_TARGET_MAP_SCHEMA_VERSION:
        raise ValueError("unsupported documentation target-map schema version")
    if ui_target_map.get("schema_version") != target_map.get("schema_version"):
        raise ValueError("documentation target-map schema mismatch")
    if target_map.get("manifest_schema_version") != manifest.get("schema_version"):
        raise ValueError("documentation manifest/target-map schema mismatch")
    if tuple(target_map.get("locales", ())) != DOCUMENTATION_LOCALES:
        raise ValueError("documentation target-map locale matrix mismatch")
    if target_map.get("bpm_version") != _manifest_bpm_version(manifest):
        raise ValueError("documentation target-map BPM version mismatch")
    if not isinstance(target_map.get("targets"), dict):
        raise ValueError("documentation target-map targets are missing")
    return target_map


def _validate_topic_outputs(site_root: Path, manifest: dict[str, Any]) -> None:
    topics = manifest.get("topics")
    if not isinstance(topics, dict) or not topics:
        raise ValueError("documentation topics are missing")

    for topic_id, topic in topics.items():
        if not isinstance(topic_id, str) or not isinstance(topic, dict):
            raise ValueError("documentation topic registry is malformed")
        outputs = topic.get("output")
        anchors = topic.get("anchors")
        if not isinstance(outputs, dict) or not isinstance(anchors, dict):
            raise ValueError(f"documentation topic {topic_id} is incomplete")
        for locale in DOCUMENTATION_LOCALES:
            output = outputs.get(locale)
            if not isinstance(output, str) or _resolve_artifact_file(site_root, output) is None:
                raise ValueError(f"documentation topic {topic_id} has a broken {locale} output")


def _validate_targets(manifest: dict[str, Any], target_map: dict[str, Any]) -> None:
    topics = manifest.get("topics")
    targets = target_map.get("targets")
    if not isinstance(topics, dict) or not isinstance(targets, dict):
        raise ValueError("documentation targets are malformed")

    for target_id, target in targets.items():
        if not isinstance(target_id, str) or not isinstance(target, dict):
            raise ValueError("documentation target registry is malformed")
        kind = target.get("kind")
        source_id = target.get("source_id")
        if not isinstance(kind, str) or not isinstance(source_id, str):
            raise ValueError(f"documentation target {target_id} is incomplete")
        if target_id != f"{kind}:{source_id}":
            raise ValueError(f"documentation target {target_id} identity mismatch")

        topic_id = target.get("topic_id")
        if not isinstance(topic_id, str) or topic_id not in topics:
            raise ValueError(f"documentation target {target_id} references an unknown topic")
        topic = topics[topic_id]
        if not isinstance(topic, dict):
            raise ValueError(f"documentation target {target_id} topic is malformed")

        anchor_id = target.get("anchor_id")
        if anchor_id is not None:
            anchors = topic.get("anchors")
            if (
                not isinstance(anchor_id, str)
                or not isinstance(anchors, dict)
                or anchor_id not in anchors
            ):
                raise ValueError(f"documentation target {target_id} references an unknown anchor")


def load_documentation_catalog(site_root: Path | None = None) -> DocumentationCatalog | None:
    """Return a validated documentation catalog, or ``None`` when it must fail closed."""

    root = site_root or Path(get_settings().DOCUMENTATION_SITE_DIR)
    if not root.is_absolute():
        root = get_settings().ROOT_DIR / root

    manifest_path = root / "manifest.json"
    if not manifest_path.is_file():
        return None

    try:
        manifest = _load_json_object(manifest_path)
        locales = _validate_manifest_identity(manifest)
        target_map = _load_validated_target_map(root, manifest)
        _validate_topic_outputs(root, manifest)
        _validate_targets(manifest, target_map)
    except OSError, ValueError, json.JSONDecodeError:
        return None

    default_locale = manifest["default_locale"]
    return DocumentationCatalog(
        site_root=root,
        manifest=manifest,
        target_map=target_map,
        locales=locales,
        default_locale=default_locale,
    )


def documentation_artifact_problem(site_root: Path | None = None) -> str | None:
    """Classify an unavailable documentation artifact without exposing parser errors."""

    root = site_root or Path(get_settings().DOCUMENTATION_SITE_DIR)
    if not root.is_absolute():
        root = get_settings().ROOT_DIR / root

    manifest_path = root / "manifest.json"
    if not manifest_path.is_file():
        return "missing"
    try:
        manifest = _load_json_object(manifest_path)
    except OSError, ValueError, json.JSONDecodeError:
        return "incompatible"

    bpm_version = _manifest_bpm_version(manifest)
    if bpm_version and bpm_version != get_settings().APP_VERSION:
        return "stale"

    locales = manifest.get("locales")
    if isinstance(locales, list) and locales and all(isinstance(locale, str) for locale in locales):
        if not all((root / locale / "index.html").is_file() for locale in locales):
            return "incomplete"

    catalog = load_documentation_catalog(root)
    if catalog is None:
        return "incompatible"
    if not catalog.locales:
        return "incomplete"
    if not all((root / locale / "index.html").is_file() for locale in catalog.locales):
        return "incomplete"
    return None


def resolve_documentation_artifact_disposition(site_root: Path | None = None) -> str:
    """Return the All Settings no-link disposition for the installed artifact."""

    problem = documentation_artifact_problem(site_root)
    if problem is None:
        return "available"
    if problem == "missing":
        return "artifact_unavailable"
    return f"artifact_{problem}"


def resolve_documentation_home_links(site_root: Path | None = None) -> dict[str, str] | None:
    """Resolve the product documentation home target for every supported locale."""

    catalog = load_documentation_catalog(site_root)
    if catalog is None:
        return None
    return catalog.locale_urls_for_target(DOCUMENTATION_HOME_TARGET_ID)


def resolve_documentation_contextual_help_links(
    site_root: Path | None = None,
) -> dict[str, dict[str, str]]:
    """Resolve contextual help target URLs by product surface and locale."""

    catalog = load_documentation_catalog(site_root)
    if catalog is None:
        return {}

    resolved: dict[str, dict[str, str]] = {}
    for surface_id, target_id in DOCUMENTATION_CONTEXTUAL_HELP_TARGET_IDS.items():
        urls = catalog.locale_urls_for_target(target_id)
        if urls is not None:
            resolved[surface_id] = urls
    return resolved


def resolve_documentation_deep_help_links(
    site_root: Path | None = None,
) -> dict[str, dict[str, str]]:
    """Resolve specific UI deep-help target URLs by product control and locale."""

    catalog = load_documentation_catalog(site_root)
    if catalog is None:
        return {}

    resolved: dict[str, dict[str, str]] = {}
    for control_id, target_id in DOCUMENTATION_DEEP_HELP_TARGET_IDS.items():
        urls = catalog.locale_urls_for_target(target_id)
        if urls is not None:
            resolved[control_id] = urls
    return resolved


def resolve_all_settings_row_help_links(
    site_root: Path | None = None,
) -> dict[str, dict[str, str]]:
    """Resolve policy and known-preference row-help targets for every locale."""

    catalog = load_documentation_catalog(site_root)
    if catalog is None:
        return {}

    targets = catalog.target_map.get("targets")
    if not isinstance(targets, dict):
        return {}

    resolved: dict[str, dict[str, str]] = {}
    for target_id, target in targets.items():
        if not isinstance(target, dict) or target.get("kind") not in {"policy", "known-preference"}:
            continue
        urls = catalog.locale_urls_for_target(target_id)
        if urls is not None:
            resolved[target_id] = urls
    return resolved
