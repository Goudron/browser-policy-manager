# BPM 0.9.0 DITA Publishing Toolchain Decision

Status: Accepted  
Decision date: 2026-06-21  
Backlog task: `BPM090-M2-06`

## Decision

BPM 0.9.0 product documentation will be authored as OASIS DITA 1.3 XML and published with the
standalone DITA Open Toolkit 4.4 distribution. Release builds use Eclipse Temurin JRE
`21.0.11+10` (HotSpot). DITA-OT itself supports Java 17 or later, but accepting whichever Java is
on a workstation would make local and CI results needlessly different.

The portal build uses the bundled `html5` transformation. It does not use the DITA 2.0 preview,
PDF output, a container image, a system package, or a third-party DITA-OT plug-in. A small
repository-owned plug-in, `org.bpm.docs.html5` version `0.9.0`, may extend the bundled transform
with BPM templates, semantic landmarks, and styles. It must contain no Java code and is licensed
with BPM under MPL-2.0. Search indexing, manifest generation, and orchestration remain BPM-owned
tools rather than DITA-OT plug-ins.

This task selects the toolchain; it does not install it. `BPM090-M3-03` must create the lock file,
bootstrap command, local cache, and notices before a documentation build is accepted.

## Pinned Components

| Component | Pin | License | Use |
| --- | --- | --- | --- |
| DITA Open Toolkit | `4.4`, release asset `dita-ot-4.4.zip` | Apache-2.0 | DITA validation, preprocessing, key/reference resolution, and HTML5 publishing |
| Eclipse Temurin JRE | `21.0.11+10`, HotSpot | GPL-2.0 with Classpath Exception | Exact Java runtime for local and CI release builds |
| DITA authoring level | OASIS DITA `1.3` | OASIS specification terms | Stable source grammar; DITA 2.0 preview features are forbidden |
| Output transform | bundled `html5` from DITA-OT `4.4` | Included in DITA-OT | Static portal pages and navigation input |
| BPM HTML customization | `org.bpm.docs.html5` `0.9.0` | MPL-2.0 | Repository-owned accessible shell hooks and styling |
| Build wrapper | BPM `0.9.0`, Python `>=3.14` standard library only | MPL-2.0 | Lock verification, clean builds, six-locale matrix, and deterministic post-processing |

The official DITA-OT archive URL is
`https://github.com/dita-ot/dita-ot/releases/download/4.4/dita-ot-4.4.zip`. The Temurin lock uses
official `adoptium/temurin21-binaries` release assets for tag `jdk-21.0.11+10`; it must contain a
separate URL and upstream SHA-256 for each supported OS/architecture. Mutable `latest` URLs and
floating container tags are forbidden in release builds.

DITA-OT 4.4 includes transitive components under Apache-2.0, ICU, EPL-1.0/LGPL-2.1, MPL-1.0, MIT,
and W3C terms. `BPM090-M3-03` must preserve the distribution's license files and record the full
upstream component/version/license table in the documentation toolchain notices. The Java and
DITA toolchains are build inputs and are not copied into the BPM runtime or documentation artifact.

## Lock And Reproducibility Contract

`documentation/config/toolchain-lock.json`, introduced by `BPM090-M3-03`, is the only installation
authority. It records exact versions, immutable release URLs, archive SHA-256 values, supported
platforms, licenses, and the first-party plug-in version. A bootstrap fails on an unknown platform,
missing digest, digest mismatch, version mismatch, or unrecorded plug-in.

The wrapper will provide these stable entry points:

- `make setup-docs-toolchain` performs the explicitly networked, checksum-verified bootstrap;
- `make docs-build` performs a clean offline build for all six locales;
- `make test-docs` validates DITA, links, output contracts, and determinism.

The bootstrap extracts archives into an ignored documentation tool cache and never installs Java
or DITA-OT globally. CI restores or creates the same checksum-addressed cache and invokes the same
wrapper. A developer's current Java may be used for exploratory diagnostics only. In particular,
the repository's observed OpenJDK 25 installation is not release-build evidence.

After bootstrap, builds are offline: no plug-in registry, package manager, remote schema, remote
font, CDN, API, or external-link fetch is permitted. DITA grammars and XML catalogs resolve from
the locked distribution and repository. Remote hyperlinks are emitted as links but are not opened
during publishing. The wrapper sets explicit source, output, temporary, locale, timezone, and
encoding inputs; generated timestamps and absolute workspace paths may not enter publishable files.

Two clean builds from the same source and lock must produce byte-equivalent publishable files after
documented archive normalization. Any unavoidable normalization must be narrow and tested rather
than hidden behind a broad file rewrite.

## Six-Locale Contract

One DITA project definition drives exactly these locale builds: `en`, `ru`, `de`, `zh-CN`, `fr`,
and `es-ES`. Sources and output are UTF-8; every root map/topic carries the exact `xml:lang`; paths,
keys, IDs, and anchors remain locale-independent. A missing map, translation, referenced asset, or
locale-specific screenshot fails the matrix and may not silently fall back to English.

DITA-OT provides standards-based XML processing and bundles ICU4J `77.1`, so the selected engine
can process Unicode and CJK source consistently. Locale-aware search tokenization and ranking are
not delegated to DITA-OT; they are deterministic BPM build outputs covered by later search tasks.

## Accessibility Contract

The bundled HTML5 transform is selected because it emits native HTML5 and supports embedded
`nav` navigation and semantic header/footer extension points. That is a suitable base, not an
accessibility certification. The first-party customization and portal tests must preserve or add:

- correct page `lang`, title, heading hierarchy, landmarks, and a keyboard-visible skip link;
- usable navigation, focus order, and focus indication without JavaScript-only navigation;
- authored alternative text and captions for localized screenshots;
- semantic tables, lists, notes, code, and link purpose;
- zoom, reflow, contrast, reduced-motion, and narrow-screen behavior.

`BPM090-M2-10` owns the detailed WCAG/security contract and `BPM090-M3-08` owns theme/browser
implementation. DITA validation, static output assertions, keyboard browser tests, and the six-
locale matrix are all required; a successful DITA transform alone is never treated as proof of
accessibility.

## Installation And Update Procedure

Installation is intentionally two-phase:

1. `BPM090-M3-03` downloads each selected official asset once, verifies its upstream SHA-256,
   records the immutable URL/digest in the lock, preserves license notices, and implements
   `make setup-docs-toolchain`.
2. The command extracts into the ignored checksum-addressed cache, installs only the local
   repository-owned plug-in, verifies Java and `dita --version`, then runs a minimal offline DITA
   1.3 HTML5 smoke build.

Updates are never automatic. A maintainer opens a focused change that updates the decision and
lock, reviews DITA-OT migration notes and every changed bundled license/dependency, regenerates the
cache from empty, and runs validation, two-build reproducibility, all six locale builds,
accessibility contracts, and documentation browser smoke. A DITA-OT or Java security update may
change the patch pin without changing this architecture, but it still requires those checks.
Adding any third-party plug-in requires a separate decision with an exact version, immutable
archive digest, license/provenance review, offline installation path, and demonstrated need.

## Alternatives Rejected

- **Floating latest DITA-OT or Java:** easy to start, impossible to reproduce or audit reliably.
- **Official DITA-OT container as the only path:** useful upstream, but adds a container runtime
  requirement and mutable base layers; an archive lock works in local and CI environments alike.
- **System DITA-OT/JDK packages:** versions and layouts vary by operating system and update outside
  the repository lock.
- **Third-party web-help/search plug-ins:** add supply-chain, license, localization, and CSP surface
  while BPM already needs its own manifest and deterministic non-AI search contract.
- **DITA 2.0 preview:** the grammar is not a final standard in DITA-OT 4.4 and would weaken source
  stability without helping the 0.9.0 portal.
- **PDF toolchain:** the Administrator/DevOps guide is part of the static web portal for source
  deployment and operations; PDF dependencies, pagination testing, and distribution-specific
  installer variants provide no current acceptance value.

## Official Sources

Verified on 2026-06-21:

- DITA-OT download, release date, and Apache-2.0 license: `https://www.dita-ot.org/download`
- DITA-OT 4.4 documentation and supported outputs: `https://www.dita-ot.org/4.4/`
- DITA XML/1.3 and DITA 2.0 preview status: `https://www.dita-ot.org/dev/topics/dita-xml-input`
- DITA-OT core dependency/license inventory: `https://www.dita-ot.org/4.4/reference/third-party-software`
- HTML5 processing and native navigation: `https://www.dita-ot.org/4.3/reference/html5-processing`
- Temurin `21.0.11+10` official release: `https://github.com/adoptium/temurin21-binaries/releases/tag/jdk-21.0.11%2B10`
- Temurin licensing and distribution FAQ: `https://adoptium.net/docs/faq/`
