from __future__ import annotations

import json
import re
from pathlib import Path

from tests.docs_index import doc_path_from_index

REPO_ROOT = Path(__file__).resolve().parents[4]
CONTRACT_PATH = (
    REPO_ROOT / "docs/architecture/profile-editor-chrome-baseline-presentation-contract-0.9.6.md"
)
FIXTURE_MARKER = "<!-- bpm096-editor-chrome-baseline-presentation-contract-v1 -->"


def _fixture() -> dict[str, object]:
    source = CONTRACT_PATH.read_text(encoding="utf-8")
    match = re.search(
        rf"{re.escape(FIXTURE_MARKER)}\s*```json\s*(\{{.*?\}})\s*```",
        source,
        flags=re.DOTALL,
    )
    assert match, "profile editor chrome baseline presentation fixture is missing"
    payload = json.loads(match.group(1))
    assert isinstance(payload, dict)
    return payload


def test_editor_chrome_contract_is_active_planning_only_and_backlog_linked() -> None:
    assert (
        doc_path_from_index(
            "architecture/profile-editor-chrome-baseline-presentation-contract-0.9.6.md",
            status="active",
        )
        == CONTRACT_PATH
    )
    source = " ".join(CONTRACT_PATH.read_text(encoding="utf-8").split()).casefold()
    assert "`bpm096-m2-06`" in source
    assert "adds no template, browser module, api, locale catalog, css" in source
    assert "m4 preparation and m5 ui work remain unimplemented" in source

    backlog = (
        REPO_ROOT / "docs/bpm_0_9_6_profile_creation_guided_editor_backlog_2026-08-20.md"
    ).read_text(encoding="utf-8")
    assert "### BPM096-M2-06 — Editor chrome baseline presentation contract" in backlog
    assert "profile-editor-chrome-baseline-presentation-contract-0.9.6.md" in backlog


def test_all_three_editors_share_only_server_authoritative_baseline_facts() -> None:
    contract = _fixture()
    assert contract["contract_id"] == "bpm096-profile-editor-chrome-baseline-presentation"
    assert contract["contract_version"] == 1
    assert contract["status"] == "planning-only-no-runtime-change"
    assert contract["surfaces"] == ["guided", "all-settings", "json"]
    assert contract["shared_chrome"] == {
        "future_template_owner": "app/templates/profiles/_page_editor_chrome.html",
        "one_authoritative_fact_set_per_surface": True,
        "saved_profile_only": True,
        "facts": ["profile-name", "schema", "starter-preset", "cis-baseline"],
    }

    inputs = contract["authoritative_inputs"]
    assert inputs["profile_name"] == {"source": "ProfileRead.name", "client_inference": "forbidden"}
    assert inputs["schema"] == {
        "source": "ProfileRead.schema_version",
        "presentation": "server-resolved-exact-saved-schema-identity",
        "client_catalog_reconstruction": "forbidden",
    }
    assert inputs["starter_preset"]["source"] == "ProfileRead.baseline_display.starter"
    assert inputs["starter_preset"]["flags_or_catalog_inference"] == "forbidden"
    assert inputs["cis_baseline"]["source"] == "ProfileRead.baseline_display.cis"
    assert inputs["cis_baseline"]["flags_or_compliance_inference"] == "forbidden"
    assert inputs["cross_editor_parity"] == (
        "same-saved-profile-revision-means-identical-locale-neutral-identities-availability-status-and-current-claim"
    )


def test_no_selector_or_writable_shadow_control_can_survive_in_an_editor() -> None:
    boundary = _fixture()["read_only_boundary"]
    assert boundary["schema_preset_cis_mutation_surfaces"] == [
        "preparation-create",
        "preparation-duplicate",
        "explicit-schema-conversion",
    ]
    assert set(boundary["forbidden_editor_controls"]) == {
        "select",
        "radio",
        "checkbox",
        "text-input",
        "hidden-input",
        "contenteditable",
        "writable-shadow-state",
    }
    assert set(boundary["forbidden_editor_payload_fields"]) == {
        "schema_version",
        "target_schema_id",
        "starter_id",
        "cis_baseline_id",
        "baseline_provenance",
        "baseline_display",
    }
    assert boundary["disabled_selector_is_not_read_only_presentation"] is True
    assert boundary["saved_profile_schema_change_path"] == "explicit-schema-conversion-only"


def test_invalidated_and_unavailable_cis_states_never_become_current_claims() -> None:
    contract = _fixture()
    truth = contract["cis_truth"]
    assert truth["none"] == {
        "identity_state": "none",
        "display_status": "none",
        "current_claim": False,
        "display": "None",
    }
    assert truth["verified"]["current_claim"] is True
    assert truth["manual_review"]["current_claim"] is False
    assert truth["invalidated"] == {
        "identity_state": "catalog",
        "display_status": "invalidated",
        "current_claim": False,
        "display": "historical-identity-plus-invalidated-and-reason",
    }
    assert truth["unavailable"]["current_claim"] is False
    assert set(truth["prohibited_current_claim_statuses"]) == {
        "none",
        "manual-review",
        "invalidated",
        "unavailable",
    }
    assert contract["starter_truth"]["replacement_or_flag_match"] == "forbidden"


def test_accessibility_locale_responsive_and_conversion_entry_are_shared_boundaries() -> None:
    contract = _fixture()
    assert contract["accessibility"]["structure"] == (
        "named-profile-heading-plus-semantic-read-only-fact-list"
    )
    assert contract["accessibility"]["noncurrent_cis"] == [
        "localized-status",
        "localized-reason",
        "local-recovery-or-next-action-when-required",
    ]
    assert contract["locale"]["source_catalog_roots"] == [
        "app/i18n_src/en",
        "app/i18n_src/ru",
        "app/i18n_src/de",
        "app/i18n_src/es-ES",
        "app/i18n_src/fr",
        "app/i18n_src/zh-CN",
    ]
    assert contract["locale"]["generated_runtime_catalog_edit"] == "forbidden"
    assert contract["responsive"]["supported_narrow_viewport_px"] == 320
    assert "no-fact-or-noncurrent-reason-is-hidden" in contract["responsive"]["requirements"]
    assert contract["conversion_entry"] == {
        "owner": "existing-explicit-schema-conversion-flow",
        "shared_entry": "one-localized-review-action-in-shared-chrome-when-the-saved-profile-is-eligible",
        "entry_is_not": [
            "schema-selector",
            "schema-save-payload",
            "automatic-conversion",
            "baseline-reapply-control",
        ],
        "unavailable_or_blocked": "truthful-localized-state-and-recovery-in-the-conversion-flow",
    }
