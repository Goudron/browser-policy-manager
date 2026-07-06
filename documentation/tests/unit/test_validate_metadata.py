from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

DOCUMENTATION_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = DOCUMENTATION_ROOT / "tools/validate_metadata.py"
SPEC = importlib.util.spec_from_file_location("validate_metadata", MODULE_PATH)
assert SPEC and SPEC.loader
validate_metadata = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validate_metadata)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _vocabulary(repo: Path) -> Path:
    registry = repo / "registry.json"
    _write_json(registry, {"items": [{"id": "policy-a"}, {"id": "policy-b"}]})
    markdown = repo / "registry.md"
    markdown.write_text("| `api-read` | Read API |\n", encoding="utf-8")
    vocabulary = repo / "vocabulary.json"
    _write_json(
        vocabulary,
        {
            "schema_version": 1,
            "dita_version": "1.3",
            "attributes": {
                "audience": ["admin", "user"],
                "platform": ["linux", "windows"],
            },
            "otherprops_groups": {
                "policy": {
                    "source": "registry.json",
                    "identity_field": "id",
                    "collection": "items",
                },
                "api": {
                    "source": "registry.md",
                    "table_identity_pattern": "api-[a-z]+",
                },
            },
        },
    )
    return vocabulary


def test_metadata_validation_accepts_fixed_attributes_and_registered_otherprops(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(validate_metadata, "REPOSITORY_ROOT", tmp_path)
    vocabulary = validate_metadata.load_vocabulary(_vocabulary(tmp_path))
    source = tmp_path / "topic.dita"
    source.write_text(
        '<topic id="topic" audience="admin user" platform="linux" '
        'otherprops="policy(policy-a policy-b) api(api-read)">'
        "<title>Topic</title></topic>",
        encoding="utf-8",
    )

    assert validate_metadata.validate_xml(source, vocabulary) == []
    assert validate_metadata.source_files([source]) == [source]


def test_load_json_rejects_duplicate_keys_and_unreadable_files(tmp_path: Path) -> None:
    duplicate = tmp_path / "duplicate.json"
    duplicate.write_text('{"a": 1, "a": 2}', encoding="utf-8")

    with pytest.raises(validate_metadata.MetadataError, match="duplicate JSON key"):
        validate_metadata.load_json(duplicate)
    with pytest.raises(validate_metadata.MetadataError, match="cannot read metadata vocabulary"):
        validate_metadata.load_json(tmp_path / "missing.json")


def test_vocabulary_rejects_bad_schema_and_registry_contracts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(validate_metadata, "REPOSITORY_ROOT", tmp_path)
    bad_schema = tmp_path / "bad-schema.json"
    _write_json(bad_schema, {"schema_version": 2, "dita_version": "2.0"})
    with pytest.raises(validate_metadata.MetadataError, match="unsupported metadata vocabulary"):
        validate_metadata.load_vocabulary(bad_schema)

    broken_registry = tmp_path / "broken-registry.json"
    _write_json(broken_registry, {"items": [{"wrong": "value"}]})
    vocabulary = tmp_path / "vocabulary.json"
    _write_json(
        vocabulary,
        {
            "schema_version": 1,
            "dita_version": "1.3",
            "attributes": {},
            "otherprops_groups": {
                "policy": {
                    "source": "broken-registry.json",
                    "identity_field": "id",
                    "collection": "items",
                }
            },
        },
    )
    with pytest.raises(validate_metadata.MetadataError, match="invalid registry contract"):
        validate_metadata.load_vocabulary(vocabulary)

    empty_markdown = tmp_path / "empty.md"
    empty_markdown.write_text("| no identities |\n", encoding="utf-8")
    _write_json(
        vocabulary,
        {
            "schema_version": 1,
            "dita_version": "1.3",
            "attributes": {},
            "otherprops_groups": {
                "api": {
                    "source": "empty.md",
                    "table_identity_pattern": "api-[a-z]+",
                }
            },
        },
    )
    with pytest.raises(validate_metadata.MetadataError, match="no registry identities"):
        validate_metadata.load_vocabulary(vocabulary)

    unsupported = tmp_path / "registry.txt"
    unsupported.write_text("policy-a", encoding="utf-8")
    _write_json(
        vocabulary,
        {
            "schema_version": 1,
            "dita_version": "1.3",
            "attributes": {},
            "otherprops_groups": {"policy": {"source": "registry.txt"}},
        },
    )
    with pytest.raises(validate_metadata.MetadataError, match="unsupported registry source"):
        validate_metadata.load_vocabulary(vocabulary)


def test_otherprops_validation_reports_syntax_unknown_groups_empty_and_unknown_values(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(validate_metadata, "REPOSITORY_ROOT", tmp_path)
    vocabulary = validate_metadata.load_vocabulary(_vocabulary(tmp_path))

    assert validate_metadata._validate_otherprops("plain-token", vocabulary, "context") == [
        "context: otherprops must use group(value) syntax"
    ]
    errors = validate_metadata._validate_otherprops(
        "missing(value) policy() policy(policy-z)",
        vocabulary,
        "context",
    )
    assert "context: unknown otherprops group 'missing'" in errors
    assert "context: empty otherprops group 'policy'" in errors
    assert "context: unknown policy value(s): policy-z" in errors


def test_xml_validation_reports_parse_fixed_attribute_and_otherprops_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(validate_metadata, "REPOSITORY_ROOT", tmp_path)
    vocabulary = validate_metadata.load_vocabulary(_vocabulary(tmp_path))
    broken = tmp_path / "broken.dita"
    broken.write_text("<topic>", encoding="utf-8")
    assert "invalid XML" in validate_metadata.validate_xml(broken, vocabulary)[0]

    invalid = tmp_path / "invalid.dita"
    invalid.write_text(
        '<topic id="bad" audience="guest" otherprops="policy(policy-z)">'
        "<title>Bad</title></topic>",
        encoding="utf-8",
    )
    errors = validate_metadata.validate_xml(invalid, vocabulary)
    assert any("unknown audience value(s): guest" in error for error in errors)
    assert any("unknown policy value(s): policy-z" in error for error in errors)


def test_source_files_accepts_directories_and_rejects_non_dita_inputs(tmp_path: Path) -> None:
    root = tmp_path / "sources"
    root.mkdir()
    topic = root / "topic.dita"
    map_file = root / "map.ditamap"
    ignored = root / "notes.md"
    topic.write_text("<topic/>", encoding="utf-8")
    map_file.write_text("<map/>", encoding="utf-8")
    ignored.write_text("notes", encoding="utf-8")

    assert validate_metadata.source_files([root]) == [map_file, topic]
    with pytest.raises(validate_metadata.MetadataError, match="not a DITA source or directory"):
        validate_metadata.source_files([ignored])


def test_main_reports_success_validation_errors_and_configuration_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(validate_metadata, "REPOSITORY_ROOT", tmp_path)
    vocabulary = _vocabulary(tmp_path)
    source = tmp_path / "topic.dita"
    source.write_text('<topic id="ok" audience="admin"><title>OK</title></topic>', encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        ["validate_metadata.py", str(source), "--vocabulary", str(vocabulary)],
    )
    assert validate_metadata.main() == 0
    assert "Validated conditional metadata in 1 DITA source files." in capsys.readouterr().out

    source.write_text('<topic id="bad" audience="guest"><title>Bad</title></topic>', encoding="utf-8")
    assert validate_metadata.main() == 1
    assert "unknown audience value(s): guest" in capsys.readouterr().err

    monkeypatch.setattr(
        sys,
        "argv",
        ["validate_metadata.py", str(tmp_path / "notes.md"), "--vocabulary", str(vocabulary)],
    )
    assert validate_metadata.main() == 2
    assert "metadata validation failed" in capsys.readouterr().err
