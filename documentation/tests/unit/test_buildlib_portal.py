from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from documentation.buildlib import portal
from documentation.buildlib.shared import BuildError


def _write(path: Path, content: str | bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content, encoding="utf-8")
    return path


def _valid_page(locale: str, links: str = "") -> str:
    return (
        f'<html lang="{locale}"><body class="bpm-docs-shell"><h1 id="top">Title</h1>'
        '<nav aria-label="one"></nav><nav aria-label="two"></nav>'
        '<nav aria-label="three"></nav><div data-docs-tree-host></div>'
        f'<main id="main-content">{links}</main></body></html>'
    )


def _valid_site(root: Path) -> None:
    for locale in portal.LOCALES:
        _write(root / locale / "index.html", _valid_page(locale))


def test_html_parser_collects_contract_fields_and_rejects_duplicate_ids() -> None:
    parser = portal._HTMLLinks()
    parser.feed(
        '<HTML lang="en"><BODY class="bpm-docs-shell extra"><H1 id="one">Title</H1>'
        '<MAIN id="main-content" data-docs-tree-host></MAIN><NAV aria-label="tree"></NAV>'
        '<div role="tree" data-docs-tree></div><a href="page.html">Link</a>'
        '<script src="ok.js" defer></script><script>inline()</script>'
        '<style>x</style><iframe></iframe><form></form><div onclick="x" style="x"></div>'
        "</BODY></HTML>"
    )
    assert parser.html_lang == "en"
    assert parser.h1_count == parser.main_count == parser.tree_host_count == 1
    assert parser.embedded_tree_count == 1
    assert parser.links == ["page.html", "ok.js"]
    assert "bpm-docs-shell" in parser.body_classes
    assert "tree" in parser.nav_labels
    assert "forbidden inline script content" in parser.forbidden
    assert "forbidden element <style>" in parser.forbidden
    assert "forbidden attribute 'onclick'" in parser.forbidden
    parser.handle_endtag("div")

    duplicate = portal._HTMLLinks()
    with pytest.raises(BuildError, match="duplicate generated HTML id"):
        duplicate.feed('<div id="same"></div><span id="same"></span>')


def test_html_document_caches_success_and_wraps_read_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    page = _write(tmp_path / "page.html", _valid_page("en"))
    cache: dict[Path, portal._HTMLLinks] = {}
    assert portal._html_document(page, cache) is portal._html_document(page, cache)
    original = Path.read_text

    def fail(path: Path, *args: object, **kwargs: object) -> str:
        if path == page:
            raise UnicodeDecodeError("utf-8", b"x", 0, 1, "bad")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", fail)
    with pytest.raises(BuildError, match="cannot parse generated HTML"):
        portal._html_document(page, {})


def test_output_validation_accepts_a_complete_relative_site(tmp_path: Path) -> None:
    _valid_site(tmp_path)
    target = _write(tmp_path / "en/page.html", _valid_page("en"))
    (tmp_path / "en/index.html").write_text(
        _valid_page(
            "en",
            '<a href="https://example.test">external</a><a href="page.html#top">peer</a>'
            '<a href=".">directory</a>',
        ),
        encoding="utf-8",
    )
    assert target.is_file()
    portal.validate_output(tmp_path)


def test_output_validation_reports_every_failure_class(tmp_path: Path) -> None:
    with pytest.raises(BuildError, match="entry point for every locale"):
        portal.validate_output(tmp_path)

    _valid_site(tmp_path)
    bad = _write(
        tmp_path / "en/index.html",
        '<html lang="ru"><body><h1 id="dup">One</h1><h1>Two</h1>'
        '<div role="tree"></div><script>bad()</script><a href="http://bad">http</a>'
        '<a href="//host/path">host</a><a href="/absolute">absolute</a>'
        '<a href="missing.html">missing</a><a href="../de/index.html#missing">fragment</a>'
        "</body></html>",
    )
    _write(tmp_path / "leak.bin", str(portal.REPOSITORY_ROOT).encode())
    with pytest.raises(BuildError) as error:
        portal.validate_output(tmp_path)
    diagnostic = str(error.value)
    for fragment in (
        "leaks absolute workspace path",
        "html lang must be",
        "exactly one h1",
        "main#main-content",
        "portal shell class",
        "navigation tree host",
        "must not embed navigation tree",
        "distinct navigation labels",
        "forbidden inline script",
        "forbidden generated link scheme",
        "generated link must be relative",
        "missing generated target",
        "missing generated fragment",
    ):
        assert fragment in diagnostic
    assert bad.is_file()
    _write(tmp_path / "other/page.html", "<html><body><h1>Other</h1></body></html>")
    with pytest.raises(BuildError):
        portal.validate_output(tmp_path)


def test_link_normalizers_only_rewrite_owned_local_assets(tmp_path: Path) -> None:
    for locale in portal.LOCALES:
        (tmp_path / locale).mkdir(parents=True)
    locale_root = tmp_path / "en"
    _write(locale_root / "target.html", "target")
    page = _write(
        locale_root / "page.html",
        '<a href="../target.html?q=1#top">normalize</a>'
        '<a href="../present.html">current</a><a href="../absent.html">absent</a>'
        '<a href="https://example.test">external</a><a href="target.html">local</a>',
    )
    _write(tmp_path / "present.html", "current")
    portal._normalize_locale_root_links(tmp_path)
    normalized = page.read_text(encoding="utf-8")
    assert 'href="target.html?q=1#top"' in normalized
    assert 'href="../present.html"' in normalized and 'href="../absent.html"' in normalized

    screenshot = _write(locale_root / "assets/screenshots/shot.png", b"png")
    page.write_text(
        '<img src="file:///workspace/assets/screenshots/en/shot.png?q=1#x">'
        '<img src="/workspace/assets/screenshots/en/missing.png">'
        '<img src="/workspace/assets/other/en/shot.png">'
        '<img src="https://example.test/assets/screenshots/en/shot.png">'
        '<img src="//host/assets/screenshots/en/shot.png">',
        encoding="utf-8",
    )
    portal._normalize_screenshot_links(tmp_path)
    content = page.read_text(encoding="utf-8")
    assert screenshot.name in content and "file:" not in content
    assert "missing.png" in content and "https://example.test" in content and "//host" in content


def test_shell_tag_locale_peer_and_root_anchor_helpers(tmp_path: Path) -> None:
    assert portal._body_with_shell_class("<body>") == '<body class="bpm-docs-shell">'
    assert portal._body_with_shell_class('<body class="existing">') == (
        '<body class="existing bpm-docs-shell">'
    )
    assert portal._body_with_shell_class('<body class="bpm-docs-shell">') == (
        '<body class="bpm-docs-shell">'
    )
    assert 'lang="de"' in portal._html_with_locale("<html><body></body></html>", "de")
    assert 'lang="ru"' in portal._html_with_locale('<html lang="en"><body></body></html>', "ru")
    with pytest.raises(BuildError, match="lacks an html root"):
        portal._html_with_locale("<body></body>", "en")

    page = _write(tmp_path / "en/guide/page.html", "page")
    peer = _write(tmp_path / "ru/guide/page.html", "peer")
    fallback = _write(tmp_path / "de/index.html", "fallback")
    assert portal._locale_peer(tmp_path, page, "en", "ru") == peer
    assert portal._locale_peer(tmp_path, page, "en", "de") == fallback
    with pytest.raises(BuildError, match="outside its locale root"):
        portal._locale_peer(tmp_path, tmp_path / "outside", "en", "ru")

    index = tmp_path / "en/index.html"
    anchors = portal._portal_root_anchor_targets(tmp_path, index, "en", ' id="a-user-guide"')
    assert 'id="a-user-guide"' not in anchors
    assert anchors
    assert portal._portal_root_anchor_targets(tmp_path, page, "en", "") == ""


def test_portal_shell_renders_current_product_controls_and_rejects_locale_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    page = _write(tmp_path / "en/index.html", "page")
    for locale in portal.LOCALES:
        _write(tmp_path / locale / "index.html", "peer")
    monkeypatch.setattr(portal, "_navigation_host", lambda *_args: "tree")
    monkeypatch.setattr(portal, "_navigation_breadcrumbs", lambda *_args: "crumbs")
    monkeypatch.setattr(portal, "_product_version", lambda: "0.9.4")
    shell = portal._portal_shell(tmp_path, page, "en", "<h1>Body</h1>")
    assert "v0.9.4" in shell and "data-docs-locale-select" in shell
    assert "data-documentation-assistant-widget" in shell and "tree" in shell and "crumbs" in shell

    monkeypatch.setattr(portal, "PRODUCT_LOCALE_OPTIONS", portal.PRODUCT_LOCALE_OPTIONS[:-1])
    with pytest.raises(BuildError, match="locales must match"):
        portal._portal_shell(tmp_path, page, "en", "body")


def test_theme_and_screenshot_asset_installers_are_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    theme = tmp_path / "theme"
    theme.mkdir()
    monkeypatch.setattr(portal, "THEME_ROOT", theme)
    for filename in portal.THEME_FILES:
        _write(theme / filename, filename)
    scripts = (
        portal.SEARCH_SCRIPT,
        portal.MODEL_MANAGER_SCRIPT,
        portal.ASSISTANT_RENDERER_SCRIPT,
        portal.ASSISTANT_STATE_MACHINE_SCRIPT,
        portal.ASSISTANT_CONVERSATION_SCRIPT,
        portal.ASSISTANT_TRANSPORT_SCRIPT,
        portal.ASSISTANT_SHELL_SCRIPT,
    )
    for filename in scripts:
        _write(theme / filename, filename)
    locale_root = tmp_path / "site/en"
    portal._install_theme_assets(locale_root)
    assert (locale_root / "assets" / scripts[-1]).is_file()
    (theme / scripts[-1]).unlink()
    with pytest.raises(BuildError, match="missing portal script asset"):
        portal._install_theme_assets(locale_root)
    (theme / portal.THEME_FILES[0]).unlink()
    with pytest.raises(BuildError, match="missing portal theme asset"):
        portal._install_theme_assets(locale_root)

    screenshots = tmp_path / "screenshots"
    monkeypatch.setattr(portal, "SCREENSHOT_ROOT", screenshots)
    with pytest.raises(BuildError, match="missing localized screenshot assets"):
        portal._install_screenshot_assets(locale_root)
    _write(screenshots / "en/one.png", b"one")
    _write(screenshots / "en/ignore.txt", b"ignore")
    portal._install_screenshot_assets(locale_root)
    assert (locale_root / "assets/screenshots/one.png").read_bytes() == b"one"


def test_transient_screenshot_cleanup_removes_only_expected_trees(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    screenshots = tmp_path / "screenshots"
    monkeypatch.setattr(portal, "SCREENSHOT_ROOT", screenshots)
    for locale in portal.LOCALES:
        _write(screenshots / locale / "shot.png", b"expected")
        (tmp_path / locale).mkdir(parents=True, exist_ok=True)
    transient = _write(tmp_path / "en/tmp/assets/screenshots/en/shot.png", b"copy")
    _write(tmp_path / "en/shallow/shot.png", b"keep")
    _write(tmp_path / "en/other/assets/screenshots/ru/shot.png", b"keep")
    _write(tmp_path / "en/unknown/assets/screenshots/en/unknown.png", b"keep")
    portal._remove_dita_transient_screenshot_copies(tmp_path)
    assert not transient.exists() and (tmp_path / "en/shallow/shot.png").is_file()

    _write(tmp_path / "en/bad/assets/screenshots/en/shot.png", b"copy")
    _write(tmp_path / "en/bad/unexpected.txt", b"bad")
    with pytest.raises(BuildError, match="unexpected generated files"):
        portal._remove_dita_transient_screenshot_copies(tmp_path)


def test_apply_page_and_orchestration_cover_success_and_missing_anchors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    page = _write(tmp_path / "en/index.html", "<html><head></head><body><h1>X</h1></body></html>")
    monkeypatch.setattr(portal, "_portal_shell", lambda *_args: "<main>shell</main>")
    portal._apply_portal_shell_to_page(tmp_path, page, "en")
    content = page.read_text(encoding="utf-8")
    assert "<main>shell</main>" in content and portal.SEARCH_SCRIPT in content
    broken = _write(tmp_path / "en/broken.html", "<html><body></body></html>")
    with pytest.raises(BuildError, match="lacks head/body shell anchors"):
        portal._apply_portal_shell_to_page(tmp_path, broken, "en")

    empty_root = tmp_path / "empty"
    with pytest.raises(BuildError, match="generated locale root is missing"):
        portal.apply_portal_shell(empty_root)
    for locale in portal.LOCALES:
        _write(empty_root / locale / "index.html", "page")
    calls: list[str] = []
    monkeypatch.setattr(
        portal, "_install_theme_assets", lambda path: calls.append(f"theme:{path.name}")
    )
    monkeypatch.setattr(
        portal, "_install_screenshot_assets", lambda path: calls.append(f"shots:{path.name}")
    )
    monkeypatch.setattr(
        portal, "generate_navigation_files", lambda _root: calls.append("navigation")
    )
    monkeypatch.setattr(portal, "generate_assistant_copy_files", lambda _root: calls.append("copy"))
    monkeypatch.setattr(
        portal,
        "_apply_portal_shell_to_page",
        lambda _root, _page, locale: calls.append(f"page:{locale}"),
    )
    portal.apply_portal_shell(empty_root)
    assert calls.count("navigation") == calls.count("copy") == 1
    assert sum(call.startswith("page:") for call in calls) == len(portal.LOCALES)


def _assistant_contract() -> dict[str, object]:
    return copy.deepcopy(portal._read_json_file(portal.DOCUMENTATION_ASSISTANT_COPY))


def test_assistant_copy_contract_and_payload_accept_current_six_locale_source() -> None:
    contract = portal._documentation_assistant_copy_contract()
    assert contract["locales"] == list(portal.LOCALES)
    payload = portal._assistant_copy_payload("en")
    assert payload["locale"] == "en"
    assert payload["messages"]["states"]
    assert set(payload["messages"]["shell"]) == set(portal._ASSISTANT_SHELL_LABEL_KEYS)
    with pytest.raises(BuildError, match="unsupported assistant copy locale"):
        portal._assistant_copy_payload("xx")


@pytest.mark.parametrize(
    ("mutation", "diagnostic"),
    [
        (lambda value: value.update(contract_id="wrong"), "identifier is invalid"),
        (lambda value: value.update(locales=[]), "locales diverge"),
        (lambda value: value.update(catalog=[]), "incomplete locale coverage"),
        (lambda value: value.update(state_templates=[]), "templates have incomplete"),
        (lambda value: value.update(catalog_rules=[]), "rules are missing"),
        (
            lambda value: value["catalog_rules"].update(state_ids=[1]),
            "state inventory is invalid",
        ),
        (
            lambda value: value["catalog_rules"].update(state_fields=[]),
            "state field inventory is invalid",
        ),
        (lambda value: value["catalog"].update(en=[]), "catalog is invalid for en"),
        (
            lambda value: value["catalog"]["en"].update(states=[]),
            "state catalog diverges for en",
        ),
        (
            lambda value: value["catalog"]["en"]["states"].update(
                {value["catalog_rules"]["state_ids"][0]: []}
            ),
            "state copy is invalid",
        ),
        (
            lambda value: value["catalog"]["en"]["states"][
                value["catalog_rules"]["state_ids"][0]
            ].update(title=""),
            "state copy is empty",
        ),
        (lambda value: value["catalog"]["en"].update(dialogue=[]), "dialogue copy diverges"),
        (
            lambda value: value["catalog"]["en"]["dialogue"].update(scope=""),
            "dialogue copy is empty",
        ),
        (lambda value: value["state_templates"].update(en=[]), "templates are invalid"),
        (
            lambda value: value["state_templates"]["en"].update(live="bad"),
            "live template is invalid",
        ),
        (
            lambda value: value["state_templates"]["en"].update(aria="bad"),
            "aria template is invalid",
        ),
    ],
)
def test_assistant_copy_contract_rejects_each_failure_class(
    monkeypatch: pytest.MonkeyPatch, mutation: object, diagnostic: str
) -> None:
    contract = _assistant_contract()
    mutation(contract)  # type: ignore[operator]
    monkeypatch.setattr(portal, "_read_json_file", lambda _path: contract)
    with pytest.raises(BuildError, match=diagnostic):
        portal._documentation_assistant_copy_contract()


def test_generate_assistant_copy_files_is_complete_and_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with pytest.raises(BuildError, match="generated locale root is missing"):
        portal.generate_assistant_copy_files(tmp_path)
    for locale in portal.LOCALES:
        (tmp_path / locale).mkdir(parents=True)
    monkeypatch.setattr(portal, "_assistant_copy_payload", lambda locale: {"locale": locale})
    portal.generate_assistant_copy_files(tmp_path)
    assert json.loads((tmp_path / "ru/assistant-copy.json").read_text())["locale"] == "ru"
