# BPM 0.9.2: Russian Documentation Heading Review

Date: 2026-07-19
Status: ready for Russian-language product-owner sign-off
Backlog item: `BPM092-M10-05`
Policy: [Locale Editorial Style Policy](documentation-locale-editorial-style-0.9.2.md)

## Scope and method

The review covers every Russian DITA `title` element. It checks for an
English-calqued infinitive or reader-addressed imperative, a terminal full stop,
agreement and aspect in the resulting Russian noun phrase, and preservation of
visible BPM UI names.

The initial candidate inventory contained 11 imperative headings and four
headings with a terminal full stop. The revised source preserves topic IDs,
links, metadata, technical literals, and UI labels. The automated heading
contract is a regression check only; the sign-off below remains a native-Russian
editorial decision.

## Findings and dispositions

| Topic or element | Before | After | Disposition and Russian rationale |
| --- | --- | --- | --- |
| `admin-task-review-devops-configuration-sources` | `Просмотрите источники конфигурации DevOps` | `Проверка источников конфигурации DevOps` | Imperative becomes a concise nominal task title. |
| `admin-task-review-network-exposure-proxy-readiness` | `Просмотрите вопросы о уязвимости сети и готовности прокси-сервера.` | `Проверка сетевой доступности и готовности к работе через прокси` | Removes reader address, the unidiomatic `о уязвимости` construction, and the terminal full stop. |
| `admin-task-run-import-review-export-scenario` | `Запуск сценария импорта, проверки, экспорта и передачи соответствия требованиям.` | `Запуск сценария импорта, проверки, экспорта и передачи соответствия требованиям` | Removes the terminal full stop from a nominal heading. |
| `admin-task-run-validate-before-apply-update` | `Подтвердите и примените обновление профиля с помощью expected_revision.` | `Проверка и применение обновления профиля с параметром expected_revision` | Replaces a direct instruction with a nominal workflow title; keeps the API parameter literal unchanged. |
| `cis-concept-levels-channels-layers` | `Выбор между уровнями CIS, каналами и сгенерированными слоями.` | `Выбор между уровнями CIS, каналами и сгенерированными слоями` | Removes the terminal full stop. |
| `cis-concept-orientation` | `Ознакомьтесь с рекомендациями CIS в BPM` | `Рекомендации CIS в BPM` | A concept title names the subject rather than addressing the reader. |
| `fx-reference-managed-preference-locking` | `Ссылка на блокировку управляемых предпочтений` | `Блокировка управляемых предпочтений` | Replaces the literal `reference` calque with the actual reference subject. |
| `fx-reference-managed-preference-locking#a-type-values` | `Введите значения` | `Значения типов` | Replaces an imperative section heading with a noun phrase matching its content. |
| `fx-task-review-complex-policy-configuration` | `Перед экспортом проверьте сложную конфигурацию политики.` | `Проверка сложной конфигурации политики перед экспортом` | Uses a nominal task heading and removes the terminal full stop. |
| `ug-concept-schema-aware-behavior#a-state-meanings` | `Поддерживаемые, недоступные, устаревшие, неизвестные и необработанные состояния.` | `Поддерживаемые, недоступные, устаревшие, неизвестные и необработанные состояния` | Removes the terminal full stop. |
| `ug-task-choose-profile-identity-schema` | `Установите Идентификация профиля и канал схемы.` | `Настройка раздела «Идентификация профиля» и канала схемы` | Uses the nominal form and preserves the exact Russian UI label `Идентификация профиля`. |
| `ug-task-review-attention-items` | `Просмотрите элементы внимания Все настройки` | `Проверка требующих внимания элементов в разделе «Все настройки»` | Restores natural Russian agreement and retains the UI name `Все настройки`. |
| `ug-task-review-guided-profile` | `Просмотрите управляемый профиль` | `Проверка профиля в режиме «Пошаговый редактор»` | Names the task naturally and preserves the exact editor-mode label. |
| `ug-task-use-guided-editor` | `Пройдите шесть шагов Пошаговый редактор` | `Шесть шагов режима «Пошаговый редактор»` | Removes the reader-addressed imperative and supplies the required grammatical link to the UI name. |
| `ug-task-use-guided-editor` figure title | `Обзор Пошаговый редактор` | `Обзор режима «Пошаговый редактор»` | Corrects the adjacent caption’s grammatical construction while preserving the mode name. |
| `ug-troubleshoot-schema-mismatch` | `Устраните несоответствие схемы` | `Устранение несоответствия схемы` | Uses the established nominal troubleshooting pattern. |

## Exceptions and sign-off

Accepted exceptions: none. Procedural body steps deliberately retain the polite
plural imperative where an action is required; this policy applies the nominal
rule to titles and headings, not to instructions.

| Review responsibility | Evidence | State |
| --- | --- | --- |
| Automated source scan | No title contains the reviewed imperative forms or a terminal full stop. | complete |
| Contract and metadata validation | Heading-style contract and DITA metadata validation. | complete |
| Russian-language product-owner review | Read the rendered Russian titles in the installed documentation and accept or amend the wording. | pending sign-off |

No accepted exception may be added without documenting the topic ID, visible
text, rationale, and approving Russian-language reviewer.

Release-gate sign-off: accepted — Valery Ledovskoy, 2026-07-22.
