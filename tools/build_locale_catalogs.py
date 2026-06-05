#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from app.core.locales import ACTIVE_CATALOG_LOCALES
from app.core.schema_channels import SUPPORTED_SCHEMA_CHANNELS
from app.services.policy_schema_service import load_policy_schema
from app.web.firefox_wizard_shell.inline_editors import FIELD_LABEL_KEYS
from app.web.firefox_wizard_shell.serializer import humanize_identifier

REPO_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_I18N_DIR = REPO_ROOT / "app" / "i18n"
SOURCE_I18N_DIR = REPO_ROOT / "app" / "i18n_src"
CATALOG_ORDER_FILENAME = "catalog-order.json"
GENERATED_DIRNAME = "generated"
OVERRIDES_DIRNAME = "overrides"

NAMESPACE_ORDER: tuple[str, ...] = (
    "common",
    "library",
    "wizard",
    "settings",
    "json",
    "policy-labels",
)


def namespace_for_key(key: str) -> str:
    if key.startswith(("profiles.shell_policy_", "profiles.schema_field_")):
        return "policy-labels"
    if key.startswith("profiles.settings_"):
        return "settings"
    if key.startswith("profiles.wizard_"):
        return "wizard"
    if key.startswith(
        (
            "profiles.library_",
            "profiles.compare_",
            "profiles.clone_",
            "profiles.import_",
            "profiles.lifecycle_",
        )
    ):
        return "library"
    if key.startswith("profiles.advanced_") or key in {
        "profiles.download_firefox_policies_json",
        "profiles.editor_formatted",
        "profiles.editor_mode_switched",
        "profiles.editor_note",
        "profiles.editor_section_hint",
        "profiles.editor_title_section",
        "profiles.format",
        "profiles.validate",
        "profiles.validation_failed",
        "profiles.validation_idle",
        "profiles.validation_ok",
        "profiles.validation_ready",
        "profiles.validation_result_invalid",
    }:
        return "json"
    return "common"


def to_snake_case(value: str) -> str:
    return re.sub(
        r"[-:\s]+",
        "_",
        re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value),
    ).lower()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=4) + "\n",
        encoding="utf-8",
    )


def source_locale_dir(source_dir: Path, locale: str) -> Path:
    return source_dir / locale


def source_namespace_path(source_dir: Path, locale: str, namespace: str) -> Path:
    return source_locale_dir(source_dir, locale) / f"{namespace}.json"


def generated_namespace_path(source_dir: Path, locale: str, namespace: str) -> Path:
    return source_dir / GENERATED_DIRNAME / locale / f"{namespace}.json"


def override_namespace_path(source_dir: Path, locale: str, namespace: str) -> Path:
    return source_dir / OVERRIDES_DIRNAME / locale / f"{namespace}.json"


def load_catalog_order(source_dir: Path = SOURCE_I18N_DIR) -> list[str]:
    return list(json.loads((source_dir / CATALOG_ORDER_FILENAME).read_text(encoding="utf-8")))


def policy_label_defaults() -> dict[str, str]:
    labels = {
        label_key: humanize_identifier(field_name)
        for field_name, label_key in FIELD_LABEL_KEYS.items()
    }
    for channel in SUPPORTED_SCHEMA_CHANNELS:
        schema = load_policy_schema(channel)
        for definition in schema.policies.values():
            if definition.ui is None:
                continue
            labels[f"profiles.shell_policy_{to_snake_case(definition.id)}"] = humanize_identifier(
                definition.id
            )
    return labels


def policy_label_order(key_order: list[str]) -> list[str]:
    return [key for key in key_order if namespace_for_key(key) == "policy-labels"]


def build_policy_label_segment(
    locale: str,
    *,
    source_dir: Path = SOURCE_I18N_DIR,
    key_order: list[str] | None = None,
) -> dict[str, str]:
    defaults = policy_label_defaults()
    ordered_keys = policy_label_order(key_order or load_catalog_order(source_dir))
    unsupported_keys = [key for key in ordered_keys if key not in defaults]
    if unsupported_keys:
        joined = ", ".join(unsupported_keys[:5])
        raise ValueError(f"Policy label keys are not backed by metadata: {joined}")

    segment = {key: defaults[key] for key in ordered_keys}
    overrides_path = override_namespace_path(source_dir, locale, "policy-labels")
    if overrides_path.is_file():
        overrides = load_json(overrides_path)
        unsupported_overrides = sorted(set(overrides) - set(defaults))
        if unsupported_overrides:
            joined = ", ".join(unsupported_overrides[:5])
            raise ValueError(f"Policy label overrides are not backed by metadata: {joined}")
        for key, value in overrides.items():
            if key in segment:
                segment[key] = value
    return segment


def write_generated_policy_label_segments(
    *,
    source_dir: Path = SOURCE_I18N_DIR,
    key_order: list[str] | None = None,
) -> None:
    resolved_order = key_order or load_catalog_order(source_dir)
    for locale in ACTIVE_CATALOG_LOCALES:
        write_json(
            generated_namespace_path(source_dir, locale, "policy-labels"),
            build_policy_label_segment(locale, source_dir=source_dir, key_order=resolved_order),
        )


def split_runtime_catalogs(
    *,
    runtime_dir: Path = RUNTIME_I18N_DIR,
    source_dir: Path = SOURCE_I18N_DIR,
) -> None:
    order: list[str] | None = None
    for locale in ACTIVE_CATALOG_LOCALES:
        catalog = load_json(runtime_dir / f"{locale}.json")
        if order is None:
            order = list(catalog)

        namespace_catalogs: dict[str, dict[str, str]] = {
            namespace: {} for namespace in NAMESPACE_ORDER
        }
        for key, value in catalog.items():
            namespace_catalogs[namespace_for_key(key)][key] = value

        for namespace, namespace_catalog in namespace_catalogs.items():
            if namespace == "policy-labels":
                continue
            write_json(
                source_namespace_path(source_dir, locale, namespace),
                namespace_catalog,
            )

    write_json(source_dir / CATALOG_ORDER_FILENAME, order or [])
    resolved_order = order or []
    defaults = policy_label_defaults()
    for locale in ACTIVE_CATALOG_LOCALES:
        catalog = load_json(runtime_dir / f"{locale}.json")
        overrides = {
            key: catalog[key]
            for key in policy_label_order(resolved_order)
            if key in catalog and catalog[key] != defaults.get(key)
        }
        write_json(override_namespace_path(source_dir, locale, "policy-labels"), overrides)
    write_generated_policy_label_segments(source_dir=source_dir, key_order=resolved_order)


def load_source_catalog(
    locale: str,
    *,
    source_dir: Path = SOURCE_I18N_DIR,
) -> dict[str, str]:
    catalog: dict[str, str] = {}
    for namespace in NAMESPACE_ORDER:
        path = (
            generated_namespace_path(source_dir, locale, namespace)
            if namespace == "policy-labels"
            else source_namespace_path(source_dir, locale, namespace)
        )
        if not path.is_file():
            raise FileNotFoundError(f"Missing locale namespace file: {path}")
        segment = load_json(path)
        duplicate_keys = sorted(set(catalog) & set(segment))
        if duplicate_keys:
            joined = ", ".join(duplicate_keys[:5])
            raise ValueError(f"Duplicate keys in {locale}/{namespace}: {joined}")
        catalog.update(segment)
    return catalog


def ordered_catalog(catalog: dict[str, str], key_order: list[str]) -> dict[str, str]:
    ordered: dict[str, str] = {}
    for key in key_order:
        if key in catalog:
            ordered[key] = catalog[key]
    for namespace in NAMESPACE_ORDER:
        for key, value in catalog.items():
            if key not in ordered and namespace_for_key(key) == namespace:
                ordered[key] = value
    return ordered


def build_catalogs(
    *,
    source_dir: Path = SOURCE_I18N_DIR,
) -> dict[str, dict[str, str]]:
    key_order = load_catalog_order(source_dir)
    return {
        locale: ordered_catalog(
            load_source_catalog(locale, source_dir=source_dir),
            key_order,
        )
        for locale in ACTIVE_CATALOG_LOCALES
    }


def write_runtime_catalogs(
    catalogs: dict[str, dict[str, str]],
    *,
    runtime_dir: Path = RUNTIME_I18N_DIR,
) -> None:
    for locale, catalog in catalogs.items():
        write_json(runtime_dir / f"{locale}.json", catalog)


def check_runtime_catalogs(
    *,
    source_dir: Path = SOURCE_I18N_DIR,
    runtime_dir: Path = RUNTIME_I18N_DIR,
) -> list[str]:
    mismatches: list[str] = []
    key_order = load_catalog_order(source_dir)
    for locale in ACTIVE_CATALOG_LOCALES:
        generated_path = generated_namespace_path(source_dir, locale, "policy-labels")
        expected_generated = build_policy_label_segment(
            locale,
            source_dir=source_dir,
            key_order=key_order,
        )
        if not generated_path.is_file() or load_json(generated_path) != expected_generated:
            mismatches.append(f"generated/{locale}/policy-labels")

    for locale, built_catalog in build_catalogs(source_dir=source_dir).items():
        runtime_catalog = load_json(runtime_dir / f"{locale}.json")
        if runtime_catalog != built_catalog:
            mismatches.append(locale)
    return mismatches


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build runtime app/i18n catalogs from namespace source files."
    )
    parser.add_argument(
        "--split-from-runtime",
        action="store_true",
        help="Regenerate app/i18n_src from current app/i18n runtime catalogs.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero when app/i18n differs from generated output.",
    )
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=SOURCE_I18N_DIR,
        help=f"Locale source directory (default: {SOURCE_I18N_DIR})",
    )
    parser.add_argument(
        "--runtime-dir",
        type=Path,
        default=RUNTIME_I18N_DIR,
        help=f"Runtime locale directory (default: {RUNTIME_I18N_DIR})",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.split_from_runtime:
        split_runtime_catalogs(runtime_dir=args.runtime_dir, source_dir=args.source_dir)
        return 0

    if args.check:
        mismatches = check_runtime_catalogs(
            source_dir=args.source_dir,
            runtime_dir=args.runtime_dir,
        )
        if mismatches:
            print("Runtime locale catalogs differ from source: " + ", ".join(mismatches))
            return 1
        return 0

    write_generated_policy_label_segments(source_dir=args.source_dir)
    write_runtime_catalogs(
        build_catalogs(source_dir=args.source_dir),
        runtime_dir=args.runtime_dir,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
