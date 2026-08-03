from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
CORPUS_PATH = ROOT / "documentation/config/search-rag-evaluation-corpus-0.9.3.json"
LOCALES = ("en", "ru", "de", "zh-CN", "fr", "es-ES")

pytestmark = pytest.mark.docs_contract


def _corpus() -> dict:
    return json.loads(CORPUS_PATH.read_text(encoding="utf-8"))


def test_evaluation_corpus_has_the_exact_six_locale_matrix_and_review_boundary() -> None:
    corpus = _corpus()

    assert corpus["schema_version"] == 1
    assert corpus["backlog_item"] == "BPM093-M2-03"
    assert corpus["target_bpm_version"] == "0.9.3"
    assert corpus["status"] == "accepted"
    assert corpus["synthetic"] is True
    assert tuple(corpus["locales"]) == LOCALES
    assert corpus["review_policy"]["english"] == "source-reviewed"
    assert corpus["review_policy"]["non_english"] == "localized-reviewed"
    assert "Maintainer acceptance" in corpus["review_policy"]["required_before_release"]
    assert corpus["locale_review"]["accepted_by"] == "project maintainer interactive acceptance"
    assert corpus["locale_review"]["accepted_on"] == "2026-07-28"
    assert corpus["locale_review"]["locales"] == {locale: "accepted" for locale in LOCALES}


def test_evaluation_corpus_expands_to_minimum_search_and_answer_cases_per_locale() -> None:
    corpus = _corpus()
    minimums = corpus["minimum_cases_per_locale"]

    assert len(corpus["domains"]) == 4
    for locale in LOCALES:
        search_count = len(corpus["domains"]) * len(corpus["search_templates"][locale])
        search_count += len(corpus["boundary_cases"][locale]["search"])
        answer_count = len(corpus["domains"]) * len(corpus["answer_templates"][locale])
        answer_count += len(corpus["boundary_cases"][locale]["dialogue"])
        assert search_count >= minimums["search"] == 40
        assert answer_count >= minimums["answer_dialogue"] == 24


def test_evaluation_corpus_covers_required_difficulty_and_expected_evidence() -> None:
    corpus = _corpus()

    assert set(domain["id"] for domain in corpus["domains"]) == {
        "profile-library",
        "firefox-ai-controls",
        "api-validation",
        "cis-baseline",
    }
    for domain in corpus["domains"]:
        assert domain["topic_id"]
        assert domain["citation_id"]
        assert domain["identifier"]
        for locale in LOCALES:
            assert len(domain["terms"][locale]) == 5

    for locale in LOCALES:
        search = corpus["boundary_cases"][locale]["search"]
        dialogue = corpus["boundary_cases"][locale]["dialogue"]
        assert {case[2] for case in search} >= {"abstain", "clarify", "refuse"}
        assert {case[2] for case in dialogue} >= {"answer", "abstain", "clarify", "refuse"}
        assert any(case[3] for case in dialogue if case[2] == "answer")
