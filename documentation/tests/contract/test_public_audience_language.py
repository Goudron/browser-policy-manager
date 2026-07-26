from __future__ import annotations

from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DITA_ROOT = REPOSITORY_ROOT / "documentation" / "src" / "dita"
LOCALES = ("en", "ru", "de", "zh-CN", "fr", "es-ES")

pytestmark = pytest.mark.docs_contract


def _source_text(paths: list[Path]) -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in paths)


def test_user_troubleshooting_uses_product_actions_and_support_language() -> None:
    source = _source_text(
        [
            path
            for locale in LOCALES
            for path in sorted((DITA_ROOT / locale / "user").glob("ug-troubleshoot-*.dita"))
        ]
    ).lower()

    forbidden = (
        "internal storage",
        "internen speicher",
        "внутреннюю память",
        "内部存储",
        "stockage interne",
        "almacenamiento interno",
        "maintainer review",
        "support or maintainer",
        "überprüfung durch den betreuer",
        "проверки сопровождающим",
        "维护人员查看",
        "révision du responsable",
        "revisión del mantenedor",
        "browser testing caveat",
    )

    assert [fragment for fragment in forbidden if fragment in source] == []


def test_admin_topics_do_not_publish_product_roadmap_status_as_user_guidance() -> None:
    source = _source_text(sorted((DITA_ROOT / "en" / "admin").glob("*.dita"))).lower()

    forbidden = (
        "planned but not implemented yet",
        "not delivered in this release",
        "future product documentation portal",
        "future production architecture",
        "future work, not current behavior",
        "rolling upgrades are planned",
        "deferred production capabilities",
        "later distribution/runtime tasks",
    )

    assert [fragment for fragment in forbidden if fragment in source] == []
