from __future__ import annotations


def get_wizard_steps() -> list[dict[str, object]]:
    """Return the ordered task-first steps for the main wizard flow."""

    return [
        {
            "step": 1,
            "label_key": "profiles.wizard_step_one",
            "label_fallback": "Start",
            "copy_key": "profiles.wizard_step_one_copy",
            "copy_fallback": "Profile name, Firefox channel, and a starting preset.",
            "progress_key": "profiles.wizard_progress_one",
            "progress_fallback": "Step 1 of 8: start",
        },
        {
            "step": 2,
            "label_key": "profiles.wizard_step_two",
            "label_fallback": "Network & browser basics",
            "copy_key": "profiles.wizard_step_two_copy",
            "copy_fallback": "Connection settings, proxy, updates, downloads, and common browser behavior.",
            "progress_key": "profiles.wizard_progress_two",
            "progress_fallback": "Step 2 of 8: Network & browser basics",
        },
        {
            "step": 3,
            "label_key": "profiles.wizard_step_three",
            "label_fallback": "Home & startup",
            "copy_key": "profiles.wizard_step_three_copy",
            "copy_fallback": "Homepage, startup pages, new tabs, Firefox Home, and related user-facing surfaces.",
            "progress_key": "profiles.wizard_progress_three",
            "progress_fallback": "Step 3 of 8: Home & startup",
        },
        {
            "step": 4,
            "label_key": "profiles.wizard_step_four",
            "label_fallback": "Search & navigation",
            "copy_key": "profiles.wizard_step_four_copy",
            "copy_fallback": "Default search, managed engines, suggestions, and address bar behavior.",
            "progress_key": "profiles.wizard_progress_four",
            "progress_fallback": "Step 4 of 8: Search & navigation",
        },
        {
            "step": 5,
            "label_key": "profiles.wizard_step_five",
            "label_fallback": "Privacy & security",
            "copy_key": "profiles.wizard_step_five_copy",
            "copy_fallback": "Privacy controls, permissions, cookies, hardening, and security-related preferences.",
            "progress_key": "profiles.wizard_progress_five",
            "progress_fallback": "Step 5 of 8: Privacy & security",
        },
        {
            "step": 6,
            "label_key": "profiles.wizard_step_six",
            "label_fallback": "Accounts, languages, add-ons & sites",
            "copy_key": "profiles.wizard_step_six_copy",
            "copy_fallback": "Mozilla account sign-in, browser language, translation, add-ons, and website handling.",
            "progress_key": "profiles.wizard_progress_six",
            "progress_fallback": "Step 6 of 8: Accounts, languages, add-ons & sites",
        },
        {
            "step": 7,
            "label_key": "profiles.wizard_step_seven",
            "label_fallback": "AI & smart features",
            "copy_key": "profiles.wizard_step_seven_copy",
            "copy_fallback": "Built-in AI surfaces, visual search, and future smart browser features.",
            "progress_key": "profiles.wizard_progress_seven",
            "progress_fallback": "Step 7 of 8: AI & smart features",
        },
        {
            "step": 8,
            "label_key": "profiles.wizard_step_eight",
            "label_fallback": "Review & export",
            "copy_key": "profiles.wizard_step_eight_copy",
            "copy_fallback": "Review the current setup, check advanced items, and download JSON or YAML.",
            "progress_key": "profiles.wizard_progress_eight",
            "progress_fallback": "Step 8 of 8: Review & export",
        },
    ]
