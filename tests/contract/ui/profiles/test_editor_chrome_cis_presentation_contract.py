from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from bs4 import BeautifulSoup

from app.core.locales import ACTIVE_CATALOG_LOCALES
from app.core.profile_baseline_provenance import (
    CONTRACT_ID,
    CONTRACT_VERSION,
    baseline_display,
)
from app.web.profiles import templates


def _digest(character: str) -> str:
    return character * 64


def _catalog_cis_envelope(
    *,
    baseline_id: str,
    status: str,
    reason_code: str | None,
) -> dict[str, Any]:
    return {
        "contract_id": CONTRACT_ID,
        "contract_version": CONTRACT_VERSION,
        "lineage": {
            "kind": "prepared",
            "source_profile_id": None,
            "source_revision": None,
            "plan_digest": None,
        },
        "starter": {
            "identity_state": "custom-imported",
            "catalog_id": None,
            "catalog_version": None,
            "preset_id": None,
            "definition_sha256": None,
            "resolved_schema_artifact_id": None,
            "disposition": "custom-imported",
        },
        "cis": {
            "identity_state": "catalog",
            "catalog_id": "firefox-cis-generated-layers",
            "catalog_version": "1.0.0",
            "baseline_id": baseline_id,
            "benchmark_id": "cis-firefox-esr-gpo",
            "benchmark_version": "1.0.0",
            "layer_sha256": _digest("a"),
            "merge_rules_sha256": _digest("b"),
            "merge_result_sha256": _digest("c"),
            "resolved_schema_artifact_id": "release-153",
            "proof_digest": _digest("d"),
            "display_status": status,
            "current_claim": status == "verified",
            "reason_code": reason_code,
        },
    }


def _none_envelope() -> dict[str, Any]:
    envelope = _catalog_cis_envelope(baseline_id="cis_l1", status="verified", reason_code=None)
    envelope["cis"].update(
        {
            "identity_state": "none",
            "catalog_id": None,
            "catalog_version": None,
            "baseline_id": None,
            "benchmark_id": None,
            "benchmark_version": None,
            "layer_sha256": None,
            "merge_rules_sha256": None,
            "merge_result_sha256": None,
            "resolved_schema_artifact_id": None,
            "proof_digest": None,
            "display_status": "none",
            "current_claim": False,
            "reason_code": None,
        }
    )
    return envelope


def _render_cis_fact(envelope: dict[str, Any]):
    catalog = json.loads(Path("app/i18n/en.json").read_text(encoding="utf-8"))
    html = templates.get_template("profiles/_page_editor_chrome.html").render(
        {
            "editing_profile_initial": {
                "id": 1,
                "name": "CIS chrome projection",
                "schema_version": "release-153",
                "is_deleted": False,
                # Raw compliance deliberately looks current here.  The chrome
                # may only consume the persisted-envelope projection below.
                "compliance": {"status": "current", "current_claims": True},
                "baseline_display": baseline_display(deepcopy(envelope)),
            },
            "editing_profile_schema_version": "release-153",
            "editing_profile_schema_label": "Firefox 153",
            "schema_channels_catalog": {
                "default_value": "release-153",
                "default_label": "Firefox 153",
            },
            "profiles_route_mode": "edit",
            "editing_profile_id": 1,
            "include_deleted": False,
            "settings_href": "/profiles/1/settings",
            "json_href": "/profiles/1/json",
            "documentation_deep_help_links": {},
            "tr": lambda key, fallback="": catalog.get(key, fallback),
        }
    )
    fact = BeautifulSoup(html, "html.parser").find(id="profile-cis-fact")
    assert fact is not None
    assert fact.name == "dd"
    return fact


@pytest.mark.parametrize(
    ("envelope", "status", "current_claim", "text", "reason_key"),
    (
        (_none_envelope(), "none", "false", "None", None),
        (
            _catalog_cis_envelope(baseline_id="cis_l1", status="verified", reason_code=None),
            "verified",
            "true",
            "CIS Level 1 · 1.0.0 Evidence verified",
            None,
        ),
        (
            _catalog_cis_envelope(baseline_id="cis_l2", status="verified", reason_code=None),
            "verified",
            "true",
            "CIS Level 2 · 1.0.0 Evidence verified",
            None,
        ),
        (
            _catalog_cis_envelope(
                baseline_id="cis_l1",
                status="manual-review",
                reason_code="cis_merge_manual_review_required",
            ),
            "manual-review",
            "false",
            "CIS Level 1 · 1.0.0 Manual review required",
            "profiles.editor_chrome_cis_reason_merge_review",
        ),
        (
            _catalog_cis_envelope(
                baseline_id="cis_l2",
                status="invalidated",
                reason_code="compliance_target_proof_unavailable",
            ),
            "invalidated",
            "false",
            "CIS Level 2 · 1.0.0 Evidence invalidated",
            "profiles.editor_chrome_cis_reason_conversion",
        ),
        (
            _catalog_cis_envelope(
                baseline_id="cis_l1",
                status="unavailable",
                reason_code="cis_schema_unavailable",
            ),
            "unavailable",
            "false",
            "CIS Level 1 · 1.0.0 Saved CIS baseline unavailable",
            "profiles.editor_chrome_cis_reason_schema_unavailable",
        ),
    ),
)
def test_shared_chrome_renders_each_persisted_cis_projection_without_current_claim_inference(
    envelope: dict[str, Any],
    status: str,
    current_claim: str,
    text: str,
    reason_key: str | None,
) -> None:
    fact = _render_cis_fact(envelope)

    assert fact.get("data-saved-profile-cis-display-status") == status
    assert fact.get("data-saved-profile-cis-current-claim") == current_claim
    assert text in fact.get_text(" ", strip=True)
    if reason_key is None:
        assert fact.get("aria-describedby") is None
    else:
        reason = fact.find(id="profile-cis-reason")
        assert reason is not None
        assert fact.get("aria-describedby") == "profile-cis-reason"
        assert reason.get_text(" ", strip=True)
        assert "Review the saved profile and CIS decisions" in reason.get_text(" ", strip=True)


def test_cis_chrome_uses_only_baseline_display_and_every_runtime_locale_has_its_copy() -> None:
    source = Path("app/templates/profiles/_page_editor_chrome.html").read_text(encoding="utf-8")
    required_keys = {
        "profiles.editor_chrome_cis_label",
        "profiles.editor_chrome_cis_none",
        "profiles.editor_chrome_cis_level_1",
        "profiles.editor_chrome_cis_level_2",
        "profiles.editor_chrome_cis_verified",
        "profiles.editor_chrome_cis_manual_review",
        "profiles.editor_chrome_cis_invalidated",
        "profiles.editor_chrome_cis_unavailable",
        "profiles.editor_chrome_cis_reason_conversion",
        "profiles.editor_chrome_cis_reason_schema_unavailable",
        "profiles.editor_chrome_cis_recovery",
    }

    assert 'initial_baseline_display.get("cis", {})' in source
    assert "initial_profile.compliance" not in source
    assert "wizard_starter_catalog" not in source
    for locale in ACTIVE_CATALOG_LOCALES:
        catalog = json.loads(Path(f"app/i18n/{locale}.json").read_text(encoding="utf-8"))
        assert required_keys <= set(catalog)
