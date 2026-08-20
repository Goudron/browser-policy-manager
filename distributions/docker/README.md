# BPM 0.9.5.1 Docker distribution

This is the reproducible, single-node Docker distribution for Browser Policy
Manager 0.9.5.1. It contains the base BPM wheel, its released Alembic migration
payload, and the verified 0.9.5.1 product-documentation archive.

It is intentionally not a production topology. BPM 0.9.5.1 does not provide
authentication, authorization, TLS termination, reverse-proxy configuration,
backup automation, HA, or a PostgreSQL Compose deployment. The reference
Compose file binds the HTTP port to loopback only.

## Build and start

Build only from a tree that has a verified documentation package:

```bash
make docs-package
make docs-package-verify
make docker-build
```

Apply migrations explicitly to the named `bpm-data` volume before the first
start and before accepting a version whose release notes declare migrations:

```bash
make docker-migrate
make docker-up
curl -fsS http://127.0.0.1:8000/health/ready
```

Open `http://127.0.0.1:8000/profiles` after readiness succeeds. The image runs
as the unprivileged `bpm` user; persistent SQLite state is only in
`/var/lib/bpm`, backed by the named volume.

`make docker-down` stops the application but preserves the volume. Removing a
volume is a data-destructive operation and is intentionally not automated by a
Make target.

## Release verification

Run the actual image gate after the build:

```bash
make docker-smoke
```

The gate creates a disposable volume, runs `migrate`, starts BPM, proves the
base image has no optional AI distributions, checks the product version,
health/readiness, and installed documentation, then restarts BPM against the
same volume. Its output is release evidence, not an image publication step.

The Docker base is pinned to the OCI index digest for
`python:3.14.3-slim-bookworm`, and `requirements.lock` fixes the exact
base-runtime dependency resolution for Linux amd64. Its selected platform
manifest and the resulting image digest must be recorded when the image is
published. The initial release target is `linux/amd64`; multi-architecture
publication requires a separately reviewed lock and smoke evidence.

## Configuration boundary

The reference service accepts BPM's existing `BPM_*` settings. In particular,
`BPM_DATABASE_URL`, `BPM_DOCUMENTATION_SITE_DIR`, `BPM_ENABLE_CORS`, and
`BPM_CORS_ALLOW_ORIGINS` remain operator-owned configuration. Do not expose
this default instance beyond its loopback binding until organization-owned
controls for authentication, authorization, TLS, backups, monitoring, and
incident response are in place.
