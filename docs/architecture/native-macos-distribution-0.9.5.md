# BPM 0.9.5.1 Native macOS DMG Distribution Contract

Status: active native-DMG release-delivery contract.

## Scope

BPM 0.9.5.1 has two native DMG distribution targets for macOS 14 and later:

| Target | Runner used for assembly | Artifact |
| --- | --- | --- |
| Intel (`x64`) | `macos-15-intel` | `browser-policy-manager-0.9.5.1-macos-x64.dmg` |
| Apple Silicon (`arm64`) | `macos-14` | `browser-policy-manager-0.9.5.1-macos-arm64.dmg` |

They are independently frozen by `distributions/macos/targets.json` and built
only by the matching native macOS architecture. The process does not use a
container, VM, WSL, cross-compiled application, or the user's system Python.
`tools/macos_distribution.py` is the release-assembly entrypoint and does not
import BPM runtime modules.

## Bundle and lifecycle boundary

Each DMG contains `Browser Policy Manager.app`, a `BPM Migrate.command`, a
copy-to-Applications shortcut, and an operator readme. The application bundle is a
PyInstaller onedir payload containing private CPython 3.14.6, the exact
base-only dependency resolution, BPM code, the verified documentation archive
contents, Alembic configuration, and the released migration tree. Optional
`dev`, `ai`, and `postgres` extras, including NumPy, ONNX Runtime, and
Tokenizers, are absent.

The immutable program bundle is intended for `/Applications`. Default state is
owned by the installing user at
`~/Library/Application Support/Browser Policy Manager`; it includes the SQLite
database. The application does not modify system Python, `PATH`, firewall
policy, or another user's state. Removing the app leaves the state directory
for operator-controlled recovery.

DMG mount, copying to Applications, and server startup never invoke Alembic.
Before first use and every migration-bearing update, the operator runs
`BPM Migrate.command`, then opens the application. It serves only
`127.0.0.1:8000` by default. There is no launchd service, automatic login
item, privileged helper, or an automatic privileged deployment change.

## Evidence and release boundary

The manual `Native macOS DMG distribution gate` workflow first builds the
checksum-verified documentation archive, then builds frontend assets and runs
the native build/smoke gate on both architectures. The smoke proof mounts the
DMG, copies the app into a disposable Applications directory, proves migration
is explicit, runs migration, checks root/readiness/help/profiles, and restarts
against the same state directory. It uploads a DMG, checksum, build
environment, manifest, and smoke receipt for 30 days.

Those artifacts provide the build and clean-device evidence for the release
publication gate. Acceptance records a valid Developer ID signature, an Apple
notarization ticket, and clean-device testing on macOS 14+ Intel and Apple
Silicon Macs.

`distributions/releases/0.9.5.1/` is the versioned index for final release
assets. The protected Apple Developer publication workflow records the
Developer ID signature, submits the exact DMG to Apple notarization, staples
its ticket, and stages its checksum and receipts for the GitHub Release
`v0.9.5.1`.
