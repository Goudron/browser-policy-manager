from __future__ import annotations

import importlib.util
import json
import tarfile
from pathlib import Path

import pytest

DOCUMENTATION_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = DOCUMENTATION_ROOT / "tools/build_docs.py"
SPEC = importlib.util.spec_from_file_location("build_docs", MODULE_PATH)
assert SPEC and SPEC.loader
build_docs = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build_docs)


def test_source_link_validation_accepts_keys_files_and_fragments(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source.dita"
    target = tmp_path / "target.dita"
    source.write_text(
        '<topic id="source"><title>Source</title><body>'
        '<xref keyref="topic.target"/><xref href="target.dita#target/a-detail"/>'
        "</body></topic>",
        encoding="utf-8",
    )
    target.write_text(
        '<topic id="target"><title>Target</title><body><section id="a-detail">'
        "<title>Detail</title></section></body></topic>",
        encoding="utf-8",
    )
    keys = tmp_path / "keys.ditamap"
    keys.write_text('<map id="keys"><keydef keys="topic.target" href="target.dita"/></map>')
    monkeypatch.setattr(build_docs, "DOCUMENTATION_ROOT", tmp_path)
    monkeypatch.setattr(build_docs, "dita_sources", lambda: [keys, source, target])

    build_docs.validate_source_links()


def test_source_link_validation_reports_unknown_key_and_missing_target(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source.dita"
    source.write_text(
        '<topic id="source"><title>Source</title><body>'
        '<xref keyref="topic.missing"/><xref href="missing.dita"/>'
        "</body></topic>",
        encoding="utf-8",
    )
    monkeypatch.setattr(build_docs, "DOCUMENTATION_ROOT", tmp_path)
    monkeypatch.setattr(build_docs, "dita_sources", lambda: [source])

    with pytest.raises(build_docs.BuildError) as error:
        build_docs.validate_source_links()

    assert "unknown keyref 'topic.missing'" in str(error.value)
    assert "missing local target 'missing.dita'" in str(error.value)


def test_source_link_validation_reports_malformed_xml_with_file_context(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "broken.dita"
    source.write_text('<topic id="broken"><title>Broken</topic>', encoding="utf-8")
    monkeypatch.setattr(build_docs, "dita_sources", lambda: [source])

    with pytest.raises(build_docs.BuildError, match=r"invalid DITA XML .*broken\.dita"):
        build_docs.validate_source_links()


def test_fast_check_validates_one_changed_topic_and_reports_affected_outputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = tmp_path
    documentation = repository / "documentation"
    topic = documentation / "src/dita/en/user/topic.dita"
    target = documentation / "src/dita/en/user/target.dita"
    topic.parent.mkdir(parents=True)
    topic.write_text(
        '<topic id="ug-task-fast-loop"><title>Fast loop</title><body>'
        '<xref href="target.dita#target/detail"/></body></topic>',
        encoding="utf-8",
    )
    target.write_text(
        '<topic id="target"><title>Target</title><body><section id="detail">'
        "<title>Detail</title></section></body></topic>",
        encoding="utf-8",
    )
    monkeypatch.setattr(build_docs, "REPOSITORY_ROOT", repository)
    monkeypatch.setattr(build_docs, "DOCUMENTATION_ROOT", documentation)

    report = build_docs.fast_check(["documentation/src/dita/en/user/topic.dita"], emit=False)

    assert report["checked"] == ["documentation/src/dita/en/user/topic.dita"]
    assert report["locales"] == ["en"]
    assert report["guide_roots"] == ["user"]
    assert report["search_indexes"] == ["en"]
    assert "documentation/build/site/en/user/ug-task-fast-loop.html" in report["affected_outputs"]
    assert "documentation/build/site/search/en/index.json" in report["affected_outputs"]
    assert report["recommended_next_checks"] == ["make test-docs-contract", "make docs-validate"]


def test_fast_check_rejects_broken_changed_dita_without_full_build(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = tmp_path
    documentation = repository / "documentation"
    topic = documentation / "src/dita/ru/user/broken.dita"
    topic.parent.mkdir(parents=True)
    topic.write_text('<topic id="broken"><title>Broken</topic>', encoding="utf-8")
    monkeypatch.setattr(build_docs, "REPOSITORY_ROOT", repository)
    monkeypatch.setattr(build_docs, "DOCUMENTATION_ROOT", documentation)

    with pytest.raises(build_docs.BuildError, match="focused source link validation failed"):
        build_docs.fast_check(["documentation/src/dita/ru/user/broken.dita"], emit=False)


def test_failure_diagnostics_name_smallest_documentation_context(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = tmp_path
    documentation = repository / "documentation"
    diagnostics_root = documentation / "reports/diagnostics"
    topic = documentation / "src/dita/en/user/ug-task-diagnostics.dita"
    topic.parent.mkdir(parents=True)
    topic.write_text(
        '<topic id="ug-task-diagnostics"><title>Diagnostics</title></topic>',
        encoding="utf-8",
    )
    monkeypatch.setattr(build_docs, "REPOSITORY_ROOT", repository)
    monkeypatch.setattr(build_docs, "DOCUMENTATION_ROOT", documentation)
    monkeypatch.setattr(build_docs, "DIAGNOSTICS_ROOT", diagnostics_root)

    payload = build_docs._diagnostic_payload(
        build_docs.BuildError("focused source link validation failed"),
        ["documentation/src/dita/en/user/ug-task-diagnostics.dita"],
    )
    context = payload["contexts"][0]

    assert payload["backlog_item"] == "BPM090-M11-06"
    assert payload["focused_rerun"] == (
        'make docs-fast-check DOCS_CHANGED="documentation/src/dita/en/user/ug-task-diagnostics.dita"'
    )
    assert context["topic_id"] == "ug-task-diagnostics"
    assert context["locale"] == "en"
    assert context["guide"] == "user"
    assert context["source_line"] == 1
    assert context["target_url"] == "/help/en/user/ug-task-diagnostics.html"
    assert context["query"]
    assert context["screenshot_state"]
    assert context["focused_rerun"] == (
        "make docs-fast-check DOCS_CHANGED=documentation/src/dita/en/user/ug-task-diagnostics.dita"
    )

    artifact = build_docs.write_failure_diagnostic(
        build_docs.BuildError("focused source link validation failed"),
        ["documentation/src/dita/en/user/ug-task-diagnostics.dita"],
    )
    written = json.loads(artifact.read_text(encoding="utf-8"))
    assert artifact.parent == diagnostics_root
    assert written["contexts"][0]["target_url"] == "/help/en/user/ug-task-diagnostics.html"


def _minimal_site(root: Path) -> None:
    localized_keydefs = {locale: build_docs._localized_map_keydefs(locale) for locale in build_docs.LOCALES}
    for locale in build_docs.LOCALES:
        locale_root = root / locale
        locale_root.mkdir(parents=True)
        (locale_root / "index.html").write_text(
            f'<!doctype html><html lang="{locale}"><head><title>{locale}</title></head>'
            '<body><h1>Home</h1><a id="top" href="page.html#detail">Page</a></body></html>',
            encoding="utf-8",
        )
        (locale_root / "page.html").write_text(
            f'<!doctype html><html lang="{locale}"><head><title>{locale} page</title></head>'
            '<body><h1 id="detail">Detail</h1><pre><code>{}</code></pre>'
            '<table><caption>Data</caption><tr><th scope="col">Name</th></tr></table>'
            '<div class="note">Note</div></body></html>',
            encoding="utf-8",
        )
        for _guide_id, filename, _anchor, _url_root in build_docs.GUIDE_MAPS:
            for keyref in build_docs._guide_topic_keyrefs("en", filename):
                topic_id = keyref.removeprefix("topic.")
                topic_path = localized_keydefs[locale][keyref]
                output = locale_root / topic_path.parent.name / f"{topic_id}.html"
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text(
                    f'<!doctype html><html lang="{locale}"><head><title>{topic_id}</title></head>'
                    f"<body><h1>{topic_id}</h1></body></html>",
                    encoding="utf-8",
                )


def test_generated_link_validation_accepts_complete_six_locale_site(tmp_path: Path) -> None:
    _minimal_site(tmp_path)
    build_docs.apply_portal_shell(tmp_path)

    build_docs.validate_output(tmp_path)


def test_locale_root_link_normalization_keeps_dita_outputs_inside_locale_root(tmp_path: Path) -> None:
    locale_root = tmp_path / "en"
    (locale_root / "user").mkdir(parents=True)
    (locale_root / "index.html").write_text(
        '<!doctype html><html lang="en"><head><link href="../commonltr.css"></head>'
        '<body><h1>Home</h1><a href="../user/topic.html#top">Topic</a></body></html>',
        encoding="utf-8",
    )
    (locale_root / "commonltr.css").write_text("body {}", encoding="utf-8")
    (locale_root / "user/topic.html").write_text(
        '<!doctype html><html lang="en"><head><link href="../commonltr.css"></head>'
        '<body><h1 id="top">Topic</h1></body></html>',
        encoding="utf-8",
    )

    build_docs._normalize_locale_root_links(tmp_path)

    index = (locale_root / "index.html").read_text(encoding="utf-8")
    topic = (locale_root / "user/topic.html").read_text(encoding="utf-8")
    assert 'href="commonltr.css"' in index
    assert 'href="user/topic.html#top"' in index
    assert 'href="../commonltr.css"' in topic


def test_generated_link_validation_rejects_missing_fragment(tmp_path: Path) -> None:
    _minimal_site(tmp_path)
    page = tmp_path / "en/index.html"
    page.write_text(
        '<html lang="en"><head><title>Broken</title></head>'
        '<body><h1>Broken</h1><a href="page.html#missing">Broken</a></body></html>',
        encoding="utf-8",
    )
    build_docs.apply_portal_shell(tmp_path)

    with pytest.raises(build_docs.BuildError, match="missing generated fragment"):
        build_docs.validate_output(tmp_path)


def test_portal_shell_adds_accessibility_landmarks_theme_assets_and_locale_peers(
    tmp_path: Path,
) -> None:
    _minimal_site(tmp_path)

    build_docs.apply_portal_shell(tmp_path)

    for locale in build_docs.LOCALES:
        html = (tmp_path / locale / "index.html").read_text(encoding="utf-8")
        assert 'class="bpm-docs-shell"' in html
        assert 'href="#main-content"' in html
        assert '<main id="main-content"' in html
        assert 'class="bpm-docs-search"' in html
        assert 'role="search"' in html
        assert 'id="bpm-docs-search-query"' in html
        assert 'data-search-index-href="../search/' in html or 'data-search-index-href="search/' in html
        assert 'role="status" aria-live="polite"' in html
        assert 'bpm-docs-search.js" defer' in html
        assert 'class="bpm-docs-breadcrumbs"' in html
        assert 'aria-label=' in html
        assert f'hreflang="{locale}" lang="{locale}" aria-current="true"' in html
        assert 'href="#a-user-guide"' in html
        assert 'BPM 0.9.0' in html
        assert (tmp_path / locale / "assets/bpm-docs.css").is_file()
        assert (tmp_path / locale / "assets/bpm-docs-print.css").is_file()
        assert (tmp_path / locale / "assets/bpm-docs-search.js").is_file()

    build_docs.validate_output(tmp_path)


def test_portal_shell_validation_rejects_inline_styles_and_active_content(tmp_path: Path) -> None:
    _minimal_site(tmp_path)
    build_docs.apply_portal_shell(tmp_path)
    page = tmp_path / "en/index.html"
    page.write_text(
        page.read_text(encoding="utf-8").replace("<h1>Home</h1>", '<h1 style="color:red">Home</h1>')
        + "<script></script>",
        encoding="utf-8",
    )

    with pytest.raises(build_docs.BuildError) as error:
        build_docs.validate_output(tmp_path)

    assert "forbidden attribute 'style'" in str(error.value)
    assert "forbidden script element" in str(error.value)


def test_tree_hashes_detect_changed_and_added_publishable_files(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    (first / "index.html").write_text("same", encoding="utf-8")
    (second / "index.html").write_text("same", encoding="utf-8")

    assert build_docs.tree_hashes(first) == build_docs.tree_hashes(second)
    (second / "index.html").write_text("changed", encoding="utf-8")
    (second / "extra.css").write_text("extra", encoding="utf-8")
    assert build_docs.tree_hashes(first) != build_docs.tree_hashes(second)


def _artifact_fixture(tmp_path: Path) -> tuple[Path, dict[str, object]]:
    policy = {
        "schema_version": 1,
        "target_bpm_version": "0.9.0",
        "archive": {"root": "bpm-documentation-0.9.0"},
    }
    root = tmp_path / "bpm-documentation-0.9.0"
    _minimal_site(root)
    build_docs.apply_portal_shell(root)
    build_docs.generate_manifest_files(root)
    integrity = {
        "runtime_ready": False,
        "runtime_blockers": ["runtime-ready six locale search indexes"],
        "files": build_docs.tree_hashes(root),
    }
    (root / "artifact-integrity.json").write_text(
        json.dumps(integrity, sort_keys=True) + "\n", encoding="utf-8"
    )
    return root, policy


def test_normalized_archives_are_byte_identical_and_verifiable(tmp_path: Path) -> None:
    root, policy = _artifact_fixture(tmp_path)
    first = tmp_path / "first.tar.gz"
    second = tmp_path / "second.tar.gz"

    build_docs.create_archive(root, first)
    build_docs.create_archive(root, second)

    assert first.read_bytes() == second.read_bytes()
    assert build_docs.verify_archive(first, policy) == build_docs.verify_archive(second, policy)
    with tarfile.open(first, "r:gz") as bundle:
        assert all(member.mtime == 0 and member.uid == 0 and member.gid == 0 for member in bundle)
        assert all(member.mode == (0o755 if member.isdir() else 0o644) for member in bundle)


def test_manifest_generation_lists_guides_locales_search_and_target_map(tmp_path: Path) -> None:
    _minimal_site(tmp_path)
    build_docs.apply_portal_shell(tmp_path)

    build_docs.generate_manifest_files(tmp_path)

    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    target_map = json.loads((tmp_path / "ui-target-map.json").read_text(encoding="utf-8"))
    assert manifest["schema_version"] == 1
    assert manifest["locales"] == list(build_docs.LOCALES)
    assert set(manifest["guides"]) == {
        "user-guide",
        "firefox-policy-guide",
        "cis-settings-guide",
        "api-integration-guide",
        "administrator-guide",
    }
    assert len(manifest["topics"]) == 156
    assert set(manifest["search"]) == set(build_docs.LOCALES)
    search_payload = json.loads((tmp_path / manifest["search"]["en"]["path"]).read_text(encoding="utf-8"))
    assert search_payload["contract_id"] == "bpm-doc-search-corpus-results-0.9.0"
    assert search_payload["contract_schema_version"] == 1
    assert search_payload["normalization_contract_id"] == "bpm-doc-search-normalization-aliases-0.9.0"
    assert search_payload["normalization_schema_version"] == 1
    assert search_payload["ranking_contract_id"] == "bpm-doc-search-ranking-typo-0.9.0"
    assert search_payload["ranking_schema_version"] == 1
    assert search_payload["facets_contract_id"] == "bpm-doc-search-facets-filters-0.9.0"
    assert search_payload["facets_schema_version"] == 1
    assert search_payload["quality_contract_id"] == "bpm-doc-search-quality-performance-0.9.0"
    assert search_payload["quality_schema_version"] == 1
    assert search_payload["integrity_contract_id"] == "bpm-doc-search-integrity-drift-0.9.0"
    assert search_payload["integrity_schema_version"] == 1
    assert search_payload["result_schema_version"] == 1
    assert search_payload["target_bpm_version"] == "0.9.0"
    assert search_payload["search_mode"] == "deterministic-local-static"
    assert search_payload["non_ai_boundary"] == "no-ai-no-rag-no-embeddings-no-generative-answers"
    assert search_payload["status"] == "ready"
    assert search_payload["index_kind"] == "dita-document-corpus-v1"
    assert search_payload["allowlisted_cross_locale_fields"] == ["identifiers"]
    assert search_payload["normalization"]["unicode_form"] == "NFKC"
    assert search_payload["normalization"]["alias_group_count"] == 5
    assert search_payload["normalization"]["query_fixture_count"] == 3
    assert search_payload["ranking"]["ranking_order"] == [
        "exact_identifier",
        "title",
        "alias",
        "heading",
        "body",
        "bounded_typo",
    ]
    assert search_payload["ranking"]["weights"]["exact_identifier"] > search_payload["ranking"]["weights"]["title"]
    assert search_payload["ranking"]["ranking_fixture_count"] == 5
    assert search_payload["filtering"]["composition"] == (
        "AND across facet fields; OR within values of the same facet field."
    )
    assert search_payload["filtering"]["url_state"]["parameters"]["guide_id"] == "guide"
    assert search_payload["filtering"]["filter_fixture_count"] == 5
    assert search_payload["facet_counts"]["guide_id"]["user-guide"] > 0
    assert search_payload["facet_counts"]["firefox_channel"]["release-152"] > 0
    assert search_payload["facet_counts"]["policy_category"]["ai_smart"] > 0
    assert search_payload["facet_counts"]["cis_level"]["level-1"] > 0
    assert search_payload["facet_counts"]["cis_control_state"]["mapped"] > 0
    assert search_payload["facet_counts"]["api_area"]["validation"] > 0
    assert search_payload["quality"]["fixture_count"] == 9
    assert set(search_payload["quality"]["categories"]) >= {
        "exact",
        "natural_language",
        "typo",
        "synonym",
        "channel",
        "cis",
        "api",
        "no_result",
        "adversarial",
    }
    assert search_payload["performance_report"]["document_count"] == len(manifest["topics"])
    assert search_payload["performance_report"]["quality_fixture_count"] == 9
    assert search_payload["performance_report"]["deterministic_scan_units"] == len(manifest["topics"]) * 9
    assert search_payload["performance_report"]["max_observed_visible_results"] <= 50
    assert search_payload["integrity_report"]["status"] == "pass"
    assert search_payload["integrity_report"]["failure_count"] == 0
    assert search_payload["integrity_report"]["counts"]["manifest_topics"] == len(manifest["topics"])
    assert search_payload["integrity_report"]["document_integrity"]["missing_topic_ids"] == []
    assert search_payload["integrity_report"]["document_integrity"]["duplicate_document_ids"] == []
    assert search_payload["integrity_report"]["anchor_integrity"]["stale_target_anchors"] == []
    assert search_payload["integrity_report"]["snippet_integrity"]["broken_snippet_document_ids"] == []
    assert search_payload["integrity_report"]["inventory_gap_integrity"]["api"]["missing_source_ids"] == []
    assert {fixture["locale"] for fixture in search_payload["query_fixtures"]} == {"en"}
    ranking_results = {
        result["fixture_id"]: result
        for result in search_payload["ranking_fixture_results"]
    }
    assert ranking_results["exact-policy-ai-controls"]["top_topic_id"] == "fx-concept-complex-policy-families"
    assert ranking_results["exact-policy-ai-controls"]["score_breakdown"]["exact_identifier"] > 0
    assert ranking_results["title-api-validation"]["top_topic_id"] == "admin-task-validate-firefox-policies-json"
    assert ranking_results["title-api-validation"]["score_breakdown"]["title"] > 0
    assert ranking_results["typo-en-profile-library"]["top_topic_id"] == "ug-task-use-profile-library"
    assert ranking_results["typo-en-profile-library"]["score_breakdown"]["bounded_typo"] > 0
    filter_results = {
        result["fixture_id"]: result
        for result in search_payload["filter_fixture_results"]
    }
    assert filter_results["en-api-validation"]["result_count"] >= 1
    assert "admin-task-validate-firefox-policies-json" in filter_results["en-api-validation"]["result_topic_ids"]
    assert filter_results["en-api-validation"]["url_query"] == (
        "api_area=validation&guide=administrator-guide"
    )
    assert filter_results["en-empty-api-cis"]["result_count"] == 0
    assert filter_results["en-empty-api-cis"]["empty_result_message"]
    quality_results = {
        result["fixture_id"]: result
        for result in search_payload["quality_fixture_results"]
    }
    assert quality_results["en-exact-ai-controls"]["top_topic_id"] == "fx-concept-complex-policy-families"
    assert quality_results["en-exact-ai-controls"]["required_score_component_value"] > 0
    assert quality_results["en-natural-profile-library"]["top_topic_id"] == "ug-task-use-profile-library"
    assert quality_results["en-typo-profile-library"]["required_score_component_value"] > 0
    assert quality_results["en-channel-release-ai"]["result_count"] == 1
    assert quality_results["en-cis-recommendation"]["top_topic_id"] == "cis-settings-guide"
    assert quality_results["en-api-validation"]["top_topic_id"] == "admin-task-validate-firefox-policies-json"
    assert quality_results["en-no-result"]["result_count"] == 0
    assert quality_results["en-adversarial-html-like"]["result_count"] == 0
    assert set(search_payload["searchable_fields"]) == {
        "title",
        "shortdesc",
        "headings",
        "body",
        "keywords",
        "identifiers",
        "aliases",
    }
    assert set(search_payload["document_required_fields"]) >= {"source", "searchable", "facets"}
    assert set(search_payload["result_required_fields"]) >= {"snippet", "score_breakdown", "facets"}
    assert len(search_payload["documents"]) == len(manifest["topics"])
    first_document = search_payload["documents"][0]
    assert first_document["locale"] == "en"
    assert first_document["document_id"] == f"en:{first_document['topic_id']}"
    assert first_document["url"].startswith("/help/en/")
    assert first_document["source"]["output_path"].startswith("en/")
    assert first_document["searchable"]["title"]
    assert first_document["searchable"]["body"]
    assert first_document["topic_id"] in first_document["searchable"]["identifiers"]
    assert first_document["filter_facets"]["locale"] == ["en"]
    assert first_document["filter_facets"]["guide_id"] == [first_document["guide_id"]]
    assert first_document["filter_facets"]["bpm_version"] == ["0.9.0"]
    assert set(first_document["normalized"]["fields"]) == set(search_payload["searchable_fields"])
    assert first_document["normalized"]["tokens"]
    assert first_document["topic_id"] in first_document["normalized"]["fields"]["identifiers"]

    ai_documents = [
        document
        for document in search_payload["documents"]
        if "firefox-ai-controls" in document["normalized"]["alias_ids"]
    ]
    assert ai_documents
    assert any("aicontrols" in document["normalized"]["tokens"] for document in ai_documents)
    assert any("ai_smart" in document["filter_facets"]["policy_category"] for document in ai_documents)

    api_documents = [
        document
        for document in search_payload["documents"]
        if "validation" in document["filter_facets"]["api_area"]
    ]
    assert api_documents
    assert any(document["topic_id"] == "admin-task-validate-firefox-policies-json" for document in api_documents)

    ru_payload = json.loads((tmp_path / manifest["search"]["ru"]["path"]).read_text(encoding="utf-8"))
    assert all(document["locale"] == "ru" for document in ru_payload["documents"])
    assert all(document["url"].startswith("/help/ru/") for document in ru_payload["documents"])
    assert all(
        document["source"]["output_path"].startswith("ru/")
        for document in ru_payload["documents"]
    )
    ru_filter_results = {
        result["fixture_id"]: result
        for result in ru_payload["filter_fixture_results"]
    }
    assert ru_filter_results["ru-empty-api-cis"]["result_count"] == 0
    assert ru_filter_results["ru-empty-api-cis"]["empty_result_message"].startswith("Нет страниц")
    ru_quality_results = {
        result["fixture_id"]: result
        for result in ru_payload["quality_fixture_results"]
    }
    assert ru_quality_results["ru-natural-profile-library"]["top_topic_id"] == "ug-task-use-profile-library"
    assert ru_quality_results["ru-no-result"]["result_count"] == 0
    assert manifest["ui_target_map"]["sha256"] == build_docs._file_sha256(
        tmp_path / "ui-target-map.json"
    )
    assert len(target_map["targets"]) == 452
    assert "policy:AIControls" in target_map["targets"]
    assert "capability:CAP-SET-001" in target_map["targets"]
    assert "cis:1.1.1.1" in target_map["targets"]
    assert "api-operation:API-VAL-001" in target_map["targets"]
    build_docs.validate_manifest_files(tmp_path)


def test_search_indexes_are_reproducible_for_clean_publish_trees(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    for root in (first, second):
        _minimal_site(root)
        build_docs.apply_portal_shell(root)
        build_docs.generate_manifest_files(root)

    for locale in build_docs.LOCALES:
        relative = Path("search") / locale / "index.json"
        assert (first / relative).read_bytes() == (second / relative).read_bytes()


def test_package_removes_stale_outputs_before_validation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive = tmp_path / "stale.tar.gz"
    checksum = tmp_path / "stale.tar.gz.sha256"
    archive.write_bytes(b"stale")
    checksum.write_text("stale", encoding="ascii")
    monkeypatch.setattr(build_docs, "DIST_ROOT", tmp_path)
    monkeypatch.setattr(build_docs, "_artifact_policy", lambda: {"schema_version": 1})
    monkeypatch.setattr(build_docs, "artifact_paths", lambda _policy: (archive, checksum))
    monkeypatch.setattr(
        build_docs,
        "validate_sources",
        lambda: (_ for _ in ()).throw(build_docs.BuildError("invalid source")),
    )

    with pytest.raises(build_docs.BuildError, match="invalid source"):
        build_docs.package()

    assert not archive.exists()
    assert not checksum.exists()


def test_makefile_exposes_only_the_implemented_documentation_build_targets() -> None:
    makefile = (DOCUMENTATION_ROOT.parent / "Makefile").read_text(encoding="utf-8")

    for target in (
        "test-docs",
        "test-docs-contract",
        "test-docs-ui",
        "docs-snapshot",
        "docs-fast-check",
        "docs-coverage",
        "docs-validate",
        "docs-build",
        "docs-install-dev",
        "docs-reproducibility-check",
        "docs-package",
        "docs-package-verify",
    ):
        assert f"{target}:" in makefile
    for deferred in ("docs-screenshots-check",):
        assert f"{deferred}:" not in makefile
