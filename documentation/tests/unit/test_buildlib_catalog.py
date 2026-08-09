from __future__ import annotations

import copy
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from types import SimpleNamespace

import pytest

from documentation.buildlib import catalog
from documentation.buildlib.shared import BuildError


def _write(path: Path, content: str | bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content, encoding="utf-8")
    return path


def _taxonomy() -> tuple[dict[str, object], dict[str, object]]:
    taxonomy = {
        "documents": [
            {
                "guide_id": "guide",
                "sections": [
                    {
                        "section_id": "start",
                        "label_key": "section.start",
                        "canonical_label": "Start",
                    }
                ],
            }
        ]
    }
    labels = {
        "locales": list(catalog.LOCALES),
        "labels": {
            "section.start": {
                locale: "Start" if locale == "en" else f"Start-{locale}"
                for locale in catalog.LOCALES
            }
        },
    }
    return taxonomy, labels


def test_map_titles_topic_order_and_section_labels_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(catalog, "DOCUMENTATION_ROOT", tmp_path)
    source = _write(
        tmp_path / "src/dita/en/maps/guide.ditamap", "<map><title> Guide   title </title></map>"
    )
    assert catalog._map_title("en", "guide.ditamap") == "Guide title"
    source.write_text("<broken", encoding="utf-8")
    with pytest.raises(BuildError, match="cannot read localized map title"):
        catalog._map_title("en", "guide.ditamap")
    source.write_text("<map><title> </title></map>", encoding="utf-8")
    with pytest.raises(BuildError, match="map title is missing"):
        catalog._map_title("en", "guide.ditamap")

    monkeypatch.setattr(catalog, "_guide_topic_keyrefs", lambda *_args: ["bad"])
    with pytest.raises(BuildError, match="unsupported topic key"):
        catalog._navigation_topic_order("guide.ditamap")

    taxonomy, labels = _taxonomy()
    monkeypatch.setattr(catalog, "_read_json_file", lambda _path: labels)
    assert catalog._navigation_section_labels(taxonomy)["section.start"]["en"] == "Start"
    mutations = (
        ({**labels, "locales": []}, "exact locale matrix"),
        ({**labels, "labels": {}}, "taxonomy label keys"),
        (
            {**labels, "labels": {"section.start": {"en": "Start"}}},
            "must own every locale",
        ),
        (
            {
                **labels,
                "labels": {"section.start": {locale: "" for locale in catalog.LOCALES}},
            },
            "must be non-empty",
        ),
        (
            {
                **labels,
                "labels": {
                    "section.start": {
                        locale: "Wrong" if locale == "en" else f"Start-{locale}"
                        for locale in catalog.LOCALES
                    }
                },
            },
            "canonical English",
        ),
        (
            {
                **labels,
                "labels": {"section.start": {locale: "Start" for locale in catalog.LOCALES}},
            },
            "must not fall back",
        ),
    )
    for payload, diagnostic in mutations:
        monkeypatch.setattr(catalog, "_read_json_file", lambda _path, payload=payload: payload)
        with pytest.raises(BuildError, match=diagnostic):
            catalog._navigation_section_labels(taxonomy)


def test_navigation_path_alignment_and_artifact_record_diagnostics(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(catalog, "GUIDE_MAPS", (("guide", "guide.ditamap", "a", "user"),))
    topic = {"guide_id": "guide", "output": {"en": "en/topic.html"}}
    topics = {"guide": topic, "topic": topic}
    assert catalog._current_navigation_topic(
        topics, tmp_path / "en/topic.html", tmp_path, "en"
    ) == (
        "guide",
        "topic",
    )
    assert (
        catalog._current_navigation_topic(topics, tmp_path / "en/other.html", tmp_path, "en")
        is None
    )
    with pytest.raises(BuildError, match="outside site root"):
        catalog._current_navigation_topic(topics, tmp_path.parent / "outside", tmp_path, "en")
    assert catalog._locale_navigation_href("en/topic.html", "en") == "topic.html"
    with pytest.raises(BuildError, match="outside locale root"):
        catalog._locale_navigation_href("ru/topic.html", "en")

    root = {"children": []}
    manifest = {"artifact": {"bpm_version": "0.9.4", "documentation_version": "0.9.4"}}
    monkeypatch.setattr(catalog, "_manifest_navigation_root", lambda *_args: root)
    valid = {
        "schema_version": 1,
        "locale": "en",
        "documentation_version": "0.9.4",
        "root": root,
        "node_count": 1,
    }
    catalog._validate_navigation_manifest_alignment("en", valid, manifest)
    cases = (
        ({**valid, "locale": "ru"}, manifest, "locale mismatch"),
        (valid, {}, "artifact metadata is missing"),
        (
            {**valid, "documentation_version": "wrong"},
            manifest,
            "version diverges",
        ),
        ({**valid, "root": {}}, manifest, "source diverges"),
        ({**valid, "node_count": 2}, manifest, "node count diverges"),
    )
    for payload, manifest_payload, diagnostic in cases:
        with pytest.raises(BuildError, match=diagnostic):
            catalog._validate_navigation_manifest_alignment("en", payload, manifest_payload)

    encoded = json.dumps(valid).encode()
    record = {
        "sha256": catalog._payload_sha256(encoded),
        "path": "en/navigation.json",
        "format_version": 1,
        "node_count": 1,
    }
    monkeypatch.setattr(catalog, "_validate_schema", lambda *_args: None)
    assert (
        catalog._validate_navigation_artifact_record(
            "en", record, encoded, manifest, context="fixture"
        )
        == valid
    )
    for replacement, diagnostic in (
        ({**record, "sha256": "wrong"}, "SHA-256 mismatch"),
        ({**record, "format_version": 2}, "format version mismatch"),
        ({**record, "node_count": 2}, "node count mismatch"),
    ):
        with pytest.raises(BuildError, match=diagnostic):
            catalog._validate_navigation_artifact_record(
                "en", replacement, encoded, manifest, context="fixture"
            )


def test_revision_json_schema_and_localized_xml_failures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        catalog.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=1, stdout="bad", stderr=""),
    )
    with pytest.raises(BuildError, match="40-character source revision"):
        catalog._source_revision()

    broken = _write(tmp_path / "broken.json", "{")
    with pytest.raises(BuildError, match="cannot read documentation JSON schema"):
        catalog._schema(broken)
    with pytest.raises(BuildError, match="cannot read documentation JSON"):
        catalog._read_json_file(broken)
    schema = _write(
        tmp_path / "schema.json",
        json.dumps({"type": "object", "required": ["value"]}),
    )
    with pytest.raises(BuildError, match="schema validation failed"):
        catalog._validate_schema({}, schema)

    monkeypatch.setattr(catalog, "DOCUMENTATION_ROOT", tmp_path)
    with pytest.raises(BuildError, match="cannot read localized key map"):
        catalog._localized_map_keydefs("en")
    with pytest.raises(BuildError, match="cannot read localized guide map"):
        catalog._guide_topic_keyrefs("en", "missing.ditamap")
    with pytest.raises(BuildError, match="missing localized key"):
        catalog._localized_topic_roots("topic.x", {locale: {} for locale in catalog.LOCALES})
    bad_topic = _write(tmp_path / "bad.dita", "<broken")
    hrefs = {locale: {"topic.x": bad_topic} for locale in catalog.LOCALES}
    with pytest.raises(BuildError, match="cannot read localized topic"):
        catalog._localized_topic_roots("topic.x", hrefs)


def test_search_config_normalization_and_topic_helpers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    invalid_facets = {"facet_fields": {"bpm_version": {"values": ["wrong"]}}}
    monkeypatch.setattr(catalog, "_read_json_file", lambda _path: invalid_facets)
    with pytest.raises(BuildError, match="must derive from the product version"):
        catalog._search_facets_filters()
    monkeypatch.setattr(catalog, "_read_json_file", lambda _path: {"contract_id": "wrong"})
    with pytest.raises(BuildError, match="unsupported search domain"):
        catalog._search_domain_ranking_facets()

    config = {
        "normalization": {"unicode_form": "NFKC", "strip_diacritics": True},
        "alias_groups": [],
    }
    assert "cafe" in catalog._normalize_search_text("en", "Café", config)
    assert catalog._normalize_search_text("zh-CN", "策略", config)
    with pytest.raises(BuildError, match="unsupported search locale"):
        catalog._normalize_search_text("xx", "text", config)
    fake_match = SimpleNamespace(group=lambda _index: "''")
    monkeypatch.setattr(
        catalog,
        "SEARCH_TOKEN_PATTERN",
        SimpleNamespace(finditer=lambda _text: [fake_match]),
    )
    assert catalog._normalize_search_text("en", "ignored", config) == []

    typo = {
        "typo_tolerance": {
            "min_token_length": 1,
            "max_token_length": 10,
            "max_distance_by_length": [],
            "excluded_token_patterns": [],
        }
    }
    assert catalog._max_typo_distance("word", typo) == 0
    assert catalog._topic_kind(ET.fromstring("<troubleshooting/>")) == "troubleshooting"
    with pytest.raises(BuildError, match="unsupported publishable"):
        catalog._topic_kind(ET.fromstring("<map/>"))
    assert catalog._topic_shortdesc(ET.fromstring("<topic><title>T</title></topic>")) == ""
    assert catalog._api_operation_area("WEB-PROFILES") == "ui"
    with pytest.raises(BuildError, match="cannot derive API"):
        catalog._api_operation_area("UNKNOWN")


def test_facet_metadata_legacy_shapes_counts_quality_and_integrity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payloads = iter(
        (
            {"policies": [], "managed_preferences": []},
            {"policies": [{"policy_id": "P", "channel_support": {"supported_channels": []}}]},
        )
    )
    monkeypatch.setattr(catalog, "_read_json_file", lambda _path: next(payloads))
    assert catalog._policy_facet_metadata()["P"] == {
        "firefox_channel": [],
        "policy_category": [],
    }

    cis_payloads = iter(
        (
            {"recommendations": [{"recommendation_id": "C", "assessment": "manual"}]},
            {
                "topics": [{"recommendation_id": "C"}],
                "provenance_only_records": [{"recommendation_id": "P", "level": "2"}],
            },
        )
    )
    monkeypatch.setattr(catalog, "_read_json_file", lambda _path: next(cis_payloads))
    metadata = catalog._cis_facet_metadata()
    assert metadata["P"]["cis_level"] == ["level-2"]
    assert "manual-review" in metadata["C"]["cis_control_state"]

    assert catalog._document_filter_facets(
        {"filter_facets": None, "facets": {"none": None, "many": [2, 1], "one": 3}}
    ) == {"none": [], "many": ["1", "2"], "one": ["3"]}
    counts = catalog._facet_counts(
        [{"filter_facets": {"field": ["known", "unknown"]}}],
        {"facet_fields": {"field": {"values": ["known"]}}},
    )
    assert counts == {"field": {"known": 1}}

    base = {
        "coverage_requirements": {
            "locales": [],
            "categories": ["exact"],
            "cjk_required_locales": [],
            "minimum_locale_fixture_count": 1,
        },
        "quality_fixtures": [],
    }
    with pytest.raises(BuildError, match="locale matrix mismatch"):
        catalog._validate_quality_fixture_coverage(base)
    base["coverage_requirements"]["locales"] = list(catalog.LOCALES)
    with pytest.raises(BuildError, match="categories are incomplete"):
        catalog._validate_quality_fixture_coverage(base)

    assert catalog._duplicates(["x", "x"]) == ["x"]
    assert (
        catalog._snippet_source(
            {"searchable": {"body": ["one", "two"]}},
            {"snippet_integrity": {"source_fields": ["body"]}},
        )
        == "one two"
    )
    assert (
        catalog._snippet_source(
            {"searchable": {}}, {"snippet_integrity": {"source_fields": ["body"]}}
        )
        == ""
    )


def test_search_integrity_reports_bad_documents_targets_and_control_characters(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(catalog, "_policy_ids", lambda: set())
    monkeypatch.setattr(catalog, "_cis_recommendation_ids", lambda: set())
    monkeypatch.setattr(catalog, "_api_operation_topic_ids", lambda: {})
    topics = {"topic": {"output": {"en": "en/topic.html"}, "anchors": {"present": {}}}}
    documents = [
        {
            "document_id": "doc",
            "topic_id": "topic",
            "locale": "ru",
            "url": "/bad",
            "source": {"output_path": "wrong"},
            "searchable": {"body": "bad\x01"},
        }
    ]
    targets = {
        "targets": {
            "missing": {"topic_id": "missing", "kind": "topic", "source_id": "missing"},
            "stale": {
                "topic_id": "topic",
                "anchor_id": "absent",
                "kind": "topic",
                "source_id": "topic",
            },
        }
    }
    config = {
        "schema_version": 1,
        "contract_id": "integrity",
        "check_categories": [],
        "snippet_integrity": {"source_fields": ["title"], "max_characters": 100},
    }
    report = catalog._search_integrity_report("en", documents, topics, targets, config)
    assert report["status"] == "fail"
    assert report["document_integrity"]["wrong_locale_document_ids"] == ["doc"]
    assert report["anchor_integrity"]["target_topic_mismatches"] == ["missing"]
    assert report["anchor_integrity"]["stale_target_anchors"]
    assert report["snippet_integrity"]["control_character_document_ids"] == ["doc"]


def test_help_target_inventory_and_policy_context_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    contract = {"schema_version": 2, "target_bpm_version": "0.9.1"}
    monkeypatch.setattr(catalog, "_read_json_file", lambda _path: contract)
    with pytest.raises(BuildError, match="unsupported All Settings"):
        catalog._all_settings_help_target_contract()
    contract["schema_version"] = 1
    contract["target_bpm_version"] = "wrong"
    with pytest.raises(BuildError, match="wrong BPM version"):
        catalog._all_settings_help_target_contract()

    monkeypatch.setattr(catalog, "_policy_ids", lambda: {"P"})
    monkeypatch.setattr(catalog, "_managed_preference_ids", lambda: {"pref"})
    with pytest.raises(BuildError, match="is missing policy"):
        catalog._validate_all_settings_help_target_coverage({})
    with pytest.raises(BuildError, match="unknown policy"):
        catalog._validate_all_settings_help_target_coverage(
            {"policy:P": {}, "policy:X": {}, "known-preference:pref": {}}
        )

    monkeypatch.setattr(catalog, "_api_operation_topic_ids", lambda: {"API": "topic"})
    monkeypatch.setattr(catalog, "_capability_topic_ids", lambda: {"CAP": "topic"})
    base_target = {"topic_id": "topic", "anchor_id": "a"}
    base = {
        "schema_version": 1,
        "default_policy_target": base_target,
        "family_targets": [],
    }
    assert catalog._policy_context_assignments(base) == {}
    cases = (
        ({**base, "schema_version": 2}, "unsupported Firefox"),
        ({**base, "default_policy_target": {"topic_id": "unknown"}}, "unknown user topic"),
        (
            {
                **base,
                "default_policy_target": {**base_target, "validation_topic_id": "unknown"},
            },
            "unknown validation topic",
        ),
        (
            {
                **base,
                "default_policy_target": {**base_target, "user_task_topic_ids": ["unknown"]},
            },
            "unknown user task topic",
        ),
        (
            {
                **base,
                "default_policy_target": {**base_target, "api_operation_ids": ["unknown"]},
            },
            "unknown API operation",
        ),
        ({**base, "family_targets": [{**base_target, "family_id": "empty"}]}, "no policy IDs"),
        (
            {
                **base,
                "family_targets": [{**base_target, "family_id": "f", "policy_ids": ["X"]}],
            },
            "unknown policy",
        ),
        (
            {
                **base,
                "family_targets": [
                    {**base_target, "family_id": "a", "policy_ids": ["P"]},
                    {**base_target, "family_id": "b", "policy_ids": ["P"]},
                ],
            },
            "more than once",
        ),
        (
            {
                **base,
                "family_targets": [
                    {
                        **base_target,
                        "family_id": "f",
                        "policy_ids": ["P"],
                        "related_policy_ids": ["X"],
                    }
                ],
            },
            "unknown related policy",
        ),
    )
    for context, diagnostic in cases:
        with pytest.raises(BuildError, match=diagnostic):
            catalog._policy_context_assignments(context)


def test_inventory_parsers_build_guards_and_artifact_path_safety(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    api = _write(
        tmp_path / "api.md",
        "ignored\n| `API-SHORT` | a |\n| `API-GOOD` | a | b | c | d | e | f | `topic` |\n",
    )
    capability = _write(
        tmp_path / "cap.md",
        "ignored\n| `CAP-SHORT` | a |\n| `CAP-GOOD` | a | b | `topic` | d |\n",
    )
    monkeypatch.setattr(catalog, "API_INVENTORY", api)
    monkeypatch.setattr(catalog, "CAPABILITY_INVENTORY", capability)
    assert catalog._api_operation_topic_ids() == {"API-GOOD": "topic"}
    assert catalog._capability_topic_ids() == {"CAP-GOOD": "topic"}

    monkeypatch.setattr(catalog, "GUIDE_MAPS", (("guide", "guide.ditamap", "a", "user"),))
    with pytest.raises(BuildError, match="guide home topic is missing"):
        catalog._build_guides({})
    site = tmp_path / "site"
    _write(site / "keep.txt", "keep")
    _write(site / "manifest.json", "ignored")
    first = catalog._manifest_build_id(site)
    (site / "manifest.json").write_text("changed", encoding="utf-8")
    assert catalog._manifest_build_id(site) == first

    assert catalog._safe_artifact_path(site, "keep.txt") == (site / "keep.txt").resolve()
    for value, diagnostic in (
        ("https://example.test/a", "not relative"),
        ("../outside", "escapes root"),
    ):
        with pytest.raises(BuildError, match=diagnostic):
            catalog._safe_artifact_path(site, value)
    with pytest.raises(BuildError, match="cannot parse generated JSON"):
        catalog._read_json_bytes(b"{", "bad.json")


def test_manifest_file_and_payload_adapters_report_missing_and_mismatched_artifacts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with pytest.raises(BuildError, match="manifest.json or ui-target-map.json is missing"):
        catalog.validate_manifest_files(tmp_path)
    with pytest.raises(BuildError, match="missing from artifact"):
        catalog.validate_manifest_payloads({})

    target_bytes = b"{}"
    manifest = {
        "ui_target_map": {"sha256": "wrong"},
        "navigation": {},
        "search": {},
        "topics": {},
    }
    _write(tmp_path / "manifest.json", json.dumps(manifest))
    _write(tmp_path / "ui-target-map.json", target_bytes)
    monkeypatch.setattr(catalog, "_validate_schema", lambda *_args: None)
    monkeypatch.setattr(catalog, "_validate_manifest_semantics", lambda *_args: None)
    with pytest.raises(BuildError, match="ui-target-map.json SHA-256"):
        catalog.validate_manifest_files(tmp_path)
    with pytest.raises(BuildError, match="archived ui-target-map.json SHA-256"):
        catalog.validate_manifest_payloads(
            {"manifest.json": json.dumps(manifest).encode(), "ui-target-map.json": target_bytes}
        )


def test_remaining_search_and_quality_branches_are_contract_driven(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = ET.fromstring('<map><topicref/><topicref keyref="topic.x"/></map>')
    assert catalog._topicrefs(root) == ["topic.x"]
    config = {
        "normalization": {"unicode_form": "NFKC", "strip_diacritics": False},
        "alias_groups": [],
    }
    assert catalog._normalize_search_text("en", "Text", config) == ["text"]

    policy_payloads = iter(
        (
            {
                "policies": [
                    {
                        "policy_id": "P",
                        "channels": {"release": {"ui": {}, "categories": ["category"]}},
                    }
                ]
            },
            {"policies": []},
        )
    )
    monkeypatch.setattr(catalog, "_read_json_file", lambda _path: next(policy_payloads))
    assert catalog._policy_facet_metadata()["P"]["policy_category"] == ["category"]

    monkeypatch.setattr(
        catalog,
        "_policy_facet_metadata",
        lambda: {"P": {"firefox_channel": [], "policy_category": ["unknown"]}},
    )
    monkeypatch.setattr(catalog, "_cis_facet_metadata", lambda: {})
    facet_fields = {
        field: {"values": []}
        for field in (
            "firefox_channel",
            "policy_category",
            "cis_level",
            "cis_control_state",
            "api_area",
        )
    }
    with pytest.raises(BuildError, match="facet values are not declared"):
        catalog._target_facets_by_topic(
            {"targets": {"policy:P": {"topic_id": "topic", "kind": "policy", "source_id": "P"}}},
            {"facet_fields": facet_fields},
        )

    common = {
        "coverage_requirements": {
            "locales": list(catalog.LOCALES),
            "categories": ["exact"],
            "cjk_required_locales": [],
            "minimum_locale_fixture_count": 1,
        },
        "quality_fixtures": [{"locale": locale, "category": "exact"} for locale in catalog.LOCALES],
    }
    too_few = copy.deepcopy(common)
    too_few["quality_fixtures"] = too_few["quality_fixtures"][1:]
    with pytest.raises(BuildError, match="fixture count is too low"):
        catalog._validate_quality_fixture_coverage(too_few)
    missing_category = copy.deepcopy(common)
    missing_category["coverage_requirements"]["categories"] = ["exact", "other"]
    missing_category["quality_fixtures"].append({"locale": "en", "category": "other"})
    with pytest.raises(BuildError, match="categories are incomplete for"):
        catalog._validate_quality_fixture_coverage(missing_category)
    missing_cjk = copy.deepcopy(common)
    missing_cjk["coverage_requirements"]["categories"] = ["exact", "cjk"]
    missing_cjk["coverage_requirements"]["cjk_required_locales"] = ["zh-CN"]
    missing_cjk["quality_fixtures"].append({"locale": "en", "category": "cjk"})
    with pytest.raises(BuildError, match="CJK fixture is missing"):
        catalog._validate_quality_fixture_coverage(missing_cjk)

    facets = {
        "filter_fixtures": [{"fixture_id": "empty", "locale": "en", "filters": {}}],
        "url_state": {"parameters": {}},
        "empty_result": {"messages": {"en": "empty"}},
    }
    expected = catalog._filter_fixture_results("en", [], facets)
    context = catalog._SearchValidationContext(
        locale="en",
        payload={"filter_fixture_results": expected},
        manifest={},
        target_map={},
        contract={},
        aliases={},
        ranking={},
        facets=facets,
        domain_ranking={},
        quality={},
        integrity={},
    )
    reporter = catalog.ValidationReporter(BuildError, artifact="fixture")
    catalog._validate_search_filter_stage(context, reporter, [], facets["filter_fixtures"])


def test_build_guard_failures_cover_guides_targets_and_topic_outputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(catalog, "LOCALES", ("en",))
    monkeypatch.setattr(catalog, "GUIDE_MAPS", (("guide", "guide.ditamap", "a", "user"),))
    context = {
        "default_policy_target": {"topic_id": "guide", "anchor_id": "a"},
        "family_targets": [],
    }
    monkeypatch.setattr(catalog, "_read_json_file", lambda _path: context)
    monkeypatch.setattr(
        catalog,
        "_all_settings_help_target_contract",
        lambda: {
            "known_preference_targets": {"topic_id": "guide", "anchor_id": "a"},
            "source_inventory": "inventory",
        },
    )
    monkeypatch.setattr(catalog, "_policy_context_assignments", lambda _context: {})
    monkeypatch.setattr(catalog, "_policy_ids", lambda: set())
    monkeypatch.setattr(catalog, "_managed_preference_ids", lambda: set())
    monkeypatch.setattr(catalog, "_cis_recommendation_ids", lambda: set())
    monkeypatch.setattr(catalog, "_api_operation_topic_ids", lambda: {})
    monkeypatch.setattr(catalog, "_capability_topic_ids", lambda: {})
    with pytest.raises(BuildError, match="missing guide topic"):
        catalog._build_target_map({})

    monkeypatch.setattr(catalog, "_api_operation_topic_ids", lambda: {"API": "missing"})
    with pytest.raises(BuildError, match="Administrator Guide topic"):
        catalog._build_target_map(
            {
                "guide": {
                    "anchors": {"a": {}},
                    "output": {"en": "en/index.html"},
                    "title": {"en": "Guide"},
                }
            }
        )

    monkeypatch.setattr(catalog, "_localized_map_keydefs", lambda _locale: {})
    monkeypatch.setattr(catalog, "_guide_titles", lambda _filename: {"en": "Guide"})
    with pytest.raises(BuildError, match="missing guide landing output"):
        catalog._build_topics(tmp_path)
    _write(tmp_path / "en/index.html", "index")
    monkeypatch.setattr(catalog, "_guide_topic_keyrefs", lambda *_args: ["bad"])
    with pytest.raises(BuildError, match="unsupported topic key"):
        catalog._build_topics(tmp_path)
    monkeypatch.setattr(catalog, "_guide_topic_keyrefs", lambda *_args: ["topic.guide"])
    with pytest.raises(BuildError, match="more than one guide map"):
        catalog._build_topics(tmp_path)

    source = _write(tmp_path / "sources/user/child.dita", "<task><title>Child</title></task>")
    monkeypatch.setattr(catalog, "_localized_map_keydefs", lambda _locale: {"topic.child": source})
    monkeypatch.setattr(catalog, "_guide_topic_keyrefs", lambda *_args: ["topic.child"])
    monkeypatch.setattr(
        catalog,
        "_localized_topic_roots",
        lambda *_args: {"en": ET.fromstring("<task><title>Child</title></task>")},
    )
    with pytest.raises(BuildError, match="missing topic output"):
        catalog._build_topics(tmp_path)


def _adapter_manifest(target_bytes: bytes) -> dict[str, object]:
    return {
        "ui_target_map": {"sha256": catalog._payload_sha256(target_bytes)},
        "navigation": {},
        "search": {},
        "topics": {},
    }


def test_manifest_file_adapter_reports_each_owned_artifact_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target_bytes = b"{}"
    target = _write(tmp_path / "ui-target-map.json", target_bytes)
    manifest = _adapter_manifest(target_bytes)
    manifest_path = _write(tmp_path / "manifest.json", json.dumps(manifest))
    monkeypatch.setattr(catalog, "_validate_schema", lambda *_args: None)
    monkeypatch.setattr(catalog, "_validate_manifest_semantics", lambda *_args: None)
    monkeypatch.setattr(
        catalog,
        "_search_quality_performance",
        lambda: {"performance_budget": {"max_index_bytes_per_locale": 4}},
    )

    manifest["navigation"] = {"en": {"path": "en/navigation.json"}}
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(BuildError, match="navigation source is missing"):
        catalog.validate_manifest_files(tmp_path)
    navigation = _write(tmp_path / "en/navigation.json", "{}")
    monkeypatch.setattr(catalog, "_validate_navigation_artifact_record", lambda *_a, **_k: {})
    monkeypatch.setattr(catalog, "_navigation_payload", lambda *_args: {"different": True})
    with pytest.raises(BuildError, match="navigation source diverges"):
        catalog.validate_manifest_files(tmp_path)

    manifest["navigation"] = {}
    manifest["search"] = {
        "en": {"path": "search/en/index.json", "sha256": "wrong", "document_count": 0}
    }
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(BuildError, match="search file is missing"):
        catalog.validate_manifest_files(tmp_path)
    search = _write(tmp_path / "search/en/index.json", b"12345")
    with pytest.raises(BuildError, match="size budget exceeded"):
        catalog.validate_manifest_files(tmp_path)
    search.write_bytes(b"{}")
    with pytest.raises(BuildError, match="search SHA-256 mismatch"):
        catalog.validate_manifest_files(tmp_path)
    manifest["search"]["en"]["sha256"] = catalog._file_sha256(search)
    manifest["search"]["en"]["document_count"] = 1
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(BuildError, match="document count mismatch"):
        catalog.validate_manifest_files(tmp_path)
    manifest["search"] = {}
    manifest["topics"] = {"topic": {"output": {"en": "en/missing.html"}}}
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(BuildError, match="topic output is missing"):
        catalog.validate_manifest_files(tmp_path)
    assert target.is_file() and navigation.is_file()


def test_manifest_payload_adapter_reports_each_owned_artifact_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = b"{}"
    manifest = _adapter_manifest(target)
    monkeypatch.setattr(catalog, "_validate_schema", lambda *_args: None)
    monkeypatch.setattr(catalog, "_validate_manifest_semantics", lambda *_args: None)
    monkeypatch.setattr(
        catalog,
        "_search_quality_performance",
        lambda: {"performance_budget": {"max_index_bytes_per_locale": 4}},
    )

    def payloads(extra: dict[str, bytes] | None = None) -> dict[str, bytes]:
        return {
            "manifest.json": json.dumps(manifest).encode(),
            "ui-target-map.json": target,
            **(extra or {}),
        }

    manifest["navigation"] = {"en": {"path": "en/navigation.json"}}
    with pytest.raises(BuildError, match="navigation source is missing"):
        catalog.validate_manifest_payloads(payloads())
    monkeypatch.setattr(catalog, "_validate_navigation_artifact_record", lambda *_a, **_k: {})
    catalog.validate_manifest_payloads(payloads({"en/navigation.json": b"{}"}))

    manifest["navigation"] = {}
    manifest["search"] = {
        "en": {"path": "search/en/index.json", "sha256": "wrong", "document_count": 0}
    }
    with pytest.raises(BuildError, match="search file is missing"):
        catalog.validate_manifest_payloads(payloads())
    with pytest.raises(BuildError, match="size budget exceeded"):
        catalog.validate_manifest_payloads(payloads({"search/en/index.json": b"12345"}))
    with pytest.raises(BuildError, match="search SHA-256 mismatch"):
        catalog.validate_manifest_payloads(payloads({"search/en/index.json": b"{}"}))
    search = b"{}"
    manifest["search"]["en"]["sha256"] = catalog._payload_sha256(search)
    manifest["search"]["en"]["document_count"] = 1
    with pytest.raises(BuildError, match="document count mismatch"):
        catalog.validate_manifest_payloads(payloads({"search/en/index.json": search}))
    manifest["search"] = {}
    manifest["topics"] = {"topic": {"output": {"en": "en/missing.html"}}}
    with pytest.raises(BuildError, match="topic output is missing"):
        catalog.validate_manifest_payloads(payloads())

    search = b"{}"
    manifest["search"] = {
        "en": {
            "path": "search/en/index.json",
            "sha256": catalog._payload_sha256(search),
            "document_count": 0,
        }
    }
    manifest["topics"] = {"topic": {"output": {"en": "en/topic.html"}}}
    monkeypatch.setattr(catalog, "_validate_search_index_semantics", lambda *_args: None)
    catalog.validate_manifest_payloads(
        payloads({"search/en/index.json": search, "en/topic.html": b"topic"})
    )


def test_manifest_generation_requires_authoritative_navigation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(catalog, "LOCALES", ("en",))
    monkeypatch.setattr(catalog, "_build_topics", lambda _root: {})
    monkeypatch.setattr(catalog, "_build_target_map", lambda _topics: {})
    monkeypatch.setattr(catalog, "_validate_schema", lambda *_args: None)
    with pytest.raises(BuildError, match="navigation source is missing"):
        catalog.generate_manifest_files(tmp_path)
    _write(tmp_path / "en/navigation.json", "{}")
    monkeypatch.setattr(catalog, "_navigation_payload", lambda *_args: {"different": True})
    with pytest.raises(BuildError, match="navigation source diverges"):
        catalog.generate_manifest_files(tmp_path)
