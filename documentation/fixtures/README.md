# Documentation Fixtures

Fixtures are compact, deterministic, synthetic inputs for DITA build, manifest, search,
localization, screenshot, and serving tests. They may model invalid input when clearly named and
paired with an expected diagnostic.

`fixture-catalog-0.9.0.json` is the maintained index for `BPM090-M11-05`. It maps each compact
fixture to a category and failure domain so a documentation failure can start from one small input
instead of a generated site, production database, browser download, or large external corpus.

The owning suite/domain is declared in `documentation/tests/suite-boundaries-0.9.0.json`. If a
fixture is useful to more than one domain, keep one source of truth and reference it from the
boundary contract rather than copying it.

`metadata-filter/` is the compact DITA input used to prove that locale and Firefox-channel filters
select different output from one source topic without copied prose.

`profile-states/`, `policy-preference-states/`, `locale-states/`, `search-states/`,
`screenshot-states/`, and `api-states/` provide versioned synthetic state inputs for documentation
contracts. They use `.invalid` hosts, `$BPM_BASE_URL`, and stable fixture IDs only; never replace
them with customer exports or environment-specific values.

`cis-workflows/level-workflows-0.9.0.json` defines compact deterministic Level 1 and Level 2 CIS
workflow inputs for documentation contracts. It contains synthetic route and review expectations,
not customer profiles or official CIS source expression.

Do not store production databases, exported customer profiles, secrets, private hosts, full
external corpora, official CIS PDFs, browser downloads, or generated sites here.
