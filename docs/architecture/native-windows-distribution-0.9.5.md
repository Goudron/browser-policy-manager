# BPM 0.9.5.1 Native Windows Distribution Contract

Status: active release-delivery contract.

## Scope

BPM 0.9.5.1 delivers one native `windows/x64` MSI:

| Supported target | Artifact |
| --- | --- |
| Windows 10 x64 and Windows 11 x64 | `browser-policy-manager-0.9.5.1-windows-x64.msi` |

This installer is a direct Windows installation. WSL is neither installed nor
used by the MSI. Existing documentation for source deployment through WSL is
a separate route and does not describe this package.

`distributions/windows/targets.json` freezes the MSI name, WiX version,
CPython 3.14.6 Windows installer checksum, WinSW service wrapper checksum,
Windows service account, and permanent upgrade code. `tools/windows_distribution.py`
is the only release entrypoint; it does not import BPM runtime modules.

## Payload and ownership

The MSI installs an immutable private payload at
`C:\Program Files\Browser Policy Manager`:

- verified CPython 3.14.6 and a private base-only virtual environment;
- BPM 0.9.5.1 wheel and the Windows-specific locked base resolution;
- verified product documentation, Alembic configuration, and migration tree;
- `bpm.cmd`, elevated `bpm-migrate.cmd`, and the pinned WinSW service host;
- release manifest, licence, and BPM/WinSW third-party notices.

It creates the operator-owned `C:\ProgramData\Browser Policy Manager` state
directory and default `bpm.env` without overwriting an existing configuration.
The `BPM` service is manual and runs as `NT AUTHORITY\LocalService`; only that
service account and local administrators obtain write access to state. The
installer does not modify system Python, `PATH`, WSL, or firewall policy.

Base packages exclude `dev`, `ai`, and `postgres` extras. `uvloop` is absent
from the Windows lock because it is not a Windows runtime dependency; Uvicorn
uses the standard asyncio implementation there. This is a platform packaging
adaptation, not an optional BPM feature.

## Database and update lifecycle

MSI install, MSI upgrade, service registration, and service start never invoke
Alembic. An administrator must back up the database, install the exact MSI,
run the elevated `bpm-migrate.cmd`, and explicitly start `BPM`. Ordinary MSI
uninstall stops and unregisters the service but deliberately preserves
`ProgramData`, including the SQLite database and configuration. Downgrade is
blocked; Alembic downgrade is not a rollback procedure.

## Build, validation, and publication

The MSI build requires a native Windows x64 host, a checksum-verified
documentation package, WiX 4.0.6, and the two verified upstream binaries
named in `targets.json`. It produces transient evidence under
`artifacts/windows-packages/0.9.5.1/windows-10-11-x64/`.

The smoke gate uses a clean elevated Windows x64 host to prove silent install,
no automatic service start or migration, explicit migration, service start,
root/ready/help/profiles probes, stop/start persistence, and state retention
after uninstall. `windows-2022` CI validates assembly and this gate; it is not
evidence of Windows 10 compatibility. The release acceptance matrix therefore
also requires recorded clean smoke evidence on an actual Windows 10 x64 host
and an actual Windows 11 x64 host. The manual `windows-native-compatibility`
workflow targets dedicated self-hosted runners labelled `windows-10-x64` and
`windows-11-x64`, verifies the published MSI checksum and Authenticode status,
then retains a non-secret compatibility receipt for each host.

`make windows-package-stage-release` accepts only the smoke-passed MSI with a
valid Authenticode signature and writes the asset, checksum, build environment,
smoke receipt, and build receipt beneath
`distributions/releases/0.9.5.1/assets/windows-10-11-x64/`. It merges the MSI
into the common `SHA256SUMS` and `release-manifest.json` alongside Linux
packages. The publisher uploads those files to draft GitHub Release `v0.9.5.1`;
regular Git and Git LFS are not distribution channels.
