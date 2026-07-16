from __future__ import annotations

from tests.docs_index import doc_path_from_index

SELECTION_PATH = "architecture/linux-distribution-selection-0.9.1.md"


def _selection() -> str:
    return doc_path_from_index(SELECTION_PATH, status="active").read_text(encoding="utf-8")


def _normalized_selection() -> str:
    return " ".join(_selection().split())


def test_linux_distribution_selection_is_active_dated_and_scoped_to_091() -> None:
    selection = _normalized_selection()

    assert "Status: **Accepted for BPM 0.9.1**" in selection
    assert "Decision date: 2026-07-07" in selection
    assert "Selection-rule backlog item: `BPM091-M2-07`" in selection
    assert "Implementation backlog item: `BPM091-M6-04`" in selection
    assert "Implementation confirmation date: 2026-07-11" in selection
    assert "Maintainer approval: **Confirmed during interactive backlog execution on 2026-07-11**" in selection
    assert "Evidence checked on 2026-07-07." in selection
    assert "rechecked on 2026-07-11" in selection
    assert "does not write the installation commands" in selection
    assert "does not claim that the selected order is a precise market-share ranking" in selection


def test_linux_distribution_selection_records_sources_limitations_and_method() -> None:
    selection = _selection()

    for required in (
        "DistroWatch page-hit ranking",
        "not usage, quality, or market share",
        "TechRadar \"Best Linux distro for developers of 2025\"",
        "Ubuntu adoption notes / W3Techs references",
        "BPM Administrator/DevOps scope",
        "active, general-purpose, and suitable for source deployment",
        "Debian/Ubuntu `apt`, Fedora/RHEL-family `dnf`, and Arch-family `pacman`",
        "stable/LTS variants",
        "Record excluded close candidates",
    ):
        assert required in selection

    for url in (
        "https://distrowatch.com/dwres.php?resource=popularity",
        "https://en.wikipedia.org/wiki/DistroWatch#Page_rankings",
        "https://www.techradar.com/best/best-linux-distro-for-developers",
        "https://en.wikipedia.org/wiki/Ubuntu#Installed_base",
        "https://releases.ubuntu.com/",
        "https://www.debian.org/releases/",
        "https://fedoraproject.org/",
        "https://linuxmint.com/download.php",
        "https://wiki.manjaro.org/index.php?title=The_Rolling_Release_Development_Model",
        "https://forum.manjaro.org/c/announcements/stable-updates/12",
    ):
        assert f"`{url}`" in selection


def test_linux_distribution_selection_names_exact_five_targets() -> None:
    selection = _selection()

    selected_rows = [line for line in selection.splitlines() if line.startswith("| ") and " | `" in line]
    assert len([line for line in selected_rows if line.startswith("| 1 |")]) == 1

    for distro, command_family in (
        ("Ubuntu LTS", "`apt`"),
        ("Debian Stable", "`apt`"),
        ("Fedora current stable", "`dnf`"),
        ("Linux Mint current stable", "`apt`"),
        ("Manjaro current stable branch", "`pacman`"),
    ):
        assert f"| {distro} | {command_family} |" in selection

    assert "exact commands for both Ubuntu and Linux Mint" in selection


def test_linux_distribution_selection_freezes_exact_command_authoring_targets() -> None:
    selection = _selection()
    normalized = _normalized_selection()

    for distro, target, package_command in (
        ("Ubuntu LTS", "Ubuntu 26.04 LTS", "`apt-get`"),
        ("Debian Stable", "Debian 13.5 (`trixie`)", "`apt-get`"),
        ("Fedora current stable", "Fedora Linux 44", "`dnf`"),
        ("Linux Mint current stable", "Linux Mint 22.3 (`Zena`)", "`apt-get`"),
        (
            "Manjaro current stable branch",
            "Manjaro stable branch after the 2026-06-26 stable update",
            "`pacman`",
        ),
    ):
        assert f"| {distro} | {target} | {package_command} |" in selection

    assert "pacman-mirrors -G" in selection
    assert "newer release appearing after 2026-07-11 does not silently change this table" in selection
    assert "Ubuntu and Linux Mint therefore keep separate sequences" in normalized


def test_linux_distribution_selection_records_rejected_candidates_and_command_gate() -> None:
    selection = _selection()
    normalized = _normalized_selection()

    for candidate in (
        "MX Linux",
        "Arch Linux",
        "openSUSE Leap/Tumbleweed",
        "CentOS Stream / Rocky Linux / AlmaLinux",
        "CachyOS / EndeavourOS",
    ):
        assert f"| {candidate} |" in selection

    for required in (
        "Exact command authoring",
        "`BPM091-M6-04`",
        "`BPM091-M6-05`",
        "`BPM091-M6-06`",
        "change this note and its test before writing commands",
        "name the exact distribution release or branch",
        "provide the exact command sequence",
        "health/readiness verification",
        "database migration or explicit no-migration statement",
        "documentation build verification",
        "rollback/stop condition",
        "documentation/config/documentation-sufficiency-review-protocol-0.9.1.json",
    ):
        assert required in normalized

    assert "`BPM091-M6-02`" not in selection


def test_linux_distribution_selection_names_focused_and_release_checks() -> None:
    selection = _selection()

    for command in (
        "./.venv/bin/pytest -q tests/test_linux_distribution_selection_091.py",
        "make test-docs-contract",
        "make docs-release-check",
        "make test-release",
    ):
        assert f"`{command}`" in selection
