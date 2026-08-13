# BPM 0.9.5 native Windows MSI

This directory owns the native `x64` Windows installer for BPM 0.9.5. It is
not a WSL wrapper: the MSI installs BPM, its private CPython runtime, and its
Windows Service directly on the Windows host.

The supported product targets are Windows 10 x64 and Windows 11 x64. A build
on `windows-2022` proves assembly only; release acceptance requires the clean
install/upgrade smoke matrix on actual Windows 10 and Windows 11 x64 hosts.
Run the manual `Native Windows MSI compatibility evidence` workflow once on
each clean, dedicated self-hosted runner labelled `windows-10-x64` and
`windows-11-x64`; it downloads and verifies the signed GitHub Release asset
before generating its non-secret compatibility receipt.

## Layout and lifecycle

- immutable program payload: `C:\Program Files\Browser Policy Manager`;
- operator-owned configuration, SQLite database, and logs:
  `C:\ProgramData\Browser Policy Manager`;
- manual `BPM` Windows Service under `NT AUTHORITY\LocalService`; and
- explicit, elevated `bpm-migrate.cmd` before the first service start and
  before each migration-bearing update.

The MSI never invokes Alembic or starts BPM during install or upgrade. It does
not modify a system Python, `PATH`, firewall policy, or WSL. Normal uninstall
stops and unregisters the service but preserves `ProgramData` for
operator-controlled recovery.

## Build and release commands

Run these only from a native elevated Windows x64 host with the pinned WiX
tool installed. The documentation package must already be built and verified:

```powershell
make docs-package
make docs-package-verify
make windows-package-build
make windows-package-smoke
```

The result is transient evidence under
`artifacts/windows-packages/0.9.5/windows-10-11-x64/`. Staging a release
additionally requires an Authenticode-valid MSI; set the certificate material
only in the protected release environment, then run:

```powershell
make windows-package-stage-release
```

It writes the MSI, checksum, build environment, smoke receipt, and signed
build receipt to the ignored upload area
`distributions/releases/0.9.5/assets/windows-10-11-x64/`, and merges its
metadata into the shared release manifest. Publish those generated files to
the existing GitHub Release `v0.9.5`, never as regular Git or Git LFS blobs.
