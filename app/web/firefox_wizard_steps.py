from __future__ import annotations


def get_wizard_steps() -> list[dict[str, object]]:
    """Return the ordered task-first steps for the main wizard flow."""

    return [
        {
            "id": "start",
            "step": 1,
            "label_key": "profiles.wizard_step_one",
            "label_fallback": "Profile & baseline",
            "copy_key": "profiles.wizard_step_one_copy",
            "copy_fallback": "Profile name, Firefox channel, scenario, starting preset, and CIS layer.",
            "progress_key": "profiles.wizard_progress_one",
            "progress_fallback": "Step 1 of 6: Profile & baseline",
        },
        {
            "id": "browser_defaults",
            "step": 2,
            "label_key": "profiles.wizard_step_two",
            "label_fallback": "Browser access & defaults",
            "copy_key": "profiles.wizard_step_two_copy",
            "copy_fallback": "Network access, browser behavior, home surfaces, search, and navigation defaults.",
            "progress_key": "profiles.wizard_progress_two",
            "progress_fallback": "Step 2 of 6: Browser access & defaults",
        },
        {
            "id": "privacy",
            "step": 3,
            "label_key": "profiles.wizard_step_three",
            "label_fallback": "Security & privacy",
            "copy_key": "profiles.wizard_step_three_copy",
            "copy_fallback": "Privacy controls, permissions, cookies, cleanup, and hardening posture.",
            "progress_key": "profiles.wizard_progress_three",
            "progress_fallback": "Step 3 of 6: Security & privacy",
        },
        {
            "id": "users_features",
            "step": 4,
            "label_key": "profiles.wizard_step_four",
            "label_fallback": "Users, add-ons & sites",
            "copy_key": "profiles.wizard_step_four_copy",
            "copy_fallback": "Mozilla accounts, language, translation, add-ons, bookmarks, and website handling.",
            "progress_key": "profiles.wizard_progress_four",
            "progress_fallback": "Step 4 of 6: Users, add-ons & sites",
        },
        {
            "id": "ai",
            "step": 5,
            "label_key": "profiles.wizard_step_five",
            "label_fallback": "AI & smart features",
            "copy_key": "profiles.wizard_step_five_copy",
            "copy_fallback": "Built-in AI surfaces, visual search, and smart browser features.",
            "progress_key": "profiles.wizard_progress_five",
            "progress_fallback": "Step 5 of 6: AI & smart features",
        },
        {
            "id": "review",
            "step": 6,
            "label_key": "profiles.wizard_step_six",
            "label_fallback": "Review & export",
            "copy_key": "profiles.wizard_step_six_copy",
            "copy_fallback": "Check the setup in plain language, then save and download the version you want.",
            "progress_key": "profiles.wizard_progress_six",
            "progress_fallback": "Step 6 of 6: Review & export",
        },
    ]
