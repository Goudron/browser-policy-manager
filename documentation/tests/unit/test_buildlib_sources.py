from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from documentation.buildlib import sources
from documentation.buildlib.shared import BuildError


def _roots(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    repository = tmp_path / "repository"
    documentation = repository / "documentation"
    documentation.mkdir(parents=True)
    monkeypatch.setattr(sources, "REPOSITORY_ROOT", repository)
    monkeypatch.setattr(sources, "DOCUMENTATION_ROOT", documentation)
    return repository, documentation


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_dita_discovery_target_confinement_and_xml_id_cache(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _repository, documentation = _roots(tmp_path, monkeypatch)
    topic = _write(documentation / "src/dita/en/user/topic.dita", '<topic id="topic"/>')
    map_path = _write(documentation / "src/shared/map.ditamap", '<map id="map"/>')
    _write(documentation / "src/generated/firefox/readme.txt", "ignored")
    _write(documentation / "src/generated/cis/policy.xml", '<topic id="policy"/>')

    assert sources.dita_sources() == sorted([topic, map_path])
    assert sources._source_target(topic, "https://example.test/help") == (topic, "")
    assert sources._source_target(topic, "#topic") == (topic.resolve(), "topic")
    with pytest.raises(BuildError, match="forbidden link scheme"):
        sources._source_target(topic, "http://example.test/help")
    with pytest.raises(BuildError, match="forbidden link scheme"):
        sources._source_target(topic, "//example.test/help")
    with pytest.raises(BuildError, match="escapes documentation workspace"):
        sources._source_target(topic, "../../../../../../../../outside.dita")

    cache: dict[Path, set[str]] = {}
    assert sources._xml_ids(topic, cache) == {"topic"}
    topic.write_text("<broken", encoding="utf-8")
    assert sources._xml_ids(topic, cache) == {"topic"}
    with pytest.raises(BuildError, match="invalid DITA XML"):
        sources._xml_ids(topic, {})


def test_full_source_validation_is_fail_closed_for_empty_and_all_link_failures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _repository, documentation = _roots(tmp_path, monkeypatch)
    monkeypatch.setattr(sources, "dita_sources", lambda: [])
    with pytest.raises(BuildError, match="no DITA source files"):
        sources.validate_source_links()

    topic = _write(
        documentation / "src/dita/en/user/topic.dita",
        '<topic id="topic"><xref conkeyref="unknown/detail"/>'
        '<xref href="https://example.test"/><xref href="http://example.test"/>'
        '<xref href="missing.dita"/><xref href="target.dita#missing"/></topic>',
    )
    target = _write(
        topic.parent / "target.dita", '<topic id="target"><section id="present"/></topic>'
    )
    monkeypatch.setattr(sources, "dita_sources", lambda: [topic, target])

    with pytest.raises(BuildError) as error:
        sources.validate_source_links()
    diagnostic = str(error.value)
    assert "unknown conkeyref" in diagnostic
    assert "forbidden link scheme" in diagnostic
    assert "missing local target" in diagnostic
    assert "missing DITA fragment" in diagnostic

    valid = _write(
        documentation / "src/dita/en/user/valid.dita",
        '<topic id="valid"><xref href="target.dita#target/present"/>'
        '<xref href="target.dita"/></topic>',
    )
    monkeypatch.setattr(sources, "dita_sources", lambda: [valid, target])
    sources.validate_source_links()
    malformed = _write(documentation / "src/dita/en/user/malformed.dita", "<broken")
    monkeypatch.setattr(sources, "dita_sources", lambda: [malformed])
    with pytest.raises(BuildError, match="invalid DITA XML"):
        sources.validate_source_links()


def test_focused_source_validation_filters_inputs_and_reports_every_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _repository, documentation = _roots(tmp_path, monkeypatch)
    assert sources.validate_focused_source_links([documentation / "readme.txt"]) is None
    keys = _write(documentation / "src/shared/keys.ditamap", '<map keys="known other"/>')
    missing = documentation / "src/dita/en/user/missing.dita"
    broken = _write(documentation / "src/dita/en/user/broken.dita", "<broken")
    topic = _write(
        documentation / "src/dita/en/user/topic.dita",
        '<topic id="topic"><xref keyref="unknown"/><xref conkeyref="known/detail"/>'
        '<xref href="https://example.test"/><xref href="http://example.test"/>'
        '<xref href="absent.dita"/><xref href="target.dita#target/missing"/>'
        '<xref href="valid.dita#valid/present"/><xref href="valid.dita"/></topic>',
    )
    _write(topic.parent / "target.dita", '<topic id="target"/>')
    _write(topic.parent / "valid.dita", '<topic id="valid"><section id="present"/></topic>')
    monkeypatch.setattr(sources, "dita_sources", lambda: [keys])

    with pytest.raises(BuildError) as error:
        sources.validate_focused_source_links([missing, broken, topic])
    diagnostic = str(error.value)
    for fragment in (
        "changed DITA source is missing",
        "invalid DITA XML",
        "unknown keyref",
        "forbidden link scheme",
        "missing local target",
        "missing DITA fragment",
    ):
        assert fragment in diagnostic


def test_source_key_scan_ignores_unreadable_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    readable = _write(tmp_path / "readable.ditamap", "<map keys='alpha beta' keys=\"gamma\"/>")
    unreadable = _write(tmp_path / "unreadable.ditamap", "<map/>")
    original = Path.read_text

    def read_text(path: Path, *args: object, **kwargs: object) -> str:
        if path == unreadable:
            raise OSError("denied")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", read_text)
    assert sources._source_keys_from_text([unreadable, readable]) == {"alpha", "beta", "gamma"}
    assert sources._source_line_hint(unreadable) is None


def test_changed_path_resolution_and_git_discovery(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository, _documentation = _roots(tmp_path, monkeypatch)
    discover_changed = sources._git_changed_paths
    changed = repository / "documentation/topic.dita"
    untracked = repository / "docs/architecture/contract.md"
    responses = iter(
        (
            SimpleNamespace(returncode=0, stdout="documentation/topic.dita\n", stderr=""),
            SimpleNamespace(returncode=0, stdout="docs/architecture/contract.md\n", stderr=""),
        )
    )
    monkeypatch.setattr(sources.subprocess, "run", lambda *_args, **_kwargs: next(responses))
    assert sources._git_changed_paths() == [untracked, changed]
    assert sources._changed_paths(["documentation/topic.dita", str(changed)]) == [changed]
    monkeypatch.setattr(sources, "_git_changed_paths", lambda: [])
    assert sources._changed_paths([]) == []
    with pytest.raises(BuildError, match="outside repository"):
        sources._resolve_changed_path(str(tmp_path / "outside"))

    monkeypatch.setattr(
        sources.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=1, stdout="out", stderr="err"),
    )
    with pytest.raises(BuildError, match="out"):
        discover_changed()


@pytest.mark.parametrize(
    ("relative", "kind", "locales", "guides", "indexes"),
    [
        ("docs/architecture/a.md", "architecture-contract", set(sources.LOCALES), set(), set()),
        ("documentation/src/dita/en/maps/user-guide.ditamap", "dita", {"en"}, {"user"}, {"en"}),
        ("documentation/src/dita/ru/user/topic.dita", "dita", {"ru"}, {"user"}, {"ru"}),
        (
            "documentation/src/shared/filters/web.ditaval",
            "shared-source",
            set(sources.LOCALES),
            {root for *_rest, root in sources.GUIDE_MAPS},
            set(sources.LOCALES),
        ),
        (
            "documentation/src/generated/firefox/policy.dita",
            "generated-source",
            set(sources.LOCALES),
            {"firefox"},
            set(sources.LOCALES),
        ),
        (
            "documentation/src/generated/unknown/policy.dita",
            "generated-source",
            set(sources.LOCALES),
            set(),
            set(sources.LOCALES),
        ),
        ("documentation/assets/theme/theme.css", "theme-asset", set(sources.LOCALES), set(), set()),
        ("documentation/assets/screenshots/de/a.png", "screenshot-asset", {"de"}, set(), {"de"}),
        (
            "documentation/config/search-quality.json",
            "search-config",
            set(sources.LOCALES),
            set(),
            set(sources.LOCALES),
        ),
        ("documentation/config/other.json", "config-input", set(), set(), set()),
        ("documentation/fixtures/example.json", "fixtures-input", set(), set(), set()),
        ("documentation/runbooks/install.md", "runbooks-input", set(), set(), set()),
        ("documentation/tests/fixture.json", "tests-input", set(), set(), set()),
    ],
)
def test_fast_scope_classifies_every_owned_input(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    relative: str,
    kind: str,
    locales: set[str],
    guides: set[str],
    indexes: set[str],
) -> None:
    repository, _documentation = _roots(tmp_path, monkeypatch)
    scope = sources._fast_scope(repository / relative)
    assert scope is not None
    assert (scope["kind"], scope["locales"], scope["guide_roots"], scope["search_indexes"]) == (
        kind,
        locales,
        guides,
        indexes,
    )


def test_fast_scope_rejects_unknown_and_handles_locale_map_without_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository, documentation = _roots(tmp_path, monkeypatch)
    assert sources._fast_scope(repository) is None
    assert sources._fast_scope(documentation) is None
    assert sources._fast_scope(repository / "unknown/file") is None
    scope = sources._fast_scope(documentation / "src/dita/en/maps/unknown.ditamap")
    assert scope is not None and scope["guide_roots"] == set()
    assert sources._fast_scope(documentation / "assets/screenshots/unknown/a.png") is None


def test_topic_line_fixture_and_diagnostic_helpers_are_total(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository, documentation = _roots(tmp_path, monkeypatch)
    topic = _write(documentation / "src/dita/en/user/topic.dita", "\n<topic id='topic'>\n</topic>")
    assert sources._topic_id(topic) == "topic"
    assert sources._topic_id(documentation / "missing.dita") is None
    broken = _write(documentation / "broken.dita", "<broken")
    assert sources._topic_id(broken) is None
    assert sources._source_line_hint(topic, "topic") == 2
    assert sources._source_line_hint(documentation / "missing") is None
    empty = _write(documentation / "empty.txt", "")
    assert sources._source_line_hint(empty) is None
    plain = _write(documentation / "plain.txt", "plain")
    assert sources._source_line_hint(plain) == 1

    fixture = _write(documentation / "fixture.json", json.dumps({"items": [{"id": "first"}]}))
    assert sources._first_fixture_entry(fixture, "items") == {"id": "first"}
    assert sources._first_fixture_entry(fixture, "missing") is None
    fixture.write_text("{", encoding="utf-8")
    assert sources._first_fixture_entry(fixture, "items") is None

    query = _write(
        documentation / "query.json", json.dumps({"queries": [{"id": "q", "query": "x"}]})
    )
    shot = _write(documentation / "shot.json", json.dumps({"capture_matrix": [{"id": "screen"}]}))
    monkeypatch.setattr(sources, "SEARCH_STATE_FIXTURE", query)
    monkeypatch.setattr(sources, "SCREENSHOT_STATE_FIXTURE", shot)
    context = sources._diagnostic_context(topic)
    assert context["target_url"] == "/help/en/user/topic.html"
    assert (context["query_fixture_id"], context["screenshot_state"]) == ("q", "screen")
    payload = sources._diagnostic_payload(
        BuildError("first\nsecond"), [str(tmp_path / "outside"), str(topic)]
    )
    assert payload["error_summary"] == "first"
    assert len(payload["contexts"]) == 1
    assert (
        sources._diagnostic_payload(BuildError("x"), [])["focused_rerun"] == "make docs-fast-check"
    )
    monkeypatch.setattr(sources, "DIAGNOSTICS_ROOT", repository / "reports")
    assert sources.write_failure_diagnostic(BuildError("x"), [str(topic)]).is_file()


def test_changed_input_validation_and_affected_outputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository, documentation = _roots(tmp_path, monkeypatch)
    topic = _write(documentation / "src/dita/en/user/topic.dita", '<topic id="topic"/>')
    missing = documentation / "config/missing.json"
    empty = _write(documentation / "config/empty.json", "")
    invalid = _write(documentation / "config/invalid.json", "{")
    ignored = repository / "unknown"
    with pytest.raises(BuildError) as error:
        sources._validate_changed_inputs([ignored, missing, empty, invalid])
    assert (
        "missing" in str(error.value)
        and "empty" in str(error.value)
        and "invalid JSON" in str(error.value)
    )

    scope = sources._fast_scope(topic)
    assert scope is not None
    index_scope = {**scope, "guide_roots": {"index"}}
    original_fast_scope = sources._fast_scope
    monkeypatch.setattr(
        sources,
        "_fast_scope",
        lambda path: index_scope if path == topic else original_fast_scope(path),
    )
    outputs = sources._affected_output_paths([scope, index_scope], [topic, ignored])
    assert "documentation/build/site/en/index.html" in outputs
    assert "documentation/build/site/search/en/index.json" in outputs
    no_id = _write(documentation / "src/dita/en/user/no-id.dita", "<topic/>")
    assert sources._affected_output_paths([], [no_id]) == [
        "documentation/build/site/search/en/index.json"
    ]


def test_fast_check_reports_empty_and_populated_scopes_with_progress(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repository, documentation = _roots(tmp_path, monkeypatch)
    unknown = _write(repository / "unknown.txt", "x")
    monkeypatch.setattr(sources, "_changed_paths", lambda _arguments: [unknown])
    report = sources.fast_check([], emit=True)
    assert report["checked"] == []
    assert "no changed documentation inputs" in capsys.readouterr().out
    assert report["recommended_next_checks"] == ["make docs-release-handoff"]
    assert sources.fast_check([], emit=False)["checked"] == []

    topic = _write(documentation / "src/dita/en/user/topic.dita", '<topic id="topic"/>')
    theme = _write(documentation / "assets/theme/theme.css", "body{}")
    monkeypatch.setattr(sources, "_changed_paths", lambda _arguments: [topic, theme])
    monkeypatch.setattr(sources, "dita_sources", lambda: [topic])
    report = sources.fast_check([str(topic), str(theme)], emit=True)
    output = capsys.readouterr().out
    assert report["checked"] == [
        sources._relative_repo_path(topic),
        sources._relative_repo_path(theme),
    ]
    assert "Fast check passed" in output and "Affected locales: de, en" in output
    assert "Selected scope:" in output
    assert "Skipped release-only checks (intentional):" in output
    assert "make docs-release-handoff" in output
    assert sources.fast_check([str(topic), str(theme)], emit=False)["checked"]

    monkeypatch.setattr(sources, "_changed_paths", lambda _arguments: [theme])
    report = sources.fast_check([str(theme)], emit=True)
    assert report["affected_outputs"] == []
    monkeypatch.setattr(
        sources,
        "_affected_output_paths",
        lambda _scopes, _dita: [f"output-{index}" for index in range(31)],
    )
    sources.fast_check([str(theme)], emit=True)
    assert "1 more" in capsys.readouterr().out


def test_fast_authoring_guards_cover_localized_shape_semantics_readme_and_registered_fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository, documentation = _roots(tmp_path, monkeypatch)
    _english = _write(
        documentation / "src/dita/en/user/topic.dita",
        '<task id="topic"><title>English</title><taskbody><steps><step><cmd>Go</cmd>'
        '<info><note type="warning">Warning</note></info></step></steps></taskbody></task>',
    )
    localized = _write(
        documentation / "src/dita/ru/user/topic.dita",
        '<task id="topic"><title>Русский</title><taskbody><steps><step><cmd>Go</cmd>'
        '<info><note type="warning">Предупреждение</note></info></step></steps></taskbody></task>',
    )
    sources._validate_localized_shape([localized])
    localized.write_text(
        localized.read_text(encoding="utf-8").replace("</taskbody>", "<section/></taskbody>"),
        encoding="utf-8",
    )
    with pytest.raises(BuildError, match="localized structural shape"):
        sources._validate_localized_shape([localized])

    policy = _write(
        documentation / "src/dita/en/user/ug-task-import-policies-json.dita",
        '<task id="policy"><title>Policy</title><taskbody><example>'
        '<codeblock outputclass="language-json">{"flags": {}}</codeblock>'
        "</example></taskbody></task>",
    )
    with pytest.raises(BuildError, match="complete top-level policies document"):
        sources._validate_semantic_markup([policy])

    figure = _write(
        documentation / "src/dita/en/user/figure.dita",
        '<topic id="figure"><title>Figure</title><body><fig id="figure-id">'
        '<title>Caption</title><image keyref="image.key"/></fig></body></topic>',
    )
    with pytest.raises(BuildError, match="keyed image and localized alt text"):
        sources._validate_semantic_markup([figure])

    readme = _write(repository / "README.md", '```json\n{"policies": {}}\n```\n')
    assert sources._fast_scope(readme)["kind"] == "readme"
    sources._validate_readme_policies([readme])

    fixture = _write(
        documentation / "fixtures/example.json",
        json.dumps({"schema_version": 1, "target_bpm_version": "0.9.0", "synthetic": True}),
    )
    catalog = _write(
        documentation / "fixtures/catalog.json",
        json.dumps({"fixtures": [{"path": "documentation/fixtures/example.json"}]}),
    )
    monkeypatch.setattr(sources, "FIXTURE_CATALOG", catalog)
    sources._validate_registered_fixtures([fixture])
    fixture.write_text(json.dumps({"schema_version": 2, "synthetic": False}), encoding="utf-8")
    with pytest.raises(BuildError, match="registered fixture"):
        sources._validate_registered_fixtures([fixture])


def test_fast_authoring_guard_failure_branches_and_reported_guards(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository, documentation = _roots(tmp_path, monkeypatch)

    outside_dita = _write(repository / "outside.dita", '<topic id="outside"/>')
    sources._validate_localized_shape([outside_dita])

    missing_peer = _write(
        documentation / "src/dita/de/user/missing-peer.dita", '<topic id="missing-peer"/>'
    )
    with pytest.raises(BuildError, match="missing English peer"):
        sources._validate_localized_shape([missing_peer])

    localized_broken_peer = _write(
        documentation / "src/dita/fr/user/broken-peer.dita", '<topic id="broken-peer"/>'
    )
    _write(documentation / "src/dita/en/user/broken-peer.dita", "<broken")
    with pytest.raises(BuildError, match="cannot compare localized shape"):
        sources._validate_localized_shape([localized_broken_peer])

    sources._validate_semantic_markup([repository / "README.md"])
    broken_markup = _write(documentation / "src/dita/en/user/broken-markup.dita", "<broken")
    sources._validate_semantic_markup([broken_markup])
    valid_markup = _write(
        documentation / "src/dita/en/user/semantic-markup.dita",
        '<topic id="semantic"><title>Semantic</title><body><fig id="figure">'
        '<title>Caption</title><image keyref="image.key"><alt>Localized alt</alt></image>'
        '</fig><note type="warning">Warning</note></body></topic>',
    )
    sources._validate_semantic_markup([valid_markup])
    valid_policy = _write(
        documentation / "src/dita/en/user/valid-policies-json.dita",
        '<topic id="policy"><body><codeblock outputclass="language-json">'
        '{"policies": {}}</codeblock></body></topic>',
    )
    sources._validate_semantic_markup([valid_policy])
    invalid_markup = _write(
        documentation / "src/dita/en/user/invalid-policies-json.dita",
        '<topic id="invalid"><title><uicontrol>Nested</uicontrol></title><body>'
        "<uicontrol/><note>not warning</note><fig/>"
        '<codeblock outputclass="plain">ignored</codeblock>'
        '<codeblock outputclass="language-json">{</codeblock>'
        "</body></topic>",
    )
    with pytest.raises(BuildError) as semantic_error:
        sources._validate_semantic_markup([invalid_markup])
    for message in (
        "empty uicontrol",
        "uicontrol is nested in title",
        "admonition must be a non-empty warning note",
        "figure requires an id and title",
        "figure requires a keyed image and localized alt text",
        "invalid JSON codeblock",
        "requires a complete top-level policies document",
    ):
        assert message in str(semantic_error.value)

    readme = _write(repository / "README.md", "```json\n{\n```\n")
    with pytest.raises(BuildError, match="invalid JSON codeblock"):
        sources._validate_readme_policies([readme])
    readme.write_text('```json\n{"flags": {}}\n```\n', encoding="utf-8")
    with pytest.raises(BuildError, match="complete top-level Firefox policies document"):
        sources._validate_readme_policies([readme])

    localized_policy = _write(
        documentation / "src/dita/ru/user/guard-policies-json.dita", '<topic id="guard"/>'
    )
    fixture = _write(documentation / "fixtures/guard.json", "{}")
    monkeypatch.setattr(sources, "_changed_paths", lambda _arguments: [localized_policy, fixture])
    monkeypatch.setattr(sources, "_validate_changed_inputs", lambda _paths: None)
    monkeypatch.setattr(sources, "validate_focused_source_links", lambda _paths: None)
    monkeypatch.setattr(sources, "_validate_localized_shape", lambda _paths: None)
    monkeypatch.setattr(sources, "_validate_semantic_markup", lambda _paths: None)
    monkeypatch.setattr(sources, "_validate_readme_policies", lambda _paths: None)
    monkeypatch.setattr(sources, "_validate_registered_fixtures", lambda _paths: None)
    report = sources.fast_check([], emit=False)
    assert {
        "localized structural shape when a locale topic changed",
        "complete Firefox policies.json document shape",
        "affected registered fixture shape",
    } <= set(report["checked_guards"])


def test_metadata_validation_and_combined_validation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _repository, _documentation = _roots(tmp_path, monkeypatch)
    calls: list[str] = []
    monkeypatch.setattr(
        sources.subprocess,
        "run",
        lambda command, **_kwargs: (
            calls.append(command[1]) or SimpleNamespace(returncode=0, stdout="", stderr="")
        ),
    )
    monkeypatch.setattr(sources, "validate_source_links", lambda: calls.append("links"))
    sources.validate_sources()
    assert calls[-1] == "links"

    monkeypatch.setattr(
        sources.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=1, stdout="bad", stderr="worse"),
    )
    with pytest.raises(BuildError, match="bad"):
        sources._metadata_validation()
