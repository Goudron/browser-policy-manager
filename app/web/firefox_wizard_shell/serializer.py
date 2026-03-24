from __future__ import annotations

from collections.abc import Callable
from typing import Any


def serialize_policy(
    definition,
    step: int,
    *,
    inline_editor_builder: Callable[[Any], dict[str, Any] | None],
) -> dict[str, Any]:
    ui = definition.ui
    assert ui is not None

    return {
        "id": definition.id,
        "label": humanize_identifier(definition.id),
        "description_key": definition.description_key,
        "subsection": ui.subsection,
        "subsection_label": humanize_identifier(ui.subsection),
        "widget": ui.widget,
        "complexity": ui.complexity,
        "deprecated": definition.deprecated,
        "preserve_unknown_fields": ui.preserve_unknown_fields,
        "support_level": ui.support_level,
        "tags": list(ui.tags),
        "target": f"shell-policy:{step}:{definition.id}",
        "inline_editor": inline_editor_builder(definition),
    }


def humanize_identifier(value: str) -> str:
    if not value:
        return ""

    pieces: list[str] = []
    current: list[str] = []
    for char in value:
        if char in {"_", "-", ":"}:
            if current:
                pieces.append("".join(current))
                current = []
            continue
        if current and char.isupper() and (current[-1].islower() or current[-1].isdigit()):
            pieces.append("".join(current))
            current = [char]
            continue
        current.append(char)
    if current:
        pieces.append("".join(current))

    return " ".join(piece for piece in pieces if piece)
