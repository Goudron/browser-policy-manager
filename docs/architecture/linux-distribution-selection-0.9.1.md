# BPM 0.9.1 Linux Distribution Selection

Status: **Accepted for BPM 0.9.1**
Decision date: 2026-07-07
Selection-rule backlog item: `BPM091-M2-07`
Implementation backlog item: `BPM091-M6-04`
Implementation confirmation date: 2026-07-11
Maintainer approval: **Confirmed during interactive backlog execution on 2026-07-11**

## Purpose

The Administrator/DevOps source-install documentation for BPM 0.9.1 must include exact Linux
installation commands for five worldwide-popular Linux distributions. There is no authoritative
global install-base registry for Linux distributions, so this note records a reproducible selection
rule, the dated evidence considered, the selected distributions, and the guardrail that command
authoring must not begin until this set is recorded.

This note selects documentation targets only. It does not write the installation commands and does
not claim that the selected order is a precise market-share ranking.

## Evidence Date

Evidence checked on 2026-07-07.

The selected set and current command-authoring targets were rechecked on 2026-07-11. The original
selection date remains part of the decision history; the later date freezes the exact releases or
rolling-branch snapshot that `BPM091-M6-05` must use.

## Evidence Sources

| Source | Use | Limitation |
| --- | --- | --- |
| DistroWatch page-hit ranking and DistroWatch description | Popularity/interest proxy for active Linux distribution pages. | DistroWatch page hits are explicitly not usage, quality, or market share; they are page accesses by DistroWatch visitors. |
| TechRadar "Best Linux distro for developers of 2025" | Current developer-oriented source-install relevance signal. | Editorial recommendation, not install-base measurement. |
| Ubuntu adoption notes / W3Techs references | Ubuntu server/developer ubiquity signal. | Web-server share is not desktop distribution share. |
| BPM Administrator/DevOps scope | Fit for source deployment, package-manager coverage, and command maintainability. | Product-specific tie-breaker, not an external popularity metric. |

Primary source URLs:

- `https://distrowatch.com/dwres.php?resource=popularity`
- `https://en.wikipedia.org/wiki/DistroWatch#Page_rankings`
- `https://www.techradar.com/best/best-linux-distro-for-developers`
- `https://en.wikipedia.org/wiki/Ubuntu#Installed_base`

Official release-target verification URLs checked on 2026-07-11:

- `https://releases.ubuntu.com/`
- `https://www.debian.org/releases/`
- `https://fedoraproject.org/`
- `https://linuxmint.com/download.php`
- `https://wiki.manjaro.org/index.php?title=The_Rolling_Release_Development_Model`
- `https://forum.manjaro.org/c/announcements/stable-updates/12`

## Selection Method

Use the following rule for BPM 0.9.1:

1. Start from distributions that are active, general-purpose, and suitable for source deployment on
   a maintainer or administrator workstation/server.
2. Prefer distributions that appear in at least one popularity/interest signal and at least one
   developer/admin relevance signal.
3. Include at least one representative of the major command families needed for source installation:
   Debian/Ubuntu `apt`, Fedora/RHEL-family `dnf`, and Arch-family `pacman`.
4. Prefer stable/LTS variants for exact command authoring when the distribution offers both stable
   and short-lived releases.
5. Break ties by maintainability for BPM docs: official repositories, Python packaging path,
   availability of build dependencies, and similarity to existing Administrator/DevOps evidence.
6. Record excluded close candidates so future maintainers can revisit the choice without guessing.

## Selected Distributions

| Slot | Distribution target | Command family | Why selected |
| --- | --- | --- | --- |
| 1 | Ubuntu LTS | `apt` | Broad user/developer/server relevance, strong documentation ecosystem, and stable LTS cadence. |
| 2 | Debian Stable | `apt` | Long-lived upstream base, stable server/admin target, and existing Administrator/DevOps command parity. |
| 3 | Fedora current stable | `dnf` | Developer/admin relevance, RHEL-family package model, and non-Debian package coverage. |
| 4 | Linux Mint current stable | `apt` | Popular desktop target and Ubuntu-based user environment that still needs exact user-facing commands. |
| 5 | Manjaro current stable branch | `pacman` | Popular Arch-family target with a friendlier admin surface than raw Arch for BPM source-install docs. |

The selected set intentionally contains two Ubuntu/Debian-family desktop/admin targets because users
will expect exact commands for both Ubuntu and Linux Mint, not only a shared "Debian-like" summary.

## Frozen Command-Authoring Targets

`BPM091-M6-05` must author and `BPM091-M6-06` must validate commands against the following exact
targets. A newer release appearing after 2026-07-11 does not silently change this table; update this
decision and its contract first.

| Distribution target | Frozen validation target | Package command | Target evidence |
| --- | --- | --- | --- |
| Ubuntu LTS | Ubuntu 26.04 LTS | `apt-get` | Canonical listed Ubuntu 26.04 among current LTS releases on 2026-07-11. |
| Debian Stable | Debian 13.5 (`trixie`) | `apt-get` | Debian identified 13 as stable and 13.5 as its current point release on 2026-07-11. |
| Fedora current stable | Fedora Linux 44 | `dnf` | Fedora identified Linux 44 as its latest release on 2026-07-11. |
| Linux Mint current stable | Linux Mint 22.3 (`Zena`) | `apt-get` | Linux Mint identified 22.3 as its recommended latest release on 2026-07-11. |
| Manjaro current stable branch | Manjaro stable branch after the 2026-06-26 stable update | `pacman` | Manjaro is rolling-release; the validation transcript must record `pacman-mirrors -G` and the fully updated package state rather than infer a fixed point release. |

The command topics may share repository checkout and BPM runtime steps, but package installation,
Python availability checks, and observed command output remain target-owned evidence. Ubuntu and
Linux Mint therefore keep separate sequences even where their package names agree.

## Close Candidates Not Selected

| Candidate | Reason not selected for the first BPM 0.9.1 command set |
| --- | --- |
| MX Linux | Strong DistroWatch interest signal, but lower fit for BPM source-deployment command maintenance than Debian/Ubuntu/Mint. |
| Arch Linux | Important upstream family, but Manjaro is the selected Arch-family target for this user-facing documentation pass. |
| openSUSE Leap/Tumbleweed | Strong developer/admin fit, but would be the sixth family after the selected five. |
| CentOS Stream / Rocky Linux / AlmaLinux | Important enterprise family, but BPM 0.9.1 asks for five worldwide-popular distributions, and Fedora covers the `dnf` path first. |
| CachyOS / EndeavourOS | Strong current interest signals in some communities, but less suitable as first-pass general source-install documentation targets. |

## Maintainer Approval Rule

This record is the maintainer-review point for the selected set. Exact command authoring for
`BPM091-M6-05` may begin only after `BPM091-M6-04` is confirmed in this file and its contract test.
Validation evidence belongs to `BPM091-M6-06`. If a maintainer wants a different distribution or
validation target, change this note and its test before writing commands.

## Command Authoring Constraints

Future command topics must:

- name the exact distribution release or branch used for validation;
- provide the exact command sequence, not a family-level summary;
- include health/readiness verification, database migration or explicit no-migration statement,
  documentation build verification, and rollback/stop condition;
- follow `documentation/config/documentation-sufficiency-review-protocol-0.9.1.json`;
- keep simulation or hands-on evidence attached to the sufficiency review record.

## Verification

Focused check: `./.venv/bin/pytest -q tests/integration/app/test_linux_distribution_selection_091.py`

```bash
./.venv/bin/pytest -q tests/integration/app/test_linux_distribution_selection_091.py
```

Release gates: `make test-docs-contract`, `make docs-release-check`, `make test-release`

```bash
make test-docs-contract
make docs-release-check
make test-release
```
