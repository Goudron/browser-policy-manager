# app/web/profile_navigation.py
# Shared URL and focus-target helpers for profile editor routes.

from __future__ import annotations

from urllib.parse import quote

from app.web.firefox_preferences import get_wizard_preferences_catalog
from app.web.firefox_settings_catalog import get_wizard_settings_catalog
from app.web.firefox_wizard_shell import get_wizard_schema_shell_catalog


def resolve_safe_profiles_return_url(raw_return_url: str | None) -> str | None:
    if not raw_return_url:
        return None
    if not raw_return_url.startswith("/profiles"):
        return None
    if raw_return_url.startswith("//") or "://" in raw_return_url:
        return None
    return raw_return_url


def resolve_focus_target(raw_focus_target: str | None) -> str | None:
    if not raw_focus_target:
        return None
    focus_target = raw_focus_target.strip()
    if not focus_target or len(focus_target) > 160:
        return None
    return focus_target


def resolve_include_deleted_flag(raw_include_deleted: str | None) -> bool:
    if raw_include_deleted is None:
        return False
    return raw_include_deleted.strip().lower() in {"1", "true", "yes", "on"}


def resolve_settings_shell_focus_step(
    focus_target: str | None,
    schema_version: str | None,
    wizard_schema_shell_catalog: dict[str, object] | None = None,
) -> int | None:
    normalized_focus = (focus_target or "").strip()
    if not normalized_focus:
        return None
    if normalized_focus == "settings-schema-shell-step-8":
        return 8
    if normalized_focus.startswith("shell-policy:"):
        parts = normalized_focus.split(":", 2)
        if len(parts) >= 3:
            try:
                return int(parts[1])
            except ValueError:
                return None
    if (
        normalized_focus in {"raw", "deprecated", "unknown"}
        or normalized_focus.startswith("raw:")
        or normalized_focus.startswith("deprecated:")
        or normalized_focus.startswith("unknown:")
    ):
        return 8
    if not normalized_focus.startswith("policy:") or not schema_version:
        return None

    policy_id = normalized_focus.split(":", 1)[1].strip()
    if not policy_id:
        return None

    shell_catalog = wizard_schema_shell_catalog or get_wizard_schema_shell_catalog(
        get_wizard_preferences_catalog(get_wizard_settings_catalog())
    )
    channels = shell_catalog.get("channels", {})
    if not isinstance(channels, dict):
        return None
    channel_data = channels.get(schema_version, {})
    if not isinstance(channel_data, dict):
        return None
    channel_steps = channel_data.get("steps", {})
    if not isinstance(channel_steps, dict):
        return None
    for step_key, step_data in channel_steps.items():
        if not isinstance(step_data, dict):
            continue
        items = [
            *(step_data.get("recommended") or []),
            *(step_data.get("additional") or []),
            *(step_data.get("raw_fallback") or []),
        ]
        if any(item.get("id") == policy_id for item in items if isinstance(item, dict)):
            try:
                return int(step_key)
            except (TypeError, ValueError):
                return None
    return None


def resolve_json_focus_target_from_settings_focus(
    focus_target: str | None,
) -> str | None:
    if not focus_target:
        return None
    normalized_focus = focus_target.strip()
    if not normalized_focus:
        return None
    if normalized_focus.startswith("policy:"):
        return normalized_focus
    if normalized_focus == "settings-schema-shell-step-8":
        return "raw"
    return None


def resolve_settings_focus_target_from_json_focus(
    focus_target: str | None,
) -> str | None:
    if not focus_target:
        return None
    normalized_focus = focus_target.strip()
    if not normalized_focus or normalized_focus == "editor":
        return None
    if normalized_focus.startswith("policy:"):
        return normalized_focus
    if (
        normalized_focus in {"details", "download", "context", "raw", "deprecated", "unknown"}
        or normalized_focus.startswith("raw:")
        or normalized_focus.startswith("deprecated:")
        or normalized_focus.startswith("unknown:")
    ):
        return "settings-schema-shell-step-8"
    return normalized_focus


def build_profile_json_href(
    profile_id: int,
    *,
    return_url: str | None = None,
    focus_target: str | None = None,
    include_deleted: bool = False,
) -> str:
    return _build_profile_mode_href(
        profile_id,
        "json",
        return_url=return_url,
        focus_target=focus_target,
        include_deleted=include_deleted,
    )


def build_profile_settings_href(
    profile_id: int,
    *,
    return_url: str | None = None,
    focus_target: str | None = None,
    include_deleted: bool = False,
) -> str:
    return _build_profile_mode_href(
        profile_id,
        "settings",
        return_url=return_url,
        focus_target=focus_target,
        include_deleted=include_deleted,
    )


def build_profile_route_path(
    profile_id: int,
    mode: str,
    *,
    include_deleted: bool = False,
) -> str:
    if mode == "settings":
        base_path = f"/profiles/{profile_id}/settings"
    elif mode == "json":
        base_path = f"/profiles/{profile_id}/json"
    else:
        base_path = f"/profiles/{profile_id}/edit"
    return f"{base_path}?include_deleted=true" if include_deleted else base_path


def _build_profile_mode_href(
    profile_id: int,
    mode: str,
    *,
    return_url: str | None = None,
    focus_target: str | None = None,
    include_deleted: bool = False,
) -> str:
    params: list[str] = []
    if include_deleted:
        params.append("include_deleted=true")
    if return_url:
        params.append(f"return={quote(return_url, safe='/')}")
    if focus_target:
        params.append(f"focus={quote(focus_target, safe=':-_')}")
    suffix = f"?{'&'.join(params)}" if params else ""
    return f"/profiles/{profile_id}/{mode}{suffix}"
