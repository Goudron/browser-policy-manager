# BPM distribution staging

This repository-owned directory is the staging root for future BPM distributives.

For a future-version native package run, start with the manual
[`NATIVE_DISTRIBUTION_PLAYBOOK.md`](NATIVE_DISTRIBUTION_PLAYBOOK.md). It
creates and dispatches a reviewed, version-scoped contour only when
distributives are requested; it is not part of ordinary release CI.

`documentation/` contains the verified, versioned PDF documentation release only; it is not a
build cache. It must never contain local models, RAG indexes, embeddings, logs, reports,
credentials, source DITA or an unpacked documentation site.

`docker/` owns the BPM 0.9.5.1 Docker release recipe and its single-node Compose reference. Its
image is built from a base wheel, explicit Alembic payload, and a verified documentation archive;
it does not use the local documentation-site cache. See [`docker/README.md`](docker/README.md).

`native/` owns the five BPM 0.9.5.1 `linux/amd64` native package recipes: Ubuntu 26.04, Debian
13.5, Fedora 44, Linux Mint 22.3, and Manjaro stable. Packages contain the common private Python
runtime and use explicit migration. Builders write transient evidence under `artifacts/`; the
checked release store and upload staging live under [`releases/0.9.5.1/`](releases/0.9.5.1/).
See [`native/README.md`](native/README.md).

`windows/` owns the BPM 0.9.5.1 native `x64` MSI for Windows 10 and Windows 11.
It installs directly on Windows, not through WSL, and keeps migrations and
service activation explicit. See [`windows/README.md`](windows/README.md).

`macos/` owns the BPM 0.9.5.1 native `x64` and `arm64` DMG distribution for
macOS 14 and later. Its release gate includes device smoke testing and the
normal Developer ID signing/notarization publication boundary. It keeps
migration explicit and all state in the installing user's Library directory.
See [`macos/README.md`](macos/README.md).
