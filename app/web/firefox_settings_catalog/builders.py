from __future__ import annotations

from typing import Any

NO_VALUE = object()


def chip(chip_id: str, label_key: str, fallback: str) -> dict[str, str]:
    return {
        "id": chip_id,
        "label_key": label_key,
        "fallback": fallback,
    }


def doc_target(
    area_id: str,
    target: str,
    label_key: str,
    fallback: str,
) -> dict[str, str]:
    return {
        "area_id": area_id,
        "target": target,
        "label_key": label_key,
        "fallback": fallback,
    }


def preset(
    preset_id: str,
    pref: str,
    value: Any,
    status: str,
    value_type: str,
    label_key: str,
    description_key: str,
) -> dict[str, Any]:
    return {
        "id": preset_id,
        "pref": pref,
        "value": value,
        "status": status,
        "type": value_type,
        "label_key": label_key,
        "description_key": description_key,
    }


def known_pref(
    pref: str,
    fallback: str,
    description_fallback: str,
    *,
    value_type: str = "",
    status: str = "",
    value: Any = NO_VALUE,
    label_key: str = "",
    description_key: str = "",
    value_control: str = "",
    value_options: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    item = {
        "pref": pref,
        "label_key": label_key,
        "fallback": fallback,
        "description_key": description_key,
        "description_fallback": description_fallback,
        "type": value_type,
        "status": status,
    }
    if value_control:
        item["value_control"] = value_control
    if value_options:
        item["value_options"] = value_options
    if value is not NO_VALUE:
        item["value"] = value
    return item


def value_option(value: Any, fallback: str, label_key: str = "") -> dict[str, Any]:
    item = {
        "value": value,
        "fallback": fallback,
    }
    if label_key:
        item["label_key"] = label_key
    return item


def pref_doc(
    area_id: str,
    preset_id: str,
    label_key: str,
    fallback: str,
) -> dict[str, str]:
    return {
        "area_id": area_id,
        "target": f"preference-preset:{preset_id}",
        "label_key": label_key,
        "fallback": fallback,
    }


def bundle_item(
    pref: str,
    value: Any,
    status: str,
    value_type: str,
) -> dict[str, Any]:
    return {
        "pref": pref,
        "value": value,
        "status": status,
        "type": value_type,
    }


def pref_bundle(
    bundle_id: str,
    area_id: str,
    label_key: str,
    description_key: str,
    items: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "id": bundle_id,
        "area_id": area_id,
        "label_key": label_key,
        "description_key": description_key,
        "items": items,
    }
