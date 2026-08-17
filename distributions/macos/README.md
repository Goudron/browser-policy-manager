# BPM 0.9.5 native macOS DMG

This contour builds separate native macOS DMGs for Intel (`x64`) and Apple
Silicon (`arm64`) Macs. It is a native application bundle, not a container,
VM, WSL, or a wrapper around the system Python.

## Test build and lifecycle

The manual GitHub Actions workflow `Native macOS DMG distribution gate` builds
and smoke-tests both targets on GitHub-hosted macOS runners. Its DMGs are
test artifacts only: they use an ad-hoc signature, not a Developer ID
signature, and are not notarized because release signing material is not
present in the workflow. macOS may therefore ask a tester to explicitly
approve opening the application. Do not treat this artifact as a production
release.

After copying `Browser Policy Manager.app` from the mounted DMG to
`/Applications`, a tester must run `BPM Migrate.command` from the DMG before
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
`artifacts/macos-packages/0.9.5/<target>/`. A release process is intentionally
deferred until an Apple Developer signing identity and notarization credentials
are supplied; only a signed and notarized DMG may be staged in the versioned
release store.
