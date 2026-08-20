# BPM 0.9.5.1 native macOS DMG

This contour builds separate native macOS DMGs for Intel (`x64`) and Apple
Silicon (`arm64`) Macs. It is a native application bundle, not a container,
VM, WSL, or a wrapper around the system Python.

## Distribution lifecycle

The manual GitHub Actions workflow `Native macOS DMG distribution gate` builds
and smoke-tests both targets on GitHub-hosted macOS runners. Release
publication uses the normal Developer ID signing and Apple notarization
boundary before the verified DMG is staged in the versioned release store.

After copying `Browser Policy Manager.app` from the mounted DMG to
`/Applications`, an operator must run `BPM Migrate.command` from the DMG before
the first launch and before every migration-bearing update. The application
then starts BPM at `http://127.0.0.1:8000`; its default state (SQLite database
included) is under `~/Library/Application Support/Browser Policy Manager`.
The app never changes system Python, PATH, firewall policy, or another user's
state. Removing the app does not remove that state directory.

Local assembly and smoke need a native macOS host and a verified documentation
package:

```bash
make docs-package
make docs-package-verify
make macos-package-build TARGET=all
make macos-package-smoke TARGET=all
```

The generated DMGs and receipts are transient evidence under
`artifacts/macos-packages/0.9.5.1/<target>/`. The verified signed and notarized
DMGs are staged in `distributions/releases/0.9.5.1/assets/` for publication.
