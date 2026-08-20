# BPM 0.9.5.1 Docker Distribution Contract

Status: active release-delivery contract.

## Scope

The Docker distribution is a Linux single-node delivery of the existing BPM
0.9.5.1 release runtime. It does not change application behavior or widen the
product security and deployment boundary. It contains:

- a wheel built from the BPM 0.9.5.1 base package without `dev`, `ai`, or
  `postgres` extras;
- the exact Linux amd64 base-runtime dependency resolution in
  `distributions/docker/requirements.lock`;
- the released Alembic configuration and migration tree;
- the verified `bpm-documentation-0.9.5.1.tar.gz` package extracted to the
  runtime documentation path;
- one persistent SQLite volume at `/var/lib/bpm`; and
- an unprivileged `bpm` runtime user.

The Dockerfile is `distributions/docker/Dockerfile`; its reference operational
surface is `distributions/docker/compose.yaml`. The base is the pinned OCI
index digest for `python:3.14.3-slim-bookworm`, and the first release platform
is Linux amd64.

## Database lifecycle

`app.main` verifies the released Alembic head during startup but must not
perform writes or upgrades. The image preserves this boundary:

```text
make docker-build
make docker-migrate   # explicit `alembic upgrade head`
make docker-up        # `uvicorn`; verifies the exact release head
```

The application may be stopped and started without removing `bpm-data`. A
volume deletion, database restore, and migration recovery stay operator-owned
actions governed by `database-upgrade-matrix-0.9.5.md`.

## Release gate

Before publishing an image, maintainers run:

```text
make docs-package
make docs-package-verify
make docker-build
make docker-smoke
```

`docker-smoke` proves a clean image starts only after explicit migration,
responds on `/`, `/health`, `/health/ready`, `/help/`, has BPM `0.9.5.1`, has no
NumPy, ONNX Runtime, or Tokenizers distribution, and remains ready after a
restart on the same temporary volume. The release record retains the source
revision, documentation-archive checksum, base-image digest, image digest,
platform, command transcript, and smoke result.

## Explicit exclusions

This delivery does not provide a production claim. Authentication,
authorization, TLS termination, reverse proxy, firewall policy, backup
automation, monitoring, audit logging, HA/failover, PostgreSQL Compose
topology, and multi-platform release are outside its scope. The Compose port
is loopback-bound by default; any broader exposure is an operator decision.
