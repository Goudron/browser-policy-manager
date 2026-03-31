Minimal unsigned WebExtension fixture for deterministic Firefox live policy tests.

Stable identifiers:

- Add-on ID: `bpm-live-test@example.org`
- Display name: `BPM Live Test Extension`

This fixture is packaged into `test-extension.xpi` by the live-test harness and
served from the local project HTTP server. It is intended for enterprise policy
flows such as `ExtensionSettings`, not for production browser use.
