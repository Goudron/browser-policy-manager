from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
EN_DITA_ROOT = REPO_ROOT / "documentation" / "src" / "dita" / "en"
LOCALIZED_LOCALES = ("ru", "de", "zh-CN", "fr", "es-ES")
M10_LOCALIZED_TOPICS = (
    "cis/cis-concept-orientation.dita",
    "admin/admin-concept-integration-audience.dita",
    "admin/admin-task-gate-control-product-startup.dita",
    "firefox/fx-concept-release-esr-differences.dita",
    "admin/admin-task-plan-devops-storage-logs-backups.dita",
    "admin/admin-task-verify-source-update-rollback-stop.dita",
    "admin/admin-troubleshoot-documentation-portal-build-links.dita",
    "admin/admin-troubleshoot-failed-startup-probes.dita",
    "admin/admin-task-review-devops-configuration-sources.dita",
    "admin/admin-task-verify-windows-wsl-source-deployment.dita",
    "admin/admin-task-install-debian-13-source.dita",
    "admin/admin-task-install-fedora-44-source.dita",
    "admin/admin-task-install-linux-mint-22-3-source.dita",
    "admin/admin-task-install-manjaro-stable-source.dita",
    "admin/admin-task-install-ubuntu-26-04-source.dita",
    "admin/admin-task-run-source-update-migrations-docs.dita",
    "admin/admin-task-verify-linux-source-deployment.dita",
    "admin/admin-task-plan-monitoring-backup-update-windows.dita",
    "admin/admin-troubleshoot-schema-cache-validation.dita",
    "admin/admin-task-prepare-source-update-evidence.dita",
    "admin/admin-troubleshoot-import-export-failures.dita",
)


def _topic(relative_path: str) -> str:
    return (EN_DITA_ROOT / relative_path).read_text(encoding="utf-8")


def test_m10_localized_topics_exclude_internal_build_and_status_narration():
    forbidden_fragments = (
        "M12-08",
        "make docs",
        "make test-fast",
        "documentation/tests/",
        "documentation/build/",
        "app/core/config.py",
    )

    for locale in LOCALIZED_LOCALES:
        dita_root = REPO_ROOT / "documentation" / "src" / "dita" / locale
        for relative_path in M10_LOCALIZED_TOPICS:
            source = (dita_root / relative_path).read_text(encoding="utf-8").lower()
            for fragment in forbidden_fragments:
                assert fragment.lower() not in source, f"{locale}/{relative_path}: {fragment}"


def test_m10_english_topics_remove_implementation_and_maintainer_narration():
    integration = _topic("admin/admin-concept-integration-audience.dita")
    cis = _topic("cis/cis-concept-orientation.dita")
    startup_gate = _topic("admin/admin-task-gate-control-product-startup.dita")
    channels = _topic("firefox/fx-concept-release-esr-differences.dita")
    update_plan = _topic("admin/admin-task-plan-devops-storage-logs-backups.dita")
    rollback = _topic("admin/admin-task-verify-source-update-rollback-stop.dita")

    for leaked_text, source in (
        ("maintainers", integration),
        ("generated OpenAPI contract", integration),
        ("route/model source", integration),
        ("plans 53 recommendation topics", cis),
        ("M12-08", startup_gate),
        ("future schema", channels.lower()),
        ("future update-from-source", update_plan),
        ("future production/HA/reverse-proxy planning", rollback),
    ):
        assert leaked_text not in source


def test_m10_operational_troubleshooting_uses_evidence_and_escalation_not_source_repair():
    portal = _topic("admin/admin-troubleshoot-documentation-portal-build-links.dita")
    startup = _topic("admin/admin-troubleshoot-failed-startup-probes.dita")
    wsl = _topic("admin/admin-task-verify-windows-wsl-source-deployment.dita")
    schema = _topic("admin/admin-troubleshoot-schema-cache-validation.dita")
    import_export = _topic("admin/admin-troubleshoot-import-export-failures.dita")

    for leaked_text, source in (
        ("make docs-", portal),
        ("documentation/tests/", portal),
        ("documentation/build/", portal),
        ("changing code", startup),
        ("make test-fast", startup),
        ("make docs-", startup),
        ("changing BPM code", wsl),
        ("make test-fast", wsl),
        ("documentation/tests/", schema),
        ("documentation/tests/", import_export),
    ):
        assert leaked_text not in source
    assert "BPM deployment owner" in portal
    assert "BPM deployment owner" in startup
    assert "BPM deployment owner" in wsl
    assert "BPM deployment owner" in schema


def test_m10_moves_documentation_maintenance_commands_out_of_deployment_topics():
    maintenance_protocol = (
        REPO_ROOT / "documentation" / "runbooks" / "debugging-protocol.md"
    ).read_text(encoding="utf-8")
    update = _topic("admin/admin-task-run-source-update-migrations-docs.dita")
    linux = _topic("admin/admin-task-verify-linux-source-deployment.dita")
    monitoring = _topic("admin/admin-task-plan-monitoring-backup-update-windows.dita")
    evidence = _topic("admin/admin-task-prepare-source-update-evidence.dita")

    for source in (update, linux, monitoring):
        assert "make docs-" not in source
        assert "make test-fast" not in source
    assert "changing code" not in evidence

    for distribution in (
        "admin/admin-task-install-debian-13-source.dita",
        "admin/admin-task-install-fedora-44-source.dita",
        "admin/admin-task-install-linux-mint-22-3-source.dita",
        "admin/admin-task-install-manjaro-stable-source.dita",
        "admin/admin-task-install-ubuntu-26-04-source.dita",
    ):
        source = _topic(distribution)
        assert "make setup-docs-toolchain" not in source
        assert "make docs-validate" not in source
        assert "make docs-build" not in source

    assert "make docs-validate" in maintenance_protocol
    assert "make docs-build" in maintenance_protocol
