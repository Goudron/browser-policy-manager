from __future__ import annotations

from tests.web_profiles_page_helpers import static_source, template_source


def test_all_settings_configured_mode_domain_summary_contract_is_wired():
    settings_template = template_source("_page_settings_workspace.html")
    dom_source = static_source("profiles_dom.js")
    bootstrap_source = static_source("profiles_bootstrap_core.js")
    list_source = static_source("profiles_all_settings_list.js")
    css_source = static_source("profiles_css/21-settings.css")

    for snippet in (
        'id="all-settings-configured-summary"',
        'id="all-settings-source-filters"',
        "profiles.settings_configured_domains_label",
        "profiles.settings_source_filters_label",
    ):
        assert snippet in settings_template
    assert 'id="all-settings-category-summary"' not in settings_template
    assert "all-settings-state-summary" not in settings_template

    assert 'allSettingsCategorySummaryEl: byId("all-settings-category-summary")' not in dom_source
    assert 'allSettingsConfiguredSummaryEl: byId("all-settings-configured-summary")' in dom_source
    assert 'allSettingsSourceFiltersEl: byId("all-settings-source-filters")' in dom_source
    assert 'allSettingsSourceFilterButtons: all("[data-settings-source-filter]")' in dom_source
    assert "allSettingsCategorySummaryEl," not in bootstrap_source
    assert "allSettingsConfiguredSummaryEl," in bootstrap_source
    assert "allSettingsSourceFiltersEl," in bootstrap_source
    assert "allSettingsSourceFilterButtons," in bootstrap_source

    for snippet in (
        "function buildConfiguredDomainSummaries(entries)",
        "function buildCategorySummaries(entries)",
        "function renderDomainSummaryCards(container, summaries, snapshot, options = {})",
        "function renderConfiguredSummary()",
        "function updateSourceFilterButtons()",
        'snapshot.activeMode !== "configured"',
        "filterHiddenInMode(snapshot.activeFilter, snapshot.activeMode)",
        "data-settings-domain-card",
        "data-settings-domain-configured-count",
        "data-settings-domain-hidden-available-count",
        "data-settings-domain-attention-count",
        "data-settings-domain-mapped-count",
        "data-settings-domain-raw-count",
        "data-settings-domain-deprecated-count",
        "profiles.wizard_shell_badge_mapped",
        "profiles.wizard_shell_badge_raw",
        "profiles.wizard_shell_badge_deprecated",
        "data-settings-source-filter",
        "raw-fallback",
        "profiles.settings_configured_domain_configured",
        "profiles.settings_configured_domain_attention",
        "profiles.settings_configured_domain_available",
        "function sourceLabel(source)",
        "function entryAttentionBadges(entry)",
        "function renderEntryBadges(entry)",
        "data-settings-entry-state-badge",
        "data-settings-entry-category-badge",
        "data-settings-entry-source",
        "data-settings-entry-attention",
    ):
        assert snippet in list_source
    assert "source:cis" in settings_template

    for snippet in (
        ".all-settings-domain-summary",
        ".all-settings-domain-card",
        ".all-settings-domain-card-coverage",
        ".all-settings-domain-card-count.has-attention",
        ".all-settings-source-filter-bar",
        ".all-settings-source-filter-button",
        ".all-settings-list-badges",
        ".all-settings-list-badge",
        ".all-settings-list-badge.has-attention",
    ):
        assert snippet in css_source
