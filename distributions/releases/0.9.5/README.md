# BPM 0.9.5 release assets

This is the versioned release store for BPM 0.9.5 native Linux packages, the
native Windows x64 MSI, and future signed/notarized native macOS DMGs. Git tracks this index, `SHA256SUMS`, and
`release-manifest.json`; it deliberately does not track generated package
binaries.

The packages are staged locally in `assets/` by:

```bash
make native-package-stage-release
make windows-package-stage-release
```

Those commands accept only packages whose per-target checksum and build receipt
match; Windows staging also requires a valid Authenticode signature. `assets/`
is ignored by Git and is the exact upload set for the GitHub
Release tag [`v0.9.5`](https://github.com/Goudron/browser-policy-manager/releases/tag/v0.9.5).
Publish its files as GitHub Release assets, not as ordinary Git blobs and not
through Git LFS. GitHub blocks ordinary Git files above 100 MiB, while this
release contains Debian packages above that limit; GitHub Release assets allow
each file below 2 GiB.

The current manual macOS workflow emits unsigned, non-notarized test
evidence only; it must not be copied to this store or published. A later Apple
Developer release workflow may stage a DMG here only after it records a valid
Developer ID signature and a stapled Apple notarization ticket.

Downloaders must verify the selected package with `SHA256SUMS` before
installation. `release-manifest.json` binds every asset to its target, source
revision, builder provenance, and per-target build receipt.
