# BPM 0.9.5.1 Native Linux Distribution Contract

Status: active release-delivery contract.

## Targets and scope

BPM 0.9.5.1 supplies native `linux/amd64` packages for the five Linux targets
already selected and validated for source installation:

| Target | Artifact format | Artifact name |
| --- | --- | --- |
| Ubuntu 26.04 LTS | Debian package | `browser-policy-manager_0.9.5.1-1~ubuntu26.04_amd64.deb` |
| Debian 13.5 | Debian package | `browser-policy-manager_0.9.5.1-1~debian13_amd64.deb` |
| Fedora 44 | RPM | `browser-policy-manager-0.9.5.1-1.fc44.x86_64.rpm` |
| Linux Mint 22.3 | Debian package | `browser-policy-manager_0.9.5.1-1~linuxmint22.3_amd64.deb` |
| Manjaro stable | Arch package | `browser-policy-manager-0.9.5.1-1-x86_64.pkg.tar.zst` |

`distributions/native/targets.json` is the machine-readable source of truth
for names, target provenance, runtime dependencies, and the private runtime.
It retains the target evidence defined in
`live-source-install-privileged-validation-contract-0.9.1.md`; Mint is built
only from its authenticated local image and is never substituted with Ubuntu.

This delivery is a single-node BPM application package. It does not claim
authentication, authorization, TLS termination, reverse proxy, firewall policy,
backup automation, monitoring, audit logging, PostgreSQL topology, HA/failover,
or an automatic production deployment.

## Package payload and ownership

Every package contains the same release payload:

- checksum-verified CPython 3.14.6 at `/opt/bpm/runtime`;
- a private base-only virtual environment at `/opt/bpm/venv`;
- BPM 0.9.5.1 wheel and exact base runtime dependency resolution;
- Alembic configuration and the complete released migration tree;
- the verified `bpm-documentation-0.9.5.1.tar.gz` tree at
  `/opt/bpm/documentation/site`;
- immutable release manifest, license, and third-party notices under `/opt/bpm`;
- operator configuration at `/etc/bpm/bpm.env`;
- runtime data directory `/var/lib/bpm`; and
- `/usr/bin/bpm`, `/usr/bin/bpm-migrate`, and a disabled `bpm.service` unit.

The private runtime is required for the common package contract: Debian 13.5
and Linux Mint 22.3 do not supply the BPM minimum Python 3.14. It never
replaces, patches, or becomes the system Python. Base packages exclude the
`dev`, `ai`, and `postgres` extras; NumPy, ONNX Runtime, and Tokenizers are not
in the release runtime.

Packages create the `bpm` system user and make it the sole owner of
`/var/lib/bpm`. Package removal deliberately keeps that user and data directory
for operator-controlled recovery. The systemd unit runs as that unprivileged
user with a read-only program tree and a writable state directory only.

## Database and service lifecycle

Application startup verifies the exact released Alembic head but must not
write the schema. Therefore package installation, package upgrade, systemd
daemon reload, service enablement, service start, and `bpm serve` never invoke
Alembic. The first activation and every migration-bearing update remain
operator-controlled:

```text
sudo bpm-migrate
sudo systemctl enable --now bpm
curl -fsS http://127.0.0.1:8000/health/ready
```

For update, stop writers, create and restore-check an appropriate database
backup, install the exact new package, run `sudo bpm-migrate`, and start BPM.
The database recovery rules in `database-upgrade-matrix-0.9.5.md` govern the
operation. `alembic downgrade` is not a rollback procedure.

## Build and release verification

Native release artifacts are built only after the product documentation package
is present and checksum-verified:

```text
make docs-package
make docs-package-verify
make native-package-build TARGET=<target>
make native-package-smoke TARGET=<target>
```

The builder mounts source read-only, isolates an amd64 target container, limits
CPU, memory, process, and open-file resources, and writes only transient
artifacts under `artifacts/native-packages/0.9.5.1/<target>/`. The receipt
contains the source revision, documentation checksum, frozen image/ISO
evidence, artifact checksum, architecture, and explicit-migration contract.

After all five packages pass their target smoke, `make native-package-stage-release`
creates the versioned release store at `distributions/releases/0.9.5.1/`.
`release-manifest.json` and `SHA256SUMS` are tracked delivery metadata;
`assets/` is ignored local upload staging containing the package, its checksum,
the target build-environment receipt, and its build receipt. The release
publisher uploads that exact staging set to the GitHub Release tag `v0.9.5.1`.
It must not commit the package binaries as ordinary Git blobs: GitHub blocks
files over 100 MiB and multiple BPM packages exceed this. GitHub Release assets
permit individual files under 2 GiB, so they are the release channel; Git LFS
is not used for distributable packages.

The smoke gate creates a fresh target userspace, installs the generated native
artifact through its own package manager, proves the unprivileged payload and
absence of optional AI distributions, performs `bpm-migrate`, checks root,
health, readiness, profiles, and installed documentation, then stops and
restarts BPM against the same state directory. Manjaro evidence additionally
records the stable branch after a full update.

`make native-package-smoke-all` runs targets one at a time. It is a manual
release gate; regular PR CI keeps only the fast manifest/package contract.
