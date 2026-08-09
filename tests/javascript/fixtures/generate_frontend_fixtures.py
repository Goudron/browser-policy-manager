from __future__ import annotations

import argparse
import gzip
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.core.schema_channels import CURRENT_RELEASE_SCHEMA_CHANNEL  # noqa: E402
from app.web.firefox_all_settings_categories import (  # noqa: E402
    get_all_settings_category_catalog,
)
from app.web.firefox_preferences import get_wizard_preferences_catalog  # noqa: E402
from app.web.firefox_starter_presets import build_wizard_starter_document  # noqa: E402
from app.web.firefox_wizard_shell import get_wizard_schema_shell_catalog  # noqa: E402
from tests.support import (  # noqa: E402
    build_all_settings_inventory_counts,
    build_all_settings_source_state_regression_fixtures,
    build_corporate_cis_l2_profile_fixture,
)

OUTPUT_PATH = Path(__file__).with_name("all_settings.json.gz")


def _documentation_row_help_links() -> dict[str, dict[str, str]]:
    inventory = json.loads(
        (
            REPO_ROOT / "docs/architecture/firefox-policy-documentation-inventory-0.9.0.json"
        ).read_text(encoding="utf-8")
    )
    return {
        **{
            f"policy:{item['policy_id']}": {"en": f"/help/en/policy/{item['policy_id']}"}
            for item in inventory["policies"]
        },
        **{
            f"known-preference:{item['preference_id']}": {
                "en": f"/help/en/preference/{item['preference_id']}"
            }
            for item in inventory["managed_preferences"]
        },
    }


def build_payload() -> dict[str, Any]:
    schema_version = CURRENT_RELEASE_SCHEMA_CHANNEL
    preferences = get_wizard_preferences_catalog()
    shell = get_wizard_schema_shell_catalog(preferences)
    categories = get_all_settings_category_catalog()
    source_fixtures = build_all_settings_source_state_regression_fixtures(
        schema_version=schema_version
    )
    source_by_id = {fixture.id: fixture for fixture in source_fixtures}
    enterprise = build_corporate_cis_l2_profile_fixture(schema_version=schema_version)
    known_pref = next(
        item["pref"] for item in preferences.get("known_preferences", []) if item.get("pref")
    )

    basic_flags = build_wizard_starter_document("basic_corporate", schema_version)
    unknown_flags = {
        "DisableTelemetry": True,
        "CustomEnterprisePolicy": {"enabled": True},
        "Preferences": {
            known_pref: {"Value": True, "Status": "default", "Type": "boolean"},
            "company.managed.preference": {
                "Value": "strict",
                "Status": "locked",
                "Type": "string",
            },
        },
    }
    invalid_flags = {
        "DisableTelemetry": True,
        "Preferences": {known_pref: {"Value": True, "Status": "default", "Type": "boolean"}},
    }
    raw_fallback = source_by_id["raw-fallback-policy"]
    expected_decision = next(
        decision
        for decision in enterprise.decisions
        if decision.get("review_required") and decision.get("path") == ["AppAutoUpdate"]
    )

    variants: dict[str, dict[str, Any]] = {
        "blank": {
            "schema_version": schema_version,
            "flags": {},
            "counts": (
                build_all_settings_inventory_counts(
                    schema_version=schema_version, flags={}
                ).as_dict()
            ),
        },
        "basicCorporate": {
            "schema_version": schema_version,
            "flags": basic_flags,
            "counts": (
                build_all_settings_inventory_counts(
                    schema_version=schema_version, flags=basic_flags
                ).as_dict()
            ),
        },
        "cisL2": {
            "schema_version": schema_version,
            "flags": enterprise.flags,
            "compliance": enterprise.compliance,
            "counts": (
                build_all_settings_inventory_counts(
                    schema_version=schema_version, flags=enterprise.flags
                ).as_dict()
            ),
            "manual_review_count": enterprise.manual_review_count,
        },
        "unknownImport": {
            "schema_version": schema_version,
            "flags": unknown_flags,
            "counts": (
                build_all_settings_inventory_counts(
                    schema_version=schema_version, flags=unknown_flags
                ).as_dict()
            ),
            "known_pref": known_pref,
        },
        "rawFallback": {
            "schema_version": schema_version,
            "flags": raw_fallback.flags,
            "compliance": raw_fallback.compliance,
            "raw_id": raw_fallback.expectation.entry_id,
        },
        "invalid": {
            "schema_version": schema_version,
            "flags": invalid_flags,
            "issues": [
                {"policy": "DisableTelemetry", "path": ["DisableTelemetry"]},
                {"policy": "Preferences", "path": ["Preferences", known_pref, "Value"]},
            ],
            "known_pref": known_pref,
        },
    }

    return {
        "schema_version": schema_version,
        "all_settings_category_catalog": categories,
        "wizard_preferences_catalog": preferences,
        "wizard_schema_shell_catalog": shell,
        "source_state_cases": [
            {
                "id": fixture.id,
                "schema_version": fixture.schema_version,
                "flags": fixture.flags,
                "compliance": fixture.compliance,
                "expectation": asdict(fixture.expectation),
                "manual_edits": [asdict(edit) for edit in fixture.manual_edits],
            }
            for fixture in source_fixtures
        ],
        "profile_variants": variants,
        "enterprise": {
            "schema_version": enterprise.schema_version,
            "flags": enterprise.flags,
            "compliance": enterprise.compliance,
            "configured_count": (
                enterprise.configured_policy_count + enterprise.configured_preference_count
            ),
            "manual_review_count": enterprise.manual_review_count,
            "expected_path": ".".join(expected_decision["path"]),
            "expected_reason": expected_decision["reason"],
            "expected_recommendation": expected_decision["recommendation_ids"][0],
        },
        "documentation_row_help_links": _documentation_row_help_links(),
    }


def render_payload() -> bytes:
    serialized = json.dumps(
        build_payload(), ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    return gzip.compress(serialized, compresslevel=9, mtime=0)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build native frontend test fixtures.")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rendered = render_payload()
    if args.check:
        if not OUTPUT_PATH.is_file() or OUTPUT_PATH.read_bytes() != rendered:
            print(f"stale native frontend fixture: {OUTPUT_PATH.relative_to(REPO_ROOT)}")
            return 1
        print("native frontend fixture is current")
        return 0
    OUTPUT_PATH.write_bytes(rendered)
    print(f"wrote {OUTPUT_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
