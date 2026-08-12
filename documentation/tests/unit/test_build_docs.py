from __future__ import annotations

import copy
import importlib.util
import json
import tarfile
from pathlib import Path

import pytest

from documentation.buildlib.validation import ValidationIssue, ValidationReporter, ValidationStage

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
    assert report["recommended_next_checks"] == ["make docs-release-handoff"]
    assert "schema and direct links" in report["checked_guards"]
    assert "binary PDF build, verification, and delivery" in report["skipped_release_only_checks"]


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
    localized_keydefs = {
        locale: build_docs._localized_map_keydefs(locale) for locale in build_docs.LOCALES
    }
    for locale in build_docs.LOCALES:
        locale_root = root / locale
        locale_root.mkdir(parents=True)
        guide_anchors = "".join(
            f'<section id="{anchor}"><h2>{guide_id}</h2></section>'
            for guide_id, _filename, anchor, _url_root in build_docs.GUIDE_MAPS
        )
        (locale_root / "index.html").write_text(
            f'<!doctype html><html lang="{locale}"><head><title>{locale}</title></head>'
            f'<body><h1>Home</h1><a id="top" href="page.html#detail">Page</a>{guide_anchors}</body></html>',
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


def _navigation_nodes(payload: dict[str, object]) -> dict[str, dict[str, object]]:
    nodes: dict[str, dict[str, object]] = {}

    def visit(node: dict[str, object], parent: str, level: int) -> None:
        nodes[str(node["node_id"])] = {"node": node, "parent": parent, "level": level}
        for child in node["children"]:
            visit(child, str(node["node_id"]), level + 1)

    visit(payload["root"], "", 1)
    return nodes


def test_generated_link_validation_accepts_complete_six_locale_site(tmp_path: Path) -> None:
    _minimal_site(tmp_path)
    build_docs.apply_portal_shell(tmp_path)

    build_docs.validate_output(tmp_path)


def test_locale_root_link_normalization_keeps_dita_outputs_inside_locale_root(
    tmp_path: Path,
) -> None:
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


def test_screenshot_link_normalization_points_to_locale_assets(tmp_path: Path) -> None:
    locale_root = tmp_path / "en"
    screenshot = locale_root / "assets/screenshots/ug-library-overview-desktop-light.png"
    topic = locale_root / "user/ug-task-use-profile-library.html"
    screenshot.parent.mkdir(parents=True)
    topic.parent.mkdir(parents=True)
    screenshot.write_bytes(b"png")
    topic.write_text(
        '<!doctype html><html lang="en"><body><h1>Topic</h1>'
        '<img src="file:/tmp/dita/input/assets/screenshots/en/ug-library-overview-desktop-light.png">'
        "</body></html>",
        encoding="utf-8",
    )

    build_docs._normalize_screenshot_links(tmp_path)

    html = topic.read_text(encoding="utf-8")
    assert 'src="../assets/screenshots/ug-library-overview-desktop-light.png"' in html


def test_transient_dita_screenshot_copies_are_removed_from_publishable_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    screenshot_source = tmp_path / "source/en"
    screenshot_source.mkdir(parents=True)
    screenshot_name = "ug-library-overview-desktop-light.png"
    (screenshot_source / screenshot_name).write_bytes(b"source")
    monkeypatch.setattr(build_docs, "SCREENSHOT_ROOT", tmp_path / "source")

    locale_root = tmp_path / "site/en"
    canonical = locale_root / "assets/screenshots" / screenshot_name
    transient = (
        locale_root
        / "home/build/.publish-example/.site-dita-temp/en/input/assets/screenshots/en"
        / screenshot_name
    )
    canonical.parent.mkdir(parents=True)
    transient.parent.mkdir(parents=True)
    canonical.write_bytes(b"source")
    transient.write_bytes(b"source")

    build_docs._remove_dita_transient_screenshot_copies(tmp_path / "site")

    assert canonical.is_file()
    assert not (locale_root / "home").exists()


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
        assert 'class="bpm-docs-discovery-tools"' in html
        assert 'class="bpm-docs-assistant-widget"' in html
        assert "data-documentation-assistant-widget" in html
        assert f'data-assistant-locale="{locale}"' in html
        assert 'data-assistant-expanded="false"' in html
        assert "data-assistant-toggle" in html
        assert "data-assistant-panel hidden" in html
        assert 'class="bpm-docs-assistant-entry"' not in html
        assert 'data-assistant-state="unavailable"' in html
        assert 'role="log"' in html
        assert 'data-assistant-message-roles="user assistant system"' in html
        assert "data-assistant-question" in html
        assert "data-assistant-install" in html
        assert "data-assistant-clear" in html
        assert "data-assistant-send" in html
        assert "data-assistant-stop" in html
        assert "data-local-model-manager" not in html
        assert "data-assistant-web-control" not in html
        assert "data-assistant-web-toggle" not in html
        assistant_copy = json.loads(
            (tmp_path / locale / "assistant-copy.json").read_text(encoding="utf-8")
        )
        assert assistant_copy["locale"] == locale
        assert assistant_copy["messages"]["states"]["ready"]["title"]
        assert assistant_copy["messages"]["states"]["ready"]["live"]
        assert assistant_copy["messages"]["states"]["ready"]["aria"]
        assert assistant_copy["messages"]["shell"]["assistant_ready"]
        assert assistant_copy["messages"]["shell"]["assistant_clear_short"]
        assert assistant_copy["messages"]["shell"]["assistant_external_sources"]
        assert "assistant-copy.json" not in html
        assert (
            'data-search-index-href="../search/' in html
            or 'data-search-index-href="search/' in html
        )
        assert 'role="status" aria-live="polite"' in html
        assert 'bpm-docs-search.js" defer' in html
        assert 'bpm-docs-model-manager.js" defer' in html
        assert 'bpm-docs-assistant-renderer.js" defer' in html
        assert 'bpm-docs-assistant-state-machine.js" defer' in html
        assert 'bpm-docs-assistant-web-mode.js" defer' not in html
        assert 'bpm-docs-assistant-conversation.js" defer' in html
        assert 'bpm-docs-assistant-transport.js" defer' in html
        assert 'bpm-docs-assistant-shell.js" defer' in html
        assert '<meta name="theme-color" content="#edf2f7">' in html
        assert "bpm-docs-theme-control" in html
        assert "data-docs-theme-select" in html
        assert '<option value="system">' in html
        assert '<option value="light">' in html
        assert '<option value="dark">' in html
        assert 'class="bpm-docs-breadcrumbs"' in html
        assert "aria-label=" in html
        assert "data-docs-locale-select" in html
        assert '<option value="system" data-docs-locale-system>' in html
        assert f'<option value="{locale}"' in html
        assert "data-docs-locale-href=" in html
        assert "data-docs-locale-matches=" in html
        header = html[html.index('<header class="bpm-docs-header">') : html.index("</header>")]
        sidebar = html[html.index('<aside class="bpm-docs-sidebar"') : html.index("</aside>")]
        assert 'href="#a-user-guide"' not in header
        assert 'href="#a-firefox-policy-guide"' not in header
        assert "data-docs-tree-host" in sidebar
        assert 'data-navigation-href="navigation.json"' in sidebar
        assert "data-navigation-locale=" in sidebar
        assert 'data-current-tree-node="documentation-root"' in sidebar
        assert 'aria-busy="true"' in sidebar
        assert "data-docs-tree-status" in sidebar
        assert "<noscript>" in sidebar
        assert 'role="tree"' not in sidebar
        assert "data-tree-node=" not in sidebar
        for _guide_id, _filename, anchor, _url_root in build_docs.GUIDE_MAPS:
            assert f'id="{anchor}"' in html
        navigation = json.loads((tmp_path / locale / "navigation.json").read_text(encoding="utf-8"))
        nodes = _navigation_nodes(navigation)
        assert navigation["locale"] == locale
        assert navigation["node_count"] == len(nodes)
        assert list(nodes)[:3] == [
            "documentation-root",
            "user-guide",
            "section:user-guide:orient-and-plan",
        ]
        assert nodes["user-guide"]["node"]["anchor"] == "a-user-guide"
        assert nodes["firefox-policy-guide"]["node"]["anchor"] == "a-firefox-policy-guide"
        if locale == "ru":
            assert nodes["documentation-root"]["node"]["label"] == "Документы"
            assert nodes["section:user-guide:orient-and-plan"]["node"]["label"] == (
                "Планирование работы с профилями"
            )
        assert f"v{build_docs._product_version()}" in html
        assert "Documentation 0.9.1" not in html
        assert (tmp_path / locale / "assets/bpm-docs.css").is_file()
        assert (tmp_path / locale / "assets/bpm-docs-print.css").is_file()
        assert (tmp_path / locale / "assets/bpm-docs-search.js").is_file()
        assert (tmp_path / locale / "assets/bpm-docs-model-manager.js").is_file()
        assert (tmp_path / locale / "assets/bpm-docs-assistant-renderer.js").is_file()
        assert (tmp_path / locale / "assets/bpm-docs-assistant-state-machine.js").is_file()
        assert not (tmp_path / locale / "assets/bpm-docs-assistant-web-mode.js").exists()
        assert (tmp_path / locale / "assets/bpm-docs-assistant-conversation.js").is_file()
        assert (tmp_path / locale / "assets/bpm-docs-assistant-transport.js").is_file()
        assert (tmp_path / locale / "assets/bpm-docs-assistant-shell.js").is_file()
        assert (
            tmp_path / locale / "assets/screenshots/ug-library-overview-desktop-light.png"
        ).is_file()

    build_docs.validate_output(tmp_path)


def test_portal_navigation_tree_expands_current_topic_without_translated_paths(
    tmp_path: Path,
) -> None:
    _minimal_site(tmp_path)
    build_docs.apply_portal_shell(tmp_path)

    first_topic_id = build_docs._navigation_topic_order("user-guide.ditamap")[0]
    first_topic_title = build_docs._navigation_model(tmp_path)["topics"][first_topic_id]["title"][
        "ru"
    ]
    html = (tmp_path / "ru" / "user" / f"{first_topic_id}.html").read_text(encoding="utf-8")
    sidebar = html[html.index('<aside class="bpm-docs-sidebar"') : html.index("</aside>")]
    navigation = json.loads((tmp_path / "ru/navigation.json").read_text(encoding="utf-8"))
    nodes = _navigation_nodes(navigation)

    assert 'aria-label="Дерево документации"' in sidebar
    assert 'href="../index.html"' in sidebar
    assert 'data-navigation-href="../navigation.json"' in sidebar
    assert f'data-current-tree-node="{first_topic_id}"' in sidebar
    assert 'role="tree"' not in sidebar
    assert nodes["user-guide"]["node"]["href"] == "index.html#a-user-guide"
    assert nodes["section:user-guide:orient-and-plan"]["node"]["label"] == (
        "Планирование работы с профилями"
    )
    assert nodes[first_topic_id]["node"]["href"] == f"user/{first_topic_id}.html"
    assert nodes[first_topic_id]["parent"] == "section:user-guide:orient-and-plan"
    assert nodes[first_topic_id]["level"] == 4
    assert "ug-reference-product-version_ru" not in sidebar

    breadcrumbs_start = html.index('<nav class="bpm-docs-breadcrumbs"')
    breadcrumbs = html[breadcrumbs_start : html.index("</nav>", breadcrumbs_start)]
    assert 'href="../index.html">Документы</a>' in breadcrumbs
    assert 'href="../index.html#a-user-guide"' in breadcrumbs
    assert f'<li aria-current="page">{first_topic_title}</li>' in breadcrumbs


def test_portal_navigation_tree_keeps_short_guides_flat(tmp_path: Path) -> None:
    _minimal_site(tmp_path)
    build_docs.apply_portal_shell(tmp_path)

    first_topic_id = build_docs._navigation_topic_order("firefox-policy-guide.ditamap")[0]
    navigation = json.loads((tmp_path / "en/navigation.json").read_text(encoding="utf-8"))
    nodes = _navigation_nodes(navigation)

    assert nodes[first_topic_id]["parent"] == "firefox-policy-guide"
    assert nodes[first_topic_id]["level"] == 3
    assert not any(node_id.startswith("section:firefox-policy-guide:") for node_id in nodes)


def test_portal_navigation_tree_supports_hash_guide_activation_script(
    tmp_path: Path,
) -> None:
    _minimal_site(tmp_path)
    build_docs.apply_portal_shell(tmp_path)

    html = (tmp_path / "en" / "index.html").read_text(encoding="utf-8")
    sidebar = html[html.index('<aside class="bpm-docs-sidebar"') : html.index("</aside>")]
    script = (tmp_path / "en" / "assets" / "bpm-docs-search.js").read_text(encoding="utf-8")
    navigation = json.loads((tmp_path / "en/navigation.json").read_text(encoding="utf-8"))
    nodes = _navigation_nodes(navigation)

    assert "data-docs-tree-host" in sidebar
    assert f'data-navigation-version="{build_docs._product_version()}"' in sidebar
    assert 'role="tree"' not in sidebar
    assert nodes["documentation-root"]["node"]["label"] == "Documents"
    assert nodes["user-guide"]["node"]["anchor"] == "a-user-guide"
    assert nodes["administrator-guide"]["node"]["anchor"] == "a-administrator-guide"
    assert "setupNavigationHost" in script
    assert "validatedNavigationNodes" in script
    assert "expectedVersion = host.dataset.navigationVersion" in script
    assert "renderNavigationTree" in script
    assert "guideItemForHash" in script
    assert "window.location.hash" in script
    assert "hashchange" in script
    assert "setCurrentTreeItem(tree, guide)" in script
    assert 'tree.querySelectorAll("[data-tree-branch]")' in script
    assert 'event.key === "Enter" && item.hasAttribute("data-tree-branch")' in script
    assert 'requiredExpandedTreeNodes(tree).has(item.dataset.treeNode || "")' in script


def test_generated_compatibility_versions_follow_the_product_version(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    product_version = "9.8.7"
    monkeypatch.setattr(build_docs, "_product_version", lambda: product_version)
    _minimal_site(tmp_path)
    build_docs.apply_portal_shell(tmp_path)
    build_docs.generate_manifest_files(tmp_path)

    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    target_map = json.loads((tmp_path / "ui-target-map.json").read_text(encoding="utf-8"))
    assert manifest["artifact"]["bpm_version"] == product_version
    assert manifest["artifact"]["documentation_version"] == product_version
    assert target_map["bpm_version"] == product_version

    for locale in build_docs.LOCALES:
        navigation = json.loads((tmp_path / locale / "navigation.json").read_text(encoding="utf-8"))
        search = json.loads(
            (tmp_path / "search" / locale / "index.json").read_text(encoding="utf-8")
        )
        page = (tmp_path / locale / "index.html").read_text(encoding="utf-8")
        assert navigation["documentation_version"] == product_version
        assert search["target_bpm_version"] == product_version
        assert all(
            document["versions"]["bpm_version"] == product_version
            and document["versions"]["documentation_version"] == product_version
            for document in search["documents"]
        )
        assert f'data-navigation-version="{product_version}"' in page
        assert f'data-tree-storage-key="bpm-docs-tree:{locale}:{product_version}"' in page


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
        "administrator-guide",
    }
    assert len(manifest["topics"]) == 164
    assert set(manifest["navigation"]) == set(build_docs.LOCALES)
    for locale, record in manifest["navigation"].items():
        navigation_path = tmp_path / record["path"]
        navigation = json.loads(navigation_path.read_text(encoding="utf-8"))
        assert record["path"] == f"{locale}/navigation.json"
        assert record["sha256"] == build_docs._file_sha256(navigation_path)
        assert record["format_version"] == 1
        assert record["node_count"] == navigation["node_count"]
        assert navigation["locale"] == locale
    assert set(manifest["search"]) == set(build_docs.LOCALES)
    search_payload = json.loads(
        (tmp_path / manifest["search"]["en"]["path"]).read_text(encoding="utf-8")
    )
    assert search_payload["contract_id"] == "bpm-doc-search-corpus-results-0.9.0"
    assert search_payload["contract_schema_version"] == 1
    assert (
        search_payload["normalization_contract_id"] == "bpm-doc-search-normalization-aliases-0.9.0"
    )
    assert search_payload["normalization_schema_version"] == 1
    assert search_payload["ranking_contract_id"] == "bpm-doc-search-ranking-typo-0.9.0"
    assert search_payload["ranking_schema_version"] == 1
    assert search_payload["facets_contract_id"] == "bpm-doc-search-facets-filters-0.9.0"
    assert search_payload["facets_schema_version"] == 1
    assert (
        search_payload["domain_ranking_contract_id"] == "bpm-doc-search-domain-ranking-facets-0.9.3"
    )
    assert search_payload["domain_ranking_schema_version"] == 1
    assert search_payload["quality_contract_id"] == "bpm-doc-search-quality-performance-0.9.0"
    assert search_payload["quality_schema_version"] == 1
    assert search_payload["integrity_contract_id"] == "bpm-doc-search-integrity-drift-0.9.0"
    assert search_payload["integrity_schema_version"] == 1
    assert search_payload["result_schema_version"] == 1
    assert search_payload["target_bpm_version"] == build_docs._product_version()
    assert search_payload["search_mode"] == "deterministic-local-static"
    assert search_payload["non_ai_boundary"] == "no-ai-no-rag-no-embeddings-no-generative-answers"
    assert search_payload["status"] == "ready"
    assert search_payload["index_kind"] == "dita-document-corpus-v1"
    assert search_payload["allowlisted_cross_locale_fields"] == ["identifiers"]
    assert search_payload["normalization"]["unicode_form"] == "NFKC"
    assert search_payload["normalization"]["alias_group_count"] == 6
    assert search_payload["normalization"]["query_fixture_count"] == 4
    assert search_payload["domain_ranking"] == {
        "preserved_sources": [
            "identifiers",
            "title",
            "aliases",
            "headings",
            "body",
            "bounded_typo",
        ],
        "evidence_fields": [
            "topic_id",
            "document_id",
            "score",
            "score_breakdown",
            "matched_fields",
            "identifiers",
            "filter_facets",
        ],
        "preserved_facets": [
            "locale",
            "guide_id",
            "topic_kind",
            "firefox_channel",
            "policy_category",
            "cis_level",
            "cis_control_state",
            "api_area",
            "bpm_version",
        ],
        "maximum_evidence_rows": 50,
    }
    assert search_payload["ranking"]["ranking_order"] == [
        "exact_identifier",
        "title",
        "alias",
        "heading",
        "body",
        "bounded_typo",
    ]
    assert (
        search_payload["ranking"]["weights"]["exact_identifier"]
        > search_payload["ranking"]["weights"]["title"]
    )
    assert search_payload["ranking"]["ranking_fixture_count"] == 5
    assert search_payload["filtering"]["composition"] == (
        "AND across facet fields; OR within values of the same facet field."
    )
    assert search_payload["filtering"]["url_state"]["parameters"]["guide_id"] == "guide"
    assert search_payload["filtering"]["filter_fixture_count"] == 5
    assert search_payload["facet_counts"]["guide_id"]["user-guide"] > 0
    assert search_payload["facet_counts"]["firefox_channel"]["release-153"] > 0
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
    assert (
        search_payload["performance_report"]["deterministic_scan_units"]
        == len(manifest["topics"]) * 9
    )
    assert search_payload["performance_report"]["max_observed_visible_results"] <= 50
    assert search_payload["integrity_report"]["status"] == "pass"
    assert search_payload["integrity_report"]["failure_count"] == 0
    assert search_payload["integrity_report"]["counts"]["manifest_topics"] == len(
        manifest["topics"]
    )
    assert search_payload["integrity_report"]["document_integrity"]["missing_topic_ids"] == []
    assert search_payload["integrity_report"]["document_integrity"]["duplicate_document_ids"] == []
    assert search_payload["integrity_report"]["anchor_integrity"]["stale_target_anchors"] == []
    assert (
        search_payload["integrity_report"]["snippet_integrity"]["broken_snippet_document_ids"] == []
    )
    assert (
        search_payload["integrity_report"]["inventory_gap_integrity"]["api"]["missing_source_ids"]
        == []
    )
    assert {fixture["locale"] for fixture in search_payload["query_fixtures"]} == {"en"}
    ranking_results = {
        result["fixture_id"]: result for result in search_payload["ranking_fixture_results"]
    }
    assert (
        ranking_results["exact-policy-ai-controls"]["top_topic_id"]
        == "fx-concept-complex-policy-families"
    )
    assert ranking_results["exact-policy-ai-controls"]["score_breakdown"]["exact_identifier"] > 0
    assert (
        ranking_results["title-api-validation"]["top_topic_id"]
        == "admin-task-validate-firefox-policies-json"
    )
    assert ranking_results["title-api-validation"]["score_breakdown"]["title"] > 0
    assert (
        ranking_results["typo-en-profile-library"]["top_topic_id"] == "ug-task-use-profile-library"
    )
    assert ranking_results["typo-en-profile-library"]["score_breakdown"]["bounded_typo"] > 0
    filter_results = {
        result["fixture_id"]: result for result in search_payload["filter_fixture_results"]
    }
    assert filter_results["en-api-validation"]["result_count"] >= 1
    assert (
        "admin-task-validate-firefox-policies-json"
        in filter_results["en-api-validation"]["result_topic_ids"]
    )
    assert filter_results["en-api-validation"]["url_query"] == (
        "api_area=validation&guide=administrator-guide"
    )
    assert filter_results["en-empty-api-cis"]["result_count"] == 0
    assert filter_results["en-empty-api-cis"]["empty_result_message"]
    quality_results = {
        result["fixture_id"]: result for result in search_payload["quality_fixture_results"]
    }
    assert (
        quality_results["en-exact-ai-controls"]["top_topic_id"]
        == "fx-concept-complex-policy-families"
    )
    assert quality_results["en-exact-ai-controls"]["required_score_component_value"] > 0
    assert (
        quality_results["en-natural-profile-library"]["top_topic_id"]
        == "ug-task-use-profile-library"
    )
    assert quality_results["en-typo-profile-library"]["required_score_component_value"] > 0
    assert quality_results["en-channel-release-ai"]["result_count"] == 1
    assert quality_results["en-cis-recommendation"]["top_topic_id"] == "cis-settings-guide"
    assert (
        quality_results["en-api-validation"]["top_topic_id"]
        == "admin-task-validate-firefox-policies-json"
    )
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
    assert first_document["filter_facets"]["bpm_version"] == [build_docs._product_version()]
    assert set(first_document["normalized"]["fields"]) == set(search_payload["searchable_fields"])
    assert "tokens" not in first_document["normalized"]
    assert first_document["topic_id"] in first_document["normalized"]["fields"]["identifiers"]

    ai_documents = [
        document
        for document in search_payload["documents"]
        if "firefox-ai-controls" in document["normalized"]["alias_ids"]
    ]
    assert ai_documents
    assert any(
        "aicontrols" in document["normalized"]["fields"]["identifiers"] for document in ai_documents
    )
    assert any(
        "ai_smart" in document["filter_facets"]["policy_category"] for document in ai_documents
    )

    api_documents = [
        document
        for document in search_payload["documents"]
        if "validation" in document["filter_facets"]["api_area"]
    ]
    assert api_documents
    assert any(
        document["topic_id"] == "admin-task-validate-firefox-policies-json"
        for document in api_documents
    )

    ru_payload = json.loads(
        (tmp_path / manifest["search"]["ru"]["path"]).read_text(encoding="utf-8")
    )
    assert all(document["locale"] == "ru" for document in ru_payload["documents"])
    assert all(document["url"].startswith("/help/ru/") for document in ru_payload["documents"])
    assert all(
        document["source"]["output_path"].startswith("ru/") for document in ru_payload["documents"]
    )
    ru_filter_results = {
        result["fixture_id"]: result for result in ru_payload["filter_fixture_results"]
    }
    assert ru_filter_results["ru-empty-api-cis"]["result_count"] == 0
    assert ru_filter_results["ru-empty-api-cis"]["empty_result_message"].startswith("Нет страниц")
    ru_quality_results = {
        result["fixture_id"]: result for result in ru_payload["quality_fixture_results"]
    }
    assert (
        ru_quality_results["ru-natural-profile-library"]["top_topic_id"]
        == "ug-task-use-profile-library"
    )
    assert ru_quality_results["ru-no-result"]["result_count"] == 0
    assert manifest["ui_target_map"]["sha256"] == build_docs._file_sha256(
        tmp_path / "ui-target-map.json"
    )
    assert len(target_map["targets"]) == 525
    assert "policy:AIControls" in target_map["targets"]
    assert "known-preference:network.IDN_show_punycode" in target_map["targets"]
    assert "capability:CAP-SET-001" in target_map["targets"]
    assert "cis:1.1.1.1" in target_map["targets"]
    assert "api-operation:API-VAL-001" in target_map["targets"]
    api_targets = {
        target_id: target
        for target_id, target in target_map["targets"].items()
        if target_id.startswith("api-operation:")
    }
    assert len(api_targets) == 17
    assert all(target["topic_id"].startswith("admin-") for target in api_targets.values())
    assert all(target["topic_id"] in manifest["topics"] for target in api_targets.values())
    assert "topic:api-integration-guide" not in target_map["targets"]
    assert "topic:api-concept-administrator-integration-landing" not in target_map["targets"]
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


def test_staged_search_validation_rejects_each_semantic_failure_class(tmp_path: Path) -> None:
    _minimal_site(tmp_path)
    build_docs.apply_portal_shell(tmp_path)
    build_docs.generate_manifest_files(tmp_path)
    base_manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    search_path = tmp_path / base_manifest["search"]["en"]["path"]
    base_search = json.loads(search_path.read_text(encoding="utf-8"))

    def rewrite(payload: dict[str, object]) -> None:
        manifest = copy.deepcopy(base_manifest)
        build_docs._write_json(search_path, payload)
        manifest["search"]["en"]["sha256"] = build_docs._file_sha256(search_path)
        build_docs._write_json(tmp_path / "manifest.json", manifest)

    cases = (
        (
            "contract",
            lambda payload: payload.__setitem__("search_mode", "network"),
            "search index mode mismatch for en",
        ),
        (
            "fixtures",
            lambda payload: payload.__setitem__("query_fixtures", []),
            "search index query fixtures mismatch for en",
        ),
        (
            "documents",
            lambda payload: payload["documents"][0]["searchable"].pop("title"),
            "search document searchable fields mismatch for en/",
        ),
        (
            "ranking",
            lambda payload: payload.__setitem__("ranking_fixture_results", []),
            "search index ranking fixture results mismatch for en",
        ),
        (
            "filters",
            lambda payload: payload.__setitem__("filter_fixture_results", []),
            "search index filter fixture results mismatch for en",
        ),
        (
            "quality",
            lambda payload: payload.__setitem__("quality_fixture_results", []),
            "search index quality fixture results mismatch for en",
        ),
        (
            "budgets",
            lambda payload: payload.__setitem__("performance_report", {}),
            "search index performance report mismatch for en",
        ),
    )
    for _failure_class, mutate, diagnostic in cases:
        payload = copy.deepcopy(base_search)
        mutate(payload)
        rewrite(payload)
        with pytest.raises(build_docs.BuildError, match=diagnostic):
            build_docs.validate_manifest_files(tmp_path)


def test_manifest_validation_stages_preserve_stable_diagnostics(tmp_path: Path) -> None:
    _minimal_site(tmp_path)
    build_docs.apply_portal_shell(tmp_path)
    build_docs.generate_manifest_files(tmp_path)
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    target_map = json.loads((tmp_path / "ui-target-map.json").read_text(encoding="utf-8"))
    topic_id = next(iter(manifest["topics"]))
    manifest["topics"][topic_id]["dita_key"] = "topic.wrong"
    with pytest.raises(build_docs.BuildError, match=rf"topic {topic_id} has inconsistent DITA key"):
        build_docs._validate_manifest_semantics(manifest, target_map)


def test_validation_reporter_exposes_typed_stage_without_changing_diagnostic() -> None:
    reporter = ValidationReporter(build_docs.BuildError, artifact="manifest.json", locale="en")
    with pytest.raises(build_docs.BuildError, match="stable diagnostic"):
        reporter.require(ValidationStage.MANIFEST_TOPICS, False, "stable diagnostic")
    assert reporter.issues[0].stage is ValidationStage.MANIFEST_TOPICS
    assert reporter.issues[0].artifact == "manifest.json"
    assert reporter.issues[0].locale == "en"


def test_validation_reporter_preserves_success_and_reclassifies_legacy_failures() -> None:
    reporter = ValidationReporter(
        build_docs.BuildError, artifact="search/en/index.json", locale="en"
    )

    reporter.require(ValidationStage.SEARCH_CONTRACT, True, "not raised")
    assert reporter.stage(ValidationStage.SEARCH_CONTRACT, lambda: "accepted") == "accepted"

    def legacy_failure() -> None:
        raise build_docs.BuildError("legacy diagnostic")

    with pytest.raises(build_docs.BuildError, match="legacy diagnostic"):
        reporter.stage(ValidationStage.SEARCH_RANKING, legacy_failure)

    assert reporter.issues == [
        ValidationIssue(
            ValidationStage.SEARCH_RANKING,
            "legacy diagnostic",
            "search/en/index.json",
            "en",
        )
    ]


def test_package_keeps_last_verified_outputs_when_source_validation_fails(
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

    assert archive.read_bytes() == b"stale"
    assert checksum.read_text(encoding="ascii") == "stale"
    assert list((tmp_path / ".quarantine").glob("documentation-package-*"))


def test_source_fingerprint_tracks_current_portal_scripts_and_local_model_copy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fingerprint = build_docs._source_fingerprint()
    assert not hasattr(build_docs, "ASSISTANT_WEB_MODE_SCRIPT")

    with monkeypatch.context() as patch:
        patch.setattr(build_docs, "SEARCH_SCRIPT", "bpm-docs-print.css")
        assert build_docs._source_fingerprint() != fingerprint

    with monkeypatch.context() as patch:
        patch.setattr(build_docs, "MODEL_MANAGER_SCRIPT", "bpm-docs-print.css")
        assert build_docs._source_fingerprint() != fingerprint

    with monkeypatch.context() as patch:
        patch.setattr(build_docs, "ASSISTANT_RENDERER_SCRIPT", "bpm-docs-print.css")
        assert build_docs._source_fingerprint() != fingerprint

    with monkeypatch.context() as patch:
        patch.setattr(build_docs, "ASSISTANT_STATE_MACHINE_SCRIPT", "bpm-docs-print.css")
        assert build_docs._source_fingerprint() != fingerprint

    with monkeypatch.context() as patch:
        patch.setattr(build_docs, "ASSISTANT_CONVERSATION_SCRIPT", "bpm-docs-print.css")
        assert build_docs._source_fingerprint() != fingerprint

    with monkeypatch.context() as patch:
        patch.setattr(build_docs, "ASSISTANT_TRANSPORT_SCRIPT", "bpm-docs-print.css")
        assert build_docs._source_fingerprint() != fingerprint

    with monkeypatch.context() as patch:
        patch.setattr(build_docs, "ASSISTANT_SHELL_SCRIPT", "bpm-docs-print.css")
        assert build_docs._source_fingerprint() != fingerprint

    with monkeypatch.context() as patch:
        patch.setattr(build_docs, "DOCUMENTATION_ASSISTANT_COPY", build_docs.MANIFEST_SCHEMA)
        assert build_docs._source_fingerprint() != fingerprint

    with monkeypatch.context() as patch:
        patch.setattr(build_docs, "PDF_PRINT_CSS", build_docs.MANIFEST_SCHEMA)
        assert build_docs._source_fingerprint() != fingerprint


def _fake_pdf_payload() -> bytes:
    payload = (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /CreationDate (D:20260801184921+03'00') >>\nendobj\n"
        b"trailer\n<< /ID [<37B735189F1AA8E704DCCD50F8032B58> "
        b"<37B735189F1AA8E704DCCD50F8032B58>] >>\n%%EOF\n"
    )
    return payload + (b"% deterministic test padding\n" * 40)


def test_pdf_candidate_build_writes_every_locale_guide_and_normalizes_metadata(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    documentation = tmp_path / "documentation"
    for locale in build_docs.LOCALES:
        maps = documentation / "src" / "dita" / locale / "maps"
        maps.mkdir(parents=True)
        for _guide_id, map_name in build_docs.PDF_GUIDE_MAPS:
            (maps / map_name).write_text("<map/>", encoding="utf-8")
    (documentation / "assets/pdf").mkdir(parents=True)
    (documentation / "assets/branding").mkdir(parents=True)
    (documentation / "assets/pdf/bpm-guide-print.css").write_text("@page {}", encoding="utf-8")
    (documentation / "assets/branding/bpm-logo.png").write_bytes(b"png")
    layout_path = documentation / "layout.json"
    policy_path = documentation / "pdf-policy.json"
    layout_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "target_bpm_version": "0.9.5",
                "locales": list(build_docs.LOCALES),
                "guides": [
                    {
                        "id": "user-guide",
                        "filename": "browser-policy-manager-user-guide-{locale}-{bpm_version}.pdf",
                    },
                    {
                        "id": "administrator-guide",
                        "filename": (
                            "browser-policy-manager-administrator-guide-{locale}-{bpm_version}.pdf"
                        ),
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    policy_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "contract_id": "bpm-pdf-generation-0.9.3",
                "backlog_item": "BPM093-M14-08",
                "candidate_root": "documentation/build/pdf",
                "candidate_path_layout": "{locale}/{filename}",
                "dita_format": "html5",
                "pdf_renderer": "chromium",
                "page_number_overlay_renderer": "native-pdf",
                "ui_footer_year": 2026,
                "source_maps": ["user-guide.ditamap", "administrator-guide.ditamap"],
                "development_cache": {
                    "schema_version": 1,
                    "root": "documentation/.cache/pdf-pipeline",
                    "unit": "locale-guide",
                    "layers": ["dita-html5", "verified-pdf"],
                    "hash_algorithm": "sha256",
                    "reuse": "verified-only",
                    "invalid_entry": "quarantine-and-rebuild",
                    "promotion": "staged-and-atomic",
                },
                "parallelism": {"max_workers": 1},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(build_docs, "DOCUMENTATION_ROOT", documentation)
    monkeypatch.setattr(build_docs, "PDF_LAYOUT_CONTRACT", layout_path)
    monkeypatch.setattr(build_docs, "PDF_GENERATION_CONTRACT", policy_path)
    monkeypatch.setattr(build_docs, "validate_sources", lambda: None)
    monkeypatch.setattr(build_docs, "toolchain", lambda: (tmp_path / "dita", tmp_path / "java"))
    monkeypatch.setattr(build_docs, "source_hashes", lambda: {"source": "unchanged"})
    monkeypatch.setattr(build_docs, "_source_fingerprint", lambda: "source-fingerprint")
    monkeypatch.setattr(build_docs, "_source_revision", lambda: "a" * 40)
    monkeypatch.setattr(
        build_docs,
        "_load_lock",
        lambda: {"components": {"dita_ot": {"version": "4.4"}}},
    )

    def fake_run_pdf(command: list[str], _env: dict[str, str]) -> None:
        output = Path(command[command.index("--output") + 1])
        output.mkdir(parents=True)

    def fake_write_pdf_print_guide(**kwargs: object) -> Path:
        print_path = Path(str(kwargs["output_root"])) / "print.html"
        print_path.write_text("<html><body>print</body></html>", encoding="utf-8")
        return print_path

    chromium_renders: list[Path] = []

    def fake_render_pdf(source: Path, target: Path, _env: dict[str, str]) -> None:
        chromium_renders.append(source)
        target.write_bytes(_fake_pdf_payload())

    monkeypatch.setattr(build_docs, "_run_pdf", fake_run_pdf)
    monkeypatch.setattr(build_docs, "_wait_for_pdf_topic_html", lambda **_kwargs: None)
    monkeypatch.setattr(build_docs, "_write_pdf_print_guide", fake_write_pdf_print_guide)
    monkeypatch.setattr(build_docs, "_render_pdf_with_chromium", fake_render_pdf)
    monkeypatch.setattr(
        build_docs, "_expected_pdf_destination_ids", lambda _path: {"bpm-topic-0001"}
    )
    monkeypatch.setattr(
        build_docs,
        "_pdf_navigation_model",
        lambda _path: (2, {"bpm-topic-0001": 2}, {"bpm-topic-0001"}),
    )
    monkeypatch.setattr(
        build_docs,
        "_pdf_navigation_model_without_destinations",
        lambda _path: (2, {}, set()),
    )
    monkeypatch.setattr(build_docs, "_overlay_pdf_page_numbers", lambda _target, _overlay: None)
    monkeypatch.setattr(build_docs, "_validate_pdf_print_contract", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(build_docs, "_canonicalize_pdf", lambda _path: None)
    candidate = tmp_path / "candidate"

    build_docs.build_pdf_tree(candidate, use_cache=False)

    files = sorted(path for path in candidate.rglob("*.pdf"))
    assert len(files) == 12
    for path in files:
        payload = path.read_bytes()
        assert build_docs.PDF_FIXED_CREATION_DATE in payload
        assert payload.count(build_docs.PDF_FIXED_DOCUMENT_ID) == 2
    build_docs.validate_pdf_tree(candidate)
    progress = capsys.readouterr().out
    assert progress.count("DITA HTML5 cache=bypassed") == 12
    assert progress.count("Chromium PDF cache=bypassed") == 12
    assert len(chromium_renders) == 24
    assert "cache lookup" not in progress


def test_pdf_pair_hashes_invalidate_only_transitive_locale_guide_inputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    documentation = tmp_path / "documentation"
    maps = documentation / "src/dita/en/maps"
    user = documentation / "src/dita/en/user/user.dita"
    admin = documentation / "src/dita/en/admin/admin.dita"
    screenshot = documentation / "assets/screenshots/en/user.png"
    maps.mkdir(parents=True)
    user.parent.mkdir(parents=True)
    admin.parent.mkdir(parents=True)
    screenshot.parent.mkdir(parents=True)
    (maps / "user-guide.ditamap").write_text(
        '<map><mapref href="keys.ditamap"/><topicref keyref="topic.user"/></map>',
        encoding="utf-8",
    )
    (maps / "administrator-guide.ditamap").write_text(
        '<map><mapref href="keys.ditamap"/><topicref keyref="topic.admin"/></map>',
        encoding="utf-8",
    )
    (maps / "keys.ditamap").write_text(
        '<map><keydef keys="topic.user" href="../user/user.dita"/>'
        '<keydef keys="topic.admin" href="../admin/admin.dita"/>'
        '<keydef keys="screenshot.user" '
        'href="../../../../assets/screenshots/en/user.png"/></map>',
        encoding="utf-8",
    )
    user.write_text(
        '<topic id="user"><title>User</title><body><image keyref="screenshot.user"/>'
        "</body></topic>",
        encoding="utf-8",
    )
    admin.write_text(
        '<topic id="admin"><title>Admin</title><body><p>Admin body</p></body></topic>',
        encoding="utf-8",
    )
    screenshot.write_bytes(b"reviewed screenshot")
    monkeypatch.setattr(build_docs, "REPOSITORY_ROOT", tmp_path)
    monkeypatch.setattr(build_docs, "DOCUMENTATION_ROOT", documentation)

    user_before = build_docs._pdf_pair_source_hashes("en", "user-guide.ditamap")
    admin_before = build_docs._pdf_pair_source_hashes("en", "administrator-guide.ditamap")

    user.write_text(
        '<topic id="user"><title>User changed</title><body>'
        '<image keyref="screenshot.user"/></body></topic>',
        encoding="utf-8",
    )
    assert build_docs._pdf_pair_source_hashes("en", "user-guide.ditamap") != user_before
    assert build_docs._pdf_pair_source_hashes("en", "administrator-guide.ditamap") == admin_before

    policy = {
        "dita_format": "html5",
        "determinism": {
            "environment": {
                "LANG": "C.UTF-8",
                "LC_ALL": "C.UTF-8",
                "TZ": "UTC",
                "SOURCE_DATE_EPOCH": "0",
            }
        },
    }
    html_with_toolchain_44 = build_docs._pdf_pair_html_inputs(
        locale="en",
        guide_id="user-guide",
        map_name="user-guide.ditamap",
        policy=policy,
        toolchain_identity={"dita_ot": "4.4", "java": "21.0.12+8"},
    )
    assert (
        build_docs._pdf_pair_html_inputs(
            locale="en",
            guide_id="user-guide",
            map_name="user-guide.ditamap",
            policy=policy,
            toolchain_identity={"dita_ot": "4.5", "java": "21.0.12+8"},
        )
        != html_with_toolchain_44
    )
    user.write_text(
        '<topic id="user"><title>User</title><body><image keyref="screenshot.user"/>'
        "</body></topic>",
        encoding="utf-8",
    )

    (maps / "user-guide.ditamap").write_text(
        '<map id="changed"><mapref href="keys.ditamap"/><topicref keyref="topic.user"/></map>',
        encoding="utf-8",
    )
    assert build_docs._pdf_pair_source_hashes("en", "user-guide.ditamap") != user_before
    assert build_docs._pdf_pair_source_hashes("en", "administrator-guide.ditamap") == admin_before
    (maps / "user-guide.ditamap").write_text(
        '<map><mapref href="keys.ditamap"/><topicref keyref="topic.user"/></map>',
        encoding="utf-8",
    )

    screenshot.write_bytes(b"changed reviewed screenshot")
    assert build_docs._pdf_pair_source_hashes("en", "user-guide.ditamap") != user_before
    assert build_docs._pdf_pair_source_hashes("en", "administrator-guide.ditamap") == admin_before


def test_pdf_pair_cache_inputs_cover_print_locale_renderer_and_toolchain_changes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    documentation = tmp_path / "documentation"
    app_i18n = tmp_path / "app/i18n"
    app_i18n.mkdir(parents=True)
    (app_i18n / "en.json").write_text('{"footer":"English"}', encoding="utf-8")
    (app_i18n / "de.json").write_text('{"footer":"Deutsch"}', encoding="utf-8")
    inputs = {
        "PDF_PRINT_CSS": documentation / "assets/pdf/print.css",
        "PDF_COVER_LOGO": documentation / "assets/branding/logo.png",
        "PDF_UI_FOOTER_TEMPLATE": tmp_path / "app/templates/footer.html",
        "PDF_LAYOUT_CONTRACT": documentation / "config/layout.json",
        "PDF_GENERATION_CONTRACT": documentation / "config/pdf.json",
    }
    for path in inputs.values():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(path.name, encoding="utf-8")
    monkeypatch.setattr(build_docs, "REPOSITORY_ROOT", tmp_path)
    for name, path in inputs.items():
        monkeypatch.setattr(build_docs, name, path)
    policy = {"ui_footer_year": 2026}
    runtime = {"chromium": {"version": "150"}, "qpdf": {"version": "12"}}

    en_before = build_docs._pdf_pair_pdf_inputs(
        locale="en",
        guide_id="user-guide",
        html_fingerprint="a" * 64,
        policy=policy,
        runtime_identity=runtime,
    )
    de_before = build_docs._pdf_pair_pdf_inputs(
        locale="de",
        guide_id="user-guide",
        html_fingerprint="a" * 64,
        policy=policy,
        runtime_identity=runtime,
    )
    inputs["PDF_PRINT_CSS"].write_text("changed print CSS", encoding="utf-8")
    assert (
        build_docs._pdf_pair_pdf_inputs(
            locale="en",
            guide_id="user-guide",
            html_fingerprint="a" * 64,
            policy=policy,
            runtime_identity=runtime,
        )
        != en_before
    )
    inputs["PDF_PRINT_CSS"].write_text("print.css", encoding="utf-8")
    (app_i18n / "en.json").write_text('{"footer":"Changed"}', encoding="utf-8")
    assert (
        build_docs._pdf_pair_pdf_inputs(
            locale="en",
            guide_id="user-guide",
            html_fingerprint="a" * 64,
            policy=policy,
            runtime_identity=runtime,
        )
        != en_before
    )
    assert (
        build_docs._pdf_pair_pdf_inputs(
            locale="de",
            guide_id="user-guide",
            html_fingerprint="a" * 64,
            policy=policy,
            runtime_identity=runtime,
        )
        == de_before
    )
    assert (
        build_docs._pdf_pair_pdf_inputs(
            locale="de",
            guide_id="user-guide",
            html_fingerprint="a" * 64,
            policy=policy,
            runtime_identity={"chromium": {"version": "151"}},
        )
        != de_before
    )


def test_pdf_cache_reuses_verified_payload_and_quarantines_corruption(
    tmp_path: Path,
) -> None:
    cache_root = tmp_path / "cache"
    payload = tmp_path / "payload"
    payload.mkdir()
    (payload / "guide.pdf").write_bytes(b"verified PDF payload")
    inputs = {"source": "a" * 64}
    fingerprint = build_docs._pdf_cache_fingerprint(inputs)

    def validate(candidate: Path) -> None:
        if (candidate / "guide.pdf").read_bytes() != b"verified PDF payload":
            raise build_docs.BuildError("invalid cached PDF")

    build_docs._store_pdf_cache_entry(
        cache_root,
        kind="verified-pdf",
        fingerprint=fingerprint,
        inputs=inputs,
        payload=payload,
        validate_payload=validate,
    )
    reused = tmp_path / "reused"
    assert build_docs._reuse_pdf_cache_entry(
        cache_root,
        kind="verified-pdf",
        fingerprint=fingerprint,
        inputs=inputs,
        destination=reused,
        validate_payload=validate,
    )
    assert (reused / "guide.pdf").read_bytes() == b"verified PDF payload"

    (cache_root / "verified-pdf" / fingerprint / "payload/guide.pdf").write_bytes(b"corrupt")
    assert not build_docs._reuse_pdf_cache_entry(
        cache_root,
        kind="verified-pdf",
        fingerprint=fingerprint,
        inputs=inputs,
        destination=tmp_path / "must-not-reuse",
        validate_payload=validate,
    )
    assert not (tmp_path / "must-not-reuse").exists()
    assert len(list((cache_root / ".quarantine").glob("verified-pdf-*"))) == 1


def test_canonicalize_pdf_replaces_qpdf_trailer_id_after_the_rewrite(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "guide.pdf"
    path.write_bytes(_fake_pdf_payload())

    monkeypatch.setattr(build_docs.shutil, "which", lambda executable: "/usr/bin/qpdf")

    def fake_run_pdf_tool(command: list[str], _operation: str) -> None:
        source = Path(command[-2])
        target = Path(command[-1])
        payload = source.read_bytes()
        if "--static-id" in command:
            payload = build_docs.PDF_DOCUMENT_ID_PATTERN.sub(
                b"/ID [<11111111111111111111111111111111> <22222222222222222222222222222222>]",
                payload,
            )
        target.write_bytes(payload)

    monkeypatch.setattr(build_docs, "_run_pdf_tool", fake_run_pdf_tool)

    build_docs._canonicalize_pdf(path)

    assert path.read_bytes().count(build_docs.PDF_FIXED_DOCUMENT_ID) == 2


def test_pdf_article_drops_temporary_local_file_links_but_keeps_external_links(
    tmp_path: Path,
) -> None:
    topic = tmp_path / "topic.html"
    topic.write_text(
        '<html><body><article><p><a href="file:///tmp/build/topic.html">Local</a>'
        '<a href="admin-reference-minimum-system-requirements.html">Topic</a>'
        '<a href="https://example.invalid/article">External</a></p></article></body></html>',
        encoding="utf-8",
    )

    article = build_docs._pdf_article_from_html(topic)

    assert "file:///" not in article
    assert "admin-reference-minimum-system-requirements.html" not in article
    assert 'href="https://example.invalid/article"' in article


def test_pdf_topic_html_waits_for_delayed_map_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    maps = tmp_path / "src/dita/de/maps"
    topic = tmp_path / "src/dita/de/admin/admin-reference.dita"
    maps.mkdir(parents=True)
    topic.parent.mkdir(parents=True)
    (maps / "keys.ditamap").write_text(
        '<map><keydef keys="topic.admin-reference" href="../admin/admin-reference.dita"/></map>',
        encoding="utf-8",
    )
    map_path = maps / "administrator-guide.ditamap"
    map_path.write_text(
        '<map><title>Administrator guide</title><topicref keyref="topic.admin-reference"/></map>',
        encoding="utf-8",
    )
    topic.write_text(
        '<reference id="admin-reference"><title>Reference</title></reference>', encoding="utf-8"
    )
    output_root = tmp_path / "output"
    ticks = iter((0.0, 0.0, 0.1, 0.2))

    def fake_sleep(_seconds: float) -> None:
        destination = output_root / "de/admin/admin-reference.html"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text("<article><h1>Reference</h1></article>", encoding="utf-8")

    monkeypatch.setattr(build_docs.time, "monotonic", lambda: next(ticks))
    monkeypatch.setattr(build_docs.time, "sleep", fake_sleep)

    build_docs._wait_for_pdf_topic_html(
        locale="de",
        guide_id="administrator-guide",
        map_path=map_path,
        output_root=output_root,
    )

    assert (output_root / "de/admin/admin-reference.html").is_file()


def test_pdf_print_guide_renders_exact_footer_page_count_and_clickable_contents(
    tmp_path: Path,
) -> None:
    maps = tmp_path / "src/dita/en/maps"
    maps.mkdir(parents=True)
    (maps / "keys.ditamap").write_text("<map/>", encoding="utf-8")
    map_path = maps / "user-guide.ditamap"
    map_path.write_text(
        "<map><title>User Guide</title><topichead><topicmeta><navtitle>Get started</navtitle></topicmeta>"
        '<topicref href="../user/start.dita"/></topichead></map>',
        encoding="utf-8",
    )
    output_root = tmp_path / "output"
    topic = output_root / "user/start.html"
    topic.parent.mkdir(parents=True)
    figures = "".join(
        '<figure><figcaption><span class="fig--title-label">'
        f"Figure {number}. "
        f"</span>Caption {number}</figcaption></figure>"
        for number in range(1, build_docs.PDF_USER_GUIDE_FIGURE_COUNT + 1)
    )
    topic.write_text(
        '<html><body><article id="temporary" class="topic task" lang="en">'
        f"<h1>Start here</h1><p>Body.</p>{figures}</article></body></html>",
        encoding="utf-8",
    )

    print_path = build_docs._write_pdf_print_guide(
        locale="en",
        guide_id="user-guide",
        map_path=map_path,
        output_root=output_root,
        total_pages=4,
        destination_pages={"bpm-section-001": 3, "bpm-topic-0001": 4},
        footer_year=2026,
    )

    rendered = print_path.read_text(encoding="utf-8")
    assert "Pages: 4" in rendered
    assert "© 2025-2026 • Valery Ledovskoy • Licensed under Mozilla Public License 2.0" in rendered
    assert 'href="#bpm-section-001-p0003"' in rendered
    assert 'id="bpm-section-001-p0003"' in rendered
    assert 'href="#bpm-topic-0001-p0004"' in rendered
    assert 'id="bpm-topic-0001-p0004" class="topic task" lang="en"' in rendered
    assert '<span class="bpm-pdf-toc__page">3</span>' in rendered
    assert '<span class="bpm-pdf-toc__page">4</span>' in rendered
    for number in range(1, build_docs.PDF_USER_GUIDE_FIGURE_COUNT + 1):
        assert f'<span class="fig--title-label">Figure {number}. </span>' in rendered


def test_pdf_print_guide_rejects_an_incomplete_user_guide_figure_inventory(
    tmp_path: Path,
) -> None:
    maps = tmp_path / "src/dita/en/maps"
    maps.mkdir(parents=True)
    (maps / "keys.ditamap").write_text("<map/>", encoding="utf-8")
    map_path = maps / "user-guide.ditamap"
    map_path.write_text(
        "<map><title>User Guide</title><topichead><topicmeta><navtitle>Get started</navtitle></topicmeta>"
        '<topicref href="../user/start.dita"/></topichead></map>',
        encoding="utf-8",
    )
    output_root = tmp_path / "output"
    topic = output_root / "user/start.html"
    topic.parent.mkdir(parents=True)
    topic.write_text(
        '<html><body><article class="topic task" lang="en">'
        "<h1>Start here</h1><p>Body.</p></article></body></html>",
        encoding="utf-8",
    )

    with pytest.raises(build_docs.BuildError, match="figure count is invalid for en: 0"):
        build_docs._write_pdf_print_guide(
            locale="en",
            guide_id="user-guide",
            map_path=map_path,
            output_root=output_root,
        )


def test_pdf_footer_text_matches_ui_identity_for_russian_and_other_locales() -> None:
    assert build_docs._pdf_footer_text("ru", current_year=2026) == (
        "© 2025-2026 • Валерий Ледовской • Лицензия Mozilla Public License 2.0"
    )
    for locale in ("en", "de", "zh-CN", "fr", "es-ES"):
        assert build_docs._pdf_footer_text(locale, current_year=2026) == (
            "© 2025-2026 • Valery Ledovskoy • Licensed under Mozilla Public License 2.0"
        )


def test_pdf_page_number_overlay_leaves_only_title_page_unnumbered(tmp_path: Path) -> None:
    overlay = build_docs._write_pdf_page_number_overlay(tmp_path, 4)
    page_count, destinations, links = build_docs._pdf_navigation_model_without_destinations(overlay)
    pages = build_docs._pdf_bbox_pages(overlay)

    assert page_count == 4
    assert destinations == {}
    assert links == set()
    assert [word.text for word in build_docs._pdf_page_words(pages[0])] == []
    for page_number, page in enumerate(pages[1:], start=2):
        words = build_docs._pdf_page_words(page)
        assert [word.text for word in words] == [str(page_number)]
        word = words[0]
        width = float(page.get("width", "0"))
        height = float(page.get("height", "0"))
        assert float(word.get("yMin", "0")) > height - 40
        assert (
            abs((float(word.get("xMin", "0")) + float(word.get("xMax", "0"))) / 2 - width / 2) < 1
        )


def test_pdf_positioned_line_text_does_not_invent_a_cjk_space() -> None:
    line = build_docs.ET.fromstring(
        '<line><word xMin="272.60" xMax="304.10">页数：</word>'
        '<word xMin="304.10" xMax="322.12">103</word></line>'
    )

    assert build_docs._pdf_positioned_line_text(line) == "页数：103"


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
