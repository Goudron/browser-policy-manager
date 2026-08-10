"""Fail closed on the BPM 0.9.4 editorial/PDF release-review record."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
REVIEW_PATH = ROOT / "documentation/config/documentation-editorial-pdf-release-review-0.9.4.json"
LOCALES = ("en", "ru", "de", "zh-CN", "fr", "es-ES")
GUIDES = ("user", "admin")
FAMILIES = ("user", "admin", "firefox", "cis")

pytestmark = pytest.mark.docs_contract


def _review() -> dict[str, object]:
    return json.loads(REVIEW_PATH.read_text(encoding="utf-8"))


def test_release_review_covers_all_locale_guide_pairs_and_authority_families() -> None:
    review = _review()

    assert review["schema_version"] == 1
    assert review["review_id"] == "bpm-0.9.4-editorial-pdf-release-review"
    assert review["backlog_item"] == "BPM094-M11-06"
    assert review["target_bpm_version"] == "0.9.4"
    assert review["release_blocking"] is True
    assert set(review["locale_reviews"]) == set(LOCALES)
    assert all(entry["state"] == "reviewed" for entry in review["locale_reviews"].values())
    assert set(review["topic_authority_review"]) == {"coverage_rule", *FAMILIES}
    for family in FAMILIES:
        authority = review["topic_authority_review"][family]
        assert authority["product_authorities"]
        assert authority["locale_authority"] == "app/i18n/{en,ru,de,zh-CN,fr,es-ES}.json"

    pdf_reviews = review["pdf_visual_reviews"]
    assert len(pdf_reviews) == len(LOCALES) * len(GUIDES)
    assert {(entry["locale"], entry["guide"]) for entry in pdf_reviews} == {
        (locale, guide) for locale in LOCALES for guide in GUIDES
    }
    for entry in pdf_reviews:
        assert entry["artifact"].startswith(f"documentation/build/pdf/{entry['locale']}/")
        assert entry["page_count"] > 1
        assert re.fullmatch(r"[0-9a-f]{64}", entry["sha256"])


def test_editorial_and_pdf_review_is_accepted_after_all_remediations() -> None:
    review = _review()

    assert review["status"] == "accepted"
    assert review["visual_checks"]["guide_wide_figure_numbering"].endswith("1 through 6")
    assert review["blocking_findings"] == []
    assert review["final_sign_off"]["state"] == "accepted"


def test_external_python_runtime_blocker_is_separate_from_editorial_defect() -> None:
    review = _review()

    evidence = review["automated_evidence"]
    assert evidence["focused_m11_contracts"].startswith("passed: 13")
    assert evidence["pdf_independent_reproducibility"].endswith("(13 files)")
    assert evidence["pdf_delivery_and_package"].startswith("passed:")
    assert evidence["docs_release_check"].startswith("passed:")
    runtime = review["external_runtime_record"]
    assert runtime["status"] == "resolved"
    assert runtime["environment"] == "CPython 3.14.6"
    assert runtime["verification"] == (
        "The exact aiosqlite health-validation case completed successfully on the local Python 3.14.6 runtime."
    )
