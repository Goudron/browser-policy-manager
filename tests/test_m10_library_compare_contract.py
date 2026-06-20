from __future__ import annotations

import json
from pathlib import Path

from tests.web_profiles_page_helpers import (
    css_source,
    static_source,
    template_source,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_library_rows_expose_permanent_delete_for_every_lifecycle_state():
    source = static_source("profiles_library_bootstrap.js")

    assert "hardDeleteProfile," in source
    assert 'data-library-lifecycle-action="hard-delete"' in source
    assert "danger-button library-row-secondary-action library-row-danger-action" in source
    assert 'li.querySelectorAll("[data-library-lifecycle-action]")' in source
    assert 'if (action === "hard-delete")' in source
    assert 't("profiles.confirm_hard_delete")' in source
    assert "await hardDeleteProfile(profile.id, windowRef.fetch);" in source
    assert 'setStatus(t("profiles.hard_delete_done"), "success");' in source
    assert "await reloadList();" in source
    assert 'setStatus(t("profiles.error_delete")' in source
    assert "actionButton.disabled = true;" in source
    assert 'actionButton?.setAttribute("aria-busy", "true");' in source

    delete_button = source.split('data-library-lifecycle-action="hard-delete"', 1)[0]
    lifecycle_branch = delete_button.rsplit("${profile.is_deleted ?", 1)[-1]
    assert "hard-delete" not in lifecycle_branch


def test_permanent_delete_confirmation_is_irreversible_in_every_locale():
    expected_fragments = {
        "en": ("archive", "cannot be restored"),
        "ru": ("архив", "невозможно"),
        "de": ("Archiv", "nicht wiederhergestellt"),
        "fr": ("archive", "ne pourra pas être restauré"),
        "es-ES": ("archivo", "no se podrá restaurar"),
        "zh-CN": ("归档", "无法恢复"),
    }

    for locale, fragments in expected_fragments.items():
        catalog = json.loads(
            (REPO_ROOT / "app" / "i18n_src" / locale / "common.json").read_text(
                encoding="utf-8"
            )
        )
        confirmation = catalog["profiles.confirm_hard_delete"]
        assert all(fragment in confirmation for fragment in fragments)


def test_compare_header_has_no_return_action_or_dead_command_column():
    template = template_source("_page_compare_workspace.html")
    css = css_source()

    assert 'class="compare-route-heading"' in template
    assert 'href="/profiles"' not in template
    assert "profiles.compare_back_to_library" not in template
    assert "profiles.compare_back_to_library" not in static_source("profiles_compare.js")
    assert ".compare-route-heading {" in css
    assert "grid-template-columns: minmax(0, 1fr);" in css
    assert "profiles.compare_back_to_library" not in (
        REPO_ROOT / "app" / "i18n_src" / "catalog-order.json"
    ).read_text(encoding="utf-8")
