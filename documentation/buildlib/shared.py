#!/usr/bin/env python3
# ruff: noqa: F401
"""Validate and reproducibly publish the six-locale BPM DITA documentation."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import tomllib
import unicodedata
import urllib.parse
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import jsonschema

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from app.core.locales import LOCALE_MATRIX  # noqa: E402
from app.core.schema_channels import HEADER_SCHEMA_CHANNELS  # noqa: E402

DOCUMENTATION_ROOT = REPOSITORY_ROOT / "documentation"
LOCK_PATH = DOCUMENTATION_ROOT / "config/toolchain-lock.json"
BUILD_ROOT = DOCUMENTATION_ROOT / "build"
DIST_ROOT = DOCUMENTATION_ROOT / "dist"
REPORTS_ROOT = DOCUMENTATION_ROOT / "reports"
DIAGNOSTICS_ROOT = REPORTS_ROOT / "diagnostics"
DEV_SITE_ROOT = REPOSITORY_ROOT / "app/documentation/site"
DEV_SITE_METADATA = REPOSITORY_ROOT / "app/documentation/.site-dev-install.json"
ARTIFACT_POLICY = DOCUMENTATION_ROOT / "config/artifact-policy.json"
FIREFOX_POLICY_CONTEXT_TARGETS = (
    DOCUMENTATION_ROOT / "config/firefox-policy-context-targets-0.9.0.json"
)
ALL_SETTINGS_HELP_TARGET_MAP = DOCUMENTATION_ROOT / "config/all-settings-help-target-map-0.9.1.json"
FIREFOX_POLICY_INDEX = (
    DOCUMENTATION_ROOT / "src/generated/firefox/firefox-policy-skeletons-0.9.0.json"
)
CIS_RECOMMENDATION_INDEX = (
    DOCUMENTATION_ROOT / "src/generated/cis/cis-recommendation-skeletons-0.9.0.json"
)
SEARCH_CORPUS_CONTRACT = DOCUMENTATION_ROOT / "config/search-corpus-and-results-0.9.0.json"
SEARCH_NORMALIZATION_ALIASES = DOCUMENTATION_ROOT / "config/search-normalization-aliases-0.9.0.json"
SEARCH_RANKING_TYPO = DOCUMENTATION_ROOT / "config/search-ranking-typo-0.9.0.json"
SEARCH_FACETS_FILTERS = DOCUMENTATION_ROOT / "config/search-facets-filters-0.9.0.json"
SEARCH_DOMAIN_RANKING_FACETS = (
    DOCUMENTATION_ROOT / "config/search-domain-ranking-facets-contract-0.9.3.json"
)
SEARCH_QUALITY_PERFORMANCE = DOCUMENTATION_ROOT / "config/search-quality-performance-0.9.0.json"
SEARCH_INTEGRITY_DRIFT = DOCUMENTATION_ROOT / "config/search-integrity-drift-0.9.0.json"
TOPIC_SECTION_TAXONOMY = DOCUMENTATION_ROOT / "config/topic-section-taxonomy-0.9.1.json"
TOPIC_SECTION_LABELS = DOCUMENTATION_ROOT / "config/topic-section-labels-0.9.1.json"
FIXTURE_CATALOG = DOCUMENTATION_ROOT / "fixtures/fixture-catalog-0.9.0.json"
SEARCH_STATE_FIXTURE = DOCUMENTATION_ROOT / "fixtures/search-states/search-query-states-0.9.0.json"
DOCUMENTATION_ASSISTANT_COPY = DOCUMENTATION_ROOT / "config/documentation-assistant-copy-0.9.3.json"
PDF_LAYOUT_CONTRACT = (
    DOCUMENTATION_ROOT / "config/future-distribution-documentation-layout-0.9.3.json"
)
PDF_GENERATION_CONTRACT = DOCUMENTATION_ROOT / "config/pdf-generation-contract-0.9.3.json"
PDF_THEME = DOCUMENTATION_ROOT / "assets/pdf/bpm-pdf-theme.yaml"
PDF_PRINT_CSS = DOCUMENTATION_ROOT / "assets/pdf/bpm-guide-print.css"
PDF_COVER_LOGO = DOCUMENTATION_ROOT / "assets/branding/bpm-logo.png"
PDF_COVER_BRANDING = DOCUMENTATION_ROOT / "assets/pdf/bpm-cover-branding.png"
PDF_UI_FOOTER_TEMPLATE = REPOSITORY_ROOT / "app/templates/profiles/_page_footer.html"
PDF_UI_FOOTER_CATALOGS = tuple(
    REPOSITORY_ROOT / f"app/i18n/{locale}.json"
    for locale in ("en", "ru", "de", "zh-CN", "fr", "es-ES")
)
PDF_BUILD_ROOT = BUILD_ROOT / "pdf"
PDF_BUILD_MANIFEST = "pdf-build-manifest.json"
PDF_GUIDE_MAPS = (
    ("user-guide", "user-guide.ditamap"),
    ("administrator-guide", "administrator-guide.ditamap"),
)
PDF_FIXED_CREATION_DATE = b"D:19700101000000+00'00'"
PDF_FIXED_UTC_CREATION_DATE = b"D:19700101000000Z"
PDF_FIXED_DOCUMENT_ID = b"0" * 32
PDF_CREATION_DATE_PATTERN = re.compile(rb"(/CreationDate\s*\()(D:\d{14}(?:[+-]\d{2}'\d{2}'|Z))(\))")
PDF_MODIFICATION_DATE_PATTERN = re.compile(rb"(/ModDate\s*\()(D:\d{14}(?:[+-]\d{2}'\d{2}'|Z))(\))")
PDF_DOCUMENT_ID_PATTERN = re.compile(rb"/ID\s*\[\s*<[0-9A-Fa-f]{32}>\s*<[0-9A-Fa-f]{32}>\s*\]")
PDF_XMP_TIMESTAMP_PATTERN = re.compile(
    rb"(<(?:dc:date|xmp:MetadataDate|xmp:CreateDate)>)(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:\d{2}))(</(?:dc:date|xmp:MetadataDate|xmp:CreateDate)>)"
)
PDF_FIXED_XMP_TIMESTAMP = b"1970-01-01T00:00:00+00:00"
PDF_FIXED_UTC_XMP_TIMESTAMP = b"1970-01-01T00:00:00Z"
SCREENSHOT_STATE_FIXTURE = (
    DOCUMENTATION_ROOT / "fixtures/screenshot-states/screenshot-states-0.9.0.json"
)
FIREFOX_POLICY_INVENTORY = (
    REPOSITORY_ROOT / "docs/architecture/firefox-policy-documentation-inventory-0.9.0.json"
)
CIS_INVENTORY = REPOSITORY_ROOT / "docs/architecture/cis-documentation-inventory-0.9.0.json"
API_INVENTORY = REPOSITORY_ROOT / "docs/architecture/api-documentation-inventory-0.9.0.md"
CAPABILITY_INVENTORY = (
    REPOSITORY_ROOT / "docs/architecture/product-user-capability-inventory-0.9.0.md"
)
MANIFEST_SCHEMA = (
    REPOSITORY_ROOT / "docs/architecture/schemas/product-documentation-manifest-v1.schema.json"
)
UI_TARGET_SCHEMA = (
    REPOSITORY_ROOT / "docs/architecture/schemas/product-documentation-ui-target-map-v1.schema.json"
)
NAVIGATION_SCHEMA = (
    REPOSITORY_ROOT / "docs/architecture/schemas/product-documentation-navigation-v1.schema.json"
)
LOCALES = ("en", "ru", "de", "zh-CN", "fr", "es-ES")
PRODUCT_LOCALE_OPTIONS = tuple(locale for locale in LOCALE_MATRIX if locale.has_catalog)
PRODUCT_HEADER_LABEL_KEYS = {
    "supported_firefox_versions": "profiles.supported_firefox_versions",
    "locales": "profiles.locale_label",
    "locale_system": "profiles.locale_system",
    "theme": "profiles.theme_label",
    "theme_system": "profiles.theme_system",
    "theme_light": "profiles.theme_light",
    "theme_dark": "profiles.theme_dark",
}
PRODUCT_FIREFOX_SCHEMA_LABEL_KEYS = {
    channel.value: channel.i18n_key for channel in HEADER_SCHEMA_CHANNELS
}
PRODUCT_LOCALE_OPTION_LABEL_KEYS = {
    "en": "profiles.locale_option_en",
    "ru": "profiles.locale_option_ru",
    "de": "profiles.locale_option_de",
    "zh-CN": "profiles.locale_option_zh_cn",
    "fr": "profiles.locale_option_fr",
    "es-ES": "profiles.locale_option_es_es",
}
SOURCE_SUFFIXES = {".dita", ".ditamap"}
LINK_ATTRIBUTES = {"href", "src"}
THEME_ROOT = DOCUMENTATION_ROOT / "assets/theme"
SCREENSHOT_ROOT = DOCUMENTATION_ROOT / "assets/screenshots"
THEME_FILES = ("bpm-docs.css", "bpm-docs-print.css")
SEARCH_SCRIPT = "bpm-docs-search.js"
MODEL_MANAGER_SCRIPT = "bpm-docs-model-manager.js"
ASSISTANT_RENDERER_SCRIPT = "bpm-docs-assistant-renderer.js"
ASSISTANT_STATE_MACHINE_SCRIPT = "bpm-docs-assistant-state-machine.js"
ASSISTANT_SHELL_SCRIPT = "bpm-docs-assistant-shell.js"
ASSISTANT_CONVERSATION_SCRIPT = "bpm-docs-assistant-conversation.js"
ASSISTANT_TRANSPORT_SCRIPT = "bpm-docs-assistant-transport.js"
PRODUCT_VERSION_FACET_PLACEHOLDER = "{product_version}"
SEARCH_TOKEN_PATTERN = re.compile(
    r"/[^\s\"'<>]+|[^\W_]+(?:[-._:/][^\W_]+)+|[^\W_]+",
    flags=re.UNICODE,
)
GUIDE_MAPS = (
    ("user-guide", "user-guide.ditamap", "a-user-guide", "user"),
    ("firefox-policy-guide", "firefox-policy-guide.ditamap", "a-firefox-policy-guide", "firefox"),
    ("cis-settings-guide", "cis-settings-guide.ditamap", "a-cis-settings-guide", "cis"),
    ("administrator-guide", "administrator-guide.ditamap", "a-administrator-guide", "admin"),
)
GUIDE_OUTPUT_ROOT_BY_MAP = {
    filename: url_root for _guide_id, filename, _anchor, url_root in GUIDE_MAPS
}
GUIDE_OUTPUT_ROOT_BY_SOURCE_DIR = {
    "api": "api",
    "admin": "admin",
    "cis": "cis",
    "firefox": "firefox",
    "json": "user",
    "user": "user",
}
_NAVIGATION_MODEL_CACHE: dict[str, dict[str, Any]] = {}
SHELL_LABELS = {
    "en": {
        "skip": "Skip to content",
        "guides": "Guides",
        "locales": "Locale",
        "breadcrumbs": "Breadcrumbs",
        "home": "Documentation home",
        "status": "Runtime package pending manifest, search, and UI target metadata.",
        "theme": "Theme",
        "theme_system": "System",
        "theme_light": "Light",
        "theme_dark": "Dark",
        "navigation_root": "Documents",
        "navigation_tree_label": "Documentation tree",
        "navigation_expand": "Expand",
        "navigation_collapse": "Collapse",
        "navigation_current": "Current page",
        "navigation_parent": "Parent",
        "navigation_back_to_root": "Back to documentation home",
        "navigation_loading": "Loading the documentation tree…",
        "navigation_unavailable": "Documentation navigation is unavailable.",
        "search": "Search documentation",
        "search_query": "Search query",
        "search_placeholder": "Search topics, policies, CIS IDs, or API operations",
        "search_submit": "Search",
        "search_clear": "Clear",
        "search_clear_filters": "Clear filters",
        "search_active_filters": "Active filters: {count}",
        "search_help": (
            "Search uses this locale’s static offline index. No AI, telemetry, or network search is used."
        ),
        "search_filters": "Filters",
        "search_results": "Search results",
        "search_loading": "Loading the local search index…",
        "search_ready": "Enter a query or choose filters to search this documentation.",
        "search_no_results": "No documentation pages match the query and selected filters.",
        "search_unavailable": "Search is unavailable because the local index could not be loaded.",
        "search_result_singular": "1 result",
        "search_result_plural": "results",
        "assistant": "BPM AI Assistant",
        "assistant_close": "Collapse BPM AI Assistant",
        "assistant_unavailable_short": "Unavailable",
        "assistant_install_model": "Install model",
        "assistant_installing": "Installing model",
        "assistant_verifying_model": "Verifying model",
        "assistant_preparing_documentation": "Preparing documentation",
        "assistant_install_failed": "Model installation could not be completed",
        "assistant_ready": "Ready",
        "assistant_clear_short": "Clear",
        "assistant_busy_short": "Working",
        "assistant_clarify": (
            "Please clarify the BPM setting, policy, guide, or task you want to discuss."
        ),
        "assistant_abstain": (
            "I could not find enough current documentation evidence to answer reliably."
        ),
        "assistant_refuse": (
            "I can help only with Browser Policy Manager documentation and settings."
        ),
        "assistant_cancelled_short": "Request cancelled",
        "assistant_time_preview": "Expected time: from {minimum} to {maximum}",
        "assistant_answer_failed": "The answer could not be completed.",
        "assistant_description": (
            "Ask BPM documentation questions when the local assistant is available. Search and guide navigation remain available independently."
        ),
        "assistant_unavailable": (
            "The local documentation assistant is unavailable. Search and navigation are available."
        ),
        "assistant_transcript": "Conversation",
        "assistant_question": "Question about BPM documentation",
        "assistant_question_placeholder": "Ask about Browser Policy Manager documentation",
        "assistant_controls_unavailable": (
            "Conversation controls are unavailable until the local assistant can be used."
        ),
        "assistant_send": "Send",
        "assistant_stop": "Stop",
        "assistant_clear": "Clear conversation",
        "assistant_answer_mode": "Answer state",
        "assistant_sources": "Sources",
        "assistant_manage_model": "Manage local model",
        "assistant_web_title": "Optional external evidence",
        "assistant_web_local_only": (
            "External evidence is off. Answers use local BPM documentation only."
        ),
        "assistant_external_sources": "External sources",
    },
    "ru": {
        "skip": "Перейти к содержимому",
        "guides": "Руководства",
        "locales": "Локаль",
        "breadcrumbs": "Навигационная цепочка",
        "home": "Главная страница документации",
        "status": "Пакет для runtime ожидает манифест, поиск и метаданные UI-целей.",
        "theme": "Тема",
        "theme_system": "Системная",
        "theme_light": "Светлая",
        "theme_dark": "Тёмная",
        "navigation_root": "Документы",
        "navigation_tree_label": "Дерево документации",
        "navigation_expand": "Развернуть",
        "navigation_collapse": "Свернуть",
        "navigation_current": "Текущая страница",
        "navigation_parent": "Родительский раздел",
        "navigation_back_to_root": "Вернуться на главную страницу документации",
        "navigation_loading": "Загружается дерево документации…",
        "navigation_unavailable": "Навигация по документации недоступна.",
        "search": "Поиск по документации",
        "search_query": "Поисковый запрос",
        "search_placeholder": "Ищите разделы, политики, CIS ID или операции API",
        "search_submit": "Найти",
        "search_clear": "Сбросить",
        "search_clear_filters": "Сбросить фильтры",
        "search_active_filters": "Активные фильтры: {count}",
        "search_help": (
            "Поиск использует статический офлайн-индекс текущей локали. ИИ, телеметрия и сетевой поиск не используются."
        ),
        "search_filters": "Фильтры",
        "search_results": "Результаты поиска",
        "search_loading": "Загружается локальный поисковый индекс…",
        "search_ready": "Введите запрос или выберите фильтры для поиска в документации.",
        "search_no_results": (
            "Нет страниц документации, соответствующих запросу и выбранным фильтрам."
        ),
        "search_unavailable": "Поиск недоступен: локальный индекс не удалось загрузить.",
        "search_result_singular": "1 результат",
        "search_result_plural": "результатов",
        "assistant": "ИИ-помощник BPM",
        "assistant_close": "Свернуть ИИ-помощника BPM",
        "assistant_unavailable_short": "Недоступен",
        "assistant_install_model": "Установить модель",
        "assistant_installing": "Устанавливается модель",
        "assistant_verifying_model": "Проверяется модель",
        "assistant_preparing_documentation": "Подготавливается документация",
        "assistant_install_failed": "Не удалось завершить установку модели",
        "assistant_ready": "Готов",
        "assistant_clear_short": "Очистить",
        "assistant_busy_short": "Выполняется",
        "assistant_clarify": (
            "Уточните, какую настройку, политику, руководство или задачу BPM вы хотите обсудить."
        ),
        "assistant_abstain": (
            "Я не нашёл достаточно актуальных сведений в документации для достоверного ответа."
        ),
        "assistant_refuse": (
            "Я могу помочь только с документацией и настройками Browser Policy Manager."
        ),
        "assistant_cancelled_short": "Запрос отменён",
        "assistant_time_preview": "Ожидаемое время: от {minimum} до {maximum}",
        "assistant_answer_failed": "Не удалось завершить ответ.",
        "assistant_description": (
            "Задавайте вопросы по документации BPM, когда локальный помощник доступен. Поиск и навигация по руководствам работают независимо."
        ),
        "assistant_unavailable": (
            "Локальный помощник по документации недоступен. Поиск и навигация доступны."
        ),
        "assistant_transcript": "Диалог",
        "assistant_question": "Вопрос по документации BPM",
        "assistant_question_placeholder": "Задайте вопрос по документации Browser Policy Manager",
        "assistant_controls_unavailable": (
            "Элементы диалога недоступны, пока нельзя использовать локального помощника."
        ),
        "assistant_send": "Отправить",
        "assistant_stop": "Остановить",
        "assistant_clear": "Очистить диалог",
        "assistant_answer_mode": "Состояние ответа",
        "assistant_sources": "Источники",
        "assistant_manage_model": "Управление локальной моделью",
        "assistant_web_title": "Необязательные внешние сведения",
        "assistant_web_local_only": (
            "Внешние сведения выключены. Ответы используют только локальную документацию BPM."
        ),
        "assistant_external_sources": "Внешние источники",
    },
    "de": {
        "skip": "Zum Inhalt springen",
        "guides": "Handbücher",
        "locales": "Sprache",
        "breadcrumbs": "Breadcrumbs",
        "home": "Startseite der Dokumentation",
        "status": "Das Runtime-Paket wartet auf Manifest, Suche und UI-Zielmetadaten.",
        "theme": "Design",
        "theme_system": "System",
        "theme_light": "Hell",
        "theme_dark": "Dunkel",
        "navigation_root": "Dokumente",
        "navigation_tree_label": "Dokumentationsbaum",
        "navigation_expand": "Aufklappen",
        "navigation_collapse": "Zuklappen",
        "navigation_current": "Aktuelle Seite",
        "navigation_parent": "Übergeordneter Abschnitt",
        "navigation_back_to_root": "Zur Startseite der Dokumentation",
        "navigation_loading": "Dokumentationsbaum wird geladen…",
        "navigation_unavailable": "Die Dokumentationsnavigation ist nicht verfügbar.",
        "search": "Dokumentation durchsuchen",
        "search_query": "Suchanfrage",
        "search_placeholder": "Themen, Richtlinien, CIS-IDs oder API-Vorgänge suchen",
        "search_submit": "Suchen",
        "search_clear": "Zurücksetzen",
        "search_clear_filters": "Filter zurücksetzen",
        "search_active_filters": "Aktive Filter: {count}",
        "search_help": (
            "Die Suche verwendet den statischen Offline-Index dieser Sprache. Keine KI, Telemetrie oder Netzwerksuche wird verwendet."
        ),
        "search_filters": "Filter",
        "search_results": "Suchergebnisse",
        "search_loading": "Lokaler Suchindex wird geladen…",
        "search_ready": (
            "Geben Sie eine Anfrage ein oder wählen Sie Filter, um diese Dokumentation zu durchsuchen."
        ),
        "search_no_results": (
            "Keine Dokumentationsseiten entsprechen der Anfrage und den ausgewählten Filtern."
        ),
        "search_unavailable": (
            "Die Suche ist nicht verfügbar, weil der lokale Index nicht geladen werden konnte."
        ),
        "search_result_singular": "1 Ergebnis",
        "search_result_plural": "Ergebnisse",
        "assistant": "BPM-KI-Assistent",
        "assistant_close": "BPM-KI-Assistent schließen",
        "assistant_unavailable_short": "Nicht verfügbar",
        "assistant_install_model": "Modell installieren",
        "assistant_installing": "Modell wird installiert",
        "assistant_verifying_model": "Modell wird überprüft",
        "assistant_preparing_documentation": "Dokumentation wird vorbereitet",
        "assistant_install_failed": "Die Modellinstallation konnte nicht abgeschlossen werden",
        "assistant_ready": "Bereit",
        "assistant_clear_short": "Löschen",
        "assistant_busy_short": "Wird bearbeitet",
        "assistant_clarify": (
            "Bitte präzisieren Sie die BPM-Einstellung, Richtlinie, Anleitung oder Aufgabe, die Sie besprechen möchten."
        ),
        "assistant_abstain": (
            "Ich konnte nicht genügend aktuelle Dokumentationsbelege für eine zuverlässige Antwort finden."
        ),
        "assistant_refuse": (
            "Ich kann nur bei Browser-Policy-Manager-Dokumentation und -Einstellungen helfen."
        ),
        "assistant_cancelled_short": "Anfrage abgebrochen",
        "assistant_time_preview": "Voraussichtliche Dauer: von {minimum} bis {maximum}",
        "assistant_answer_failed": "Die Antwort konnte nicht fertiggestellt werden.",
        "assistant_description": (
            "Stellen Sie Fragen zur BPM-Dokumentation, wenn der lokale Assistent verfügbar ist. Suche und Handbuchnavigation bleiben unabhängig verfügbar."
        ),
        "assistant_unavailable": (
            "Der lokale Dokumentationsassistent ist nicht verfügbar. Suche und Navigation sind verfügbar."
        ),
        "assistant_transcript": "Unterhaltung",
        "assistant_question": "Frage zur BPM-Dokumentation",
        "assistant_question_placeholder": (
            "Stellen Sie eine Frage zur Browser-Policy-Manager-Dokumentation"
        ),
        "assistant_controls_unavailable": (
            "Die Dialog-Steuerelemente sind erst verfügbar, wenn der lokale Assistent verwendet werden kann."
        ),
        "assistant_send": "Senden",
        "assistant_stop": "Anhalten",
        "assistant_clear": "Unterhaltung löschen",
        "assistant_answer_mode": "Antwortstatus",
        "assistant_sources": "Quellen",
        "assistant_manage_model": "Lokales Modell verwalten",
        "assistant_web_title": "Optionale externe Belege",
        "assistant_web_local_only": (
            "Externe Belege sind ausgeschaltet. Antworten verwenden nur lokale BPM-Dokumentation."
        ),
        "assistant_external_sources": "Externe Quellen",
    },
    "zh-CN": {
        "skip": "跳到内容",
        "guides": "指南",
        "locales": "语言",
        "breadcrumbs": "面包屑导航",
        "home": "文档主页",
        "status": "运行时包仍需清单、搜索和 UI 目标元数据。",
        "theme": "主题",
        "theme_system": "跟随系统",
        "theme_light": "浅色",
        "theme_dark": "深色",
        "navigation_root": "文档",
        "navigation_tree_label": "文档树",
        "navigation_expand": "展开",
        "navigation_collapse": "折叠",
        "navigation_current": "当前页面",
        "navigation_parent": "父级部分",
        "navigation_back_to_root": "返回文档主页",
        "navigation_loading": "正在加载文档树…",
        "navigation_unavailable": "文档导航不可用。",
        "search": "搜索文档",
        "search_query": "搜索查询",
        "search_placeholder": "搜索主题、策略、CIS ID 或 API 操作",
        "search_submit": "搜索",
        "search_clear": "清除",
        "search_clear_filters": "清除筛选条件",
        "search_active_filters": "已启用筛选条件：{count}",
        "search_help": "搜索使用当前语言的静态离线索引。不使用 AI、遥测或网络搜索。",
        "search_filters": "筛选条件",
        "search_results": "搜索结果",
        "search_loading": "正在加载本地搜索索引…",
        "search_ready": "输入查询或选择筛选条件以搜索此文档。",
        "search_no_results": "没有文档页面符合该查询和所选筛选条件。",
        "search_unavailable": "搜索不可用，因为无法加载本地索引。",
        "search_result_singular": "1 个结果",
        "search_result_plural": "个结果",
        "assistant": "BPM AI 助手",
        "assistant_close": "收起 BPM AI 助手",
        "assistant_unavailable_short": "不可用",
        "assistant_install_model": "安装模型",
        "assistant_installing": "正在安装模型",
        "assistant_verifying_model": "正在验证模型",
        "assistant_preparing_documentation": "正在准备文档",
        "assistant_install_failed": "无法完成模型安装",
        "assistant_ready": "就绪",
        "assistant_clear_short": "清除",
        "assistant_busy_short": "正在处理",
        "assistant_clarify": "请说明您想讨论的 BPM 设置、策略、指南或任务。",
        "assistant_abstain": "未找到足够的当前文档证据，因此无法可靠回答。",
        "assistant_refuse": "我只能帮助处理 Browser Policy Manager 的文档和设置。",
        "assistant_cancelled_short": "请求已取消",
        "assistant_time_preview": "预计用时：{minimum} 至 {maximum}",
        "assistant_answer_failed": "无法完成回答。",
        "assistant_description": (
            "本地助手可用时，您可以询问 BPM 文档问题。搜索和指南导航始终可独立使用。"
        ),
        "assistant_unavailable": "本地文档助手不可用。搜索和导航仍可使用。",
        "assistant_transcript": "对话",
        "assistant_question": "关于 BPM 文档的问题",
        "assistant_question_placeholder": "请询问有关 Browser Policy Manager 文档的问题",
        "assistant_controls_unavailable": "在本地助手可用之前，对话控件不可用。",
        "assistant_send": "发送",
        "assistant_stop": "停止",
        "assistant_clear": "清除对话",
        "assistant_answer_mode": "回答状态",
        "assistant_sources": "来源",
        "assistant_manage_model": "管理本地模型",
        "assistant_web_title": "可选的外部证据",
        "assistant_web_local_only": "外部证据已关闭。回答仅使用本地 BPM 文档。",
        "assistant_external_sources": "外部来源",
    },
    "fr": {
        "skip": "Aller au contenu",
        "guides": "Guides",
        "locales": "Langue",
        "breadcrumbs": "Fil d’Ariane",
        "home": "Accueil de la documentation",
        "status": (
            "Le paquet d’exécution attend le manifeste, la recherche et les métadonnées des cibles UI."
        ),
        "theme": "Thème",
        "theme_system": "Système",
        "theme_light": "Clair",
        "theme_dark": "Sombre",
        "navigation_root": "Documents",
        "navigation_tree_label": "Arborescence de la documentation",
        "navigation_expand": "Développer",
        "navigation_collapse": "Réduire",
        "navigation_current": "Page actuelle",
        "navigation_parent": "Section parente",
        "navigation_back_to_root": "Revenir à l’accueil de la documentation",
        "navigation_loading": "Chargement de l’arborescence de la documentation…",
        "navigation_unavailable": "La navigation dans la documentation est indisponible.",
        "search": "Rechercher dans la documentation",
        "search_query": "Requête de recherche",
        "search_placeholder": "Rechercher des rubriques, politiques, ID CIS ou opérations API",
        "search_submit": "Rechercher",
        "search_clear": "Effacer",
        "search_clear_filters": "Effacer les filtres",
        "search_active_filters": "Filtres actifs : {count}",
        "search_help": (
            "La recherche utilise l’index statique hors ligne de cette langue. Aucune IA, télémétrie ni recherche réseau n’est utilisée."
        ),
        "search_filters": "Filtres",
        "search_results": "Résultats de recherche",
        "search_loading": "Chargement de l’index de recherche local…",
        "search_ready": (
            "Saisissez une requête ou choisissez des filtres pour rechercher dans cette documentation."
        ),
        "search_no_results": (
            "Aucune page de documentation ne correspond à la requête et aux filtres sélectionnés."
        ),
        "search_unavailable": (
            "La recherche est indisponible car l’index local n’a pas pu être chargé."
        ),
        "search_result_singular": "1 résultat",
        "search_result_plural": "résultats",
        "assistant": "Assistant IA BPM",
        "assistant_close": "Réduire l’assistant IA BPM",
        "assistant_unavailable_short": "Indisponible",
        "assistant_install_model": "Installer le modèle",
        "assistant_installing": "Installation du modèle",
        "assistant_verifying_model": "Vérification du modèle",
        "assistant_preparing_documentation": "Préparation de la documentation",
        "assistant_install_failed": "L’installation du modèle n’a pas pu être terminée",
        "assistant_ready": "Prêt",
        "assistant_clear_short": "Effacer",
        "assistant_busy_short": "En cours",
        "assistant_clarify": (
            "Précisez le paramètre, la règle, le guide ou la tâche BPM dont vous voulez parler."
        ),
        "assistant_abstain": (
            "Je n’ai pas trouvé suffisamment de preuves documentaires actuelles pour répondre de manière fiable."
        ),
        "assistant_refuse": (
            "Je peux aider uniquement avec la documentation et les paramètres de Browser Policy Manager."
        ),
        "assistant_cancelled_short": "Demande annulée",
        "assistant_time_preview": "Durée estimée : de {minimum} à {maximum}",
        "assistant_answer_failed": "La réponse n’a pas pu être terminée.",
        "assistant_description": (
            "Posez des questions sur la documentation BPM lorsque l’assistant local est disponible. La recherche et la navigation dans les guides restent disponibles indépendamment."
        ),
        "assistant_unavailable": (
            "L’assistant de documentation local est indisponible. La recherche et la navigation restent disponibles."
        ),
        "assistant_transcript": "Conversation",
        "assistant_question": "Question sur la documentation BPM",
        "assistant_question_placeholder": (
            "Posez une question sur la documentation de Browser Policy Manager"
        ),
        "assistant_controls_unavailable": (
            "Les commandes de conversation sont indisponibles tant que l’assistant local ne peut pas être utilisé."
        ),
        "assistant_send": "Envoyer",
        "assistant_stop": "Arrêter",
        "assistant_clear": "Effacer la conversation",
        "assistant_answer_mode": "État de la réponse",
        "assistant_sources": "Sources",
        "assistant_manage_model": "Gérer le modèle local",
        "assistant_web_title": "Preuves externes facultatives",
        "assistant_web_local_only": (
            "Les preuves externes sont désactivées. Les réponses utilisent uniquement la documentation BPM locale."
        ),
        "assistant_external_sources": "Sources externes",
    },
    "es-ES": {
        "skip": "Ir al contenido",
        "guides": "Guías",
        "locales": "Idioma",
        "breadcrumbs": "Ruta de navegación",
        "home": "Inicio de la documentación",
        "status": (
            "El paquete de runtime espera el manifiesto, la búsqueda y los metadatos de objetivos de UI."
        ),
        "theme": "Tema",
        "theme_system": "Sistema",
        "theme_light": "Claro",
        "theme_dark": "Oscuro",
        "navigation_root": "Documentos",
        "navigation_tree_label": "Árbol de documentación",
        "navigation_expand": "Expandir",
        "navigation_collapse": "Contraer",
        "navigation_current": "Página actual",
        "navigation_parent": "Sección superior",
        "navigation_back_to_root": "Volver al inicio de la documentación",
        "navigation_loading": "Cargando el árbol de documentación…",
        "navigation_unavailable": "La navegación por la documentación no está disponible.",
        "search": "Buscar en la documentación",
        "search_query": "Consulta de búsqueda",
        "search_placeholder": "Buscar temas, políticas, ID de CIS u operaciones de API",
        "search_submit": "Buscar",
        "search_clear": "Borrar",
        "search_clear_filters": "Borrar filtros",
        "search_active_filters": "Filtros activos: {count}",
        "search_help": (
            "La búsqueda usa el índice estático sin conexión de este idioma. No se usa IA, telemetría ni búsqueda de red."
        ),
        "search_filters": "Filtros",
        "search_results": "Resultados de búsqueda",
        "search_loading": "Cargando el índice de búsqueda local…",
        "search_ready": "Escriba una consulta o elija filtros para buscar en esta documentación.",
        "search_no_results": (
            "Ninguna página de documentación coincide con la consulta y los filtros seleccionados."
        ),
        "search_unavailable": (
            "La búsqueda no está disponible porque no se pudo cargar el índice local."
        ),
        "search_result_singular": "1 resultado",
        "search_result_plural": "resultados",
        "assistant": "Asistente de IA de BPM",
        "assistant_close": "Contraer el asistente de IA de BPM",
        "assistant_unavailable_short": "No disponible",
        "assistant_install_model": "Instalar modelo",
        "assistant_installing": "Instalando el modelo",
        "assistant_verifying_model": "Verificando el modelo",
        "assistant_preparing_documentation": "Preparando la documentación",
        "assistant_install_failed": "No se pudo completar la instalación del modelo",
        "assistant_ready": "Listo",
        "assistant_clear_short": "Limpiar",
        "assistant_busy_short": "En curso",
        "assistant_clarify": (
            "Aclara el ajuste, la política, la guía o la tarea de BPM que quieres consultar."
        ),
        "assistant_abstain": (
            "No encontré suficiente evidencia actual en la documentación para responder de forma fiable."
        ),
        "assistant_refuse": (
            "Solo puedo ayudar con la documentación y la configuración de Browser Policy Manager."
        ),
        "assistant_cancelled_short": "Solicitud cancelada",
        "assistant_time_preview": "Tiempo estimado: de {minimum} a {maximum}",
        "assistant_answer_failed": "No se pudo completar la respuesta.",
        "assistant_description": (
            "Haz preguntas sobre la documentación de BPM cuando el asistente local esté disponible. La búsqueda y la navegación por las guías siguen disponibles de forma independiente."
        ),
        "assistant_unavailable": (
            "El asistente local de documentación no está disponible. La búsqueda y la navegación siguen disponibles."
        ),
        "assistant_transcript": "Conversación",
        "assistant_question": "Pregunta sobre la documentación de BPM",
        "assistant_question_placeholder": (
            "Haz una pregunta sobre la documentación de Browser Policy Manager"
        ),
        "assistant_controls_unavailable": (
            "Los controles de conversación no están disponibles hasta que se pueda usar el asistente local."
        ),
        "assistant_send": "Enviar",
        "assistant_stop": "Detener",
        "assistant_clear": "Borrar conversación",
        "assistant_answer_mode": "Estado de la respuesta",
        "assistant_sources": "Fuentes",
        "assistant_manage_model": "Gestionar el modelo local",
        "assistant_web_title": "Evidencia externa opcional",
        "assistant_web_local_only": (
            "La evidencia externa está desactivada. Las respuestas usan solo documentación BPM local."
        ),
        "assistant_external_sources": "Fuentes externas",
    },
}

SEARCH_FILTER_FIELD_LABELS = {
    "en": {
        "locale": "Documentation locale",
        "guide_id": "Guide",
        "topic_kind": "Topic type",
        "firefox_channel": "Firefox channel",
        "policy_category": "Policy category",
        "cis_level": "CIS level",
        "cis_control_state": "CIS status",
        "api_area": "API area",
        "bpm_version": "BPM version",
    },
    "ru": {
        "locale": "Локаль документации",
        "guide_id": "Руководство",
        "topic_kind": "Тип раздела",
        "firefox_channel": "Канал Firefox",
        "policy_category": "Категория политики",
        "cis_level": "Уровень CIS",
        "cis_control_state": "Состояние CIS",
        "api_area": "Область API",
        "bpm_version": "Версия BPM",
    },
    "de": {
        "locale": "Dokumentationssprache",
        "guide_id": "Handbuch",
        "topic_kind": "Seitentyp",
        "firefox_channel": "Firefox-Kanal",
        "policy_category": "Richtlinienkategorie",
        "cis_level": "CIS-Stufe",
        "cis_control_state": "CIS-Status",
        "api_area": "API-Bereich",
        "bpm_version": "BPM-Version",
    },
    "zh-CN": {
        "locale": "文档语言",
        "guide_id": "指南",
        "topic_kind": "页面类型",
        "firefox_channel": "Firefox 频道",
        "policy_category": "策略类别",
        "cis_level": "CIS 级别",
        "cis_control_state": "CIS 状态",
        "api_area": "API 区域",
        "bpm_version": "BPM 版本",
    },
    "fr": {
        "locale": "Langue de documentation",
        "guide_id": "Guide",
        "topic_kind": "Type de page",
        "firefox_channel": "Canal Firefox",
        "policy_category": "Catégorie de règle",
        "cis_level": "Niveau CIS",
        "cis_control_state": "État CIS",
        "api_area": "Domaine API",
        "bpm_version": "Version BPM",
    },
    "es-ES": {
        "locale": "Idioma de la documentación",
        "guide_id": "Guía",
        "topic_kind": "Tipo de página",
        "firefox_channel": "Canal de Firefox",
        "policy_category": "Categoría de política",
        "cis_level": "Nivel CIS",
        "cis_control_state": "Estado CIS",
        "api_area": "Área de API",
        "bpm_version": "Versión de BPM",
    },
}

SEARCH_FILTER_VALUE_LABELS = {
    "en": {
        "guide_id": {
            "user-guide": "User Guide",
            "firefox-policy-guide": "Firefox Policy Guide",
            "cis-settings-guide": "CIS Settings Guide",
            "administrator-guide": "Administrator/DevOps Guide",
        },
        "topic_kind": {
            "concept": "Concept",
            "task": "Task",
            "reference": "Reference",
            "troubleshooting": "Troubleshooting",
            "landing": "Landing page",
        },
        "firefox_channel": {
            "esr-115.38": "Firefox ESR 115.38",
            "esr-140.13": "Firefox ESR 140.13",
            "esr-153.0": "Firefox ESR 153.0",
            "release-153": "Firefox Release 153",
        },
        "policy_category": {
            "advanced": "Advanced",
            "ai_smart": "AI features",
            "browser_behavior": "Browser behavior",
            "extensions_integrations": "Extensions and integrations",
            "home_startup": "Home and startup",
            "network_access": "Network access",
            "privacy_security": "Privacy and security",
            "search": "Search",
        },
        "cis_level": {"level-1": "CIS Level 1", "level-2": "CIS Level 2"},
        "cis_control_state": {
            "mapped": "Mapped",
            "preference_mapped": "Mapped preference",
            "needs_research": "Needs research",
            "deprecated_or_removed": "Deprecated or removed",
            "manual-review": "Manual review",
            "provenance-only": "Provenance only",
        },
        "api_area": {
            "service": "Service",
            "health": "Health",
            "profiles": "Profiles",
            "validation": "Validation",
            "import-export": "Import and export",
            "ui": "User interface",
        },
    },
    "ru": {
        "guide_id": {
            "user-guide": "Руководство пользователя",
            "firefox-policy-guide": "Руководство по политикам Firefox",
            "cis-settings-guide": "Руководство по настройкам CIS",
            "administrator-guide": "Руководство администратора и DevOps",
        },
        "topic_kind": {
            "concept": "Обзор",
            "task": "Задача",
            "reference": "Справка",
            "troubleshooting": "Устранение неполадок",
            "landing": "Начальная страница",
        },
        "firefox_channel": {
            "esr-115.38": "Firefox ESR 115.38",
            "esr-140.13": "Firefox ESR 140.13",
            "esr-153.0": "Firefox ESR 153.0",
            "release-153": "Firefox Release 153",
        },
        "policy_category": {
            "advanced": "Расширенные настройки",
            "ai_smart": "Возможности ИИ",
            "browser_behavior": "Поведение браузера",
            "extensions_integrations": "Расширения и интеграции",
            "home_startup": "Домашняя страница и запуск",
            "network_access": "Доступ к сети",
            "privacy_security": "Приватность и безопасность",
            "search": "Поиск",
        },
        "cis_level": {"level-1": "CIS уровень 1", "level-2": "CIS уровень 2"},
        "cis_control_state": {
            "mapped": "Сопоставлено",
            "preference_mapped": "Сопоставлено с настройкой",
            "needs_research": "Требует уточнения",
            "deprecated_or_removed": "Устарело или удалено",
            "manual-review": "Ручная проверка",
            "provenance-only": "Только происхождение",
        },
        "api_area": {
            "service": "Служба",
            "health": "Состояние",
            "profiles": "Профили",
            "validation": "Проверка",
            "import-export": "Импорт и экспорт",
            "ui": "Интерфейс",
        },
    },
    "de": {
        "guide_id": {
            "user-guide": "Benutzerhandbuch",
            "firefox-policy-guide": "Handbuch zu Firefox-Richtlinien",
            "cis-settings-guide": "Handbuch zu CIS-Einstellungen",
            "administrator-guide": "Administrator- und DevOps-Handbuch",
        },
        "topic_kind": {
            "concept": "Überblick",
            "task": "Aufgabe",
            "reference": "Referenz",
            "troubleshooting": "Fehlerbehebung",
            "landing": "Startseite",
        },
        "firefox_channel": {
            "esr-115.38": "Firefox ESR 115.38",
            "esr-140.13": "Firefox ESR 140.13",
            "esr-153.0": "Firefox ESR 153.0",
            "release-153": "Firefox Release 153",
        },
        "policy_category": {
            "advanced": "Erweiterte Einstellungen",
            "ai_smart": "KI-Funktionen",
            "browser_behavior": "Browserverhalten",
            "extensions_integrations": "Erweiterungen und Integrationen",
            "home_startup": "Startseite und Start",
            "network_access": "Netzwerkzugriff",
            "privacy_security": "Datenschutz und Sicherheit",
            "search": "Suche",
        },
        "cis_level": {"level-1": "CIS-Stufe 1", "level-2": "CIS-Stufe 2"},
        "cis_control_state": {
            "mapped": "Zugeordnet",
            "preference_mapped": "Einstellung zugeordnet",
            "needs_research": "Klärung erforderlich",
            "deprecated_or_removed": "Veraltet oder entfernt",
            "manual-review": "Manuelle Prüfung",
            "provenance-only": "Nur Herkunftsnachweis",
        },
        "api_area": {
            "service": "Dienst",
            "health": "Status",
            "profiles": "Profile",
            "validation": "Validierung",
            "import-export": "Import und Export",
            "ui": "Benutzeroberfläche",
        },
    },
    "zh-CN": {
        "guide_id": {
            "user-guide": "用户指南",
            "firefox-policy-guide": "Firefox 策略指南",
            "cis-settings-guide": "CIS 设置指南",
            "administrator-guide": "管理员和 DevOps 指南",
        },
        "topic_kind": {
            "concept": "概念",
            "task": "任务",
            "reference": "参考",
            "troubleshooting": "故障排除",
            "landing": "首页",
        },
        "firefox_channel": {
            "esr-115.38": "Firefox ESR 115.38",
            "esr-140.13": "Firefox ESR 140.13",
            "esr-153.0": "Firefox ESR 153.0",
            "release-153": "Firefox Release 153",
        },
        "policy_category": {
            "advanced": "高级设置",
            "ai_smart": "AI 功能",
            "browser_behavior": "浏览器行为",
            "extensions_integrations": "扩展和集成",
            "home_startup": "主页和启动",
            "network_access": "网络访问",
            "privacy_security": "隐私和安全",
            "search": "搜索",
        },
        "cis_level": {"level-1": "CIS 级别 1", "level-2": "CIS 级别 2"},
        "cis_control_state": {
            "mapped": "已映射",
            "preference_mapped": "已映射到首选项",
            "needs_research": "需要核实",
            "deprecated_or_removed": "已弃用或已移除",
            "manual-review": "人工审核",
            "provenance-only": "仅保留来源",
        },
        "api_area": {
            "service": "服务",
            "health": "状态",
            "profiles": "配置文件",
            "validation": "验证",
            "import-export": "导入和导出",
            "ui": "用户界面",
        },
    },
    "fr": {
        "guide_id": {
            "user-guide": "Guide utilisateur",
            "firefox-policy-guide": "Guide des règles Firefox",
            "cis-settings-guide": "Guide des paramètres CIS",
            "administrator-guide": "Guide administrateur et DevOps",
        },
        "topic_kind": {
            "concept": "Présentation",
            "task": "Tâche",
            "reference": "Référence",
            "troubleshooting": "Dépannage",
            "landing": "Page d’accueil",
        },
        "firefox_channel": {
            "esr-115.38": "Firefox ESR 115.38",
            "esr-140.13": "Firefox ESR 140.13",
            "esr-153.0": "Firefox ESR 153.0",
            "release-153": "Firefox Release 153",
        },
        "policy_category": {
            "advanced": "Paramètres avancés",
            "ai_smart": "Fonctionnalités d’IA",
            "browser_behavior": "Comportement du navigateur",
            "extensions_integrations": "Extensions et intégrations",
            "home_startup": "Accueil et démarrage",
            "network_access": "Accès réseau",
            "privacy_security": "Vie privée et sécurité",
            "search": "Recherche",
        },
        "cis_level": {"level-1": "Niveau CIS 1", "level-2": "Niveau CIS 2"},
        "cis_control_state": {
            "mapped": "Mappé",
            "preference_mapped": "Préférence mappée",
            "needs_research": "À vérifier",
            "deprecated_or_removed": "Obsolète ou supprimé",
            "manual-review": "Examen manuel",
            "provenance-only": "Provenance uniquement",
        },
        "api_area": {
            "service": "Service",
            "health": "État",
            "profiles": "Profils",
            "validation": "Validation",
            "import-export": "Importation et exportation",
            "ui": "Interface utilisateur",
        },
    },
    "es-ES": {
        "guide_id": {
            "user-guide": "Guía de usuario",
            "firefox-policy-guide": "Guía de políticas de Firefox",
            "cis-settings-guide": "Guía de ajustes CIS",
            "administrator-guide": "Guía de administración y DevOps",
        },
        "topic_kind": {
            "concept": "Descripción general",
            "task": "Tarea",
            "reference": "Referencia",
            "troubleshooting": "Solución de problemas",
            "landing": "Página inicial",
        },
        "firefox_channel": {
            "esr-115.38": "Firefox ESR 115.38",
            "esr-140.13": "Firefox ESR 140.13",
            "esr-153.0": "Firefox ESR 153.0",
            "release-153": "Firefox Release 153",
        },
        "policy_category": {
            "advanced": "Ajustes avanzados",
            "ai_smart": "Funciones de IA",
            "browser_behavior": "Comportamiento del navegador",
            "extensions_integrations": "Extensiones e integraciones",
            "home_startup": "Inicio y arranque",
            "network_access": "Acceso de red",
            "privacy_security": "Privacidad y seguridad",
            "search": "Búsqueda",
        },
        "cis_level": {"level-1": "Nivel CIS 1", "level-2": "Nivel CIS 2"},
        "cis_control_state": {
            "mapped": "Asignado",
            "preference_mapped": "Preferencia asignada",
            "needs_research": "Requiere revisión",
            "deprecated_or_removed": "Obsoleto o eliminado",
            "manual-review": "Revisión manual",
            "provenance-only": "Solo procedencia",
        },
        "api_area": {
            "service": "Servicio",
            "health": "Estado",
            "profiles": "Perfiles",
            "validation": "Validación",
            "import-export": "Importación y exportación",
            "ui": "Interfaz de usuario",
        },
    },
}


class BuildError(RuntimeError):
    """A documentation validation or publishing failure."""


def _product_header_labels(locale: str) -> dict[str, str]:
    """Load the shared BPM header labels from the runtime locale catalog."""

    try:
        catalog = json.loads(
            (REPOSITORY_ROOT / "app" / "i18n" / f"{locale}.json").read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise BuildError(f"cannot read product locale catalog {locale}: {exc}") from exc

    keys = {
        **PRODUCT_HEADER_LABEL_KEYS,
        **{
            f"firefox_schema_{channel}": key
            for channel, key in PRODUCT_FIREFOX_SCHEMA_LABEL_KEYS.items()
        },
        **{f"locale_option_{code}": key for code, key in PRODUCT_LOCALE_OPTION_LABEL_KEYS.items()},
    }
    labels = {name: catalog.get(key) for name, key in keys.items()}
    missing = [key for key, value in labels.items() if not isinstance(value, str) or not value]
    if missing:
        raise BuildError(
            f"product locale catalog {locale} is missing header labels: {', '.join(missing)}"
        )
    return labels  # type: ignore[return-value]


def _product_version() -> str:
    try:
        project = tomllib.loads((REPOSITORY_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        version = project["project"]["version"]
    except (OSError, tomllib.TOMLDecodeError, KeyError) as exc:
        raise BuildError(f"cannot read product version: {exc}") from exc
    if not isinstance(version, str) or not version.strip():
        raise BuildError("product version is missing or invalid")
    return version


def _load_lock() -> dict[str, Any]:
    try:
        return json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BuildError(f"cannot read toolchain lock: {exc}") from exc


def toolchain() -> tuple[Path, Path]:
    lock = _load_lock()
    cache = REPOSITORY_ROOT / lock["cache_directory"]
    dita = cache / "installs" / f"dita-ot-{lock['components']['dita_ot']['version']}" / "bin/dita"
    java = cache / "installs" / f"temurin-jre-{lock['components']['java']['version']}" / "bin/java"
    for executable in (dita, java):
        if not executable.is_file() or not os.access(executable, os.X_OK):
            raise BuildError(
                f"locked toolchain executable is missing: {executable}; run make setup-docs-toolchain"
            )
    return dita, java.parent.parent
