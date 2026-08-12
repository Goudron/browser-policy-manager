# Firefox Live Testing

These tests run against a real Firefox binary without touching your everyday browser profile.

They validate the live Firefox runtime behavior of exported `policies.json` documents. They do
not drive the BPM `/profiles` UI, wizard flow, or Chromium product audit path.

## Isolation model

- Firefox runs in `headless` mode by default.
- Every test creates its own temporary Firefox profile.
- The harness reuses a checksum-verified, immutable Firefox installation under `.bpm-test-browsers/`.
- Each run clones that installation before writing `distribution/policies.json`; it never writes
  into the verified installation. Firefox ESR 115 is a separate browser binary
  from the ESR 115 policy-template source (`v5.12`) used by schema generation;
  the template tag is not a browser version or live-browser download.
- Your normal Firefox profile and settings are not reused.

## Project-local sandbox

The provisioner stores verified archives under `.bpm-test-browsers/cache/` and
channel-specific immutable installs under `.bpm-test-browsers/installs/`. The manifest
`tools/firefox_live_browsers_manifest_0_9_4.json` owns URLs, SHA-256 values, platforms,
Firefox channels, and the matching geckodriver.

If you prefer explicit paths, you can still use:

- `BPM_FIREFOX_BIN`
- `BPM_GECKODRIVER_BIN`

## Sandbox lifecycle

Treat `.bpm-test-browsers/` as disposable local state:

- it is intentionally ignored by git;
- it can be several hundred megabytes after Firefox and geckodriver are installed;
- it is safe to remove when you need to reclaim disk space or force a fresh browser install;
- it should not be copied into docs, screenshots, release bundles, or frontend vendor assets.

Use the explicit cleanup target when you want to remove the sandbox together with other ignored
local artifacts:

```bash
make clean-local-artifacts
```

After cleanup, run `make setup-firefox-live-browsers` again before the next live Firefox suite.
For a quick local size check without deleting anything, run `make repo-health` and review the
`Ignored Local Artifacts` section.

## Quick setup

Linux helper:

```bash
make setup-firefox-live-browsers
```

The helper downloads exact Linux x86-64 archives, verifies their SHA-256 values in a temporary
staging directory, checks the extracted executable versions, and only then atomically promotes a
channel-specific immutable install. It prints flushed `phase/channel` progress, including the
real completed/total channel count when invoked with `FIREFOX_CHANNEL=all`. The exact URLs and
SHA-256 values remain manifest-owned; it never resolves a floating `latest` artifact.

To install the ESR sandbox instead, pass the channel through Make:

```bash
make setup-firefox-live-browsers FIREFOX_CHANNEL=esr115
```

The supported deterministic channels are `release` (Firefox `153.0.3`), `esr153` (Firefox
`153.0esr`), `esr140` (Firefox `140.13.0esr`), and `esr115` (Firefox `115.38.0esr`), all paired
with geckodriver `0.37.1`. ESR 115 uses Mozilla's immutable
`firefox-115.38.0esr.tar.bz2` archive; its manifest SHA-256 is
`24ad694f543b251482f62b6313f1e10bdfafa3279a2aec8aae6042c0b3eed530`.
Verify a provisioned channel before a rerun:

```bash
make verify-firefox-live-browsers FIREFOX_CHANNEL=esr153
```

The exact URLs, SHA-256 values, and installed versions are owned by the manifest and provisioning
tool. Floating downloads are not accepted.

Then run:

```bash
make test-firefox-live
```

The default `pytest` run excludes `firefox_live` and `firefox_live_amo`, so use
the explicit Make target above when you want the deterministic real-browser suite.

For the reviewed end-to-end workflow with timeout, per-channel artifacts, and a terminal summary,
use:

```bash
make firefox-live-workflow FIREFOX_CHANNEL=release
```

To provision and run each independently pinned deterministic channel in sequence, retaining a
per-channel `versions.json`, `run-summary.json`, JUnit result, safe pytest log, skipped-scenario
count, and failure artifacts, use:

```bash
make firefox-live-four-channel-workflow
```

This all-channel target reports Release 153, ESR 153, ESR 140, and ESR 115 as channels `1/4`
through `4/4`; one failed channel does not suppress the retained summaries for later channels.

## AMO canary

The main `firefox_live` suite stays deterministic and avoids dependencies on external add-on services.

Real AMO extension-install coverage lives in a separate canary suite:

```bash
make test-firefox-live-amo
```

This currently verifies that Firefox can force-install `uBlock Origin` from AMO through
`ExtensionSettings`.

## Current live scenarios

- `BlockAboutConfig`: Firefox loads the policy and blocks `about:config`.
- `WebsiteFilter`: Firefox loads the policy and blocks a local test page.
- `Homepage`: Firefox loads the policy and updates runtime startup preferences inside the live browser.
- `Preferences`: Firefox applies and locks a managed runtime preference.
- `DisablePrivateBrowsing`: Firefox disables private browsing surfaces through policy.
- `RequestedLocales`: Firefox updates runtime locale preferences and locale service state.
- `OverrideFirstRunPage`: Firefox overrides the first-run welcome target and disables default welcome flow.
- `DisableAppUpdate`: Firefox hides managed update controls in `about:preferences`.
- `Proxy`: Firefox routes real HTTP traffic through a managed proxy and updates proxy prefs.
- `Certificates.Install`: Firefox trusts a managed CA and successfully opens a local HTTPS page that otherwise fails certificate validation.

These scenarios intentionally focus on the Firefox policy engine itself:

- the harness renders a canonical `policies.json`
- writes it into the isolated Firefox sandbox
- launches real Firefox with Selenium
- verifies either live browser behavior or runtime Firefox state

## Current AMO scenario

- `ExtensionSettings` + AMO: Firefox force-installs `uBlock Origin` from
  `https://addons.mozilla.org/firefox/downloads/latest/ublock-origin/latest.xpi`
  and the test confirms the installed add-on via Firefox `AddonManager`.

## CI jobs

- `.github/workflows/ci.yml`
  Does not run live Firefox suites.
- `.github/workflows/firefox-live.yml`
  Runs the deterministic local suite weekly and by manual dispatch when `run_live_tests`
  is set to `RUN`, separately for `release`, `esr153`, `esr140`, and `esr115`.
- `.github/workflows/firefox-live-amo.yml`
  Runs the separate AMO canary suite only by manual dispatch when
  `run_live_tests` is set to `RUN`, separately for `release`, `esr153`, and `esr140`.
  AMO remains external to the four-channel deterministic policy gate.
