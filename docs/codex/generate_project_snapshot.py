#!/usr/bin/env python3
"""Generate the declared, source-only Codex orientation snapshot."""

from __future__ import annotations

import hashlib
import tomllib
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = Path(__file__).with_name("PROJECT_SNAPSHOT.md")
# The orientation record deliberately has direct file inputs only.  Directories
# remain ownership boundaries in the system map, but recursively digesting them
# makes an unrelated source edit invalidate this cross-subsystem snapshot.
SOURCE_OWNERS = (
    (
        "System map",
        "release architecture maintainers",
        ("docs/architecture/current-system-map.md",),
    ),
    (
        "Snapshot generator",
        "documentation architecture and snapshot maintainers",
        ("docs/codex/generate_project_snapshot.py",),
    ),
    (
        "Architecture boundaries",
        "release architecture maintainers",
        ("docs/architecture/python-architecture-boundaries-0.9.5.md",),
    ),
    (
        "Release boundary",
        "release architecture maintainers",
        ("docs/architecture/release-incubation-development-boundary-0.9.5.md",),
    ),
    ("Application assembly", "application runtime maintainers", ("app/main.py",)),
    (
        "Configuration and database",
        "application runtime maintainers",
        ("app/core/config.py", "app/db.py"),
    ),
    (
        "Profile API/service",
        "profile lifecycle maintainers",
        ("app/api/profiles.py", "app/services/profile_service.py"),
    ),
    (
        "Schema lifecycle",
        "Firefox schema lifecycle maintainers",
        (
            "app/core/schema_channels.py",
            "app/core/lifecycle_transition_plan.py",
            "app/core/retirement_convertibility_preflight.py",
        ),
    ),
    (
        "Profile conversion",
        "Firefox profile conversion maintainers",
        ("app/core/profile_conversion_planner.py", "app/core/profile_conversion_recipes.py"),
    ),
    (
        "Retired-ESR migration",
        "release migration maintainers",
        (
            "migration_support/retirement_owner_v1.py",
            "migration_support/retirement_revision_materializer_v1.py",
        ),
    ),
    (
        "Firefox exchange",
        "Firefox policy exchange maintainers",
        ("app/services/firefox_policy_import.py", "app/services/firefox_policy_export.py"),
    ),
    (
        "Profile web route boundary",
        "profile web maintainers",
        (
            "app/web/profiles.py",
            "app/web/profiles_context.py",
            "app/templates/profiles/_page_document.html",
        ),
    ),
    (
        "Frontend source boundary",
        "profile frontend maintainers",
        (
            "app/static/profiles_modules/conversion_recommendation.mjs",
            "app/static/profiles_modules/conversion_review.mjs",
            "app/static/profiles_css/README.md",
            "tools/frontend_profile_graph_0_9_5.json",
        ),
    ),
    (
        "Schema lifecycle tooling",
        "Firefox schema tooling maintainers",
        (
            "tools/verify_firefox_schema_matrix.py",
            "tools/verify_firefox_conversion_matrix.py",
            "tools/schema_lifecycle_dry_run.py",
        ),
    ),
    (
        "Documentation workspace",
        "documentation architecture and snapshot maintainers",
        ("documentation/PROJECT_SNAPSHOT.md",),
    ),
    (
        "Current artifact ownership",
        "release artifact maintainers",
        (
            "tests/fixtures/current_artifact_owners_0_9_4.json",
            "tests/contract/docs/general/test_current_artifact_ownership.py",
        ),
    ),
)
FAST_ROUTES = (
    (
        "Architecture/import boundary",
        "make architecture",
        "tests/integration/app/test_python_architecture_contracts.py",
    ),
    ("Profile API/service", "make test-integration", "tests/integration/api/test_profiles_api.py"),
    (
        "Profile frontend",
        "make test-profile-pure-modules",
        "tests/unit/profiles/test_profile_frontend_bundles.py",
    ),
    (
        "Firefox policy exchange",
        "make test-firefox-schema-workflow",
        "tests/integration/api/test_firefox_policies_import_api.py",
    ),
    (
        "Schema lifecycle/conversion",
        "make verify-firefox-conversion-matrix",
        "tests/unit/schema/contracts/test_lifecycle_transition_plan.py",
    ),
    (
        "Conversion UI",
        "make test-profile-conversion-ux",
        "tests/browser/profiles/test_schema_conversion_ux.py",
    ),
    (
        "Retirement migration",
        "make test-postgres-integration",
        "tests/integration/db/test_retirement_owner_v1.py",
    ),
    (
        "Documentation pipeline",
        "make test-docs",
        "documentation/tests/unit/test_build_docs_structure.py",
    ),
)
EXCLUDED_BOUNDARIES = (
    "Git and local-machine state",
    "generated frontend bundles, CSS, locale catalogs, schemas, documentation artifacts, and installed sites",
    "vendor trees, dependencies, caches, reports, corpora, secrets, databases, and browser artifacts",
)


def _version() -> str:
    project = tomllib.loads((REPOSITORY_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    version = project["project"]["version"]
    if not isinstance(version, str) or not version:
        raise RuntimeError("project version is missing or invalid")
    return version


def _paths() -> list[Path]:
    paths: list[Path] = []
    for _label, _owner, relative_paths in SOURCE_OWNERS:
        for relative_path in relative_paths:
            path = REPOSITORY_ROOT / relative_path
            if not path.is_file():
                raise RuntimeError(f"snapshot source input is missing: {relative_path}")
            paths.append(path)
    return paths


def _digest() -> str:
    hasher = hashlib.sha256()
    for path in _paths():
        relative = path.relative_to(REPOSITORY_ROOT).as_posix()
        hasher.update(relative.encode())
        hasher.update(b"\0")
        hasher.update(hashlib.sha256(path.read_bytes()).digest())
    return hasher.hexdigest()


def generate_snapshot() -> str:
    lines = [
        "# BPM Codex Orientation Snapshot",
        "",
        "Generated only by `make codex-snapshot` (`docs/codex/generate_project_snapshot.py`); do not edit manually.",
        "It deliberately has no Git, local-machine, generated-artifact, or report input.",
        f"Target BPM version: `{_version()}`",
        f"Declared-source digest: `{_digest()}`",
        "",
        "## Start Here",
        "",
        "1. `AGENTS.md` and the one approved backlog task.",
        "2. `docs/architecture/current-system-map.md` for owned entrypoints and boundaries.",
        "3. The named owner and focused test below; expand only after a focused failure.",
        "",
        "## Declared Source Owners",
        "",
        *[
            f"- {label} — {owner}: " + ", ".join(f"`{path}`" for path in paths)
            for label, owner, paths in SOURCE_OWNERS
        ],
        "",
        "## Focused Verification Routes",
        "",
        *[f"- {area}: `{command}`; `{test}`" for area, command, test in FAST_ROUTES],
        "",
        "## Environment And Report Evidence Excluded From This Snapshot",
        "",
        *[f"- {boundary}" for boundary in EXCLUDED_BOUNDARIES],
        "",
        "A declared source change invalidates this Codex snapshot only. Regenerate it through its owning command; do not copy digests from evidence or edit this file by hand.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    OUTPUT_PATH.write_text(generate_snapshot(), encoding="utf-8")
    print(f"Generated {OUTPUT_PATH.relative_to(REPOSITORY_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
