from __future__ import annotations

import json

from app.compliance.firefox.cis.generation import (
    GENERATED_DIR,
    _apply_target,
    _set_nested,
    build_all_cis_layers,
    build_cis_layer,
    write_generated_layers,
)
from app.core.policy_validation import (
    load_policy_schema_for_channel,
    validate_profile_policies_or_raise,
)


def test_cis_level_2_includes_level_1_recommendations() -> None:
    l1 = build_cis_layer(1, "release-150")
    l2 = build_cis_layer(2, "release-150")

    assert len(l1.recommendation_ids) == 49
    assert len(l2.recommendation_ids) == 53
    assert set(l1.recommendation_ids) < set(l2.recommendation_ids)


def test_cis_layers_validate_against_supported_firefox_schemas() -> None:
    for layer in build_all_cis_layers():
        schema = load_policy_schema_for_channel(layer.schema_channel)
        validate_profile_policies_or_raise(layer.policies, schema)


def test_cis_generated_layers_include_policy_and_preference_targets() -> None:
    layer = build_cis_layer(2, "release-150")

    assert layer.policies["DisableTelemetry"] is True
    assert layer.policies["DisableAppUpdate"] is False
    assert layer.policies["DisableSystemAddonUpdate"] is False
    assert layer.policies["EnableTrackingProtection"]["Locked"] is True
    assert layer.policies["Preferences"]["network.IDN_show_punycode"] == {
        "Value": True,
        "Status": "locked",
        "Type": "boolean",
    }


def test_write_generated_layers_creates_deterministic_json_documents(tmp_path) -> None:
    written = write_generated_layers(output_dir=tmp_path)

    assert [path.name for path in written] == [
        "cis_l1.esr-140.10.json",
        "cis_l2.esr-140.10.json",
        "cis_l1.release-150.json",
        "cis_l2.release-150.json",
    ]
    document = json.loads((tmp_path / "cis_l2.release-150.json").read_text(encoding="utf-8"))
    assert document["level"] == 2
    assert document["schema_channel"] == "release-150"
    assert len(document["recommendation_ids"]) == 53
    assert document["policies"]["DisablePrivateBrowsing"] is True


def test_committed_generated_layers_match_generator_output() -> None:
    for layer in build_all_cis_layers():
        path = GENERATED_DIR / f"cis_l{layer.level}.{layer.schema_channel}.json"

        assert path.exists()
        assert json.loads(path.read_text(encoding="utf-8")) == layer.to_document()


def test_build_cis_layer_rejects_unknown_level_and_benchmark() -> None:
    import pytest

    with pytest.raises(ValueError, match="CIS level"):
        build_cis_layer(3, "release-150")

    with pytest.raises(ValueError, match="Unknown CIS benchmark"):
        build_cis_layer(1, "release-150", benchmark_id="missing")


def test_cis_generation_skips_unmapped_and_unsupported_targets(tmp_path) -> None:
    from tests.compliance.test_cis_firefox_sources import _mapping, _recommendation, _write_fixture

    unsupported = _mapping("1.1.1")
    unsupported["targets"][0]["schema_channels"] = {"release-150": "invalid"}
    _write_fixture(
        tmp_path,
        recommendations=[
            "ignored",
            _recommendation("1.1.1"),
            _recommendation("1.1.2"),
        ],
        mappings=[unsupported],
    )

    layer = build_cis_layer(1, "release-150", base_dir=tmp_path)

    assert layer.recommendation_ids == ()
    assert layer.policies == {}


def test_cis_generation_skips_recommendations_without_string_ids(tmp_path) -> None:
    from tests.compliance.test_cis_firefox_sources import _mapping, _write_fixture

    _write_fixture(
        tmp_path,
        recommendations=[
            {"id": 101, "level": 1, "title": "Numeric id should be ignored"},
            {"level": 1, "title": "Missing id should be ignored"},
        ],
        mappings=[_mapping("1.1.1")],
    )

    layer = build_cis_layer(1, "release-150", base_dir=tmp_path)

    assert layer.recommendation_ids == ()
    assert layer.policies == {}


def test_apply_target_rejects_unsupported_kind_and_bad_paths() -> None:
    import pytest

    with pytest.raises(ValueError, match="Cannot generate target kind"):
        _apply_target({}, {"kind": "manual", "path": ["x"], "value": True})

    with pytest.raises(ValueError, match="empty target path"):
        _set_nested({}, [], True)

    with pytest.raises(ValueError, match="through scalar"):
        _set_nested({"A": False}, ["A", "B"], True)
