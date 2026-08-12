# Documentation Toolchain Third-Party Notices

These dependencies are development/build inputs only. They are cached below
`documentation/.cache/`, are not installed globally, and are not copied into the BPM runtime or
published documentation artifact. Upstream archives retain their bundled license files.

| Component | Locked version | License | Source |
| --- | --- | --- | --- |
| DITA Open Toolkit | 4.4 | Apache-2.0; bundled transitive notices also cover ICU, EPL-1.0/LGPL-2.1, MPL-1.0, MIT, and W3C terms | `dita-ot/dita-ot` official 4.4 release |
| Eclipse Temurin JRE (HotSpot) | 21.0.12+8 | GPL-2.0 with Classpath Exception; bundled third-party notices apply | `adoptium/temurin21-binaries` official release |
| attrs | 26.1.0 | MIT | PyPI |
| iniconfig | 2.3.0 | MIT | PyPI |
| jsonschema | 4.26.0 | MIT | PyPI |
| jsonschema-specifications | 2025.9.1 | MIT | PyPI |
| packaging | 26.3 | Apache-2.0 OR BSD-2-Clause | PyPI |
| pluggy | 1.6.0 | MIT | PyPI |
| Pygments | 2.20.0 | BSD-2-Clause | PyPI |
| pytest | 9.0.3 | MIT | PyPI |
| PyYAML | 6.0.3 | MIT | PyPI |
| referencing | 0.37.0 | MIT | PyPI |
| rpds-py | 0.30.0 | MIT | PyPI |

The repository-owned `org.bpm.docs.html5` plug-in identity is reserved at version `0.9.0` under
MPL-2.0. It is not installed by this task because its source does not exist yet; adding it requires
changing its lock state and bootstrap validation in the same reviewed change.
