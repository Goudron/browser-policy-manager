import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
EN_SOURCE_PATH = REPO_ROOT / "app" / "i18n_src" / "en" / "settings.json"
EN_RUNTIME_PATH = REPO_ROOT / "app" / "i18n" / "en.json"

MODE_TITLE_KEYS = (
    "profiles.settings_mode_review",
    "profiles.settings_mode_configured",
    "profiles.settings_mode_catalog",
)
MODE_BODY_KEYS = (
    "profiles.settings_mode_review_body",
    "profiles.settings_mode_configured_body",
    "profiles.settings_mode_catalog_body",
)
INTERNAL_TERMS = (
    "schema",
    "inventory",
    "json",
    "raw",
    "mapped",
    "policy",
    "policies",
    "preference",
    "preferences",
)


def _source_catalog() -> dict[str, str]:
    return json.loads(EN_SOURCE_PATH.read_text(encoding="utf-8"))


def _runtime_catalog() -> dict[str, str]:
    return json.loads(EN_RUNTIME_PATH.read_text(encoding="utf-8"))


def _word_count(text: str) -> int:
    return len(text.replace(".", "").split())


def test_all_settings_mode_copy_is_short_task_oriented_and_runtime_synced():
    source_catalog = _source_catalog()
    runtime_catalog = _runtime_catalog()

    expected_bodies = {
        "profiles.settings_mode_review_body": "Fix items that need attention first.",
        "profiles.settings_mode_configured_body": "See what this profile applies.",
        "profiles.settings_mode_catalog_body": "Find any available setting.",
    }

    for key, expected in expected_bodies.items():
        assert source_catalog[key] == expected
        assert runtime_catalog[key] == expected
        assert _word_count(expected) <= 6
        assert expected.split()[0] in {"Fix", "See", "Find"}

    for key in MODE_TITLE_KEYS:
        assert _word_count(source_catalog[key]) <= 2
        assert runtime_catalog[key] == source_catalog[key]

    mode_copy = " ".join(source_catalog[key] for key in (*MODE_TITLE_KEYS, *MODE_BODY_KEYS)).lower()
    for term in INTERNAL_TERMS:
        assert term not in mode_copy
