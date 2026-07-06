# Generated DITA Boundary

Files below this directory are reproducible outputs from approved BPM inventories. They must declare
their generator/source version and must never be hand-edited except inside explicit reviewed region
markers documented by the generator contract.

This directory is ignored by default except for this boundary file and explicitly allowlisted
generated-source families. Do not use it as an English fallback, a scratch directory, or a place to
paste upstream documentation.

`firefox/` is the first committed generated-source exception. It is produced by
`documentation/tools/generate_firefox_policy_skeletons.py` from the maintained Firefox policy
documentation inventory and contains schema-grounded DITA reference skeletons, a generated map,
examples, channel-difference metadata, and provenance-review metadata.

`cis/` is the second committed generated-source exception. It is produced by
`documentation/tools/generate_cis_recommendation_skeletons.py` from the maintained CIS
documentation inventory and contains BPM-authored mapping-fact DITA skeletons, a generated map, and
an index that keeps unresolved recommendations as provenance-only records without publishing
restricted benchmark expression.
