import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = REPO_ROOT / "app" / "static"
TEMPLATES_DIR = REPO_ROOT / "app" / "templates"
I18N_DIR = REPO_ROOT / "app" / "i18n"


def _read_locale(locale: str) -> dict[str, str]:
    return json.loads((I18N_DIR / f"{locale}.json").read_text(encoding="utf-8"))


def _runtime_source_files() -> list[Path]:
    return [
        *sorted(STATIC_DIR.glob("*.js")),
        *sorted(TEMPLATES_DIR.rglob("*.html")),
    ]


def _runtime_i18n_keys() -> set[str]:
    keys: set[str] = set()
    for path in _runtime_source_files():
        source = path.read_text(encoding="utf-8")
        keys.update(
            re.findall(r"""t\(\s*["'](profiles\.[A-Za-z0-9_.-]+)["']""", source)
        )
        keys.update(
            re.findall(
                r"""data-i18n(?:-[a-z-]+)?=["'](profiles\.[A-Za-z0-9_.-]+)["']""",
                source,
            )
        )
        keys.update(
            re.findall(r"""key:\s*["'](profiles\.[A-Za-z0-9_.-]+)["']""", source)
        )
    return keys


def test_runtime_i18n_keys_exist_in_supported_locales():
    runtime_keys = _runtime_i18n_keys()

    assert runtime_keys
    for locale in ("en", "ru"):
        catalog = _read_locale(locale)
        missing = sorted(runtime_keys - set(catalog))
        assert missing == []


def test_library_count_labels_are_locale_catalog_backed():
    platform_source = (STATIC_DIR / "profiles_platform.js").read_text(encoding="utf-8")
    workspace_source = (STATIC_DIR / "profiles_workspace.js").read_text(encoding="utf-8")
    library_source = (STATIC_DIR / "profiles_library_bootstrap.js").read_text(
        encoding="utf-8"
    )
    en_catalog = _read_locale("en")
    ru_catalog = _read_locale("ru")

    for key in (
        "profiles.library_count_one",
        "profiles.library_count_many",
    ):
        assert key in en_catalog
        assert key in ru_catalog
        assert key in platform_source

    assert "profiles.library_count_few" in ru_catalog
    assert "profiles.library_count_few" in platform_source
    assert "libraryCountLabel(total, getCurrentLang(), t)" in workspace_source
    assert "libraryCountLabel(total, getCurrentLang(), t)" in library_source
