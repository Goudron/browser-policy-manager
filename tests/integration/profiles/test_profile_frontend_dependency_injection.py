from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STATIC = ROOT / "app" / "static"
SOURCE = ROOT / "app" / "static_src"


def test_owned_profile_runtime_has_no_global_bridge_dependency():
    owned_sources = [
        *STATIC.glob("profiles*.js"),
        *SOURCE.glob("profiles_bundle_*.js"),
        *(SOURCE / "profile_bundle_entries").glob("*.js"),
    ]
    for path in owned_sources:
        if path.name in {"profiles_head_bootstrap.js", "profiles_page_bootstrap.js"}:
            continue
        source = path.read_text(encoding="utf-8")
        assert "BPMProfiles" not in source, path


def test_editor_composition_has_explicit_imported_dependencies():
    source = (STATIC / "profiles_bootstrap.js").read_text(encoding="utf-8")

    for snippet in (
        'import { create as createBootstrapSections } from "./profiles_bootstrap_sections.js";',
        'import { create as createPreferenceRows } from "./profiles_preferences_rows.js";',
        'import { create as createSchemaShellSections } from "./profiles_schema_shell_sections.js";',
        'import * as workspaceState from "./profiles_workspace_state.js";',
        'import { create as createDirtyRouteGuard } from "./profiles_runtime_dirty_guard.js";',
        "const bootstrapSections = createBootstrapSections({",
        "createPreferenceRows,",
        "createSchemaShellSections,",
        "createWorkspaceState: () => workspaceState,",
        "createDirtyRouteGuard,",
    ):
        assert snippet in source
