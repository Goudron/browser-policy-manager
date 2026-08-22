from __future__ import annotations

from app.models.policy_schema import PolicyUiSection

UI_SECTIONS = [
    PolicyUiSection(
        id="browser_behavior",
        title_key="profiles.wizard_step_two",
        fallback="Browser behavior",
        order=20,
    ),
    PolicyUiSection(
        id="home_startup",
        title_key="profiles.wizard_step_two",
        fallback="Home and startup surfaces",
        order=30,
    ),
    PolicyUiSection(
        id="urls_sites_navigation",
        title_key="profiles.wizard_step_two",
        fallback="URLs, sites, and navigation",
        order=35,
    ),
    PolicyUiSection(
        id="sync_accounts",
        title_key="profiles.wizard_step_five",
        fallback="Accounts, language, and sync",
        order=37,
    ),
    PolicyUiSection(
        id="search",
        title_key="profiles.wizard_step_two",
        fallback="Search and address bar",
        order=40,
    ),
    PolicyUiSection(
        id="network_access",
        title_key="profiles.wizard_section_network_access",
        fallback="Network and enterprise access",
        order=50,
    ),
    PolicyUiSection(
        id="privacy_security",
        title_key="profiles.wizard_step_three",
        fallback="Privacy and security",
        order=60,
    ),
    PolicyUiSection(
        id="extensions_integrations",
        title_key="profiles.wizard_step_four",
        fallback="Extensions and integrations",
        order=70,
    ),
    PolicyUiSection(
        id="ai_smart",
        title_key="profiles.wizard_step_five",
        fallback="AI and smart features",
        order=80,
    ),
    PolicyUiSection(
        id="advanced",
        title_key="profiles.wizard_section_advanced",
        fallback="Advanced and unmapped policies",
        order=90,
    ),
]


def get_policy_ui_sections() -> list[PolicyUiSection]:
    """Return the ordered wizard sections used by the upcoming schema-driven UI."""

    return list(UI_SECTIONS)
