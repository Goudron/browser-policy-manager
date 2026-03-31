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
        title_key="profiles.wizard_step_three",
        fallback="Home and startup surfaces",
        order=30,
    ),
    PolicyUiSection(
        id="search",
        title_key="profiles.wizard_step_four",
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
        title_key="profiles.wizard_step_five",
        fallback="Privacy and security",
        order=60,
    ),
    PolicyUiSection(
        id="extensions_integrations",
        title_key="profiles.wizard_section_extensions_integrations",
        fallback="Extensions and integrations",
        order=70,
    ),
    PolicyUiSection(
        id="advanced",
        title_key="profiles.wizard_section_advanced",
        fallback="Advanced and unmapped policies",
        order=80,
    ),
]


def get_policy_ui_sections() -> list[PolicyUiSection]:
    """Return the ordered wizard sections used by the upcoming schema-driven UI."""

    return list(UI_SECTIONS)
