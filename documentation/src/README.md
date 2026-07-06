# Documentation Sources

- `dita/{locale}/` is reviewed product content. English is authored first and the other five locale
  trees are complete human-reviewed peers.
- `shared/` is hand-authored language-neutral DITA metadata and reusable identifiers.
- `generated/` is generator-owned DITA facts or skeletons and is never an authoring surface.

Each locale now owns five independently buildable guide maps under `dita/{locale}/maps/` plus
`portal.ditamap`, which aggregates them in stable order. Equivalent map filenames and IDs are
locale-independent; `xml:lang` and navigation titles belong to the locale peer. Topics are added by
their dedicated guide tasks. Do not place Markdown, generated HTML, build logs, external corpora,
or runtime application code in this source tree.
