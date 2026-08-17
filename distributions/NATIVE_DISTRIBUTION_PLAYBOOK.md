# BPM native distribution operator playbook

This is the manual, version-scoped procedure for producing BPM native
distributions. It is deliberately **not** part of the normal release CI. Run
it only when a particular BPM version needs distributives, and record the
resulting GitHub Actions run URLs in that version's release evidence.

It covers the five `linux/amd64` native packages, the native Windows x64 MSI,
and the native macOS Intel and Apple Silicon DMGs. Docker is a separate
distribution contour and is out of scope.

The 0.9.5 reference implementation is the source of truth for the executable
commands and recipes:

| Platform | Operator reference | Manual workflow |
| --- | --- | --- |
| Linux | [`native/README.md`](native/README.md) | `.github/workflows/native-linux-distribution-smoke.yml` |
| Windows | [`windows/README.md`](windows/README.md) | `.github/workflows/windows-native-distribution-smoke.yml` |
| macOS | [`macos/README.md`](macos/README.md) | `.github/workflows/macos-native-distribution-smoke.yml` |

## Operating model

1. Create a version-scoped distribution contour in Git and review it like
   release code. Do not edit a published version's manifest or reuse its
   artifact paths.
2. Merge the contour and select the exact commit to build. The commit must be
   the same for documentation, frontend assets, every package, and every
   receipt.
3. Manually dispatch the relevant workflow(s), typing `RUN` in the guarded
   input. Nothing is built merely because a commit or tag was pushed.
4. Treat CI output as evidence first. Only assets that meet the platform's
   signing and device-acceptance rules may enter the versioned release store
   or a GitHub Release.

The workflow is intentionally split from product development: no feature,
schema, service, or installation behaviour is changed as a side effect of
following this playbook.

## 1. Decide the required scope

Before changing a recipe, make a short release decision containing:

- BPM version and the immutable source commit/tag to build;
- required platforms and targets;
- whether the output is internal test evidence or a publishable release;
- named operators for signing, GitHub Release publication, and device tests;
- acceptance dates and artifact retention requirements.

Use the existing target set unless the release decision explicitly changes
support:

| Contour | Targets |
| --- | --- |
| Linux | Ubuntu 26.04, Debian 13.5, Fedora 44, Linux Mint 22.3, Manjaro stable; all `linux/amd64` |
| Windows | Windows 10 x64 and Windows 11 x64; one native x64 MSI |
| macOS | macOS 14+ Intel x64 and Apple Silicon arm64; separate native DMGs |

Do not silently substitute a nearby operating-system image. In particular,
the Mint package must use its checksum-verified official Mint image, and an
Intel macOS DMG must be built on an Intel macOS runner rather than
cross-compiled on Apple Silicon.

## 2. Prepare the next version contour

Start from the prior version's checked-in recipes. The names below are
examples for `0.9.5`; replace every version-bearing value together in the new
contour.

1. Set the BPM project version according to the normal product-release
   process, freeze the intended source commit, and create the versioned
   release-store index at `distributions/releases/<version>/`. The index,
   `SHA256SUMS`, and `release-manifest.json` are Git-tracked; binary assets
   are not.
2. Copy and update the version-specific distribution manifests, tool constants
   and artifact paths. At minimum inspect `distributions/native/`,
   `distributions/windows/`, `distributions/macos/`,
   `tools/native_distribution.py`, `tools/windows_distribution.py`,
   `tools/macos_distribution.py`, and the three manual workflows named above.
   Their target version, artifact names, artifact upload names, summaries and
   paths must agree with `pyproject.toml`.
3. Preserve the release contracts: private pinned runtime; verified
   documentation archive; deterministic profile frontend assets; explicit
   migration; and no mutation of system Python, PATH, firewall policy, or
   unrelated user state.
4. Keep the workflows `workflow_dispatch`-only and keep the `RUN` guard. A
   new version must not be added to normal push or pull-request CI.
5. Update the distribution READMEs, system map/release documentation where the
   versioned contract changed, and focused tooling tests. Regenerate the
   Codex snapshot only if one of its declared source inputs changed.
6. Review the diff specifically for stale version strings and stale artifact
   directories. Useful checks are:

   ```bash
   rg -n '0\.9\.5|bpm-0\.9\.5|browser-policy-manager-0\.9\.5' \
     distributions tools .github/workflows Makefile
   make native-package-validate
   make windows-package-validate
   make macos-package-validate TARGET=all
   ```

   Run platform-specific validation only on its native platform. The commands
   prove the inputs and manifests; native build and smoke must still run on
   their matching hosts.

7. Merge the reviewed contour before dispatching a build. Do not create a
   release asset from uncommitted local recipes or from a different checkout.

## 3. Common release inputs

Every distribution build consumes the exact verified documentation archive and
the generated profile frontend assets. The CI workflows perform these steps;
for a local native build, run the equivalent commands first:

```bash
make setup-docs-toolchain
make docs-package
make docs-package-verify
npm ci
make verify-frontend-vendor
make check-profiles-css
make build-profile-frontend-bundles
```

Keep the documentation archive and its `.sha256` sidecar together. A missing
or mismatched archive is a hard stop, not a reason to package a cached site or
to skip the check.

The selected commit must have a clean, known working tree. Generated evidence
goes only below `artifacts/`; never add it to source control. Large package
files must not be pushed as normal Git blobs or Git LFS. Final binaries belong
to GitHub Release assets (each below GitHub's 2 GiB release-asset limit).

## 4. Manual assembly and smoke gate

In GitHub Actions, select the workflow for the new version's contour, choose
the reviewed branch/commit, enter `RUN`, and start it. Do not dispatch a
workflow whose version string differs from the source version being released.

| Workflow | Expected evidence | Do not call it success until |
| --- | --- | --- |
| Native Linux distribution release gate | Five package directories, checksums, manifests, and smoke receipts | all five target builds and explicit-migration/restart smokes pass |
| Native Windows MSI distribution gate | MSI, checksum, build environment, manifest, and smoke receipt | the native `windows-2022` assembly and smoke pass; this is not Windows 10/11 device acceptance |
| Native macOS DMG distribution gate | one DMG, checksum, build environment, manifest, and smoke receipt per architecture | Intel and Apple Silicon jobs both pass; neither one stands in for the other |

The standard gates upload evidence for 30 days. Download it immediately into
the controlled release workspace, retain the workflow URL and source SHA, and
verify the selected binary against its accompanying checksum before giving it
to a tester.

If a job fails, preserve its log and artifact evidence, fix the checked-in
recipe, then dispatch a new run from the new immutable commit. Never repair a
DMG/MSI/package manually after its checksum and receipt were produced.

## 5. Platform acceptance and publication

### Linux

After every target passed its CI smoke gate, stage only receipt-verified files
from a trusted native release environment:

```bash
make native-package-stage-release
```

Review the generated `SHA256SUMS` and `release-manifest.json` in
`distributions/releases/<version>/`. Upload only the staged files in its
ignored `assets/` directory to GitHub Release `v<version>`. Before external
publication, record a clean install/upgrade test for every supported Linux
target.

### Windows

The ordinary `windows-2022` workflow proves native assembly and smoke only.
Before staging, sign the exact MSI in the protected release environment with
the authorized Authenticode certificate, then run:

```powershell
make windows-package-stage-release
```

It must validate the signature and bind the signed MSI to the release
manifest. Publish the staged asset to GitHub Release `v<version>`, then run
the separate compatibility workflow on clean, dedicated self-hosted Windows
10 x64 and Windows 11 x64 machines. It must download and verify that signed
release asset; a test against an Actions artifact is insufficient.

### macOS

The current macOS gate intentionally emits **unsigned, non-notarized test
DMGs**. They are suitable only for controlled colleague testing; do not copy
them into `distributions/releases/<version>/` and do not attach them to a
GitHub Release. Testers may need to explicitly approve opening the app in
Gatekeeper and must run `BPM Migrate.command` before the first launch and each
migration-bearing update.

For a publishable macOS release, stop here until a protected Apple Developer
workflow exists and has access to a Developer ID Application identity and
Apple notarization credentials. That workflow must sign the exact native app
and DMG, submit it for notarization, wait for acceptance, staple the ticket,
then re-verify the stapled DMG. Only then may it stage the DMG, checksum and
receipts in the release store and be tested on clean macOS 14+ Intel and
Apple Silicon devices. Never use `codesign --deep` as a substitute for this
process.

Secrets, certificates, private keys, notarization passwords and temporary
tokens belong only in protected GitHub environments or the authorized signing
host. Do not commit them, print them in a workflow summary, or place them in
an artifact.

## 6. Required tester handoff

For each candidate, provide the tester with the artifact URL, SHA-256,
supported target, source revision, known signature/notarization state and
these checks:

1. Start from a clean supported device or VM and verify the checksum.
2. Install/copy the native artifact exactly as documented; do not use WSL,
   Docker or the system Python as a substitute.
3. Prove migration remains explicit. Run the supplied migration command with
   the required elevation; installation, upgrade and normal start must not run
   it implicitly.
4. Start BPM, check `http://127.0.0.1:8000/health/ready`, documentation and
   profiles, then restart it against the same state.
5. For an update candidate, preserve the previous state, perform the explicit
   migration and repeat the checks.
6. Test normal removal and confirm that operator-owned state is retained as
   documented. Record OS version, hardware architecture, artifact checksum,
   timestamp and result.

## 7. Failure guide learned from 0.9.5

| Symptom or risk | Required response |
| --- | --- |
| A macOS app bundle starts then reports a missing bundled Python runtime | Build the `.app` through PyInstaller's native `--windowed` bundle layout. Do not hand-wrap its files in a second application bundle. |
| A packaged macOS app fails with `ModuleNotFoundError: aiosqlite` | Add and test the missing runtime dependency as a PyInstaller hidden import in the checked-in build recipe, then rebuild both architectures. |
| `codesign --deep` tries to sign `*.dist-info` or another non-code resource | Do not use deep signing. For test DMGs keep the explicit `unsigned-test-only` status. For production, sign only the actual code objects in a dedicated Developer ID workflow, then notarize and staple. |
| DMG cleanup reports that its volume is busy | Ensure the smoke/build cleanup force-detaches the mounted DMG before removing its temporary directory; verify a fresh run can mount it again. |
| One macOS architecture passes | Wait for both native jobs. Intel and arm64 bundles are independent acceptance targets. |
| A package builds but has no verified documentation or frontend assets | Stop. Rebuild the checksum-verified documentation archive and deterministic frontend bundle; never use an unverified cache. |
| An installer starts the service or migration automatically | Treat it as a release-contract regression. Restore explicit migration and explicit service activation before rebuilding. |
| An MSI is built on `windows-2022` | Treat it as assembly evidence only. Require signed release-asset checks on actual Windows 10 and Windows 11 before publication. |
| A colleague needs a macOS DMG before signing credentials exist | Hand over the unsigned test artifact with its checksum and Gatekeeper warning; do not call it a production release or stage it. |
| A generated binary is too large for normal Git | Keep it ignored and attach it to the GitHub Release, never to a commit or Git LFS. |

## 8. Closeout checklist

The distribution effort is complete only when the release record contains:

- exact source tag/commit and the successful workflow URLs;
- per-target artifact names, SHA-256 values, manifests, build environments and
  smoke receipts;
- signing and notarization evidence where publication requires it;
- clean-device acceptance records for every declared platform;
- the reviewed `SHA256SUMS` and `release-manifest.json` that match the uploaded
  assets; and
- an explicit note for intentionally test-only artifacts and their expiry.

If the release is test-only, close the record as test delivery and retain the
evidence. Do not promote it later without rerunning the appropriate signing,
notarization, checksum and device-acceptance steps.
