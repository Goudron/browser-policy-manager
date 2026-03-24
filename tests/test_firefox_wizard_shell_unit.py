from __future__ import annotations

from types import SimpleNamespace

from app.models.policy_schema import PolicyBranch, PolicyDefinition, PolicyProperty, PolicyUiMetadata
from app.web.firefox_wizard_shell import inline_editors
from app.web.firefox_wizard_shell import serializer


def _ui() -> PolicyUiMetadata:
    return PolicyUiMetadata(
        section="advanced",
        subsection="test",
        widget="object-card",
        complexity="advanced",
    )


def _prop(name: str, type_: str, **kwargs) -> PolicyProperty:
    return PolicyProperty(name=name, type=type_, **kwargs)


def test_humanize_identifier_handles_empty_and_delimiter_only_boundaries():
    assert serializer.humanize_identifier("") == ""
    assert serializer.humanize_identifier("_ProxyMode:") == "Proxy Mode"


def test_build_inline_editor_returns_none_for_non_object_supported_policy():
    definition = PolicyDefinition(id="Cookies", type="string", ui=_ui())

    assert inline_editors.build_inline_editor(definition) is None


def test_build_inline_editor_counts_unsupported_fields_and_returns_none_without_supported_fields():
    definition = PolicyDefinition(
        id="Cookies",
        type="object",
        properties={
            "Locked": _prop("Locked", "boolean"),
            "Unsupported": _prop("Unsupported", "object"),
        },
        ui=_ui(),
    )
    unsupported_only = PolicyDefinition(
        id="Cookies",
        type="object",
        properties={
            "Unsupported": _prop("Unsupported", "object"),
        },
        ui=_ui(),
    )

    editor = inline_editors.build_inline_editor(definition)

    assert editor is not None
    assert editor["unsupported_field_count"] == 1
    assert inline_editors.build_inline_editor(unsupported_only) is None


def test_object_field_spec_covers_nested_object_dictionary_array_and_fallback_paths():
    assert inline_editors._resolve_field_kind(_prop("Count", "integer")) == "number"

    nested_object = _prop(
        "Camera",
        "object",
        properties={
            "Allow": _prop("Allow", "array", items_type="string"),
            "Unsupported": _prop("Unsupported", "object"),
        },
    )
    nested_dictionary = _prop(
        "MimeTypes",
        "object",
        properties={
            "Unsupported": _prop("Unsupported", "object"),
        },
        additional_property_type="object",
        additional_property_properties={
            "action": _prop("action", "string", enum=["open", "save"]),
            "broken": _prop("broken", "object"),
        },
    )
    nested_array = _prop(
        "Handlers",
        "array",
        items_type="object",
        item_properties={
            "name": _prop("name", "string"),
            "broken": _prop("broken", "object"),
        },
    )
    unsupported_dictionary = _prop(
        "BrokenMap",
        "object",
        additional_property_type="object",
        additional_property_properties={
            "broken": _prop("broken", "object"),
        },
    )

    object_spec = inline_editors._build_object_field_spec(nested_object)
    dictionary_spec = inline_editors._build_object_field_spec(nested_dictionary)
    array_spec = inline_editors._build_object_field_spec(nested_array)

    assert object_spec is not None
    assert object_spec["kind"] == "nested-object"
    assert object_spec["unsupported_field_count"] == 1

    assert dictionary_spec is not None
    assert dictionary_spec["kind"] == "nested-dictionary-object"
    assert dictionary_spec["unsupported_field_count"] == 1

    assert array_spec is not None
    assert array_spec["kind"] == "nested-array-of-objects"
    assert array_spec["unsupported_field_count"] == 1

    assert inline_editors._build_object_field_spec(unsupported_dictionary) is None


def test_object_field_spec_returns_none_for_nested_array_without_supported_fields():
    unsupported_nested_array = _prop(
        "Handlers",
        "array",
        items_type="object",
        item_properties={
            "broken": _prop("broken", "object"),
        },
    )

    assert inline_editors._build_object_field_spec(unsupported_nested_array) is None


def test_array_and_dictionary_inline_editors_handle_json_and_unknown_items():
    json_prop = _prop("payload", "object")
    unknown_prop = SimpleNamespace(type="mystery", required=False, enum=None)
    empty_array_definition = PolicyDefinition(
        id="Bookmarks",
        type="array",
        items_type="object",
        item_properties={},
        ui=_ui(),
    )
    unknown_array_definition = SimpleNamespace(item_properties={"mystery": unknown_prop})
    unknown_dictionary_definition = SimpleNamespace(
        additional_property_properties={"mystery": unknown_prop}
    )

    assert inline_editors._resolve_array_field_kind(json_prop) == "json"
    assert inline_editors._build_array_inline_editor(empty_array_definition) is None
    assert inline_editors._build_array_inline_editor(unknown_array_definition) is None
    assert inline_editors._build_dictionary_inline_editor(unknown_dictionary_definition) is None


def test_branch_inline_editor_handles_missing_non_object_and_unsupported_fields():
    missing_branches = PolicyDefinition(id="SanitizeOnShutdown", type="object", ui=_ui())
    mixed_branches = PolicyDefinition(
        id="SanitizeOnShutdown",
        type="object",
        branches=[
            PolicyBranch(type="string"),
            PolicyBranch(
                type="object",
                properties={
                    "Locked": _prop("Locked", "boolean"),
                    "Unsupported": _prop("Unsupported", "object"),
                },
            ),
            PolicyBranch(type="boolean"),
        ],
        ui=_ui(),
    )

    assert inline_editors._build_branch_inline_editor(missing_branches) is None

    editor = inline_editors._build_branch_inline_editor(mixed_branches)

    assert editor is not None
    assert editor["kind"] == "branch"
    object_branch = next(branch for branch in editor["branches"] if branch["id"] == "object")
    assert object_branch["unsupported_field_count"] == 1


def test_serialize_policy_includes_inline_editor_payload():
    definition = PolicyDefinition(
        id="DNSOverHTTPS",
        type="object",
        description_key="policy.DNSOverHTTPS",
        ui=PolicyUiMetadata(
            section="network_access",
            subsection="dns_over_https",
            widget="object-card",
            complexity="advanced",
            preserve_unknown_fields=False,
            support_level="mapped",
            tags=["dns"],
        ),
    )

    payload = serializer.serialize_policy(
        definition,
        5,
        inline_editor_builder=lambda item: {"kind": "object-card", "id": item.id},
    )

    assert payload["label"] == "DNSOver HTTPS"
    assert payload["subsection_label"] == "dns over https"
    assert payload["target"] == "shell-policy:5:DNSOverHTTPS"
    assert payload["inline_editor"] == {"kind": "object-card", "id": "DNSOverHTTPS"}
