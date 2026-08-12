"""Strict JSON and RFC 8785 helpers shared by conversion domain modules."""

from __future__ import annotations

import json
import math
from collections.abc import Mapping, Sequence
from typing import Any

type JsonScalar = str | int | float | bool | None
type JsonValue = JsonScalar | list[JsonValue] | dict[str, JsonValue]

MAX_SAFE_JSON_INTEGER = 9_007_199_254_740_991


class ProfileConversionJsonError(ValueError):
    """Input cannot be represented as strict I-JSON/JCS."""


def strict_json_copy(value: Any, ancestors: set[int] | None = None) -> JsonValue:
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, str):
        try:
            value.encode("utf-8")
        except UnicodeEncodeError as exc:
            raise ProfileConversionJsonError from exc
        return value
    if isinstance(value, int):
        if not -MAX_SAFE_JSON_INTEGER <= value <= MAX_SAFE_JSON_INTEGER:
            raise ProfileConversionJsonError
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ProfileConversionJsonError
        return value
    ancestors = set() if ancestors is None else ancestors
    if isinstance(value, Mapping):
        object_id = id(value)
        if object_id in ancestors:
            raise ProfileConversionJsonError
        descendants = {*ancestors, object_id}
        copied: dict[str, JsonValue] = {}
        for key in value:
            if not isinstance(key, str) or key in copied:
                raise ProfileConversionJsonError
            copied[strict_json_copy(key, descendants)] = strict_json_copy(value[key], descendants)  # type: ignore[index]
        return copied
    if isinstance(value, list):
        object_id = id(value)
        if object_id in ancestors:
            raise ProfileConversionJsonError
        descendants = {*ancestors, object_id}
        return [strict_json_copy(item, descendants) for item in value]
    raise ProfileConversionJsonError


def ordered_keys(value: Mapping[str, JsonValue]) -> list[str]:
    return sorted(value, key=lambda key: key.encode("utf-16-be"))


def canonical_json(value: JsonValue) -> bytes:
    if value is None:
        return b"null"
    if value is True:
        return b"true"
    if value is False:
        return b"false"
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False, allow_nan=False).encode("utf-8")
    if isinstance(value, int):
        return str(value).encode("ascii")
    if isinstance(value, float):
        return jcs_number(value).encode("ascii")
    if isinstance(value, list):
        return b"[" + b",".join(canonical_json(item) for item in value) + b"]"
    if isinstance(value, dict):
        return (
            b"{"
            + b",".join(
                canonical_json(key) + b":" + canonical_json(value[key])
                for key in ordered_keys(value)
            )
            + b"}"
        )
    raise ProfileConversionJsonError


def jcs_number(value: float) -> str:
    if not math.isfinite(value):
        raise ProfileConversionJsonError
    if value == 0:
        return "0"
    lexical = repr(value).lower()
    mantissa, separator, exponent_text = lexical.partition("e")
    exponent = int(exponent_text) if separator else 0
    absolute = abs(value)
    if 1e-6 <= absolute < 1e21:
        if separator:
            return expand_scientific(mantissa, exponent)
        return mantissa[:-2] if mantissa.endswith(".0") else mantissa
    if not separator:
        mantissa, exponent = scientific_from_fixed(mantissa)
    mantissa = mantissa[:-2] if mantissa.endswith(".0") else mantissa
    sign = "+" if exponent >= 0 else "-"
    return f"{mantissa}e{sign}{abs(exponent)}"


def expand_scientific(mantissa: str, exponent: int) -> str:
    sign = ""
    if mantissa.startswith("-"):
        sign, mantissa = "-", mantissa[1:]
    whole, _dot, fraction = mantissa.partition(".")
    digits = whole + fraction
    decimal_index = len(whole) + exponent
    if decimal_index <= 0:
        return sign + "0." + ("0" * -decimal_index) + digits
    if decimal_index >= len(digits):
        return sign + digits + ("0" * (decimal_index - len(digits)))
    return sign + digits[:decimal_index] + "." + digits[decimal_index:]


def scientific_from_fixed(value: str) -> tuple[str, int]:
    sign = ""
    if value.startswith("-"):
        sign, value = "-", value[1:]
    whole, _dot, fraction = value.partition(".")
    digits = (whole + fraction).lstrip("0")
    if not digits:
        return "0", 0
    if whole.lstrip("0"):
        exponent = len(whole.lstrip("0")) - 1
    else:
        exponent = -(len(fraction) - len(fraction.lstrip("0")) + 1)
    remainder = digits[1:].rstrip("0")
    return sign + digits[0] + ("." + remainder if remainder else ""), exponent


def pointer(parts: Sequence[str | int]) -> str:
    return "/" + "/".join(escape_pointer_part(str(part)) for part in parts)


def escape_pointer_part(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")
