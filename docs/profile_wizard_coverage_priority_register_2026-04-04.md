# Profile Wizard Coverage Priority Register

This register implements `PB2.7 coverage prioritization by external enterprise evidence`.

It is intended for cases where local profile-library data is weak or absent. In that situation, new guided coverage should be prioritized by:

1. External enterprise evidence from Firefox Enterprise documentation and recurring admin scenarios.
2. Product judgment about how often a cluster matters in real administrator workflows.
3. UX fit: whether the cluster can be expressed as a clear scenario-first flow without turning the wizard into a schema mirror.

This register does not replace `PB2.9`.
Use it together with [`profile_wizard_advanced_only_boundaries_2026-04-04.md`](./profile_wizard_advanced_only_boundaries_2026-04-04.md).

## Scoring Model

Each cluster is reviewed against four dimensions:

- `Admin value`
  How much real enterprise/admin value the cluster tends to carry.
- `External evidence`
  How strongly the cluster is signaled by official Firefox Enterprise materials and recurring enterprise setup patterns.
- `Wizard fit`
  How well the cluster can be represented as a scenario-first flow instead of a raw schema editor.
- `Bloat risk`
  How likely the cluster is to damage the wizard if over-expanded.

Each dimension is rated `High`, `Medium`, or `Low`.

Decision meanings:

- `guided now`
  Expand guided coverage actively.
- `guided continue`
  We already started lifting this cluster; keep strengthening it.
- `quick focus + handoff`
  Keep a task-first entry and a strong jump into the technical path, but do not over-model it in guided UI yet.
- `advanced-only`
  Keep it outside guided mode by design.

## Priority Register

| Code | Cluster | Admin value | External evidence | Wizard fit | Bloat risk | Decision | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `PB2.8a` | Kiosk / shared-device | High | High | High | Medium | `guided continue` | Strong enterprise scenario with clear task-first bundles around locked homepage, site access, private session posture, and cleanup. |
| `PB2.8b` | Certificates / trust / auth | High | High | High | Medium | `guided continue` | Worth promoting as corp trust and enterprise sign-in flows. Keep deeper auth/cert shape editing available through technical controls. |
| `PB2.8c` | Extensions rollout governance | High | High | High | Medium | `guided continue` | Strong admin value and good scenario framing. Avoid going too deep into rare extension dictionaries in guided mode. |
| `PB2.8d` | Privacy / security hardening | High | High | High | Medium | `guided continue` | Hardening bundles fit guided mode well when expressed as posture and workflow rather than toggle grids. |
| `PB2.8e` | Updates / upkeep | High | High | High | Low | `guided continue` | Operationally important and easy to express clearly through upkeep posture. |
| `PB2.8f` | Site access / intranet routing | Medium | Medium | High | Medium | `guided later` | Good next guided target because it still maps well to allow/block/intranet scenarios. |
| `PB2.8g` | Home / startup / search | Medium | Medium | High | Medium | `guided later` | User-facing and easy to express, but usually lower enterprise value than trust, rollout, hardening, or upkeep. |
| `PB2.8h` | Language / locale | Medium | Medium | Medium | Low | `guided later` | Useful but narrower. Keep it behind the more operational clusters. |
| `PB2.8i` | AI surfaces | Low | Medium | Medium | High | `quick focus + handoff` | Keep guided coverage at posture/surface level. Provider/model depth should remain technical unless recurring demand becomes stronger. |

## Additional Decision Register

These clusters are not new `PB2.8x` items, but they should influence future prioritization.

| Cluster | Decision | Why |
| --- | --- | --- |
| Provider / model-specific AI rules | `quick focus + handoff` | The admin task exists, but the shape is still too irregular and open-ended for stable guided modeling. |
| Raw open-ended policy dictionaries | `advanced-only` | High structural variance and poor wizard fit. |
| Rare low-level preference bundles without a stable user task | `advanced-only` | They create schema-shaped UI rather than scenario-first UX. |
| Enterprise scenario bundles spanning multiple steps | `guided now` when coherent | Cross-step bundles often outperform raw policy lifting because they mirror how admins actually work. |

## Recommended Execution Order

This register intentionally separates `what matters most` from `what is already completed`.

1. Continue strengthening `PB2.8a` through more explicit shared-device flows only where they still improve task-first guidance.
2. Continue strengthening `PB2.8b` around common trust/auth posture, while keeping technical cards authoritative for deeper certificate and authentication detail.
3. Continue strengthening `PB2.8c`, `PB2.8d`, and `PB2.8e` as governance layers rather than raw-control expansions.
4. Take `PB2.8f` next as the most promising not-yet-fully-developed cluster.
5. Follow with `PB2.8g`, then `PB2.8h`.
6. Keep `PB2.8i` mostly at quick-focus and handoff depth unless stronger recurring demand appears.

## Usage Rules For Future Changes

- Do not add a new guided cluster only because the schema is nearby.
- Prefer scenario bundles that solve an administrator task end to end.
- If a cluster cannot be explained in one short task-first sentence, it is usually not ready for full guided promotion.
- If guided coverage grows, update coverage accounting and finish-step review in the same change.
- If a cluster is marked `quick focus + handoff`, improve entry and navigation first before considering deeper guided controls.
- Revisit this register whenever Mozilla enterprise guidance changes substantially or local usage evidence becomes strong enough to replace external priors.
