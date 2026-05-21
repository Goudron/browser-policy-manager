# Browser Policy Manager UI Glossary: `en` / `ru`

Date: `2026-05-15`

Scope: current product UI only. Supported UI locales remain `en` and `ru`.
This glossary is a maintainer reference for UI copy, tests, and future locale edits. It is not an in-app documentation surface.

The Russian column records the intended current UI terms. LOC-003 must verify Firefox/Mozilla-specific terminology against Mozilla Pontoon and SUMO before broader localization changes.

## Product Surfaces

| English UI term | Russian UI term | Notes |
|---|---|---|
| Browser Policy Manager | Менеджер профилей браузера | Product name can remain English in code and titles when needed; visible Russian UI currently uses the translated name. |
| Profile library | Библиотека профилей | Use for the profile manager surface and collection of saved profiles. |
| Library | Библиотека | Short navigation label. |
| Guided editor | Пошаговый редактор | Task-first editor for common administrator workflows. |
| All settings | Все настройки | Full visual settings manager. Do not use `Расширенные настройки` for this product mode. |
| JSON editor | JSON-редактор | Raw `policies.json` editor. Keep `JSON` untranslated. |
| Command deck | Командная панель | Shared action surface for save, validate, restore, and profile-level actions. |
| Current mode | Текущий режим | Used in editor chrome and mode switch context. |

## Profile Lifecycle

| English UI term | Russian UI term | Notes |
|---|---|---|
| Profile | Профиль | Generic managed browser profile. |
| Profile name | Имя профиля | Prefer over generic `Name` when the field is profile-specific. |
| Owner | Владелец | Current UI also has a short lowercase `владелец` in compact metadata. |
| Description | Описание | Profile metadata. |
| Draft | Черновик | Unsaved or not-yet-finalized profile state. |
| Active | Активен | Saved active profile state. |
| Deleted | Удалён | Current badge/state term for archived/deleted profiles. |
| Archive | Архивировать | User action for soft delete. The confirmation says the profile can be restored later. |
| Restore | Восстановить | Re-enable an archived/deleted profile. |
| Delete permanently | Удалить навсегда | Hard-delete action. Use only where destructive behavior is explicit. |
| Clone and adjust | Клонировать и доработать | Creates a draft based on another profile. |
| Compare | Сравнить | Compare two profiles or current setup with a saved profile. |
| Save conflict | Конфликт сохранения | Multi-tab or revision conflict. |

## Editing And Workflow

| English UI term | Russian UI term | Notes |
|---|---|---|
| Save | Сохранить | Primary persistence action. |
| Validate | Проверить | Button/action verb. |
| Validation | Проверка | Noun for validation state/results. |
| Validation passed | Проверка прошла успешно | Success result. |
| Unsaved changes | Несохранённые изменения | Dirty state. |
| All changes saved | Все изменения сохранены | Clean state. |
| Reload latest | Загрузить последнюю версию | Conflict recovery action. |
| Overwrite anyway | Всё равно перезаписать | Conflict override action. |
| Import policies.json | Импортировать policies.json | Keep `policies.json` untranslated. |
| Download Firefox policies.json | Скачать Firefox policies.json | Use `скачать` for file download action. |
| Export | Выгрузка | Product flow noun, especially final guided step. |
| Review & export | Проверка и выгрузка | Guided editor final step. |
| Format | Форматировать | JSON editor action. |
| Raw JSON | Сырой JSON | Use only for expert/low-level JSON context. |

## Firefox And Mozilla Terms

| English UI term | Russian UI term | Notes |
|---|---|---|
| Firefox | Firefox | Brand, do not translate. |
| Mozilla | Mozilla | Brand, do not translate. |
| Mozilla account | аккаунт Mozilla | Matches current Russian Mozilla/SUMO usage. |
| Firefox Home | Домашняя страница Firefox | Matches current Russian SUMO wording for Firefox Home surfaces. Avoid visible `Firefox Home` in Russian prose. |
| Home page | Домашняя страница | Browser home page. |
| Address bar | Адресная строка | Prefer over transliterated forms. |
| Search suggestions | Поисковые подсказки | Search/navigation UI. |
| Private windows | Приватные окна | Prefer Mozilla-style `приватный`, not `частный`. |
| Cookies | Куки | Avoid `cookies` or `куки-файлы` unless a specific context requires it. |
| DNS over HTTPS | DNS через HTTPS | Use full Russian wording in visible UI; `DoH` is acceptable only as a technical abbreviation where space is constrained. |
| IP protection | защита IP-адреса | Use Russian wording in visible UI. `VPN` remains an accepted technical abbreviation. |
| Site permissions | Разрешения сайтов | Browser website permission controls. |
| Add-ons | Дополнения | Prefer over `аддоны`. |
| Extensions | Расширения | Use when the UI specifically talks about extension policy/settings. |
| Website translation | Перевод сайтов | Use for website translation features. |
| Visual search | Визуальный поиск | AI/smart feature surface. |
| AI & smart features | ИИ и умные функции | Keep the AI step standalone in the Guided editor. |

## Policy And Schema Terms

| English UI term | Russian UI term | Notes |
|---|---|---|
| Policy | Политика | Firefox enterprise policy. |
| Policies | Политики | Plural. |
| Policy key | Ключ политики | Technical key in schema or JSON. |
| Managed policy | Управляемая политика | Use when contrasting with unmanaged/default browser behavior. |
| Managed preferences | Управляемые параметры | Current All settings section. |
| Preference | Параметр | Firefox preference. |
| Setting | Настройка | Generic UI setting/control. |
| Schema | Схема | JSON/schema model. |
| Schema channel | Канал схемы | `release` / `ESR` channel selector. |
| Firefox Release | Firefox Release | Product/channel label; keep `Release` when it is a channel name. |
| Firefox ESR | Firefox ESR | Keep `ESR` untranslated. |
| Deprecated | Устаревшие | Schema status. |
| Unknown | Неизвестные | Imported or unsupported keys. |
| Outside Guided editor | Вне Пошагового редактора | Review/filter term for items not covered by Guided editor. |

## Style Rules For `ru`

- Keep brands and technical identifiers untranslated: `Firefox`, `Mozilla`, `JSON`, `policies.json`, `ESR`, policy keys, preference keys, URLs, API paths, extension IDs.
- Avoid unnecessary Anglicisms: use `дополнения`, `куки`, `адресная строка`, `домашняя страница`, `разрешения сайтов`.
- Use `аккаунт Mozilla` for Mozilla account copy unless later Pontoon/SUMO verification changes the preferred style.
- Do not use `Расширенные настройки` for the visual `/settings` product mode; use `Все настройки`.
- Keep `ИИ и умные функции` as a standalone Guided editor step.
