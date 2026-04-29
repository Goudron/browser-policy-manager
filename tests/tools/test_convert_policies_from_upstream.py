from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_module():
    module_path = Path(__file__).resolve().parents[2] / "tools" / "convert_policies_from_upstream.py"
    spec = importlib.util.spec_from_file_location("bpm_convert_policies", module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_prepare_json_like_snippet_parses_union_expressions():
    module = _load_module()
    snippet = """
    {
      "policies": {
        "Proxy": {
          "Mode": "none" | "system" | "manual",
          "Locked": true | false,
          "SOCKSVersion": 4 | 5
        }
      }
    }
    """

    value = module._extract_policy_value_node("Proxy", snippet)

    assert value["Mode"] == {"__bpm_enum__": ["none", "system", "manual"]}
    assert value["Locked"] == {"__bpm_enum__": [True, False]}
    assert value["SOCKSVersion"] == {"__bpm_enum__": [4, 5]}


def test_infer_schema_from_example_value_handles_arrays_of_objects_and_enums():
    module = _load_module()
    snippet = """
    {
      "policies": {
        "SearchEngines": {
          "Add": [
            {
              "Name": "Example1",
              "Method": "GET" | "POST"
            }
          ],
          "PreventInstalls": true | false
        }
      }
    }
    """

    value = module._extract_policy_value_node("SearchEngines", snippet)
    inferred = module.infer_schema_from_example_value(value)

    assert inferred["type"] == "object"
    add_schema = inferred["properties"]["Add"]
    assert add_schema["type"] == "array"
    assert add_schema["items"]["type"] == "object"
    assert add_schema["items"]["properties"]["Method"]["enum"] == ["GET", "POST"]
    assert inferred["properties"]["PreventInstalls"]["type"] == "boolean"


def test_infer_schema_from_example_value_marks_dynamic_maps():
    module = _load_module()
    snippet = """
    {
      "policies": {
        "Preferences": {
          "browser.tabs.warnOnClose": {
            "Value": true | false,
            "Status": "locked" | "user"
          }
        }
      }
    }
    """

    value = module._extract_policy_value_node("Preferences", snippet)
    inferred = module.infer_schema_from_example_value(value)

    assert inferred["type"] == "object"
    assert inferred["properties"] == {}
    assert inferred["additional_properties"] is True
    dynamic_value = inferred["additional_properties_schema"]
    assert dynamic_value["type"] == "object"
    assert dynamic_value["properties"]["Value"]["type"] == "boolean"
    assert dynamic_value["properties"]["Status"]["enum"] == ["locked", "user"]


def test_build_schema_policy_prefers_linux_policy_examples():
    module = _load_module()
    entry = module.UpstreamPolicyEntry(
        name="Containers",
        policy_key="Containers",
        description="Containers",
        compatibility="Compatibility: Firefox 113",
        section_text=None,
        policies_json_snippet=None,
    )
    linux_policy_examples = {
        "Containers": {
            "Default": [
                {
                    "name": "My container",
                    "icon": "pet",
                    "color": "turquoise",
                }
            ]
        }
    }

    policy = module.build_schema_policy(entry, linux_policy_examples=linux_policy_examples)

    assert policy.type == "object"
    default_prop = policy.properties["Default"]
    assert default_prop["type"] == "array"
    assert default_prop["items"]["type"] == "object"
    assert default_prop["items"]["properties"]["icon"]["type"] == "string"
    assert policy.additional_properties is False


def test_build_schema_policy_special_cases_preferences_with_richer_entry_schema():
    module = _load_module()
    entry = module.UpstreamPolicyEntry(
        name="Preferences",
        policy_key="Preferences",
        description="Managed preferences",
        compatibility="Compatibility: Firefox 81, Firefox ESR 78.3",
        section_text=None,
        policies_json_snippet=None,
    )

    policy = module.build_schema_policy(entry, linux_policy_examples={})

    assert policy.type == "object"
    assert policy.additional_properties is True
    entry_schema = policy.additional_properties_schema
    assert entry_schema["properties"]["Status"]["enum"] == ["default", "locked", "user", "clear"]
    assert entry_schema["properties"]["Type"]["enum"] == ["number", "boolean", "string"]
    assert entry_schema["properties"]["Value"]["oneOf"] == [
        {"type": "boolean"},
        {"type": "number"},
        {"type": "string"},
    ]
    assert len(entry_schema["allOf"]) == 3


def test_schema_to_json_schema_emits_raw_json_schema_bundle():
    module = _load_module()
    policy = module.SchemaPolicyDefinition(
        id="DisableTelemetry",
        type="boolean",
        description_key="policy.DisableTelemetry",
        categories=["privacy"],
        min_version="60.0",
        max_version=None,
        deprecated=False,
        enum=None,
        items_type=None,
        items=None,
        properties={},
        additional_properties=True,
        additional_properties_schema=None,
    )

    schema = module.schema_to_json_schema(
        channel="release-150",
        version="149.0",
        source="test-fixture",
        policies=[policy],
    )

    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["x-bpm-channel"] == "release-150"
    assert schema["x-bpm-version"] == "149.0"
    assert schema["x-bpm-source"] == "test-fixture"
    assert schema["properties"]["DisableTelemetry"]["type"] == "boolean"
    assert schema["properties"]["DisableTelemetry"]["x-bpm-description-key"] == "policy.DisableTelemetry"


def test_build_schema_policy_marks_required_fields_from_section_text():
    module = _load_module()
    entry = module.UpstreamPolicyEntry(
        name="SearchEngines",
        policy_key="SearchEngines",
        description="Search engines",
        compatibility="Compatibility: Firefox 139, Firefox ESR 60",
        section_text=(
            "Name is the name of the search engine. (Required) "
            "URLTemplate is the search URL with {searchTerms}. (Required) "
            "Method is either GET or POST."
        ),
        policies_json_snippet="""
        {
          "policies": {
            "SearchEngines": {
              "Add": [
                {
                  "Name": "Example1",
                  "URLTemplate": "https://www.example.org/q={searchTerms}",
                  "Method": "GET"
                }
              ]
            }
          }
        }
        """,
    )

    policy = module.build_schema_policy(entry, linux_policy_examples={})
    add_item = policy.properties["Add"]["items"]

    assert add_item["properties"]["Name"]["required"] is True
    assert add_item["properties"]["URLTemplate"]["required"] is True
    assert add_item["properties"]["Method"].get("required", False) is False


def test_build_schema_policy_applies_semantic_hints_for_patterns_and_enums():
    module = _load_module()

    search_entry = module.UpstreamPolicyEntry(
        name="SearchEngines",
        policy_key="SearchEngines",
        description="Search engines",
        compatibility="Compatibility: Firefox 139, Firefox ESR 60",
        section_text="",
        policies_json_snippet="""
        {
          "policies": {
            "SearchEngines": {
              "Add": [
                {
                  "Name": "Example1",
                  "URLTemplate": "https://www.example.org/q={searchTerms}",
                  "SuggestURLTemplate": "https://www.example.org/suggestions/q={searchTerms}"
                }
              ]
            }
          }
        }
        """,
    )
    search_policy = module.build_schema_policy(search_entry, linux_policy_examples={})
    add_item = search_policy.properties["Add"]["items"]
    assert add_item["properties"]["URLTemplate"]["pattern"] == r"\{searchTerms\}"
    assert add_item["properties"]["SuggestURLTemplate"]["pattern"] == r"\{searchTerms\}"

    cookies_entry = module.UpstreamPolicyEntry(
        name="Cookies",
        policy_key="Cookies",
        description="Cookies",
        compatibility="Compatibility: Firefox 60, Firefox ESR 60",
        section_text="",
        policies_json_snippet="""
        {
          "policies": {
            "Cookies": {
              "Allow": ["https://example.org"],
              "Block": ["https://example.edu"]
            }
          }
        }
        """,
    )
    cookies_policy = module.build_schema_policy(cookies_entry, linux_policy_examples={})
    assert cookies_policy.properties["Allow"]["items"]["pattern"] == r"^https?://"

    handlers_entry = module.UpstreamPolicyEntry(
        name="Handlers",
        policy_key="Handlers",
        description="Handlers",
        compatibility="Compatibility: Firefox 78, Firefox ESR 78",
        section_text="",
        policies_json_snippet="""
        {
          "policies": {
            "Handlers": {
              "schemes": {
                "mailto": {
                  "action": "useHelperApp",
                  "handlers": [
                    {
                      "name": "Gmail",
                      "uriTemplate": "https://mail.google.com/mail/?extsrc=mailto&url=%s"
                    }
                  ]
                }
              }
            }
          }
        }
        """,
    )
    handlers_policy = module.build_schema_policy(handlers_entry, linux_policy_examples={})
    mailto = handlers_policy.properties["schemes"]["properties"]["mailto"]
    assert mailto["properties"]["action"]["enum"] == ["saveToDisk", "useHelperApp", "useSystemDefault"]
    handler_item = mailto["properties"]["handlers"]["items"]
    assert handler_item["properties"]["uriTemplate"]["pattern"] == r"^https://.*%s.*$"


def test_extract_policy_value_node_handles_trailing_commas_and_regex_strings():
    module = _load_module()
    snippet = r'''
    {
      "policies": {
        "ContentAnalysis": {
          "AllowUrlRegexList": "https://example\.com/.*",
          "DefaultResult": 0 | 1 | 2,
          "InterceptionPoints": {
            "Download": {
              "Enabled": false | true,
            },
          },
        }
      }
    }
    '''

    value = module._extract_policy_value_node("ContentAnalysis", snippet)

    assert value["AllowUrlRegexList"] == r"https://example\.com/.*"
    assert value["DefaultResult"] == {"__bpm_enum__": [0, 1, 2]}
    assert value["InterceptionPoints"]["Download"]["Enabled"] == {"__bpm_enum__": [False, True]}


def test_extract_policy_value_nodes_returns_multiple_forms_from_combined_snippet():
    module = _load_module()
    snippet = """
    {
      "policies": {
        "RequestedLocales": ["de", "en-US"]
      }
    }

    or

    {
      "policies": {
        "RequestedLocales": "de,en-US"
      }
    }
    """

    values = module._extract_policy_value_nodes("RequestedLocales", snippet)

    assert values == [["de", "en-US"], "de,en-US"]


def test_build_schema_policy_uses_one_of_for_multiple_top_level_forms():
    module = _load_module()
    entry = module.UpstreamPolicyEntry(
        name="RequestedLocales",
        policy_key="RequestedLocales",
        description="Requested locales",
        compatibility="Compatibility: Firefox 64, Firefox ESR 60.4",
        section_text="",
        policies_json_snippet="""
        {
          "policies": {
            "RequestedLocales": ["de", "en-US"]
          }
        }

        or

        {
          "policies": {
            "RequestedLocales": "de,en-US"
          }
        }
        """,
    )

    policy = module.build_schema_policy(entry, linux_policy_examples={})
    schema = module._policy_definition_to_json_schema(policy)

    assert policy.id == "RequestedLocales"
    assert "oneOf" in schema
    branch_types = {branch.get("type") for branch in schema["oneOf"]}
    assert branch_types == {"array", "string"}
    array_branch = next(branch for branch in schema["oneOf"] if branch.get("type") == "array")
    assert array_branch["items"] == {"type": "string"}


def test_merge_variant_entries_combines_policies_under_same_policy_key():
    module = _load_module()
    entries = [
        module.UpstreamPolicyEntry(
            name="SanitizeOnShutdown(All)",
            policy_key="SanitizeOnShutdown",
            description="All",
            compatibility="Compatibility: Firefox 60, Firefox ESR 60",
            section_text="all variant",
            policies_json_snippet='{"policies":{"SanitizeOnShutdown": true}}',
        ),
        module.UpstreamPolicyEntry(
            name="SanitizeOnShutdown(Selective)",
            policy_key="SanitizeOnShutdown",
            description="Selective",
            compatibility="Compatibility: Firefox 68, Firefox ESR 68",
            section_text="selective variant",
            policies_json_snippet='{"policies":{"SanitizeOnShutdown":{"Cache": true}}}',
        ),
    ]

    merged = module._merge_variant_entries(entries)

    assert len(merged) == 1
    assert merged[0].policy_key == "SanitizeOnShutdown"
    assert "or" in (merged[0].policies_json_snippet or "")


def test_merge_array_item_schemas_does_not_turn_samples_into_enum():
    module = _load_module()

    merged = module._merge_array_item_schemas(
        [
            {"type": "string", "default": "de"},
            {"type": "string", "default": "en-US"},
        ]
    )

    assert merged == {"type": "string"}


def test_build_schema_policy_applies_property_table_hints_for_dynamic_extension_settings():
    module = _load_module()
    entry = module.UpstreamPolicyEntry(
        name="ExtensionSettings",
        policy_key="ExtensionSettings",
        description="Extension settings",
        compatibility="Compatibility: Firefox 69, Firefox ESR 68.1",
        section_text="",
        policies_json_snippet="""
        {
          "policies": {
            "ExtensionSettings": {
              "*": {
                "installation_mode": "allowed",
                "allowed_types": ["extension"]
              }
            }
          }
        }
        """,
        property_descriptions={
            "installation_mode": "Maps to a string indicating the installation mode for the extension. The valid strings are allowed, blocked, force_installed, and normal_installed.",
            "allowed_types": 'Restricts which types of add-ons can be installed. Accepts a list of one or more of: "extension", "theme", "dictionary", "locale".',
            "default_area": "String that indicates where to place the extension icon by default. Possible values are navbar and menupanel.",
            "private_browsing": "A boolean that indicates whether or not this extension should be enabled in private browsing.",
        },
    )

    policy = module.build_schema_policy(entry, linux_policy_examples={})
    entry_schema = policy.additional_properties_schema

    assert entry_schema["properties"]["installation_mode"]["enum"] == [
        "allowed",
        "blocked",
        "force_installed",
        "normal_installed",
    ]
    assert entry_schema["properties"]["allowed_types"]["items"]["enum"] == [
        "extension",
        "theme",
        "dictionary",
        "locale",
    ]
    assert entry_schema["properties"]["default_area"]["enum"] == ["navbar", "menupanel"]
    assert entry_schema["properties"]["private_browsing"]["type"] == "boolean"


def test_build_schema_policy_applies_numeric_bounds_from_property_descriptions():
    module = _load_module()
    entry = module.UpstreamPolicyEntry(
        name="ExamplePolicy",
        policy_key="ExamplePolicy",
        description="Example",
        compatibility="Compatibility: Firefox 100",
        section_text="",
        policies_json_snippet="""
        {
          "policies": {
            "ExamplePolicy": {
              "TimeoutSeconds": 30,
              "Retries": [1, 2]
            }
          }
        }
        """,
        property_descriptions={
            "TimeoutSeconds": "Integer timeout value that must be between 10 and 300.",
            "Retries": "An array of integers with values from 1 to 5.",
        },
    )

    policy = module.build_schema_policy(entry, linux_policy_examples={})

    assert policy.properties["TimeoutSeconds"]["minimum"] == 10
    assert policy.properties["TimeoutSeconds"]["maximum"] == 300
    assert policy.properties["Retries"]["items"]["minimum"] == 1
    assert policy.properties["Retries"]["items"]["maximum"] == 5


def test_extract_required_property_names_ignores_only_required_to_phrasing():
    module = _load_module()
    node = {
        "type": "object",
        "properties": {
            "Category": {"type": "string"},
            "BaselineExceptions": {"type": "boolean"},
            "ConvenienceExceptions": {"type": "boolean"},
            "Locked": {"type": "boolean"},
        },
        "additional_properties": False,
    }
    section_text = (
        "`Category` can be either `strict` or `standard`. "
        "If `ConvenienceExceptions` is true, Firefox will apply exceptions automatically "
        "that are only required to fix minor issues and make convenience features available. "
        "If `Locked` is set to true, the defaults are used unless a different value is specified "
        "in policy for `BaselineExceptions` and `ConvenienceExceptions`."
    )

    required_names = module._extract_required_property_names(section_text, node)

    assert required_names == set()
