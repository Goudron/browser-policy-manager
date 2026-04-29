from __future__ import annotations

from app.models.policy_schema import (
    PolicyDefinition,
    PolicyProperty,
    PolicySchema,
    PolicyUiMetadata,
    PolicyUiSection,
)


def test_policy_schema_models_defaults_and_lookup():
    prop = PolicyProperty(
        name="Install",
        type="array",
        description_key="policy.Extensions.Install",
        items_type="string",
        required=True,
    )
    definition = PolicyDefinition(
        id="Extensions",
        type="object",
        description_key="policy.Extensions",
        properties={"Install": prop},
        ui=PolicyUiMetadata(
            section="extensions_integrations",
            subsection="extensions",
            widget="object-card",
            complexity="advanced",
        ),
    )
    schema = PolicySchema(
        channel="release-150",
        version="149.0",
        source="test-fixture",
        policies={"Extensions": definition},
        ui_sections=[
            PolicyUiSection(
                id="extensions_integrations",
                title_key="profiles.wizard_section_extensions_integrations",
                fallback="Extensions and integrations",
                order=70,
            )
        ],
    )

    assert prop.required is True
    assert definition.additional_properties is True
    assert definition.categories == []
    assert definition.ui is not None
    assert definition.ui.widget == "object-card"
    assert schema.get_policy("Extensions") is definition
    assert schema.get_policy("NoSuchPolicy") is None
    assert schema.ui_sections[0].id == "extensions_integrations"


def test_policy_definition_supports_simple_constraints():
    definition = PolicyDefinition(
        id="StartDownloadsInTempDirectory",
        type="boolean",
        enum=[True, False],
        deprecated=False,
    )

    assert definition.enum == [True, False]
    assert definition.items_type is None
    assert definition.properties == {}
    assert definition.item_properties == {}
    assert definition.additional_property_properties == {}


def test_policy_property_and_definition_support_nested_metadata_and_branches():
    prop = PolicyProperty(
        name="AllowProxies",
        type="object",
        additional_property_type="boolean",
        additional_property_enum=[True],
        properties={
            "Enabled": PolicyProperty(
                name="Enabled",
                type="boolean",
            )
        },
    )
    definition = PolicyDefinition(
        id="SanitizeOnShutdown",
        type="object",
        properties={"AllowProxies": prop},
        branches=[
            {
                "type": "object",
                "properties": {
                    "Cache": {
                        "name": "Cache",
                        "type": "boolean",
                    }
                },
                "additional_properties": False,
            },
            {
                "type": "boolean",
                "enum": [True, False],
            },
        ],
    )

    assert prop.additional_property_type == "boolean"
    assert prop.additional_property_enum == [True]
    assert prop.properties["Enabled"].type == "boolean"
    assert len(definition.branches) == 2
    assert definition.branches[0].properties["Cache"].type == "boolean"
