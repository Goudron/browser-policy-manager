from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = ROOT / "documentation"
CONFIG_PATH = DOCUMENTATION_ROOT / "config/documentation-assistant-copy-0.9.3.json"

pytestmark = pytest.mark.docs_contract

_PLACEHOLDER = re.compile(r"\{([a-z_]+)\}")


def _contract() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def _leaf_paths(value: Any, path: tuple[str, ...] = ()) -> dict[tuple[str, ...], str]:
    if isinstance(value, dict):
        result: dict[tuple[str, ...], str] = {}
        for key, child in value.items():
            result.update(_leaf_paths(child, (*path, key)))
        return result
    assert isinstance(value, str)
    return {path: value}


def test_m10_03_has_complete_natural_catalog_parity_and_placeholder_parity() -> None:
    contract = _contract()
    catalog = contract["catalog"]
    english = _leaf_paths(catalog["en"])

    assert set(catalog) == set(contract["locales"])
    assert list(catalog["en"]["states"]) == contract["catalog_rules"]["state_ids"]
    for locale in contract["locales"]:
        leaves = _leaf_paths(catalog[locale])
        assert set(leaves) == set(english), locale
        for path, value in leaves.items():
            assert value.strip(), (locale, path)
            assert set(_PLACEHOLDER.findall(value)) == set(_PLACEHOLDER.findall(english[path])), (
                locale,
                path,
            )
        for state in catalog[locale]["states"].values():
            assert set(state) == {"title", "detail", "action"}
        template = contract["state_templates"][locale]
        assert set(template) == {"live", "aria"}
        assert set(_PLACEHOLDER.findall(template["live"])) == {"title", "detail"}
        assert set(_PLACEHOLDER.findall(template["aria"])) == {"title"}

    for locale in ("ru", "de", "zh-CN", "fr", "es-ES"):
        localized = _leaf_paths(catalog[locale])
        assert all(localized[path] != value for path, value in english.items()), locale
        assert catalog[locale]["dialogue"]["scope"] != catalog["en"]["dialogue"]["scope"]
        assert (
            catalog[locale]["dialogue"]["out_of_scope"] != catalog["en"]["dialogue"]["out_of_scope"]
        )
        assert catalog[locale]["web"]["privacy"] != catalog["en"]["web"]["privacy"]


def test_m10_03_expands_static_locale_files_without_enabling_the_assistant() -> None:
    from documentation.tools import build_docs

    contract = _contract()
    source = (DOCUMENTATION_ROOT / "buildlib/portal.py").read_text(encoding="utf-8")
    script = (DOCUMENTATION_ROOT / "assets/theme/bpm-docs-search.js").read_text(encoding="utf-8")
    theme = (DOCUMENTATION_ROOT / "assets/theme/bpm-docs.css").read_text(encoding="utf-8")

    assert "generate_assistant_copy_files(site_root)" in source
    assert '"assistant-copy.json"' in source
    assert "documentation-assistant/status" not in source
    assert "documentation-assistant/chat" not in source
    assert "documentation-assistant" not in script
    assistant_button_rule = theme.split(".bpm-docs-assistant-actions button {", 1)[1].split("}", 1)[
        0
    ]
    assert "min-inline-size: 0" in assistant_button_rule
    assert "overflow-wrap: anywhere" in assistant_button_rule
    assert (
        "overflow-wrap: anywhere"
        in theme.split(".bpm-docs-assistant-entry {", 1)[1].split("}", 1)[0]
    )
    assert "stack on narrow portals" in contract["visual_layout"]
    for locale in contract["locales"]:
        payload = build_docs._assistant_copy_payload(locale)
        assert payload["locale"] == locale
        assert payload["messages"]["states"]["ready"] == {
            **contract["catalog"][locale]["states"]["ready"],
            "live": (
                contract["state_templates"][locale]["live"].format(
                    **contract["catalog"][locale]["states"]["ready"]
                )
            ),
            "aria": (
                contract["state_templates"][locale]["aria"].format(
                    **contract["catalog"][locale]["states"]["ready"]
                )
            ),
        }
        assert (
            payload["messages"]["shell"]["assistant"]
            == build_docs.SHELL_LABELS[locale]["assistant"]
        )
