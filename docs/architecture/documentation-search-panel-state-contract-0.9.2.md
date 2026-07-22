# BPM 0.9.2 Documentation Search Panel State Contract

Date: 2026-07-17
Status: active contract
Backlog item: `BPM092-M2-07`

## State Model

Documentation search owns an independent boolean `filtersExpanded`. Its initial value is `false`
for a newly opened documentation page or direct search URL. The only user event allowed to change
it is activation of the explicit advanced-filter disclosure control.

Query text, selected filters, result ranking, result rendering, URL parameters, recent-query
storage, locale, browser history, and `filtersExpanded` are separate state dimensions. A selected
filter does not imply that filters must be visible.

| State dimension | Authority | May change `filtersExpanded`? |
| --- | --- | --- |
| Query and selected filters | Existing deterministic local search and repeat-parameter URL contract. | No. |
| Result set, count, highlights, empty state | Deterministic local ranking/rendering. | No. |
| Advanced-filter visibility | Explicit disclosure toggle; retained in the current history/session UI state. | Only the toggle. |
| Locale and theme | Existing product/documentation preference behavior. | No. |

When a browser-history entry has a recorded panel state, `popstate` restores that value. When it
does not, URL hydration starts collapsed, including a direct URL with query parameters or active
filters. Search URL parameters do not gain an expansion flag and remain shareable search state,
not a presentation command.

## Required Event Behavior

| Event | Query/filter/result behavior | Required `filtersExpanded` behavior |
| --- | --- | --- |
| Initial load with no query | Show compact search row. | `false`. |
| Initial/direct URL hydration with query and/or filters | Restore query and selected filters; run deterministic search. | `false` unless the current browser-history entry records a user-selected value. |
| Recent-query hydration | Restore the permitted recent query and run search if applicable. | Preserve current value; do not expand. |
| Advanced toggle click, Space, or Enter | Keep query, filters, result set, URL, and ranking unchanged. | Toggle the boolean and record it for the current history/session entry. |
| Query submit button or Enter in query field | Run search and update its normal URL/recent-query state. | Preserve current value. |
| Filter checkbox/select change | Update selected filters, results, URL, counts, and compact summary. | Preserve current value. |
| Clear query / clear filters / clear all | Clear only the requested search data and update result/URL state. | Preserve current value. |
| Result render, empty result, result link navigation preparation | Render normal deterministic state and announcements. | Preserve current value. |
| Back/forward | Hydrate query/filter state for the destination history entry. | Restore recorded value, otherwise `false`; never infer expansion from filters/results. |
| Escape while focus is inside the search component | Does not clear query, filters, or results. | Collapse only when expanded, then return focus to the disclosure control. |

## Compact Results And Hidden Filters

Results and their live status are not advanced-filter controls. M9 separates them from the
collapsible filter/help region so that a collapsed panel can remain collapsed while search results,
result count, empty-result recovery, and links remain visible.

When filters are active while the panel is collapsed, the compact search row exposes a localized
active-filter count/summary and keyboard-reachable clear-all action. The summary names that filters
are active without enumerating a multi-line tutorial. Screen readers receive the same selected
filter/result state through associated text and the existing polite live region.

## Accessibility And Non-Goals

- The disclosure is a real button with localized accessible name, `aria-expanded`, and
  `aria-controls`; the panel’s `hidden` state agrees with the attribute.
- Tab order remains query, submit, clear, disclosure, compact filter summary/clear action when
  present, expanded filters when open, results, and result links in DOM order. Focus is never
  trapped by opening or collapsing.
- Collapsing never clears query/filter/result state. Opening never changes rank, query, filters,
  URL, or results.
- Search remains local, deterministic, offline-capable, and non-AI. This contract does not change
  ranking, corpus, facets, URL parameter names, highlighting, or locale labels.

## Failure Conditions And Evidence

The implementation fails if any submit, Enter, filter change, clear action, URL hydration,
recent-query hydration, result render, empty result, or history transition calls the expansion
setter with a value inferred from query/filter/result state. It also fails if a collapsed filter
panel hides results/status or makes active filters undiscoverable.

M9 adds unit/contract and browser tests for every table row above in all six locales, including a
collapsed search with active filters and results, an expanded search through repeated submit/clear
events, and back/forward restoration. Existing search UI/filter contracts remain authoritative for
ranking, facets, localization, URL semantics, and no-AI behavior.
