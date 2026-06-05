#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core.locales import ACTIVE_CATALOG_LOCALES, SOURCE_LOCALE

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_DIR = REPO_ROOT / "app" / "i18n_src"
POLICY_LABELS_NAMESPACE = "policy-labels"
NON_SOURCE_LOCALES = tuple(
    locale for locale in ACTIVE_CATALOG_LOCALES if locale != SOURCE_LOCALE
)
SEVERITY_ORDER = {"low": 0, "medium": 1, "high": 2}


@dataclass(frozen=True)
class Marker:
    pattern: str
    reason: str
    severity: str = "medium"
    regex: bool = False

    def matches(self, value: str) -> bool:
        if self.regex:
            return re.search(self.pattern, value) is not None
        return self.pattern in value


MARKERS: dict[str, tuple[Marker, ...]] = {
    "de": (
        Marker("Microsvont", "typo in product/vendor name", "high"),
        Marker("Dont ", "untranslated English command fragment", "high"),
        Marker("Offer ", "untranslated English command fragment", "high"),
        Marker("Skip ", "untranslated English command fragment", "high"),
        Marker("Children", "untranslated schema noun", "high"),
        Marker("Delegated", "untranslated schema adjective", "medium"),
        Marker("Feature ", "untranslated product noun", "medium"),
        Marker("Improve ", "untranslated command verb", "high"),
        Marker(" requests", "untranslated plural noun", "medium"),
        Marker(" URL template", "machine-like word order", "medium"),
        Marker(" template", "untranslated template noun", "medium"),
    ),
    "fr": (
        Marker("Activerd", "machine suffix from generated English verb", "high"),
        Marker("Dont ", "untranslated English command fragment", "high"),
        Marker("Offer ", "untranslated English command fragment", "high"),
        Marker("Skip ", "untranslated English command fragment", "high"),
        Marker("Children", "untranslated schema noun", "high"),
        Marker("Delegated", "untranslated schema adjective", "medium"),
        Marker("Feature ", "untranslated product noun", "medium"),
        Marker("Improve ", "untranslated command verb", "high"),
        Marker("Suggerer", "machine-like false friend", "high"),
        Marker("Website filtre", "machine-like word order", "medium"),
        Marker("élémenturation", "corrupted translation fragment", "high"),
        Marker(" requests", "untranslated plural noun", "medium"),
        Marker(" URL template", "machine-like word order", "medium"),
        Marker(" template", "untranslated template noun", "medium"),
    ),
    "es-ES": (
        Marker("Activard", "machine suffix from generated English verb", "high"),
        Marker("Desactivard", "machine suffix from generated English verb", "high"),
        Marker("Dont ", "untranslated English command fragment", "high"),
        Marker("Offer ", "untranslated English command fragment", "high"),
        Marker("Skip ", "untranslated English command fragment", "high"),
        Marker("Children", "untranslated schema noun", "high"),
        Marker("Delegated", "untranslated schema adjective", "medium"),
        Marker("Feature ", "untranslated product noun", "medium"),
        Marker("Improve ", "untranslated command verb", "high"),
        Marker("Installation modo", "machine-like mixed-language phrase", "high"),
        Marker("elementouracion", "corrupted translation fragment", "high"),
        Marker(" requests", "untranslated plural noun", "medium"),
        Marker(" URL template", "machine-like word order", "medium"),
        Marker(" template", "untranslated template noun", "medium"),
    ),
}


def load_json(path: Path) -> dict[str, str]:
    return json.loads(path.read_text(encoding="utf-8"))


def override_path(source_dir: Path, locale: str) -> Path:
    return source_dir / "overrides" / locale / f"{POLICY_LABELS_NAMESPACE}.json"


def finding(
    *,
    locale: str,
    key: str,
    value: str,
    marker: Marker,
) -> dict[str, str]:
    return {
        "locale": locale,
        "key": key,
        "value": value,
        "marker": marker.pattern,
        "severity": marker.severity,
        "reason": marker.reason,
    }


def collect_findings(
    *,
    source_dir: Path = DEFAULT_SOURCE_DIR,
    locales: tuple[str, ...] = NON_SOURCE_LOCALES,
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for locale in locales:
        path = override_path(source_dir, locale)
        if not path.is_file():
            continue
        catalog = load_json(path)
        for key, value in catalog.items():
            for marker in MARKERS.get(locale, ()):
                if marker.matches(value):
                    findings.append(
                        finding(locale=locale, key=key, value=value, marker=marker)
                    )

    return sorted(
        findings,
        key=lambda item: (
            item["locale"],
            -SEVERITY_ORDER[item["severity"]],
            item["key"],
            item["marker"],
        ),
    )


def summarize(findings: list[dict[str, str]]) -> dict[str, Any]:
    by_locale = Counter(item["locale"] for item in findings)
    by_severity = Counter(item["severity"] for item in findings)
    return {
        "finding_count": len(findings),
        "by_locale": dict(sorted(by_locale.items())),
        "by_severity": {
            severity: by_severity.get(severity, 0)
            for severity in ("high", "medium", "low")
        },
    }


def build_report(
    *,
    source_dir: Path = DEFAULT_SOURCE_DIR,
    locales: tuple[str, ...] = NON_SOURCE_LOCALES,
) -> dict[str, Any]:
    findings = collect_findings(source_dir=source_dir, locales=locales)
    return {
        "source_dir": source_dir.relative_to(REPO_ROOT).as_posix()
        if source_dir.is_relative_to(REPO_ROOT)
        else source_dir.as_posix(),
        "namespace": POLICY_LABELS_NAMESPACE,
        "locales": list(locales),
        "summary": summarize(findings),
        "findings": findings,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Report machine-like policy-label override fragments."
    )
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=DEFAULT_SOURCE_DIR,
        help=f"Locale source directory (default: {DEFAULT_SOURCE_DIR})",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Emit compact JSON instead of indented JSON.",
    )
    parser.add_argument(
        "--fail-on",
        choices=("none", "medium", "high"),
        default="none",
        help="Exit with 1 when findings at or above this severity exist.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(source_dir=args.source_dir)
    indent = None if args.compact else 2
    print(json.dumps(report, ensure_ascii=False, indent=indent, sort_keys=True))

    if args.fail_on == "none":
        return 0
    minimum = SEVERITY_ORDER[args.fail_on]
    has_blocking_findings = any(
        SEVERITY_ORDER[finding["severity"]] >= minimum
        for finding in report["findings"]
    )
    return 1 if has_blocking_findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
