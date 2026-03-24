from __future__ import annotations

import json
from typing import Any

from app.web.firefox_settings_catalog import get_wizard_settings_catalog


def _stable_value_key(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def _build_known_preferences(
    section_id: str,
    presets: list[dict[str, Any]],
    explicit_known_preferences: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}

    for known_pref in explicit_known_preferences or []:
        pref = known_pref["pref"]
        bucket = grouped.setdefault(
            pref,
            {
                "pref": pref,
                "section_id": section_id,
                "preset_ids": [],
                "preset_count": 0,
                "label_key": "",
                "fallback": pref,
                "description_key": "",
                "description_fallback": "",
                "value_control": "",
                "value_options": [],
                "statuses": set(),
                "types": set(),
                "values": {},
            },
        )
        if known_pref.get("label_key"):
            bucket["label_key"] = known_pref["label_key"]
        if known_pref.get("fallback"):
            bucket["fallback"] = known_pref["fallback"]
        if known_pref.get("description_key"):
            bucket["description_key"] = known_pref["description_key"]
        if known_pref.get("description_fallback"):
            bucket["description_fallback"] = known_pref["description_fallback"]
        if known_pref.get("value_control"):
            bucket["value_control"] = known_pref["value_control"]
        if known_pref.get("value_options"):
            bucket["value_options"] = list(known_pref["value_options"])
        if known_pref.get("status"):
            bucket["statuses"].add(known_pref["status"])
        if known_pref.get("type"):
            bucket["types"].add(known_pref["type"])
        if "value" in known_pref:
            bucket["values"][_stable_value_key(known_pref["value"])] = known_pref["value"]

    for preset in presets:
        pref = preset["pref"]
        bucket = grouped.setdefault(
            pref,
            {
                "pref": pref,
                "section_id": section_id,
                "preset_ids": [],
                "preset_count": 0,
                "label_key": preset["label_key"],
                "fallback": pref,
                "description_key": preset["description_key"],
                "description_fallback": "",
                "value_control": "",
                "value_options": [],
                "statuses": set(),
                "types": set(),
                "values": {},
            },
        )
        if not bucket["label_key"]:
            bucket["label_key"] = preset["label_key"]
        if not bucket["description_key"]:
            bucket["description_key"] = preset["description_key"]
        bucket["preset_ids"].append(preset["id"])
        bucket["preset_count"] = len(bucket["preset_ids"])
        bucket["statuses"].add(preset["status"])
        bucket["types"].add(preset["type"])
        bucket["values"][_stable_value_key(preset["value"])] = preset["value"]

    known_preferences = []
    for pref, bucket in grouped.items():
        statuses = sorted(bucket["statuses"])
        types = sorted(bucket["types"])
        values = list(bucket["values"].values())
        can_autofill = len(statuses) == 1 and len(types) == 1 and len(values) == 1

        known_preferences.append(
            {
                "pref": pref,
                "section_id": section_id,
                "preset_ids": bucket["preset_ids"],
                "preset_count": bucket["preset_count"],
                "label_key": bucket["label_key"],
                "fallback": bucket["fallback"],
                "description_key": bucket["description_key"],
                "description_fallback": bucket["description_fallback"],
                "value_control": bucket["value_control"],
                "value_options": bucket["value_options"],
                "status": statuses[0] if len(statuses) == 1 else "",
                "type": types[0] if len(types) == 1 else "",
                "value": values[0] if len(values) == 1 else None,
                "can_autofill": can_autofill,
            }
        )

    return sorted(known_preferences, key=lambda item: item["pref"])


def get_wizard_preferences_catalog(settings_catalog: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return the preference-focused subset of the shared Firefox Settings catalog."""

    resolved_catalog = settings_catalog or get_wizard_settings_catalog()
    sections = []
    known_preferences = []

    for section in resolved_catalog["sections"]:
        preference_section = dict(section["preferences"])
        section_known_preferences = _build_known_preferences(
            preference_section["id"],
            list(preference_section.get("presets") or []),
            list(preference_section.get("known_preferences") or []),
        )
        preference_section["known_preferences"] = section_known_preferences
        sections.append(preference_section)
        known_preferences.extend(section_known_preferences)

    return {
        "sections": sections,
        "known_preferences": known_preferences,
    }
