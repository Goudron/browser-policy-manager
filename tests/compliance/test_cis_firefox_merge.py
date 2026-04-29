from __future__ import annotations

from app.compliance.firefox.cis.generation import GeneratedCisLayer, build_cis_layer
from app.compliance.firefox.cis.merge import (
    _load_manual_review_rules,
    _load_target_metadata,
    _select_by_rule,
    _target_effective_path,
    merge_base_with_cis_layer,
)
from app.core.policy_validation import (
    load_policy_schema_for_channel,
    validate_profile_policies_or_raise,
)
from app.web.firefox_starter_presets import build_wizard_starter_document


def test_cis_merge_adds_missing_hardening_without_dropping_base_only_settings() -> None:
    base = build_wizard_starter_document("basic_corporate", "release-150")
    layer = build_cis_layer(2, "release-150")

    result = merge_base_with_cis_layer(base, layer, base_label="basic_corporate", cis_label="cis_l2")

    assert result.effective_policies["DisableDeveloperTools"] is True
    assert result.effective_policies["SSLVersionMin"] == "tls1.2"
    assert result.effective_policies["ExtensionSettings"]["*"]["installation_mode"] == "blocked"
    assert result.effective_policies["Homepage"]["URL"] == "https://intranet.example.local/"
    validate_profile_policies_or_raise(
        result.effective_policies,
        load_policy_schema_for_channel("release-150"),
    )


def test_cis_merge_keeps_base_update_and_proxy_governance_for_review() -> None:
    base = build_wizard_starter_document("basic_corporate", "release-150")
    layer = build_cis_layer(1, "release-150")

    result = merge_base_with_cis_layer(base, layer)
    decisions = {decision.path: decision for decision in result.decisions}

    assert result.effective_policies["AppAutoUpdate"] is False
    assert result.effective_policies["DisableAppUpdate"] is True
    assert result.effective_policies["DisableSystemAddonUpdate"] is True
    assert result.effective_policies["Proxy"]["Mode"] == "system"
    assert decisions[("AppAutoUpdate",)].decision == "manual_review_kept_base"
    assert decisions[("AppAutoUpdate",)].review_required is True
    assert decisions[("Proxy", "Mode")].decision == "manual_review_kept_base"
    assert result.summary["review_required"] >= 4


def test_cis_merge_reports_already_satisfied_and_cis_replacements() -> None:
    base = build_wizard_starter_document("basic_corporate", "release-150")
    layer = build_cis_layer(2, "release-150")

    result = merge_base_with_cis_layer(base, layer)
    decisions = {decision.path: decision for decision in result.decisions}

    assert decisions[("DisableTelemetry",)].decision == "already_satisfied"
    assert decisions[("DisableTelemetry",)].recommendation_ids == ("1.1.35",)
    assert decisions[("DisablePrivateBrowsing",)].decision == "added_from_cis"
    assert decisions[("SearchSuggestEnabled",)].decision == "added_from_cis"


def test_cis_merge_level_2_contains_level_1_plus_level_2_decisions() -> None:
    base = build_wizard_starter_document("blank", "release-150")
    l1 = merge_base_with_cis_layer(base, build_cis_layer(1, "release-150"))
    l2 = merge_base_with_cis_layer(base, build_cis_layer(2, "release-150"))

    assert set(l1.effective_policies) < set(l2.effective_policies)
    assert "NewTabPage" not in l1.effective_policies
    assert l2.effective_policies["NewTabPage"] is False
    assert l2.effective_policies["DisableFormHistory"] is True


def test_cis_merge_keeps_soc_sanitize_cleanup_conflicts_for_review() -> None:
    base = build_wizard_starter_document("soc_hard", "release-150")
    layer = build_cis_layer(1, "release-150")

    result = merge_base_with_cis_layer(base, layer, base_label="soc_hard", cis_label="cis_l1")
    decisions = {decision.path: decision for decision in result.decisions}

    assert result.effective_policies["SanitizeOnShutdown"]["History"] is True
    assert decisions[("SanitizeOnShutdown", "History")].decision == "manual_review_kept_base"
    assert decisions[("SanitizeOnShutdown", "History")].review_required is True


def test_cis_merge_preserves_classroom_kiosk_controls_and_adds_cis_hardening() -> None:
    base = build_wizard_starter_document("classroom_kiosk", "release-150")
    layer = build_cis_layer(2, "release-150")

    result = merge_base_with_cis_layer(
        base,
        layer,
        base_label="classroom_kiosk",
        cis_label="cis_l2",
    )
    policies = result.effective_policies

    assert policies["WebsiteFilter"]["Block"] == ["<all_urls>"]
    assert policies["WebsiteFilter"]["Exceptions"] == [
        "https://start.school.local/*",
        "https://classroom.example.local/*",
        "https://lms.example.local/*",
    ]
    assert policies["ExtensionSettings"]["*"]["installation_mode"] == "blocked"
    assert policies["ExtensionSettings"]["uBlock0@raymondhill.net"] == {
        "installation_mode": "force_installed",
        "install_url": "https://addons.mozilla.org/firefox/downloads/latest/ublock-origin/latest.xpi",
    }
    assert policies["Permissions"]["Camera"]["Allow"] == [
        "https://classroom.example.local",
        "https://lms.example.local",
    ]
    assert policies["Homepage"]["URL"] == "https://start.school.local/"
    assert policies["DisableDeveloperTools"] is True

    assert policies["SSLVersionMin"] == "tls1.2"
    assert policies["SearchSuggestEnabled"] is False
    assert policies["NewTabPage"] is False
    assert policies["DisableFormHistory"] is True
    assert policies["PasswordManagerEnabled"] is False

    validate_profile_policies_or_raise(
        policies,
        load_policy_schema_for_channel("release-150"),
    )


def test_cis_merge_rule_selection_edges() -> None:
    assert _select_by_rule("boolean_true_is_stricter", False, True) == "cis"
    assert _select_by_rule("boolean_false_is_stricter", True, False) == "cis"
    assert _select_by_rule("empty_allowlist_is_stricter", ["a"], []) == "cis"
    assert _select_by_rule("empty_allowlist_is_stricter", [], ["a"]) == "base"
    assert _select_by_rule("cookie_behavior_rank", "accept", "reject") == "cis"
    assert _select_by_rule("tls_version_min_rank", "tls1", "tls1.2") == "cis"
    assert _select_by_rule("tls_version_max_rank", "tls1.3", "tls1.2") == "base"
    assert _select_by_rule(
        "preference_locked_value",
        {"Value": True, "Status": "default"},
        {"Value": True, "Status": "locked"},
    ) == "cis"
    assert _select_by_rule(
        "preference_locked_value",
        {"Value": True, "Status": "locked"},
        {"Value": True, "Status": "locked"},
    ) == "base"
    assert _select_by_rule("preference_locked_value", True, {"Value": True}) is None
    assert _select_by_rule("preference_locked_value", {"Value": True}, {"Value": False}) is None
    assert _select_by_rule("unknown", True, False) is None


def test_cis_merge_manual_review_and_metadata_fallbacks(tmp_path) -> None:
    import yaml

    assert _load_manual_review_rules(tmp_path) == {}
    assert _target_effective_path({"kind": "manual", "path": []}) is None

    (tmp_path / "mappings.yaml").write_text(
        yaml.safe_dump(
            {
                "mappings": [
                    {
                        "recommendation_id": "1.1.1",
                        "targets": [
                            {"kind": "manual"},
                            {
                                "kind": "preference",
                                "path": ["browser.example"],
                                "merge_rule": "preference_locked_value",
                            },
                            {
                                "kind": "policy",
                                "path": ["DisableTelemetry"],
                                "merge_rule": "boolean_true_is_stricter",
                            },
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "merge_rules.yaml").write_text(
        yaml.safe_dump({"manual_review_paths": {"Proxy.Mode": {"reason": "network owner"}}}),
        encoding="utf-8",
    )

    metadata = _load_target_metadata(tmp_path)

    assert metadata[("Preferences", "browser.example")]["recommendation_ids"] == ["1.1.1"]
    assert metadata[("Preferences", "browser.example")]["merge_rule"] == "preference_locked_value"
    assert metadata[("DisableTelemetry",)]["merge_rule"] == "boolean_true_is_stricter"
    assert _load_manual_review_rules(tmp_path) == {("Proxy", "Mode"): "network owner"}


def test_cis_merge_conflict_decisions_cover_rule_outcomes(tmp_path) -> None:
    import yaml

    (tmp_path / "mappings.yaml").write_text(
        yaml.safe_dump(
            {
                "mappings": [
                    {
                        "recommendation_id": "bool-cis",
                        "targets": [
                            {
                                "kind": "policy",
                                "path": ["BlockAboutConfig"],
                                "merge_rule": "boolean_true_is_stricter",
                            }
                        ],
                    },
                    {
                        "recommendation_id": "bool-base",
                        "targets": [
                            {
                                "kind": "policy",
                                "path": ["DisableTelemetry"],
                                "merge_rule": "boolean_true_is_stricter",
                            }
                        ],
                    },
                    {
                        "recommendation_id": "unknown",
                        "targets": [{"kind": "policy", "path": ["Homepage", "URL"]}],
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    layer = GeneratedCisLayer(
        benchmark_id="fixture",
        upstream_version="1.0",
        level=1,
        schema_channel="release-150",
        recommendation_ids=("bool-cis", "bool-base", "unknown"),
        policies={
            "BlockAboutConfig": True,
            "DisableTelemetry": False,
            "Homepage": {"URL": "https://cis.example"},
        },
    )

    result = merge_base_with_cis_layer(
        {
            "BlockAboutConfig": False,
            "DisableTelemetry": True,
            "Homepage": {"URL": "https://base.example"},
        },
        layer,
        base_dir=tmp_path,
    )
    decisions = {decision.path: decision for decision in result.decisions}

    assert decisions[("BlockAboutConfig",)].decision == "cis_replaced_base"
    assert decisions[("DisableTelemetry",)].decision == "kept_base_stricter"
    assert decisions[("Homepage", "URL")].decision == "manual_review_kept_base"
    assert result.effective_policies["BlockAboutConfig"] is True
    assert result.effective_policies["DisableTelemetry"] is True
    assert result.to_dict()["summary"]["review_required"] == 1


def test_cis_merge_rule_selection_none_edges() -> None:
    assert _select_by_rule("boolean_true_is_stricter", "yes", True) is None
    assert _select_by_rule("empty_allowlist_is_stricter", "all", []) is None
    assert _select_by_rule("empty_allowlist_is_stricter", ["a"], ["b"]) is None
    assert _select_by_rule("cookie_behavior_rank", "custom", "reject") is None
