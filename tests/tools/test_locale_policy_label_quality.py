from __future__ import annotations

import json

from tools import locale_policy_label_quality


def _write_policy_label_overrides(source_dir, locale, values):
    path = source_dir / "overrides" / locale / "policy-labels.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(values, ensure_ascii=False, indent=4) + "\n",
        encoding="utf-8",
    )


def test_locale_policy_label_quality_reports_machine_like_fragments(tmp_path):
    source_dir = tmp_path / "i18n_src"
    _write_policy_label_overrides(
        source_dir,
        "fr",
        {
            "profiles.schema_field_ok": "Recommandations",
            "profiles.schema_field_bad": "Improve Suggerer",
        },
    )

    report = locale_policy_label_quality.build_report(
        source_dir=source_dir,
        locales=("fr",),
    )

    assert report["summary"] == {
        "finding_count": 2,
        "by_locale": {"fr": 2},
        "by_severity": {"high": 2, "medium": 0, "low": 0},
    }
    assert {
        (finding["key"], finding["marker"], finding["severity"])
        for finding in report["findings"]
    } == {
        ("profiles.schema_field_bad", "Improve ", "high"),
        ("profiles.schema_field_bad", "Suggerer", "high"),
    }


def test_locale_policy_label_quality_ignores_missing_locale_override_file(tmp_path):
    report = locale_policy_label_quality.build_report(
        source_dir=tmp_path / "i18n_src",
        locales=("de",),
    )

    assert report["summary"]["finding_count"] == 0
    assert report["findings"] == []


def test_checked_in_policy_label_overrides_do_not_have_known_machine_markers():
    report = locale_policy_label_quality.build_report()

    assert report["findings"] == []
