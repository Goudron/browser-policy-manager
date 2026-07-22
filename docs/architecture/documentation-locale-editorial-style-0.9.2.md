# BPM 0.9.2: Locale Editorial Style Policy

Date: 2026-07-19
Status: active policy
Backlog item: `BPM092-M10-04`

## Purpose and precedence

This policy governs visible product documentation in `en`, `ru`, `de`, `zh-CN`,
`fr`, and `es-ES`: DITA titles, headings, short descriptions, procedures, notes,
navigation labels, search labels, captions, and contextual-help labels. It is the
locale-specific supplement to the [audience and editorial contract](documentation-audience-editorial-contract-0.9.2.md).

English is a meaning source, not a grammar or word-order template. A translation
must express the same product action, consequence, limitation, and recovery path
in the idiom of its locale. Do not copy an English infinitive, capitalization
pattern, punctuation, or UI naming convention when the target language has a
different natural convention.

Product UI terminology takes precedence over a translator's synonym. Use the
accepted terminology authority for Firefox and BPM UI terms; keep brands,
identifiers, commands, paths, URLs, policy IDs, preference IDs, JSON literals,
and placeholders unchanged unless the terminology authority explicitly says
otherwise.

## Shared rules

- Use a short, specific title that identifies the user task or concept; do not
  end a title or ordinary heading with a full stop.
- Preserve the exact UI label and its capitalization when referring to a control,
  route, mode, or visible state. Translate surrounding grammar naturally.
- Use a heading as a label, not as a sentence addressed to the reader. Put
  action detail, prerequisites, consequences, and recovery in the body.
- Use the locale's ordinary quotation marks and punctuation in prose. Do not
  introduce English spacing, apostrophes, title case, or sentence patterns into
  localized text.
- Do not translate technical literals or interpolate punctuation inside a
  placeholder, `codeph`, URL, command, policy ID, preference ID, or filename.
- When a source title cannot be made natural without changing its implied scope,
  preserve the scope and record the question for the locale review; do not solve
  it with a word-for-word calque.

## Locale conventions

| Locale | Titles and headings | Procedure text | Case and punctuation | UI names |
| --- | --- | --- | --- | --- |
| `en` | Use concise sentence case. A verb-led task title is normal: `Change the interface language`. | Use direct imperative steps where an action is required. | Capitalize the first word and proper names; do not add a terminal full stop to headings. | Reproduce the English BPM UI label exactly. |
| `ru` | Use an idiomatic nominal form for task and reference titles: `Изменение языка интерфейса`, `Выбор канала схемы Firefox`, `Проверка профиля`. Do not use an English-calqued infinitive or second-person imperative as a title. | Use clear polite-plural imperative wording in steps when an action is required: `Откройте`, `Выберите`, `Проверьте`. | Use Russian sentence case and no terminal full stop in a title or ordinary heading. | Reproduce the Russian UI label exactly; retain approved brands and literals such as Firefox, JSON, URLs, and policy IDs. |
| `de` | Use a concise infinitive phrase for a task title: `Einen Firefox-Schemakanal auswählen`. Do not address the reader with `Sie` or `Ihnen` in a title. | Use the formal imperative with `Sie` in procedural sentences where it is natural. | Apply German capitalization to nouns and to the first word of a heading; do not imitate English title case or add a terminal point. | Reproduce the German BPM UI label exactly, including grammatical gender and compound nouns. |
| `zh-CN` | Use a compact verb-object or noun phrase: `选择 Firefox 架构通道`, `界面语言设置`. Do not insert spaces between Chinese words or copy English word order. | Use concise action wording without an explicit subject when the step is unambiguous. | Use Chinese punctuation in prose; titles and ordinary headings have no terminal `。`. Preserve spaces only around required Latin literals. | Reproduce the approved Chinese UI label exactly and retain product brands, identifiers, URLs, commands, and schema labels. |
| `fr` | Use an infinitive for a task title: `Changer la langue de l’interface`; use a noun phrase for a concept heading. Do not use a conjugated reader-addressed verb in a title. | Use the second-person plural imperative in procedure steps when a direct action is required. | Use sentence case: capitalize the first word and proper names, not English-style title case. Do not add a terminal full stop to a heading. | Reproduce the French BPM UI label exactly; use French apostrophes and spacing in surrounding prose. |
| `es-ES` | Use an infinitive for a task title: `Cambiar el idioma de la interfaz`; use a noun phrase for a concept heading. Do not use a conjugated reader-addressed verb in a title. | Use the formal imperative or an impersonal procedural construction consistently within a topic. | Use sentence case: capitalize the first word and proper names only. Do not add a terminal full stop to a heading. | Reproduce the approved Spanish BPM UI label exactly, including accent marks and the established product term. |

## Authorities and product terminology

The reviewed terminology source is
[`locale-terminology-authority-0.9.1.json`](../../documentation/config/locale-terminology-authority-0.9.1.json).
It gives Mozilla Pontoon priority for Firefox UI wording and Mozilla SUMO priority
for user-facing help vocabulary. The following language references determine the
orthographic and punctuation conventions used here when they apply:

| Locale | Reference | Applied rule in this policy |
| --- | --- | --- |
| `ru` | [Грамота.ру: знаки препинания в конце предложения](https://gramota.ru/biblioteka/spravochniki/pravila-russkoy-orfografii-i-punktuatsii/znaki-prepinaniya-v-kontse-predlozheniya) | A one-sentence heading has no terminal full stop. |
| `de` | [Duden: Groß- und Kleinschreibung](https://www.duden.de/sprachwissen/rechtschreibregeln/Gro%C3%9F-%20und%20Kleinschreibung) | Headings follow ordinary German capitalization; German nouns remain capitalized. |
| `zh-CN` | [SAMR: GB/T 15834-2011《标点符号用法》](https://std.samr.gov.cn/search/stdPage?q=GB%2FT15834) | Chinese prose uses the current national punctuation standard; headings remain compact labels without a final sentence stop. |
| `fr` | [Académie française: Questions de langue](https://www.academie-francaise.fr/questions-de-langue) | Apply French capitalization and typography rather than English title case. |
| `es-ES` | [RAE/ASALE: Ortografía básica, mayúscula condicionada por la puntuación](https://www.rae.es/ortograf%C3%ADa-b%C3%A1sica/uso-de-las-may%C3%BAsculas/la-may%C3%BAscula-condicionada-por-la-puntuación) | Apply Spanish sentence capitalization and punctuation rather than English title case. |

These references guide grammar and typography; the approved BPM UI catalogue
remains the authority for a rendered product label.

## Review and enforcement

1. Before editing a localized title, identify its visible element type and the
   target-language convention from the table above.
2. Verify the exact UI label in the locale catalogue and preserve all technical
   literals and placeholders.
3. Review the title with its short description and first procedural step; a
   natural title cannot be judged in isolation from its action and audience.
4. Record findings, accepted exceptions, and the reviewer source in the M10
   locale review evidence. Automated checks may detect known title patterns,
   but they do not replace native-language review.

The heading-style contract verifies that this policy exists and retains the
high-signal prohibitions. Locale-specific normalization tasks M10-05 through
M10-09 apply the policy to the source topics and record human review evidence.
