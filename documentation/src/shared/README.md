# Shared DITA Metadata

This hand-authored directory is reserved for locale-independent keys, subject schemes, DITAVAL
conditions, stable identifiers, and language-neutral reusable resources.

Localized navigation, prose, captions, alt text, warnings, and search terms belong in each locale
tree. Shared resources may not conceal an English fallback.

`metadata-subject-scheme.ditamap` enumerates fixed DITA 1.3 values for audience, platform, BPM
version, locale delivery target, Firefox channel, and CIS level. `filters/` contains orthogonal
locale and Firefox Release/ESR DITAVAL filters. Dynamic `otherprops` groups use
`policy(value)`, `cis(value)`, and `api-operation(value)` syntax and are validated against the
maintained inventories rather than copied into this directory.
