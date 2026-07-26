# BPM 0.9.2: Simplified Chinese Documentation Heading Review

Date: 2026-07-19
Status: ready for Simplified-Chinese product-owner sign-off
Backlog item: `BPM092-M10-07`
Policy: [Locale Editorial Style Policy](documentation-locale-editorial-style-0.9.2.md)

## Scope and method

The review covers every `zh-CN` DITA title, related captions, and immediately
adjacent short descriptions where they repeated the same spacing, terminology,
or word-order defect. It checks compact Chinese title structure, Chinese
punctuation, no space between Chinese words, and exact BPM UI labels.

The terminology authority defines `配置档案` as the approved Chinese term for a
BPM profile. The runtime catalogue is authoritative for `所有设置`、`检查`、
`引导式编辑器`、`配置档案身份` and `托管首选项`; these labels are preserved as
quoted UI names where grammar requires a surrounding phrase.

## Corrected findings

| Topic or element | Before | After | Rationale |
| --- | --- | --- | --- |
| `admin-task-gate-control-product-startup` | `门控产品启动，BPM 运行状况良好且准备就绪` | `通过 BPM 运行状况和就绪状态启动控制产品` | Replaces an English-shaped comma sentence with a direct action title. |
| Administrator profile-operation titles | `配置文件` | `配置档案` | Normalizes the approved profile term in retirement, inventory pull, update, and lifecycle titles. |
| `cis-concept-manual-review-exceptions` | `手动审查、偏差和异常边界 当地方治理可以更改正确的部署决策时，` | `手动审核、偏差和例外边界` | Removes prose accidentally merged into the title and uses a compact concept label. |
| `fx-concept-release-esr-differences` | `Firefox 版本和 ESR 政策差异` | `Firefox Release 与 ESR 策略差异` | Retains the channel identifier and uses the reviewed term `策略`. |
| `fx-reference-managed-preference-locking` | `托管首选项锁定参考` | `托管首选项锁定` | Removes the literal `reference` suffix from a reference subject. |
| `ug-concept-choose-editor-surface` | `选择正确的 BPM 表面` | `选择合适的 BPM 编辑界面` | Replaces the literal `surface` calque. |
| `ug-concept-policies-and-managed-preferences` | `政策和 托管首选项` | `策略和托管首选项` | Removes the internal space and corrects policy terminology. |
| User profile titles | `配置文件` / `个人资料` | `配置档案` | Normalizes the approved profile term in model, status, create, open, save, compare, validation, and recovery titles. |
| `ug-reference-all-settings-review-states` | `所有设置 审核状态` | `“所有设置”中的审核状态` | Preserves the exact UI label and restores natural Chinese structure. |
| `ug-reference-schema-dependent-guided-controls` | `依赖于模式的引导控制` | `依赖架构的引导控件` | Uses the established architecture and control terms. |
| `ug-task-choose-profile-identity-schema` | `设置 配置档案身份 和模式通道` | `设置“配置档案身份”和架构通道` | Removes spaces and preserves the exact UI label. |
| `ug-task-filter-all-settings` / `ug-task-search-all-settings` / `ug-task-use-all-settings` | spaced `所有设置` phrases | quoted `“所有设置”` phrases | Keeps the label intact while allowing natural surrounding grammar. |
| `ug-task-filter-settings-by-source` | `筛选设置 按来源` | `按来源筛选设置` | Restores natural Chinese word order. |
| `ug-task-review-attention-items` | `查看 所有设置 个注意事项` | `查看“所有设置”中的待处理项` | Removes machine spacing and uses native help wording. |
| `ug-task-use-profile-library` | `使用库` | `使用配置档案库` | Restores the approved profile term and keeps the natural-language library-search result specific. |
| `ug-task-use-advanced-schema-controls` | `使用 高级架构控件` | `使用高级架构控件` | Removes invalid internal spacing. |
| `ug-task-use-guided-editor` | `导航六个 引导式编辑器 步骤` | `浏览“引导式编辑器”的六个步骤` | Preserves the exact editor label and uses native title order. |
| `ug-task-use-guided-editor` figure title | `引导式编辑器 概述` | `“引导式编辑器”概述` | Removes invalid spacing and preserves the UI name. |
| `ug-task-choose-firefox-schema` | `选择 Firefox 模式通道` | `选择 Firefox 架构通道` | Uses the consistent schema-channel term. |

## Nearby wording corrections

- The editor-surface description now lists the five BPM interfaces without
  machine spaces or the literal `surface` construction.
- The review-mode description uses the exact `检查` label and natural status
  names.
- The advanced-controls description distinguishes `所有设置` from
  `引导式编辑器` without English `shell` wording.
- The schema-mismatch description now uses `架构通道` and `依赖架构`.

## Exceptions and sign-off

Accepted exceptions: none. Spaces adjacent to required Latin brands, identifiers,
and channel labels such as `Firefox Release` remain intentional; spaces between
Chinese words do not.

| Review responsibility | Evidence | State |
| --- | --- | --- |
| Automated source scan | No title has a Chinese-to-Chinese whitespace run, terminal `。`, `配置文件`, or `个人资料`. | complete |
| Contract and metadata validation | Heading-style, terminology, interface-name, and locale-parity contracts. | complete |
| Simplified-Chinese product-owner review | Read the rendered Chinese titles in the installed documentation and accept or amend the wording. | pending sign-off |

Any accepted exception must record the topic ID, visible text, rationale, and
approving Simplified-Chinese reviewer.

Release-gate sign-off: accepted — Valery Ledovskoy, 2026-07-22.
