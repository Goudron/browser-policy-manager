from __future__ import annotations

from app.web.firefox_wizard_shell import get_wizard_schema_shell_catalog


def test_wizard_schema_shell_catalog_exposes_steps_and_channels():
    catalog = get_wizard_schema_shell_catalog()

    assert [step["step"] for step in catalog["steps"]] == [2, 3, 4, 5, 6, 7, 8]
    assert set(catalog["channels"]) == {"esr-140.10", "release-150"}


def test_wizard_schema_shell_catalog_groups_real_policies_into_step_buckets():
    catalog = get_wizard_schema_shell_catalog()
    release_general = catalog["channels"]["release-150"]["steps"]["2"]
    release_search = catalog["channels"]["release-150"]["steps"]["4"]
    release_review = catalog["channels"]["release-150"]["steps"]["8"]

    general_recommended = {item["id"] for item in release_general["recommended"]}
    search_recommended = {item["id"] for item in release_search["recommended"]}

    assert "Proxy" in general_recommended
    assert "Authentication" in general_recommended
    assert "SearchEngines" in search_recommended
    assert release_general["preferences"][0]["id"] == "general"
    assert release_review["compatibility"]["raw_fallback"] >= 1


def test_wizard_schema_shell_catalog_marks_raw_fallback_items():
    catalog = get_wizard_schema_shell_catalog()
    review_items = catalog["channels"]["esr-140.10"]["steps"]["8"]["raw_fallback"]

    assert review_items
    assert all(item["support_level"] == "fallback" for item in review_items)
    assert all(item["target"].startswith("shell-policy:8:") for item in review_items)


def test_wizard_schema_shell_catalog_exposes_inline_editor_specs_for_phase_three_policies():
    catalog = get_wizard_schema_shell_catalog()
    step_two_items = (
        catalog["channels"]["release-150"]["steps"]["2"]["recommended"]
        + catalog["channels"]["release-150"]["steps"]["2"]["additional"]
    )
    step_three_items = (
        catalog["channels"]["release-150"]["steps"]["3"]["recommended"]
        + catalog["channels"]["release-150"]["steps"]["3"]["additional"]
        + catalog["channels"]["release-150"]["steps"]["3"]["raw_fallback"]
    )
    step_four_items = (
        catalog["channels"]["release-150"]["steps"]["4"]["recommended"]
        + catalog["channels"]["release-150"]["steps"]["4"]["additional"]
    )
    step_six_items = catalog["channels"]["release-150"]["steps"]["6"]["recommended"]

    by_id = {
        item["id"]: item
        for item in step_two_items + step_three_items + step_four_items + step_six_items
    }

    assert by_id["WindowsSSO"]["inline_editor"]["kind"] == "boolean-select"
    assert by_id["AppAutoUpdate"]["inline_editor"]["kind"] == "boolean-select"
    assert by_id["DisableAppUpdate"]["inline_editor"]["kind"] == "boolean-select"
    assert by_id["DisableSystemAddonUpdate"]["inline_editor"]["kind"] == "boolean-select"
    assert by_id["DontCheckDefaultBrowser"]["inline_editor"]["kind"] == "boolean-select"
    assert by_id["PromptForDownloadLocation"]["inline_editor"]["kind"] == "boolean-select"
    assert by_id["DNSOverHTTPS"]["inline_editor"]["kind"] == "object-card"
    assert by_id["Proxy"]["inline_editor"]["kind"] == "object-card"
    assert {field["name"] for field in by_id["Proxy"]["inline_editor"]["fields"]} >= {
        "Mode",
        "Locked",
        "HTTPProxy",
        "Passthrough",
        "AutoConfigURL",
    }
    assert by_id["Homepage"]["inline_editor"]["kind"] == "object-card"
    assert {field["name"] for field in by_id["Homepage"]["inline_editor"]["fields"]} >= {
        "StartPage",
        "URL",
        "Locked",
        "Additional",
    }
    assert by_id["FirefoxHome"]["inline_editor"]["kind"] == "object-card"
    assert by_id["FirefoxSuggest"]["inline_editor"]["kind"] == "object-card"
    assert by_id["SearchEngines"]["inline_editor"]["kind"] == "object-card"
    assert by_id["NewTabPage"]["inline_editor"]["kind"] == "boolean-select"
    assert {field["name"] for field in by_id["DNSOverHTTPS"]["inline_editor"]["fields"]} >= {
        "Enabled",
        "ProviderURL",
        "ExcludedDomains",
    }
    assert by_id["UserMessaging"]["inline_editor"]["kind"] == "object-card"
    assert by_id["WebsiteFilter"]["inline_editor"]["kind"] == "object-card"


def test_wizard_schema_shell_catalog_exposes_complex_inline_editor_specs_for_phase_five():
    catalog = get_wizard_schema_shell_catalog()
    step_two_items = (
        catalog["channels"]["release-150"]["steps"]["2"]["recommended"]
        + catalog["channels"]["release-150"]["steps"]["2"]["additional"]
    )
    step_five_items = catalog["channels"]["release-150"]["steps"]["5"]["recommended"]

    by_id = {item["id"]: item for item in step_two_items + step_five_items}

    authentication = by_id["Authentication"]["inline_editor"]
    sanitize = by_id["SanitizeOnShutdown"]["inline_editor"]

    assert authentication["kind"] == "object-card"
    assert {field["name"] for field in authentication["fields"]} >= {"SPNEGO", "AllowProxies", "PrivateBrowsing"}
    assert next(field for field in authentication["fields"] if field["name"] == "AllowProxies")["kind"] == "true-map"

    assert sanitize["kind"] == "branch"
    assert {branch["id"] for branch in sanitize["branches"]} == {"boolean", "object"}
    object_branch = next(branch for branch in sanitize["branches"] if branch["id"] == "object")
    assert {field["name"] for field in object_branch["fields"]} >= {"Cache", "Cookies", "Locked"}


def test_wizard_schema_shell_catalog_exposes_nested_object_and_cookie_inline_editors():
    catalog = get_wizard_schema_shell_catalog()
    step_five_items = (
        catalog["channels"]["release-150"]["steps"]["5"]["recommended"]
        + catalog["channels"]["release-150"]["steps"]["5"]["additional"]
        + catalog["channels"]["release-150"]["steps"]["5"]["raw_fallback"]
    )
    by_id = {item["id"]: item for item in step_five_items}

    permissions = by_id["Permissions"]["inline_editor"]
    cookies = by_id["Cookies"]["inline_editor"]

    assert permissions["kind"] == "object-card"
    camera = next(field for field in permissions["fields"] if field["name"] == "Camera")
    autoplay = next(field for field in permissions["fields"] if field["name"] == "Autoplay")
    assert camera["kind"] == "nested-object"
    assert {field["name"] for field in camera["fields"]} >= {"Allow", "Block", "BlockNewRequests", "Locked"}
    assert next(field for field in camera["fields"] if field["name"] == "Allow")["kind"] == "string-list"
    assert next(field for field in camera["fields"] if field["name"] == "Locked")["kind"] == "boolean-select"
    assert autoplay["kind"] == "nested-object"
    assert next(field for field in autoplay["fields"] if field["name"] == "Default")["kind"] == "enum-select"

    assert cookies["kind"] == "object-card"
    assert {field["name"] for field in cookies["fields"]} >= {
        "Allow",
        "AllowSession",
        "Block",
        "Locked",
        "Behavior",
        "BehaviorPrivateBrowsing",
    }
    assert next(field for field in cookies["fields"] if field["name"] == "Allow")["kind"] == "string-list"
    assert next(field for field in cookies["fields"] if field["name"] == "Behavior")["kind"] == "enum-select"


def test_wizard_schema_shell_catalog_exposes_recursive_handler_inline_editor():
    catalog = get_wizard_schema_shell_catalog()
    step_six_items = (
        catalog["channels"]["release-150"]["steps"]["6"]["recommended"]
        + catalog["channels"]["release-150"]["steps"]["6"]["additional"]
        + catalog["channels"]["release-150"]["steps"]["6"]["raw_fallback"]
    )
    by_id = {item["id"]: item for item in step_six_items}

    handlers = by_id["Handlers"]["inline_editor"]

    assert handlers["kind"] == "object-card"
    mime_types = next(field for field in handlers["fields"] if field["name"] == "mimeTypes")
    schemes = next(field for field in handlers["fields"] if field["name"] == "schemes")
    assert mime_types["kind"] == "nested-dictionary-object"
    assert {field["name"] for field in mime_types["fields"]} >= {"action", "ask"}
    assert next(field for field in mime_types["fields"] if field["name"] == "action")["kind"] == "enum-select"
    assert schemes["kind"] == "nested-object"
    mailto = next(field for field in schemes["fields"] if field["name"] == "mailto")
    assert mailto["kind"] == "nested-object"
    handlers_field = next(field for field in mailto["fields"] if field["name"] == "handlers")
    assert handlers_field["kind"] == "nested-array-of-objects"
    assert {field["name"] for field in handlers_field["fields"]} >= {"name", "uriTemplate"}


def test_wizard_schema_shell_catalog_exposes_array_inline_editor_specs_for_phase_six():
    catalog = get_wizard_schema_shell_catalog()
    step_six_items = catalog["channels"]["release-150"]["steps"]["6"]["additional"]
    by_id = {item["id"]: item for item in step_six_items}

    bookmarks = by_id["Bookmarks"]["inline_editor"]
    managed_bookmarks = by_id["ManagedBookmarks"]["inline_editor"]

    assert bookmarks["kind"] == "array-of-objects"
    assert {field["name"] for field in bookmarks["fields"]} >= {"Title", "URL", "Placement"}
    assert next(field for field in bookmarks["fields"] if field["name"] == "Placement")["kind"] == "enum-select"

    assert managed_bookmarks["kind"] == "array-of-objects"
    assert {field["name"] for field in managed_bookmarks["fields"]} >= {"toplevel_name", "children"}
    assert next(field for field in managed_bookmarks["fields"] if field["name"] == "children")["kind"] == "json"


def test_wizard_schema_shell_catalog_exposes_dictionary_inline_editor_specs_for_phase_seven():
    catalog = get_wizard_schema_shell_catalog()
    step_six_items = (
        catalog["channels"]["release-150"]["steps"]["6"]["recommended"]
        + catalog["channels"]["release-150"]["steps"]["6"]["additional"]
    )
    by_id = {item["id"]: item for item in step_six_items}

    extension_settings = by_id["ExtensionSettings"]["inline_editor"]

    assert extension_settings["kind"] == "dictionary-object"
    assert {field["name"] for field in extension_settings["fields"]} >= {
        "allowed_types",
        "installation_mode",
        "install_url",
        "updates_disabled",
    }
    assert next(field for field in extension_settings["fields"] if field["name"] == "allowed_types") == {
        "name": "allowed_types",
        "label": "allowed types",
        "kind": "string-list",
        "required": False,
        "enum": ["extension", "theme", "dictionary", "locale", "sitepermission"],
    }
    assert next(field for field in extension_settings["fields"] if field["name"] == "installation_mode")["kind"] == "enum-select"
    assert next(field for field in extension_settings["fields"] if field["name"] == "install_url")["kind"] == "text"
    assert next(field for field in extension_settings["fields"] if field["name"] == "updates_disabled")["kind"] == "boolean-select"

    install_addons_permission = by_id["InstallAddonsPermission"]["inline_editor"]
    assert install_addons_permission["kind"] == "object-card"
    assert {field["name"] for field in install_addons_permission["fields"]} >= {"Allow", "Default"}
    assert next(field for field in install_addons_permission["fields"] if field["name"] == "Allow")["kind"] == "string-list"
    assert next(field for field in install_addons_permission["fields"] if field["name"] == "Default")["kind"] == "boolean-select"


def test_wizard_schema_shell_catalog_exposes_ai_inline_editors_on_step_seven():
    catalog = get_wizard_schema_shell_catalog()
    step_seven_items = (
        catalog["channels"]["release-150"]["steps"]["7"]["recommended"]
        + catalog["channels"]["release-150"]["steps"]["7"]["additional"]
    )
    by_id = {item["id"]: item for item in step_seven_items}

    ai_controls = by_id["AIControls"]["inline_editor"]
    generative_ai = by_id["GenerativeAI"]["inline_editor"]
    visual_search = by_id["VisualSearchEnabled"]["inline_editor"]

    assert ai_controls["kind"] == "object-card"
    assert {field["name"] for field in ai_controls["fields"]} >= {
        "Default",
        "Translations",
        "PDFAltText",
        "SmartTabGroups",
        "LinkPreviewKeyPoints",
        "SidebarChatbot",
        "SmartWindow",
    }
    default_field = next(field for field in ai_controls["fields"] if field["name"] == "Default")
    assert default_field["kind"] == "nested-object"
    assert {field["name"] for field in default_field["fields"]} == {"Value", "Locked"}

    assert generative_ai["kind"] == "object-card"
    assert {field["name"] for field in generative_ai["fields"]} >= {
        "Enabled",
        "Chatbot",
        "LinkPreviews",
        "TabGroups",
        "Locked",
    }
    assert next(field for field in generative_ai["fields"] if field["name"] == "Enabled")["kind"] == "boolean-select"

    assert visual_search["kind"] == "boolean-select"


def test_wizard_schema_shell_catalog_exposes_release_150_vpn_toggle_on_step_five():
    catalog = get_wizard_schema_shell_catalog()
    step_five_items = (
        catalog["channels"]["release-150"]["steps"]["5"]["recommended"]
        + catalog["channels"]["release-150"]["steps"]["5"]["additional"]
    )
    by_id = {item["id"]: item for item in step_five_items}

    assert by_id["IPProtectionAvailable"]["inline_editor"]["kind"] == "boolean-select"
