from __future__ import annotations

from typing import Any

from app.compliance.firefox.cis.validation import BASE_DIR, load_yaml_file
from app.core.policy_validation import load_policy_schema_for_channel, validate_profile_policies


def _build_policy_from_target(target: dict[str, Any]) -> dict[str, Any] | None:
    kind = target.get("kind")
    path = target.get("path") or []
    value = target.get("value")
    if kind == "policy":
        if not path:
            return None
        root: dict[str, Any] = {}
        current = root
        for part in path[:-1]:
            current = current.setdefault(part, {})
        current[path[-1]] = value
        return root
    if kind == "preference":
        if not path:
            return None
        return {"Preferences": {path[0]: value}}
    return None


def test_cis_mapping_targets_validate_against_declared_schema_channels() -> None:
    mapping_doc = load_yaml_file(BASE_DIR / "mappings.yaml")
    mappings = mapping_doc.get("mappings", [])
    errors: list[str] = []

    for mapping in mappings:
        if not isinstance(mapping, dict):
            continue
        rec_id = mapping.get("recommendation_id", "unknown")
        for target in mapping.get("targets") or []:
            if not isinstance(target, dict):
                continue
            policy_doc = _build_policy_from_target(target)
            if not policy_doc:
                continue
            schema_channels = target.get("schema_channels") or {}
            for channel, status in schema_channels.items():
                if status != "valid":
                    continue
                schema = load_policy_schema_for_channel(channel)
                issues = validate_profile_policies(policy_doc, schema)
                if issues:
                    errors.append(
                        f"{rec_id} -> {channel} {target.get('path')} failed: "
                        f"{'; '.join(issue.message for issue in issues)}"
                    )

    assert not errors, "Invalid CIS mapping targets detected:\n" + "\n".join(errors)
