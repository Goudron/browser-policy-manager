# BPM 0.9.3 Search Engine ADR

Date: 2026-07-29

Backlog item: `BPM093-M3-05`

Status: **Accepted own-engine decision; no external replacement is selected.**

## Decision

BPM 0.9.3 selects and evolves its existing BPM-owned static lexical search as the production search
path and fallback. It does **not** adopt Pagefind `1.5.2` or Meilisearch Community Edition `1.45.1`.
The decision criterion is comparative, not an invented absolute relevance floor: an external
replacement must be no worse than the frozen previous-version control and strictly more relevant in
each supported locale. No external candidate satisfies that rule. `BPM093-G05` is closed by this
own-engine decision; M4 remains responsible for proving browser/build parity and an improved revision
of the selected engine.

The retained implementation is BPM `0.9.3` source under MPL-2.0:

| Component | Exact source and identity | Artifact boundary |
| --- | --- | --- |
| Browser search adapter | `documentation/assets/theme/bpm-docs-search.js`, repository revision `43c362c65eded97106626e7535e5250e97574a6b` | BPM-owned source; generated static assets are not committed. |
| Index builder and validator | `documentation/tools/build_docs.py`, repository revision `43c362c65eded97106626e7535e5250e97574a6b` | Clean build creates per-locale `search/{locale}/index.json`, validates manifest semantics and packages it atomically. |
| License | `pyproject.toml` project metadata and `LICENSE` | MPL-2.0; no third-party search artifact is added to the production package. |

## Evidence And Candidate Disposition

The M3-01 primary rule compares each external candidate with the frozen previous-version control in
each locale. It must preserve Top-1, MRR, Recall@5, no-result handling, and exact identifiers, then
strictly improve relevance in that locale. A macro average cannot rescue a locale regression.

| Candidate | Exact version / artifact evidence | M3-03 hard result | M3-04 operability result | Decision |
| --- | --- | --- | --- | --- |
| Current BPM static control | BPM `0.9.3`, MPL-2.0, BPM-owned source above | Frozen control: `de` Top-1/Recall@5 0.719/0.750; `zh-CN` 0.719/0.750. | Current portal browser contract passed; same-origin static fallback remains available. | Select as BPM's own engine and improve it in M4. |
| Pagefind | `1.5.2`, MIT; npm SHA-256 `539357f51b47ea98cbef10bd774b432730d5a839ade5b5a30d13df033cbe9348`; Linux x64 SHA-256 `3c8dcfdaa69946113e0257be05bdef57297c7f1a562aa168536ff7c5d4590660` | Improves `de`, but regresses versus control in `en`, `ru`, `zh-CN`, `fr`, and `es-ES`. | 24→240-document fixture: 4.86→5.85 s indexing, 3,825,090→4,025,378 bytes; P95 4.28 ms. | Reject; it is not more relevant in every locale. |
| Meilisearch Community Edition | `1.45.1`, MIT; Linux amd64 SHA-256 `35986cba02cc4c9a2f79b4f85be8c2bc0013989c208410e6cfea85b1fdc3d708` | Regresses versus control in every locale. | Loopback-only service: 136.23 ms start, 54,400 KiB RSS, 4.80 ms P95; stop leaves static control available. | Reject; it is not more relevant in every locale. |

These results concern the frozen BPM corpus and tested configurations only. They do not make a
general claim about Pagefind or Meilisearch outside BPM.

## Migration And Fallback Boundary

- The existing static browser adapter, generated per-locale indexes, facets, URL state, exact IDs,
  localized unavailable state, same-origin CSP, and safe text-node rendering remain authoritative.
- No Pagefind or Meilisearch package, service, listener, browser adapter, generated vendor index,
  or migration code may enter the production artifact from this ADR.
- The M3-04 clean static-artifact install/update/rollback evidence remains the operational fallback
  pattern. Meilisearch service loss already demonstrated that the independent static control stays
  usable.
- M4 must improve the selected own implementation rather than introduce a vendor migration. Any M4
  change remeasures the browser result against the frozen control and preserves all existing search
  and AI-disabled contracts.

## Reconsideration Rule

A new candidate or a changed configuration may be reconsidered only after it passes the same public
entry gates and produces fresh M3-03 and M3-04 evidence on the accepted six-locale corpus and
i5-7200U/7.1 GiB CPU-only host. It must be no worse than the frozen control and strictly more
relevant in every locale without weakening the identifier, facet, CSP, offline, accessibility, or
fallback contract. Amend this ADR before adding a dependency or replacing the selected own engine.

## Verification

Focused check:

```bash
./.venv/bin/pytest -q tests/test_product_documentation_release_contract.py
```
