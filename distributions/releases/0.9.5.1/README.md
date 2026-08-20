# BPM 0.9.5.1 release assets

This is the versioned release store for BPM 0.9.5.1 native Linux packages, the
native Windows x64 MSI, and the native macOS x64 and arm64 DMGs. Git tracks this
index, `SHA256SUMS`, and `release-manifest.json`; it deliberately does not track
generated package binaries.

The release process stages verified target artifacts in `assets/` and publishes
them as GitHub Release assets at the GitHub Release tag
[`v0.9.5.1`](https://github.com/Goudron/browser-policy-manager/releases/tag/v0.9.5.1),
not as ordinary Git or Git LFS blobs. The supported targets are Ubuntu 26.04,
Debian 13.5, Fedora 44, Linux Mint 22.3, Manjaro stable, Windows 10/11 x64, and
macOS 14+ x64/arm64.

Downloaders must verify the selected package with `SHA256SUMS` before
installation. `release-manifest.json` binds every asset to its target, source
revision, builder provenance, and per-target build receipt.
