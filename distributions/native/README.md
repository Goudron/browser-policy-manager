# BPM 0.9.5 native Linux distributions

This directory owns the source recipes for the five native Linux packages:
Ubuntu 26.04 LTS, Debian 13.5, Fedora 44, Linux Mint 22.3, and the Manjaro
stable branch. It is not an artifact directory.

The packages are `linux/amd64` only and contain a private, checksum-verified
CPython 3.14.6 runtime under `/opt/bpm`. This is required because Debian 13.5
and Linux Mint 22.3 do not provide the BPM minimum Python version. The package
does not replace the operating-system Python and does not install any `dev`,
`ai`, or PostgreSQL optional dependency.

Each package contains the release wheel, Alembic migrations, verified product
documentation, `/etc/bpm/bpm.env`, `/var/lib/bpm`, unprivileged `bpm` user
creation metadata, and an installed but disabled `bpm.service` unit. Migration
is always explicit:

```bash
sudo bpm-migrate
sudo systemctl enable --now bpm
curl -fsS http://127.0.0.1:8000/health/ready
```

`bpm-migrate` is never invoked by package installation, package upgrade,
service enablement, service start, or `bpm serve`. Package removal preserves
the state directory and the system account for operator-controlled recovery.

Build a target after generating and verifying the product documentation archive:

```bash
make native-package-build TARGET=ubuntu-26-04
make native-package-smoke TARGET=ubuntu-26-04
```

Artifacts are first generated as transient release evidence under
`artifacts/native-packages/`. After every target passes smoke, stage the
versioned upload set with `make native-package-stage-release`. It copies only
receipt-verified assets to `distributions/releases/0.9.5/assets/`, writes the
tracked aggregate checksum and manifest, and prepares the GitHub Release asset
upload. The binaries remain ignored by Git because several are over GitHub's
ordinary 100 MiB Git-file limit. The Mint target uses only the locally
imported, checksum-verified official Mint image; substituting Ubuntu is
forbidden.
