from __future__ import annotations

from app.models.policy_schema import PolicyDefinition, PolicyProperty, PolicySchema


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
    )
    schema = PolicySchema(
        channel="release-145",
        version="145.0",
        source="test-fixture",
        policies={"Extensions": definition},
    )

    assert prop.required is True
    assert definition.additional_properties is True
    assert definition.categories == []
    assert schema.get_policy("Extensions") is definition
    assert schema.get_policy("NoSuchPolicy") is None


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
