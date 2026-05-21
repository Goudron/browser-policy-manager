from __future__ import annotations

from typing import Any

from .serializer import humanize_identifier

FIELD_LABEL_KEYS = {
    "Add": "profiles.schema_field_add",
    "Additional": "profiles.schema_field_additional",
    "Alias": "profiles.schema_field_alias",
    "Allow": "profiles.schema_field_allow",
    "AllowNonFQDN": "profiles.schema_field_allow_non_fqdn",
    "AllowProxies": "profiles.schema_field_allow_proxies",
    "AutoConfigURL": "profiles.schema_field_auto_config_url",
    "AutoLogin": "profiles.schema_field_auto_login",
    "Autoplay": "profiles.schema_field_autoplay",
    "Block": "profiles.schema_field_block",
    "BlockNewRequests": "profiles.schema_field_block_new_requests",
    "Cache": "profiles.schema_field_cache",
    "Camera": "profiles.schema_field_camera",
    "Chatbot": "profiles.schema_field_chatbot",
    "Cookies": "profiles.schema_field_cookies",
    "Default": "profiles.schema_field_default",
    "Delegated": "profiles.schema_field_delegated",
    "Description": "profiles.schema_field_description",
    "Enabled": "profiles.schema_field_enabled",
    "Exceptions": "profiles.schema_field_exceptions",
    "ExcludedDomains": "profiles.schema_field_excluded_domains",
    "ExtensionRecommendations": "profiles.schema_field_extension_recommendations",
    "Extensions": "profiles.schema_field_extensions",
    "FTPProxy": "profiles.schema_field_ftp_proxy",
    "Fallback": "profiles.schema_field_fallback",
    "Favicon": "profiles.schema_field_favicon",
    "FeatureRecommendations": "profiles.schema_field_feature_recommendations",
    "FirefoxLabs": "profiles.schema_field_firefox_labs",
    "Folder": "profiles.schema_field_folder",
    "FormData": "profiles.schema_field_form_data",
    "HTTPProxy": "profiles.schema_field_http_proxy",
    "Highlights": "profiles.schema_field_highlights",
    "History": "profiles.schema_field_history",
    "IconURL": "profiles.schema_field_icon_url",
    "ImportEnterpriseRoots": "profiles.schema_field_import_enterprise_roots",
    "ImproveSuggest": "profiles.schema_field_improve_suggest",
    "Install": "profiles.schema_field_install",
    "LinkPreviewKeyPoints": "profiles.schema_field_link_preview_key_points",
    "LinkPreviews": "profiles.schema_field_link_previews",
    "Location": "profiles.schema_field_location",
    "Locked": "profiles.schema_field_locked",
    "Method": "profiles.schema_field_method",
    "Microphone": "profiles.schema_field_microphone",
    "Mode": "profiles.schema_field_mode",
    "MoreFromMozilla": "profiles.schema_field_more_from_mozilla",
    "NTLM": "profiles.schema_field_ntlm",
    "Name": "profiles.schema_field_name",
    "Notifications": "profiles.schema_field_notifications",
    "PDFAltText": "profiles.schema_field_pdf_alt_text",
    "Passthrough": "profiles.schema_field_passthrough",
    "Placement": "profiles.schema_field_placement",
    "Pocket": "profiles.schema_field_pocket",
    "PostData": "profiles.schema_field_post_data",
    "PreventInstalls": "profiles.schema_field_prevent_installs",
    "PrivateBrowsing": "profiles.schema_field_private_browsing",
    "ProviderURL": "profiles.schema_field_provider_url",
    "Remove": "profiles.schema_field_remove",
    "SOCKSProxy": "profiles.schema_field_socks_proxy",
    "SOCKSVersion": "profiles.schema_field_socks_version",
    "SPNEGO": "profiles.schema_field_spnego",
    "SSLProxy": "profiles.schema_field_ssl_proxy",
    "ScreenShare": "profiles.schema_field_screen_share",
    "Search": "profiles.schema_field_search",
    "Sessions": "profiles.schema_field_sessions",
    "SidebarChatbot": "profiles.schema_field_sidebar_chatbot",
    "SiteSettings": "profiles.schema_field_site_settings",
    "SkipOnboarding": "profiles.schema_field_skip_onboarding",
    "SmartTabGroups": "profiles.schema_field_smart_tab_groups",
    "SmartWindow": "profiles.schema_field_smart_window",
    "Snippets": "profiles.schema_field_snippets",
    "SponsoredPocket": "profiles.schema_field_sponsored_pocket",
    "SponsoredStories": "profiles.schema_field_sponsored_stories",
    "SponsoredSuggestions": "profiles.schema_field_sponsored_suggestions",
    "SponsoredTopSites": "profiles.schema_field_sponsored_top_sites",
    "StartPage": "profiles.schema_field_start_page",
    "Stories": "profiles.schema_field_stories",
    "SuggestURLTemplate": "profiles.schema_field_suggest_url_template",
    "TabGroups": "profiles.schema_field_tab_groups",
    "Title": "profiles.schema_field_title",
    "TopSites": "profiles.schema_field_top_sites",
    "Translations": "profiles.schema_field_translations",
    "URL": "profiles.schema_field_url",
    "URLTemplate": "profiles.schema_field_url_template",
    "Uninstall": "profiles.schema_field_uninstall",
    "UrlbarInterventions": "profiles.schema_field_urlbar_interventions",
    "UseHTTPProxyForAllProtocols": "profiles.schema_field_use_http_proxy_for_all_protocols",
    "UseProxyForDNS": "profiles.schema_field_use_proxy_for_dns",
    "Value": "profiles.schema_field_value",
    "VirtualReality": "profiles.schema_field_virtual_reality",
    "WebSuggestions": "profiles.schema_field_web_suggestions",
    "allowed_types": "profiles.schema_field_allowed_types",
    "blocked_install_message": "profiles.schema_field_blocked_install_message",
    "children": "profiles.schema_field_children",
    "default_area": "profiles.schema_field_default_area",
    "install_sources": "profiles.schema_field_install_sources",
    "install_url": "profiles.schema_field_install_url",
    "installation_mode": "profiles.schema_field_installation_mode",
    "name": "profiles.schema_field_bookmark_name",
    "private_browsing": "profiles.schema_field_private_browsing",
    "restricted_domains": "profiles.schema_field_restricted_domains",
    "temporarily_allow_weak_signatures": "profiles.schema_field_temporarily_allow_weak_signatures",
    "toplevel_name": "profiles.schema_field_toplevel_name",
    "updates_disabled": "profiles.schema_field_updates_disabled",
    "url": "profiles.schema_field_bookmark_url",
}

INLINE_EDITOR_POLICY_IDS = {
    "AIControls",
    "AppAutoUpdate",
    "Authentication",
    "BlockAboutConfig",
    "BlockAboutProfiles",
    "Bookmarks",
    "Certificates",
    "Cookies",
    "DNSOverHTTPS",
    "DisableAppUpdate",
    "DisableBuiltinPDFViewer",
    "DisableDeveloperTools",
    "DisableFirefoxAccounts",
    "DisableFirefoxStudies",
    "DisablePocket",
    "DisablePrivateBrowsing",
    "DisableSystemAddonUpdate",
    "DisableTelemetry",
    "DontCheckDefaultBrowser",
    "ExtensionSettings",
    "GenerativeAI",
    "FirefoxHome",
    "FirefoxSuggest",
    "Handlers",
    "Homepage",
    "IPProtectionAvailable",
    "InstallAddonsPermission",
    "ManagedBookmarks",
    "NewTabPage",
    "OfferToSaveLogins",
    "OverrideFirstRunPage",
    "OverridePostUpdatePage",
    "PasswordManagerEnabled",
    "Permissions",
    "PromptForDownloadLocation",
    "Proxy",
    "RequestedLocales",
    "SanitizeOnShutdown",
    "SearchBar",
    "SearchEngines",
    "SearchSuggestEnabled",
    "TranslateEnabled",
    "UserMessaging",
    "VisualSearchEnabled",
    "WebsiteFilter",
    "WindowsSSO",
    "HttpsOnlyMode",
}


def build_inline_editor(definition) -> dict[str, Any] | None:
    if definition.id not in INLINE_EDITOR_POLICY_IDS:
        return None

    if definition.id == "SanitizeOnShutdown":
        return _build_branch_inline_editor(definition)

    if definition.additional_property_type == "object" and definition.additional_property_properties:
        return _build_dictionary_inline_editor(definition)

    if definition.type == "array" and definition.items_type == "object":
        return _build_array_inline_editor(definition)

    if definition.type == "boolean":
        return {
            "kind": "boolean-select",
            "managed_fields": [],
        }

    if definition.type == "string":
        return {
            "kind": "enum-select" if definition.enum else "text",
            "enum": list(definition.enum or []),
            "managed_fields": [],
        }

    if definition.type in {"integer", "number"}:
        return {
            "kind": "number",
            "managed_fields": [],
        }

    if definition.type != "object":
        return None

    fields: list[dict[str, Any]] = []
    unsupported_count = 0
    managed_fields: list[str] = []

    for prop_name, prop in definition.properties.items():
        field_spec = _build_object_field_spec(prop)
        if field_spec is None:
            unsupported_count += 1
            continue

        managed_fields.append(prop_name)
        fields.append(
            {
                "name": prop_name,
                "label": humanize_identifier(prop_name),
                "label_key": _field_label_key(prop_name),
                **field_spec,
            }
        )

    if not fields:
        return None

    return {
        "kind": "object-card",
        "managed_fields": managed_fields,
        "fields": fields,
        "unsupported_field_count": unsupported_count,
    }


def _resolve_field_kind(prop) -> str | None:
    if prop.type == "boolean":
        return "boolean-select"
    if prop.type == "string":
        return "enum-select" if prop.enum else "text"
    if prop.type in {"integer", "number"}:
        return "number"
    if prop.type == "array" and prop.items_type == "string":
        return "string-list"
    if (
        prop.type == "object"
        and prop.additional_property_type == "boolean"
        and prop.additional_property_enum == [True]
    ):
        return "true-map"
    return None


def _build_object_field_spec(prop, *, allow_nested: bool = True) -> dict[str, Any] | None:
    field_kind = _resolve_field_kind(prop)
    if field_kind is not None:
        return {
            "kind": field_kind,
            "required": prop.required,
            "enum": list(prop.enum or []),
        }

    if allow_nested and prop.type == "object" and prop.properties:
        fields: list[dict[str, Any]] = []
        managed_fields: list[str] = []
        unsupported_count = 0

        for child_name, child_prop in prop.properties.items():
            child_spec = _build_object_field_spec(child_prop, allow_nested=True)
            if child_spec is None:
                unsupported_count += 1
                continue

            managed_fields.append(child_name)
            fields.append(
                {
                    "name": child_name,
                    "label": humanize_identifier(child_name),
                    "label_key": _field_label_key(child_name),
                    **child_spec,
                }
            )

        if fields:
            return {
                "kind": "nested-object",
                "managed_fields": managed_fields,
                "fields": fields,
                "unsupported_field_count": unsupported_count,
                "required": prop.required,
                "enum": list(prop.enum or []),
            }

    if allow_nested and prop.type == "object" and prop.additional_property_type == "object" and prop.additional_property_properties:
        nested_fields: list[dict[str, Any]] = []
        unsupported_count = 0

        for child_name, child_prop in prop.additional_property_properties.items():
            child_spec = _build_object_field_spec(child_prop, allow_nested=True)
            if child_spec is None:
                unsupported_count += 1
                continue

            nested_fields.append(
                {
                    "name": child_name,
                    "label": humanize_identifier(child_name),
                    "label_key": _field_label_key(child_name),
                    **child_spec,
                }
            )

        if nested_fields:
            return {
                "kind": "nested-dictionary-object",
                "fields": nested_fields,
                "unsupported_field_count": unsupported_count,
                "required": prop.required,
                "enum": list(prop.enum or []),
            }

    if allow_nested and prop.type == "array" and prop.items_type == "object" and prop.item_properties:
        array_item_fields: list[dict[str, Any]] = []
        unsupported_count = 0

        for child_name, child_prop in prop.item_properties.items():
            child_spec = _build_object_field_spec(child_prop, allow_nested=True)
            if child_spec is None:
                unsupported_count += 1
                continue

            array_item_fields.append(
                {
                    "name": child_name,
                    "label": humanize_identifier(child_name),
                    "label_key": _field_label_key(child_name),
                    **child_spec,
                }
            )

        if array_item_fields:
            return {
                "kind": "nested-array-of-objects",
                "fields": array_item_fields,
                "unsupported_field_count": unsupported_count,
                "required": prop.required,
                "enum": list(prop.enum or []),
            }

    return None


def _resolve_array_field_kind(prop) -> str | None:
    direct = _resolve_field_kind(prop)
    if direct is not None:
        return direct
    if prop.type in {"object", "array"}:
        return "json"
    return None


def _build_array_inline_editor(definition) -> dict[str, Any] | None:
    if not definition.item_properties:
        return None

    fields: list[dict[str, Any]] = []
    for prop_name, prop in definition.item_properties.items():
        field_kind = _resolve_array_field_kind(prop)
        if field_kind is None:
            continue
        fields.append(
            {
                "name": prop_name,
                "label": humanize_identifier(prop_name),
                "label_key": _field_label_key(prop_name),
                "kind": field_kind,
                "required": prop.required,
                "enum": list(prop.enum or []),
            }
        )

    if not fields:
        return None

    return {
        "kind": "array-of-objects",
        "fields": fields,
    }


def _build_dictionary_inline_editor(definition) -> dict[str, Any] | None:
    fields: list[dict[str, Any]] = []
    for prop_name, prop in definition.additional_property_properties.items():
        field_kind = _resolve_array_field_kind(prop)
        if field_kind is None:
            continue
        fields.append(
            {
                "name": prop_name,
                "label": humanize_identifier(prop_name),
                "label_key": _field_label_key(prop_name),
                "kind": field_kind,
                "required": prop.required,
                "enum": list(prop.enum or []),
            }
        )

    if not fields:
        return None

    return {
        "kind": "dictionary-object",
        "fields": fields,
    }


def _build_branch_inline_editor(definition) -> dict[str, Any] | None:
    if not definition.branches:
        return None

    branches: list[dict[str, Any]] = []
    for branch in definition.branches:
        if branch.type == "boolean":
            branches.append(
                {
                    "id": "boolean",
                    "kind": "boolean-select",
                }
            )
            continue

        if branch.type != "object":
            continue

        fields: list[dict[str, Any]] = []
        managed_fields: list[str] = []
        unsupported_count = 0
        for prop_name, prop in branch.properties.items():
            field_spec = _build_object_field_spec(prop)
            if field_spec is None:
                unsupported_count += 1
                continue

            managed_fields.append(prop_name)
            fields.append(
                {
                    "name": prop_name,
                    "label": humanize_identifier(prop_name),
                    "label_key": _field_label_key(prop_name),
                    **field_spec,
                }
            )

        branches.append(
            {
                "id": "object",
                "kind": "object-card",
                "managed_fields": managed_fields,
                "fields": fields,
                "unsupported_field_count": unsupported_count,
            }
        )

    return {"kind": "branch", "branches": branches}


def _field_label_key(name: str) -> str:
    return FIELD_LABEL_KEYS.get(name, "")
