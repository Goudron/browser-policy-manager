from __future__ import annotations

import json

from app.core.locales import ACTIVE_CATALOG_LOCALES
from tools import build_locale_catalogs


def test_locale_namespace_classifier_routes_known_profile_key_groups():
    assert build_locale_catalogs.namespace_for_key("profiles.wizard_title") == "wizard"
    assert build_locale_catalogs.namespace_for_key("profiles.settings_route_title") == "settings"
    assert build_locale_catalogs.namespace_for_key("profiles.library_count_many") == "library"
    assert build_locale_catalogs.namespace_for_key("profiles.compare_title") == "library"
    assert build_locale_catalogs.namespace_for_key("profiles.settings_context_title") == "settings"
    assert build_locale_catalogs.namespace_for_key("profiles.editor_title_section") == "json"
    assert build_locale_catalogs.namespace_for_key("profiles.shell_policy_pdfjs") == "policy-labels"
    assert build_locale_catalogs.namespace_for_key("profiles.schema_field_url") == "policy-labels"
    assert build_locale_catalogs.namespace_for_key("profiles.title") == "common"


def test_locale_catalog_split_and_build_roundtrip(tmp_path):
    runtime_dir = tmp_path / "runtime"
    source_dir = tmp_path / "source"
    runtime_dir.mkdir()
    catalog = {
        "profiles.title": "Title",
        "profiles.library_count_many": "Profiles",
        "profiles.wizard_title": "Wizard",
        "profiles.settings_route_title": "Settings",
        "profiles.editor_title_section": "JSON editor",
        "profiles.schema_field_allow": "Allowed sites",
        "profiles.schema_field_url": "URL",
    }
    for locale in ACTIVE_CATALOG_LOCALES:
        (runtime_dir / f"{locale}.json").write_text(
            json.dumps(catalog, ensure_ascii=False, indent=4) + "\n",
            encoding="utf-8",
        )

    build_locale_catalogs.split_runtime_catalogs(
        runtime_dir=runtime_dir,
        source_dir=source_dir,
    )
    built = build_locale_catalogs.build_catalogs(source_dir=source_dir)

    assert built == {locale: catalog for locale in ACTIVE_CATALOG_LOCALES}
    assert json.loads((source_dir / "en" / "common.json").read_text(encoding="utf-8")) == {
        "profiles.title": "Title"
    }
    assert not (source_dir / "en" / "policy-labels.json").exists()
    assert json.loads(
        (source_dir / "generated" / "en" / "policy-labels.json").read_text(encoding="utf-8")
    ) == {
        "profiles.schema_field_allow": "Allowed sites",
        "profiles.schema_field_url": "URL"
    }
    assert json.loads(
        (source_dir / "overrides" / "en" / "policy-labels.json").read_text(encoding="utf-8")
    ) == {"profiles.schema_field_allow": "Allowed sites"}
    assert build_locale_catalogs.check_runtime_catalogs(
        source_dir=source_dir,
        runtime_dir=runtime_dir,
    ) == []


def test_checked_in_runtime_locale_catalogs_match_source_segments():
    assert build_locale_catalogs.check_runtime_catalogs() == []


def test_checked_in_policy_labels_are_generated_from_metadata_and_overrides():
    source_dir = build_locale_catalogs.SOURCE_I18N_DIR
    key_order = build_locale_catalogs.load_catalog_order(source_dir)
    generated = build_locale_catalogs.build_policy_label_segment(
        "en",
        source_dir=source_dir,
        key_order=key_order,
    )

    assert generated == json.loads(
        (source_dir / "generated" / "en" / "policy-labels.json").read_text(encoding="utf-8")
    )
    assert generated["profiles.schema_field_url"] == "URL"
    assert generated["profiles.schema_field_allow"] == "Allowed sites"
    assert generated["profiles.shell_policy_disable_telemetry"] == "Disable Telemetry"
    assert not (source_dir / "en" / "policy-labels.json").exists()
