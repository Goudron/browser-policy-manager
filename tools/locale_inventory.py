#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from app.core.locales import ACTIVE_CATALOG_LOCALES, SOURCE_LOCALE

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_I18N_DIR = REPO_ROOT / "app" / "i18n"
DEFAULT_OWNERSHIP_PATH = REPO_ROOT / "docs" / "locale_ownership_2026-06-01.md"
PLACEHOLDER_RE = re.compile(r"\{[A-Za-z0-9_]+\}")


def load_catalogs(i18n_dir: Path = DEFAULT_I18N_DIR) -> dict[str, dict[str, str]]:
    catalogs: dict[str, dict[str, str]] = {}
    for locale in ACTIVE_CATALOG_LOCALES:
        path = i18n_dir / f"{locale}.json"
        catalogs[locale] = json.loads(path.read_text(encoding="utf-8"))
    return catalogs


def placeholders(value: str) -> list[str]:
    return sorted(PLACEHOLDER_RE.findall(value))


def collect_ownership_summary(
    ownership_path: Path = DEFAULT_OWNERSHIP_PATH,
) -> dict[str, object]:
    if not ownership_path.is_file():
        return {"document": None, "model": "unknown", "locales": {}}

    source = ownership_path.read_text(encoding="utf-8")
    locale_rows: dict[str, str] = {}
    locale_labels = {
        "English source copy": SOURCE_LOCALE,
        "Russian localization": "ru",
        "German localization": "de",
        "Simplified Chinese localization": "zh-CN",
        "French localization": "fr",
        "Spanish (Spain) localization": "es-ES",
    }
    for line in source.splitlines():
        if not line.startswith("| "):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 3:
            continue
        locale = locale_labels.get(cells[0])
        if locale:
            locale_rows[locale] = cells[2]

    model = "single-maintainer"
    if "no separate translator team" not in source:
        model = "review-required"

    try:
        document_path = ownership_path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        document_path = ownership_path.as_posix()

    return {
        "document": document_path,
        "model": model,
        "locales": locale_rows,
    }


def summarize_catalog(
    locale: str,
    catalog: dict[str, str],
    source_catalog: dict[str, str],
    *,
    longest_limit: int,
) -> dict[str, object]:
    source_keys = list(source_catalog)
    source_key_set = set(source_keys)
    catalog_key_set = set(catalog)
    missing_keys = [key for key in source_keys if key not in catalog_key_set]
    extra_keys = sorted(catalog_key_set - source_key_set)

    placeholder_mismatches = {
        key: {
            "source": placeholders(source_catalog[key]),
            "target": placeholders(catalog[key]),
        }
        for key in source_keys
        if key in catalog and placeholders(source_catalog[key]) != placeholders(catalog[key])
    }
    unchanged_from_source = [
        key
        for key in source_keys
        if locale != SOURCE_LOCALE
        and key in catalog
        and isinstance(source_catalog[key], str)
        and catalog[key] == source_catalog[key]
    ]
    string_values = [value for value in catalog.values() if isinstance(value, str)]
    longest_strings = sorted(
        (
            {"key": key, "length": len(value)}
            for key, value in catalog.items()
            if isinstance(value, str)
        ),
        key=lambda item: (-int(item["length"]), str(item["key"])),
    )[:longest_limit]

    return {
        "key_count": len(catalog),
        "missing_key_count": len(missing_keys),
        "extra_key_count": len(extra_keys),
        "missing_keys": missing_keys,
        "extra_keys": extra_keys,
        "placeholder_mismatch_count": len(placeholder_mismatches),
        "placeholder_mismatches": placeholder_mismatches,
        "unchanged_from_source_count": len(unchanged_from_source),
        "unchanged_from_source_keys": unchanged_from_source,
        "string_char_count": sum(len(value) for value in string_values),
        "longest_strings": longest_strings,
    }


def build_locale_inventory(
    *,
    i18n_dir: Path = DEFAULT_I18N_DIR,
    ownership_path: Path = DEFAULT_OWNERSHIP_PATH,
    longest_limit: int = 10,
) -> dict[str, Any]:
    catalogs = load_catalogs(i18n_dir)
    source_catalog = catalogs[SOURCE_LOCALE]
    summaries = {
        locale: summarize_catalog(
            locale,
            catalog,
            source_catalog,
            longest_limit=longest_limit,
        )
        for locale, catalog in catalogs.items()
    }

    return {
        "source_locale": SOURCE_LOCALE,
        "active_locales": list(ACTIVE_CATALOG_LOCALES),
        "source_key_count": len(source_catalog),
        "catalogs": summaries,
        "ownership": collect_ownership_summary(ownership_path),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Report runtime locale catalog inventory.")
    parser.add_argument(
        "--i18n-dir",
        type=Path,
        default=DEFAULT_I18N_DIR,
        help=f"Locale catalog directory (default: {DEFAULT_I18N_DIR})",
    )
    parser.add_argument(
        "--ownership",
        type=Path,
        default=DEFAULT_OWNERSHIP_PATH,
        help=f"Locale ownership document (default: {DEFAULT_OWNERSHIP_PATH})",
    )
    parser.add_argument(
        "--longest-limit",
        type=int,
        default=10,
        help="Number of longest strings to include per locale.",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Emit compact JSON instead of indented JSON.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_locale_inventory(
        i18n_dir=args.i18n_dir,
        ownership_path=args.ownership,
        longest_limit=max(args.longest_limit, 0),
    )
    indent = None if args.compact else 2
    print(json.dumps(report, ensure_ascii=False, indent=indent, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
