# Firefox Schema Lifecycle Documentation Impact Inventory (BPM 0.9.5)

Status: accepted M8-01 authoring inventory. This is the ownership handoff for
M8-02 through M8-06, not reader-facing product documentation and not authority
to alter generated documentation artifacts.

The normative machine-readable inventory is
[`firefox-schema-lifecycle-documentation-impact-inventory-0.9.5.json`](firefox-schema-lifecycle-documentation-impact-inventory-0.9.5.json).
It derives product facts from the active lifecycle catalog, conversion contract,
UI interaction contract, CIS inventory, and retirement safety contract.

## Source and generated boundaries

M8-02 authors English DITA and M8-03 supplies reviewed equivalent content in
`ru`, `de`, `zh-CN`, `fr`, and `es-ES`. The four guide maps, search records,
All settings help-target map, screenshot matrix, built site, PDFs, package, and
installed site are separate consumer boundaries. M8-04 refreshes those only after
source review; no task hand-edits generated HTML, search, manifest, PDF, or
installed output.

## Single-owner audience map

| Delivered behavior or support boundary | One audience owner | M8 authoring destination |
| --- | --- | --- |
| Four-channel choice and ESR 115 legacy-system caveat | User | User Guide |
| Policy availability by exact artifact | Firefox Policy reader | Firefox Policy Guide |
| CIS layers and presets by channel | CIS reader | CIS Settings Guide |
| Manual conversion, preview, confirmation, and apply | User | User Guide |
| Latest-ESR recommendation | User | User Guide |
| Shipped conversion preview/apply operations | API integrator | Administrator Guide |
| Retired-ESR successor migration | Administrator/DevOps operator | Administrator Guide |
| Conversion failure and retirement recovery | Support/troubleshooting reader | Administrator Guide |

A support boundary stays with the listed owner: a recommendation is not an
automatic write; a blocked, stale, invalid, or failed manual conversion does
not alter a profile; and a future retired-ESR upgrade is backup-gated Alembic
work, not a manual conversion or downgrade procedure.

## Guide and consumer disposition

All four published guide families are affected. Consequently there is no
untouched guide in this release; any later guide marked `unaffected` must name
its reason in the JSON inventory before editorial closure.

| Consumer | Owner | Disposition |
| --- | --- | --- |
| Schema inventory | Firefox Policy reader | M8-04 rebuilds it from the four-channel catalog. |
| Search | User | M8-04 adds reviewed locale aliases and regenerates deterministic search after source review. |
| Contextual help | User | M8-04 verifies existing editor targets and may add no generic replacement for inline consequence/recovery copy. |
| Screenshots | User | M8-04 refreshes only affected pre-approved matrix rows; a conversion-review scenario requires explicit approval. |

## Three-channel disposition

The machine inventory lists every confirmed active reader-facing three-channel
claim and assigns it to M8-02/M8-03, M8-04, or README M8-06. The old Firefox
153 dual-ESR contract is not rewritten: it is historical evidence and already
links to the active four-channel lifecycle contract. No current guide, index,
search target, help target, or screenshot claim may rely on that historical
record after M8 closure.
