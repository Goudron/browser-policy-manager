#!/usr/bin/env python3
"""Generate the declared, source-only documentation subsystem snapshot."""

from __future__ import annotations

import hashlib
import tomllib
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DOCUMENTATION_ROOT = REPOSITORY_ROOT / "documentation"
OUTPUT_PATH = DOCUMENTATION_ROOT / "PROJECT_SNAPSHOT.generated.md"

# Each source belongs to one reviewed snapshot owner.  Keep this list to
# entrypoints and compact authority records: a topic, generated artifact, test
# report, or local installation must not make an orientation snapshot stale.
SOURCE_OWNERS = (
    (
        "Snapshot governance",
        "documentation architecture and snapshot maintainers",
        (
            "documentation/tools/generate_subsystem_snapshot.py",
            "documentation/AGENTS.md",
            "documentation/config/documentation-test-estate-inventory-0.9.4.json",
        ),
    ),
    (
        "Documentation build",
        "documentation build tooling maintainers",
        (
            "documentation/tools/build_docs.py",
            "documentation/buildlib/lifecycle.py",
            "documentation/buildlib/sources.py",
            "documentation/buildlib/portal.py",
            "documentation/buildlib/artifacts.py",
            "documentation/buildlib/pdf.py",
        ),
    ),
    (
        "Source and publication authority",
        "documentation source-contract maintainers",
        (
            "documentation/src/dita/en/maps/user-guide.ditamap",
            "documentation/src/dita/en/maps/administrator-guide.ditamap",
            "documentation/src/dita/en/maps/keys.ditamap",
            "documentation/config/artifact-policy.json",
            "documentation/config/documentation-semantic-contracts-0.9.4.json",
        ),
    ),
    (
        "Runtime `/help/` bridge",
        "documentation runtime maintainers",
        (
            "app/documentation/router.py",
            "app/documentation/assistant_contracts.py",
            "app/documentation/assistant_service.py",
        ),
    ),
    (
        "Focused validation",
        "documentation architecture and snapshot maintainers",
        (
            "documentation/tests/unit/test_generate_subsystem_snapshot.py",
            "documentation/tests/contract/test_documentation_subsystem_snapshot.py",
            "documentation/tests/contract/test_maintained_index_snapshot_contract_0_9_3.py",
            "documentation/tests/contract/test_documentation_test_estate_inventory_0_9_4.py",
            "tests/contract/docs/general/test_codex_project_snapshot.py",
        ),
    ),
)
ARCHITECTURE_ENTRY_POINTS = (
    "product-documentation-ownership-boundary-0.9.0.md",
    "dita-publishing-toolchain-decision-0.9.0.md",
    "documentation-identifiers-and-url-conventions-0.9.0.md",
    "product-documentation-manifest-and-ui-target-schema-0.9.0.md",
    "product-documentation-provenance-review-0.9.0.md",
    "product-documentation-accessibility-security-contract-0.9.0.md",
    "product-documentation-release-contract-0.9.0.md",
    "product-user-capability-inventory-0.9.0.md",
    "firefox-policy-documentation-inventory-0.9.0.json",
    "cis-documentation-inventory-0.9.0.json",
    "api-documentation-inventory-0.9.0.md",
    "ai-component-update-runbook-0.9.3.md",
    "documentation-assistant-presentation-0.9.3.md",
    "documentation-assistant-resource-state-0.9.3.md",
    "documentation-assistant-web-mode-0.9.3.md",
)
DOCUMENTATION_COMMANDS = (
    "make docs-snapshot",
    "make codex-snapshot",
    'make docs-fast-check DOCS_CHANGED="documentation/src/dita/en/user/example.dita"',
    "make test-docs",
    "make test-docs-contract",
    "make docs-release-handoff",
)
ENVIRONMENT_REPORT_BOUNDARIES = (
    "build, distribution, installed-site, PDF, package, and generated search output",
    "browser captures, test reports, coverage, diagnostics, caches, toolchains, dependencies, and vendor trees",
    "Git state, local-machine paths, credentials, databases, and live-install transcripts",
)


def _repo_path(path: Path) -> str:
    return path.relative_to(REPOSITORY_ROOT).as_posix()


def _declared_paths() -> list[Path]:
    paths: list[Path] = []
    for _label, _owner, relative_paths in SOURCE_OWNERS:
        for relative_path in relative_paths:
            path = REPOSITORY_ROOT / relative_path
            if not path.is_file():
                raise RuntimeError(f"snapshot source input is missing: {relative_path}")
            paths.append(path)
    for name in ARCHITECTURE_ENTRY_POINTS:
        path = REPOSITORY_ROOT / "docs/architecture" / name
        if not path.is_file():
            raise RuntimeError(f"snapshot architecture input is missing: {name}")
        paths.append(path)
    return paths


def _digest(paths: list[Path]) -> str:
    hasher = hashlib.sha256()
    for path in sorted(paths):
        hasher.update(_repo_path(path).encode())
        hasher.update(b"\0")
        hasher.update(hashlib.sha256(path.read_bytes()).digest())
    return hasher.hexdigest()


def _product_version() -> str:
    try:
        project = tomllib.loads((REPOSITORY_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        version = project["project"]["version"]
    except (OSError, tomllib.TOMLDecodeError, KeyError) as exc:
        raise RuntimeError(f"cannot read product version: {exc}") from exc
    if not isinstance(version, str) or not version.strip():
        raise RuntimeError("product version is missing or invalid")
    return version


def generate_snapshot() -> str:
    paths = _declared_paths()
    lines = [
        "# BPM Documentation Subsystem Snapshot",
        "",
        "Generated only by `make docs-snapshot` (`documentation/tools/generate_subsystem_snapshot.py`); do not edit manually.",
        "It has no Git, local-machine, generated-artifact, or report input.",
        f"Target BPM version: `{_product_version()}`",
        f"Declared source digest: `{_digest(paths)}`",
        "",
        "## Declared Source Owners",
        "",
        *[
            f"- {label} — {owner}: " + ", ".join(f"`{path}`" for path in relative_paths)
            for label, owner, relative_paths in SOURCE_OWNERS
        ],
        "- Architecture entry points — documentation architecture maintainers:",
        *[f"  - `docs/architecture/{name}`" for name in ARCHITECTURE_ENTRY_POINTS],
        "",
        "## Commands",
        "",
        *[f"- `{command}`" for command in DOCUMENTATION_COMMANDS],
        "",
        "## Environment And Report Evidence Excluded From This Snapshot",
        "",
        *[f"- {boundary}" for boundary in ENVIRONMENT_REPORT_BOUNDARIES],
        "",
        "A declared source change invalidates this documentation snapshot only. Regenerate it through its owning command; do not copy digests from evidence or edit this file by hand.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    OUTPUT_PATH.write_text(generate_snapshot(), encoding="utf-8")
    print(f"Generated {OUTPUT_PATH.relative_to(REPOSITORY_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
