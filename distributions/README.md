# BPM distribution staging

This repository-owned directory is the staging root for future BPM distributives.

`documentation/` contains the verified, versioned PDF documentation release only; it is not a
build cache. It must never contain local models, RAG indexes, embeddings, logs, reports,
credentials, source DITA or an unpacked documentation site.

`docker/` owns the BPM 0.9.5 Docker release recipe and its single-node Compose reference. Its
image is built from a base wheel, explicit Alembic payload, and a verified documentation archive;
it does not use the local documentation-site cache. See [`docker/README.md`](docker/README.md).

`native/` owns the five BPM 0.9.5 `linux/amd64` native package recipes: Ubuntu 26.04, Debian
13.5, Fedora 44, Linux Mint 22.3, and Manjaro stable. Packages contain the common private Python
runtime and use explicit migration. Builders write transient evidence under `artifacts/`; the
checked release store and upload staging live under [`releases/0.9.5/`](releases/0.9.5/).
See [`native/README.md`](native/README.md).

`windows/` owns the BPM 0.9.5 native `x64` MSI for Windows 10 and Windows 11.
It installs directly on Windows, not through WSL, and keeps migrations and
service activation explicit. See [`windows/README.md`](windows/README.md).
