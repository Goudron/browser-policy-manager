"""Fail closed on the BPM 0.9.5 editorial/PDF release-review record."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
REVIEW_PATH = ROOT / "documentation/config/documentation-editorial-pdf-release-review-0.9.5.json"
LOCALES = ("en", "ru", "de", "zh-CN", "fr", "es-ES")
GUIDES = ("user", "admin")
FAMILIES = ("user", "admin", "firefox", "cis")

pytestmark = pytest.mark.docs_contract


def _review() -> dict[str, object]:
    review = json.loads(REVIEW_PATH.read_text(encoding="utf-8"))
    assert isinstance(review, dict)
    return review


def _object(value: object) -> dict[str, object]:
    assert isinstance(value, dict)
    return value


def _array(value: object) -> list[object]:
    assert isinstance(value, list)
    return value


def _string(value: object) -> str:
    assert isinstance(value, str)
    return value


def _strings(value: object) -> list[str]:
    values = _array(value)
    assert all(isinstance(item, str) for item in values)
    return [item for item in values if isinstance(item, str)]


def _integer(value: object) -> int:
    assert isinstance(value, int) and not isinstance(value, bool)
    return value


def test_m8_review_covers_all_affected_locale_families_and_pdf_pairs() -> None:
    review = _review()

    assert review["schema_version"] == 1
    assert review["review_id"] == "bpm-0.9.5-editorial-pdf-release-review"
    assert review["backlog_item"] == "BPM095-M8-05"
    assert review["target_bpm_version"] == "0.9.5"
    assert review["release_blocking"] is True
    reviewed_source = _object(review["reviewed_source"])
    assert reviewed_source["changed_physical_topic_files"] == {
        "user": 54,
        "admin": 48,
        "firefox": 12,
        "cis": 12,
    }
    locale_reviews = _object(review["locale_reviews"])
    assert set(locale_reviews) == set(LOCALES)
    for entry_value in locale_reviews.values():
        entry = _object(entry_value)
        assert entry["state"] == "reviewed"
        assert tuple(_strings(entry["reviewed_topic_families"])) == FAMILIES

    topic_authority_review = _object(review["topic_authority_review"])
    assert set(topic_authority_review) == {"coverage_rule", *FAMILIES}
    for family in FAMILIES:
        authority = _object(topic_authority_review[family])
        assert authority["product_authorities"]
        assert authority["locale_authority"] == "app/i18n/{en,ru,de,zh-CN,fr,es-ES}.json"

    pdf_reviews = _array(review["pdf_visual_reviews"])
    assert len(pdf_reviews) == len(LOCALES) * len(GUIDES)
    assert {
        (_string(_object(entry)["locale"]), _string(_object(entry)["guide"]))
        for entry in pdf_reviews
    } == {(locale, guide) for locale in LOCALES for guide in GUIDES}
    for entry_value in pdf_reviews:
        entry = _object(entry_value)
        assert entry["artifact"] == (
            "documentation/build/pdf/"
            f"{_string(entry['locale'])}/browser-policy-manager-"
            f"{'user-guide' if entry['guide'] == 'user' else 'administrator-guide'}-"
            f"{_string(entry['locale'])}-0.9.5.pdf"
        )
        assert _integer(entry["page_count"]) > 1
        assert re.fullmatch(r"[0-9a-f]{64}", _string(entry["sha256"]))


def test_m8_review_records_editorial_authority_and_approved_screenshot_boundary() -> None:
    review = _review()

    editorial = _object(review["editorial_review"])
    assert editorial["runbook"] == "documentation/runbooks/documentation-update-for-future-epics.md"
    assert len(_strings(editorial["maps_reviewed"])) == 4
    assert "Pontoon" in _string(editorial["bpm_ui_and_mozilla_terminology"])
    assert "SUMO" in _string(editorial["bpm_ui_and_mozilla_terminology"])
    assert _string(editorial["dita_and_site_ownership"]).startswith("DITA source remains")

    screenshot = _object(review["screenshot_review"])
    assert screenshot["approved_boundary"] == "0 new/36 reused"
    assert screenshot["new_rows"] == 0
    assert screenshot["reused_rows"] == 36
    assert "no pre-authorized conversion-review scenario" in _string(screenshot["reason"])

    pdf_scope = _object(review["pdf_scope"])
    assert pdf_scope["included_guides"] == ["user", "admin"]
    assert pdf_scope["excluded_standalone_guides"] == ["firefox", "cis"]
    assert "no separate Firefox or CIS PDF artifact" in _string(pdf_scope["exclusion_reason"])


def test_m8_editorial_pdf_review_is_accepted_with_reproducible_delivery_evidence() -> None:
    review = _review()

    assert review["status"] == "accepted"
    visual_checks = _object(review["visual_checks"])
    assert _string(visual_checks["guide_wide_figure_numbering"]).endswith("1 through 6")
    assert review["blocking_findings"] == []
    final_sign_off = _object(review["final_sign_off"])
    assert final_sign_off["state"] == "accepted"
    evidence = _object(review["automated_evidence"])
    assert _string(evidence["pdf_build"]).startswith("passed:")
    assert _string(evidence["pdf_binary_verification"]).startswith("passed:")
    assert _string(evidence["pdf_independent_reproducibility"]).endswith("(13 files)")
    assert _string(evidence["pdf_delivery"]).startswith("passed:")
    assert _string(evidence["docs_release_check"]).startswith("passed:")
    assert _string(evidence["docs_install_dev"]).startswith("passed:")
