from __future__ import annotations

from typing import Any

from app.models.policy_schema import PolicyUiMetadata, PolicyUiSection

from .inference import infer_section, infer_widget, preserve_unknown_fields
from .overrides import POLICY_UI_OVERRIDES
from .sections import get_policy_ui_sections as _get_policy_ui_sections


def get_policy_ui_sections() -> list[PolicyUiSection]:
    """Return the ordered wizard sections used by the upcoming schema-driven UI."""

    return _get_policy_ui_sections()


def resolve_policy_ui_metadata(
    policy_id: str,
    policy_type: str,
    *,
    schema_node: dict[str, Any] | None = None,
) -> PolicyUiMetadata:
    """Resolve UI metadata for a policy using explicit mappings plus safe fallbacks."""

    override = POLICY_UI_OVERRIDES.get(policy_id)
    widget = infer_widget(policy_type, schema_node)

    if override is not None:
        return PolicyUiMetadata.model_validate(
            {
                **override,
                "widget": widget,
                "support_level": "mapped",
                "preserve_unknown_fields": preserve_unknown_fields(schema_node),
            }
        )

    section, subsection, tags = infer_section(policy_id)
    return PolicyUiMetadata(
        section=section,
        subsection=subsection,
        widget=widget,
        complexity="advanced",
        recommended=False,
        preserve_unknown_fields=preserve_unknown_fields(schema_node),
        support_level="fallback",
        tags=tags,
    )
