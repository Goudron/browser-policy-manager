# BPM 0.9.1 live source-install privilege and retained-environment contract

Status: **Accepted by the project maintainer on 2026-07-14**
Backlog owner: `BPM091-M11-01`
Machine-readable authority:
`documentation/config/live-source-install-privileged-validation-contract-0.9.1.json`

## Decision

Docker is not installed as part of this task. The accepted read-only baseline recorded no Docker CLI,
packages, daemon, socket, group, apt source/key, data roots, or configuration on the Ubuntu 26.04
x86_64 maintainer host. Immediately before `BPM091-M11-02`, the same state and the resource floor
must be checked again. Any drift stops the installation and requires a revised approval.

The approved installation method is Docker's official Ubuntu apt repository and only
`docker-ce`, `docker-ce-cli`, `containerd.io`, `docker-buildx-plugin`, and
`docker-compose-plugin`. The exact package candidates are recorded before installation. Docker
commands run through `sudo`; the maintainer is not added to the root-equivalent `docker` group.
The convenience script, Docker Desktop, rootless setup, daemon TCP access, and unrelated host or
firewall changes are outside the boundary.

For automation, `sudo -n` reported that interactive authentication was required. The maintainer
therefore approved each graphical system authentication dialog for a bounded `pkexec` root script.
No password is requested by the assistant or passed through chat, command arguments, stdin, logs,
or evidence. Maintainer terminal commands continue to use `sudo docker`.

## Frozen targets

| M6 target | Frozen validation identity |
| --- | --- |
| Ubuntu 26.04 LTS | Docker Official Image index `sha256:b7f48194d4d8b763a478a621cdc81c27be222ba2206ca3ca6bc42b49685f3d9e`; amd64 manifest `sha256:c6c0067e0e45b7a826eaebb193cef957be28045380963a9b1eeb2a5d3c70a1b9` |
| Debian 13.5 (trixie) | Docker Official Image index `sha256:d07d1b51c39f51188e60be9b64e6bf769fa94e187f092bc32b91305cfa34ba5a`; amd64 manifest `sha256:3a953985c225a97dfb5a8f1ddc6a3ecefefc35ef51f537075e08941305045a1e` |
| Fedora Linux 44 | Docker Official Image index `sha256:6c75d5bf57cb0fa5aa4b92c6a83c86c791644496d9ac230de7711f5b8ec3b898`; amd64 manifest `sha256:89f61a124414261868224666aa7fb8df1b78397a53623774bdfb105d1612b48b` |
| Linux Mint 22.3 (Zena) | Local image imported from the authenticated official Cinnamon ISO with SHA-256 `a081ab202cfda17f6924128dbd2de8b63518ac0531bcfe3f1a1b88097c459bd4`; Ubuntu substitution is forbidden |
| Manjaro stable after 2026-06-26 | Manjaro seed index `sha256:bbf1f1d746f28e138eea610e140d2f28cbb5b7c5da2fbff034b883527aa604e9`; amd64 manifest `sha256:a411decb8d219cb4b16b39618e9aa8ce8228acad9cba5b10420f804a20ca5c84`, followed by the documented full stable update and a recorded package snapshot. The Manjaro GitLab project Makefile explicitly builds, tags, tests, and pushes `manjarolinux/base`. |

The Mint ISO checksum file must pass Linux Mint signature verification with fingerprint
`27DEB15644C6B3CF3BD7D291300F846BA25BAE09`. If its root filesystem cannot be faithfully imported,
Mint remains blocked. The pinned Manjaro image predates the selected stable-update boundary, so it
is only a reproducible seed; failure to prove the post-update branch and package state is also a
blocker.

## Isolation and resources

Only one validation container may exist at a time. Every run is labeled with the M11 owner, run
ID, and target and is limited to two CPUs, 1536 MiB RAM, 2560 MiB including swap, 512 processes,
and 4096 open files. Containers use a dedicated bridge with no published ports or host networking.
All BPM probes execute inside the container.

No host directory, user data, Docker socket, device, credential, secret, production endpoint, or
production database may enter a container. Source is checked out inside the disposable filesystem;
only reviewed evidence leaves through `docker cp`. Task-owned Docker storage may grow to
200,000,000,000 bytes while the host retains at least 20 GiB free, and global prune commands are
forbidden.

## Evidence, inventory, and retained Docker

Reviewed command-by-command JSONL transcripts and summaries are retained below
`documentation/evidence/live-source-install/0.9.1`; downloads, package caches, root filesystems,
databases, and build output stay in ignored staging or Docker storage. Evidence records the exact
image, command, exit code, bounded output, probes, resources, and disposition and is rejected if it
contains credentials or unrelated host data.

Final reconciliation is ID- and label-scoped. It never uses `docker system prune`, unscoped prune,
`apt autoremove`, or `apt clean`. Each exact target image and the imported Mint image remain local
golden images and are resolved from the local cache before any registry access. M11-owned
containers are stopped after evidence capture; failed, blocking, or evidence-needed attempts are
retained. After evidence handoff, a successful derivative container or explicitly committed
derivative image may be removed only by exact recorded identity, without deleting its golden image.
Every retained or removed object must have an immutable identity, run/target/attempt labels, final
disposition, evidence path, and byte count. Docker packages, official apt
source/key, services, data roots, sockets, and the memberless package-created `docker` group remain
as maintainer-approved project tooling. No user is added to that group. New retries always use a
fresh uniquely named container and never reuse installed state. Retention remains bounded by the
200,000,000,000-byte M11 ceiling and 20 GiB host-free floor.

This Linux-container work is not WSL evidence. Windows 10 and Windows 11 claims require genuine
hosts under `BPM091-M11-10` through `BPM091-M11-12`.

## Approval effect

The maintainer approved this boundary with persistent Docker retention on 2026-07-14. This unlocks
only `BPM091-M11-02`. A failed or partial installation is still rolled back; retention applies only
after successful installation and verification. Any later expansion of privileges, paths,
networking, resources, image provenance, or cleanup invalidates this approval.
