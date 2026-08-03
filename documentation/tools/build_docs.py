#!/usr/bin/env python3
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
DOCUMENTATION_ASSISTANT_COPY = (
    DOCUMENTATION_ROOT / "config/documentation-assistant-copy-0.9.3.json"
)
PDF_LAYOUT_CONTRACT = (
    DOCUMENTATION_ROOT / "config/future-distribution-documentation-layout-0.9.3.json"
)
PDF_GENERATION_CONTRACT = (
    DOCUMENTATION_ROOT / "config/pdf-generation-contract-0.9.3.json"
)
PDF_THEME = DOCUMENTATION_ROOT / "assets/pdf/bpm-pdf-theme.yaml"
PDF_PRINT_CSS = DOCUMENTATION_ROOT / "assets/pdf/bpm-guide-print.css"
PDF_COVER_LOGO = DOCUMENTATION_ROOT / "assets/branding/bpm-logo.png"
PDF_COVER_BRANDING = DOCUMENTATION_ROOT / "assets/pdf/bpm-cover-branding.png"
PDF_BUILD_ROOT = BUILD_ROOT / "pdf"
PDF_BUILD_MANIFEST = "pdf-build-manifest.json"
PDF_GUIDE_MAPS = (
    ("user-guide", "user-guide.ditamap"),
    ("administrator-guide", "administrator-guide.ditamap"),
)
PDF_FIXED_CREATION_DATE = b"D:19700101000000+00'00'"
PDF_FIXED_UTC_CREATION_DATE = b"D:19700101000000Z"
PDF_FIXED_DOCUMENT_ID = b"0" * 32
PDF_CREATION_DATE_PATTERN = re.compile(
    rb"(/CreationDate\s*\()(D:\d{14}(?:[+-]\d{2}'\d{2}'|Z))(\))"
)
PDF_MODIFICATION_DATE_PATTERN = re.compile(
    rb"(/ModDate\s*\()(D:\d{14}(?:[+-]\d{2}'\d{2}'|Z))(\))"
)
PDF_DOCUMENT_ID_PATTERN = re.compile(
    rb"/ID\s*\[\s*<[0-9A-Fa-f]{32}>\s*<[0-9A-Fa-f]{32}>\s*\]"
)
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
        "search_help": "Search uses this locale’s static offline index. No AI, telemetry, or network search is used.",
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
        "assistant_clarify": "Please clarify the BPM setting, policy, guide, or task you want to discuss.",
        "assistant_abstain": "I could not find enough current documentation evidence to answer reliably.",
        "assistant_refuse": "I can help only with Browser Policy Manager documentation and settings.",
        "assistant_cancelled_short": "Request cancelled",
        "assistant_time_preview": "Expected time: from {minimum} to {maximum}",
        "assistant_answer_failed": "The answer could not be completed.",
        "assistant_description": "Ask BPM documentation questions when the local assistant is available. Search and guide navigation remain available independently.",
        "assistant_unavailable": "The local documentation assistant is unavailable. Search and navigation are available.",
        "assistant_transcript": "Conversation",
        "assistant_question": "Question about BPM documentation",
        "assistant_question_placeholder": "Ask about Browser Policy Manager documentation",
        "assistant_controls_unavailable": "Conversation controls are unavailable until the local assistant can be used.",
        "assistant_send": "Send",
        "assistant_stop": "Stop",
        "assistant_clear": "Clear conversation",
        "assistant_answer_mode": "Answer state",
        "assistant_sources": "Sources",
        "assistant_manage_model": "Manage local model",
        "assistant_web_title": "Optional external evidence",
        "assistant_web_local_only": "External evidence is off. Answers use local BPM documentation only.",
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
        "search_help": "Поиск использует статический офлайн-индекс текущей локали. ИИ, телеметрия и сетевой поиск не используются.",
        "search_filters": "Фильтры",
        "search_results": "Результаты поиска",
        "search_loading": "Загружается локальный поисковый индекс…",
        "search_ready": "Введите запрос или выберите фильтры для поиска в документации.",
        "search_no_results": "Нет страниц документации, соответствующих запросу и выбранным фильтрам.",
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
        "assistant_clarify": "Уточните, какую настройку, политику, руководство или задачу BPM вы хотите обсудить.",
        "assistant_abstain": "Я не нашёл достаточно актуальных сведений в документации для достоверного ответа.",
        "assistant_refuse": "Я могу помочь только с документацией и настройками Browser Policy Manager.",
        "assistant_cancelled_short": "Запрос отменён",
        "assistant_time_preview": "Ожидаемое время: от {minimum} до {maximum}",
        "assistant_answer_failed": "Не удалось завершить ответ.",
        "assistant_description": "Задавайте вопросы по документации BPM, когда локальный помощник доступен. Поиск и навигация по руководствам работают независимо.",
        "assistant_unavailable": "Локальный помощник по документации недоступен. Поиск и навигация доступны.",
        "assistant_transcript": "Диалог",
        "assistant_question": "Вопрос по документации BPM",
        "assistant_question_placeholder": "Задайте вопрос по документации Browser Policy Manager",
        "assistant_controls_unavailable": "Элементы диалога недоступны, пока нельзя использовать локального помощника.",
        "assistant_send": "Отправить",
        "assistant_stop": "Остановить",
        "assistant_clear": "Очистить диалог",
        "assistant_answer_mode": "Состояние ответа",
        "assistant_sources": "Источники",
        "assistant_manage_model": "Управление локальной моделью",
        "assistant_web_title": "Необязательные внешние сведения",
        "assistant_web_local_only": "Внешние сведения выключены. Ответы используют только локальную документацию BPM.",
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
        "search_help": "Die Suche verwendet den statischen Offline-Index dieser Sprache. Keine KI, Telemetrie oder Netzwerksuche wird verwendet.",
        "search_filters": "Filter",
        "search_results": "Suchergebnisse",
        "search_loading": "Lokaler Suchindex wird geladen…",
        "search_ready": "Geben Sie eine Anfrage ein oder wählen Sie Filter, um diese Dokumentation zu durchsuchen.",
        "search_no_results": "Keine Dokumentationsseiten entsprechen der Anfrage und den ausgewählten Filtern.",
        "search_unavailable": "Die Suche ist nicht verfügbar, weil der lokale Index nicht geladen werden konnte.",
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
        "assistant_clarify": "Bitte präzisieren Sie die BPM-Einstellung, Richtlinie, Anleitung oder Aufgabe, die Sie besprechen möchten.",
        "assistant_abstain": "Ich konnte nicht genügend aktuelle Dokumentationsbelege für eine zuverlässige Antwort finden.",
        "assistant_refuse": "Ich kann nur bei Browser-Policy-Manager-Dokumentation und -Einstellungen helfen.",
        "assistant_cancelled_short": "Anfrage abgebrochen",
        "assistant_time_preview": "Voraussichtliche Dauer: von {minimum} bis {maximum}",
        "assistant_answer_failed": "Die Antwort konnte nicht fertiggestellt werden.",
        "assistant_description": "Stellen Sie Fragen zur BPM-Dokumentation, wenn der lokale Assistent verfügbar ist. Suche und Handbuchnavigation bleiben unabhängig verfügbar.",
        "assistant_unavailable": "Der lokale Dokumentationsassistent ist nicht verfügbar. Suche und Navigation sind verfügbar.",
        "assistant_transcript": "Unterhaltung",
        "assistant_question": "Frage zur BPM-Dokumentation",
        "assistant_question_placeholder": "Stellen Sie eine Frage zur Browser-Policy-Manager-Dokumentation",
        "assistant_controls_unavailable": "Die Dialog-Steuerelemente sind erst verfügbar, wenn der lokale Assistent verwendet werden kann.",
        "assistant_send": "Senden",
        "assistant_stop": "Anhalten",
        "assistant_clear": "Unterhaltung löschen",
        "assistant_answer_mode": "Antwortstatus",
        "assistant_sources": "Quellen",
        "assistant_manage_model": "Lokales Modell verwalten",
        "assistant_web_title": "Optionale externe Belege",
        "assistant_web_local_only": "Externe Belege sind ausgeschaltet. Antworten verwenden nur lokale BPM-Dokumentation.",
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
        "assistant_description": "本地助手可用时，您可以询问 BPM 文档问题。搜索和指南导航始终可独立使用。",
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
        "status": "Le paquet d’exécution attend le manifeste, la recherche et les métadonnées des cibles UI.",
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
        "search_help": "La recherche utilise l’index statique hors ligne de cette langue. Aucune IA, télémétrie ni recherche réseau n’est utilisée.",
        "search_filters": "Filtres",
        "search_results": "Résultats de recherche",
        "search_loading": "Chargement de l’index de recherche local…",
        "search_ready": "Saisissez une requête ou choisissez des filtres pour rechercher dans cette documentation.",
        "search_no_results": "Aucune page de documentation ne correspond à la requête et aux filtres sélectionnés.",
        "search_unavailable": "La recherche est indisponible car l’index local n’a pas pu être chargé.",
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
        "assistant_clarify": "Précisez le paramètre, la règle, le guide ou la tâche BPM dont vous voulez parler.",
        "assistant_abstain": "Je n’ai pas trouvé suffisamment de preuves documentaires actuelles pour répondre de manière fiable.",
        "assistant_refuse": "Je peux aider uniquement avec la documentation et les paramètres de Browser Policy Manager.",
        "assistant_cancelled_short": "Demande annulée",
        "assistant_time_preview": "Durée estimée : de {minimum} à {maximum}",
        "assistant_answer_failed": "La réponse n’a pas pu être terminée.",
        "assistant_description": "Posez des questions sur la documentation BPM lorsque l’assistant local est disponible. La recherche et la navigation dans les guides restent disponibles indépendamment.",
        "assistant_unavailable": "L’assistant de documentation local est indisponible. La recherche et la navigation restent disponibles.",
        "assistant_transcript": "Conversation",
        "assistant_question": "Question sur la documentation BPM",
        "assistant_question_placeholder": "Posez une question sur la documentation de Browser Policy Manager",
        "assistant_controls_unavailable": "Les commandes de conversation sont indisponibles tant que l’assistant local ne peut pas être utilisé.",
        "assistant_send": "Envoyer",
        "assistant_stop": "Arrêter",
        "assistant_clear": "Effacer la conversation",
        "assistant_answer_mode": "État de la réponse",
        "assistant_sources": "Sources",
        "assistant_manage_model": "Gérer le modèle local",
        "assistant_web_title": "Preuves externes facultatives",
        "assistant_web_local_only": "Les preuves externes sont désactivées. Les réponses utilisent uniquement la documentation BPM locale.",
        "assistant_external_sources": "Sources externes",
    },
    "es-ES": {
        "skip": "Ir al contenido",
        "guides": "Guías",
        "locales": "Idioma",
        "breadcrumbs": "Ruta de navegación",
        "home": "Inicio de la documentación",
        "status": "El paquete de runtime espera el manifiesto, la búsqueda y los metadatos de objetivos de UI.",
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
        "search_help": "La búsqueda usa el índice estático sin conexión de este idioma. No se usa IA, telemetría ni búsqueda de red.",
        "search_filters": "Filtros",
        "search_results": "Resultados de búsqueda",
        "search_loading": "Cargando el índice de búsqueda local…",
        "search_ready": "Escriba una consulta o elija filtros para buscar en esta documentación.",
        "search_no_results": "Ninguna página de documentación coincide con la consulta y los filtros seleccionados.",
        "search_unavailable": "La búsqueda no está disponible porque no se pudo cargar el índice local.",
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
        "assistant_clarify": "Aclara el ajuste, la política, la guía o la tarea de BPM que quieres consultar.",
        "assistant_abstain": "No encontré suficiente evidencia actual en la documentación para responder de forma fiable.",
        "assistant_refuse": "Solo puedo ayudar con la documentación y la configuración de Browser Policy Manager.",
        "assistant_cancelled_short": "Solicitud cancelada",
        "assistant_time_preview": "Tiempo estimado: de {minimum} a {maximum}",
        "assistant_answer_failed": "No se pudo completar la respuesta.",
        "assistant_description": "Haz preguntas sobre la documentación de BPM cuando el asistente local esté disponible. La búsqueda y la navegación por las guías siguen disponibles de forma independiente.",
        "assistant_unavailable": "El asistente local de documentación no está disponible. La búsqueda y la navegación siguen disponibles.",
        "assistant_transcript": "Conversación",
        "assistant_question": "Pregunta sobre la documentación de BPM",
        "assistant_question_placeholder": "Haz una pregunta sobre la documentación de Browser Policy Manager",
        "assistant_controls_unavailable": "Los controles de conversación no están disponibles hasta que se pueda usar el asistente local.",
        "assistant_send": "Enviar",
        "assistant_stop": "Detener",
        "assistant_clear": "Borrar conversación",
        "assistant_answer_mode": "Estado de la respuesta",
        "assistant_sources": "Fuentes",
        "assistant_manage_model": "Gestionar el modelo local",
        "assistant_web_title": "Evidencia externa opcional",
        "assistant_web_local_only": "La evidencia externa está desactivada. Las respuestas usan solo documentación BPM local.",
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
            "esr-140.12": "Firefox ESR 140.12",
            "release-152": "Firefox Release 152",
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
            "esr-140.12": "Firefox ESR 140.12",
            "release-152": "Firefox Release 152",
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
            "esr-140.12": "Firefox ESR 140.12",
            "release-152": "Firefox Release 152",
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
            "esr-140.12": "Firefox ESR 140.12",
            "release-152": "Firefox Release 152",
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
            "esr-140.12": "Firefox ESR 140.12",
            "release-152": "Firefox Release 152",
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
            "esr-140.12": "Firefox ESR 140.12",
            "release-152": "Firefox Release 152",
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
            (REPOSITORY_ROOT / "app" / "i18n" / f"{locale}.json").read_text(
                encoding="utf-8"
            )
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise BuildError(f"cannot read product locale catalog {locale}: {exc}") from exc

    keys = {
        **PRODUCT_HEADER_LABEL_KEYS,
        **{
            f"firefox_schema_{channel}": key
            for channel, key in PRODUCT_FIREFOX_SCHEMA_LABEL_KEYS.items()
        },
        **{
            f"locale_option_{code}": key
            for code, key in PRODUCT_LOCALE_OPTION_LABEL_KEYS.items()
        },
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
        project = tomllib.loads(
            (REPOSITORY_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        )
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


def dita_sources() -> list[Path]:
    roots = (
        DOCUMENTATION_ROOT / "src/dita",
        DOCUMENTATION_ROOT / "src/shared",
        DOCUMENTATION_ROOT / "src/generated/firefox",
        DOCUMENTATION_ROOT / "src/generated/cis",
    )
    return sorted(
        path for root in roots for path in root.rglob("*") if path.suffix in SOURCE_SUFFIXES
    )


def _source_target(source: Path, href: str) -> tuple[Path, str]:
    parsed = urllib.parse.urlsplit(href)
    if parsed.scheme or parsed.netloc:
        if parsed.scheme != "https":
            raise BuildError(f"{source}: forbidden link scheme in {href!r}")
        return source, ""
    target = source if not parsed.path else (source.parent / urllib.parse.unquote(parsed.path))
    resolved = target.resolve()
    try:
        resolved.relative_to(DOCUMENTATION_ROOT.resolve())
    except ValueError as exc:
        raise BuildError(f"{source}: link escapes documentation workspace: {href!r}") from exc
    return resolved, urllib.parse.unquote(parsed.fragment)


def _xml_ids(path: Path, cache: dict[Path, set[str]]) -> set[str]:
    if path not in cache:
        try:
            root = ET.parse(path).getroot()
        except (OSError, ET.ParseError) as exc:
            raise BuildError(f"invalid DITA XML {path}: {exc}") from exc
        cache[path] = {element.attrib["id"] for element in root.iter() if "id" in element.attrib}
    return cache[path]


def validate_source_links() -> None:
    sources = dita_sources()
    if not sources:
        raise BuildError("no DITA source files found")
    parsed: dict[Path, ET.Element] = {}
    keys: set[str] = set()
    for source in sources:
        try:
            root = ET.parse(source).getroot()
        except (OSError, ET.ParseError) as exc:
            raise BuildError(f"invalid DITA XML {source}: {exc}") from exc
        parsed[source] = root
        for element in root.iter():
            keys.update(element.attrib.get("keys", "").split())

    id_cache: dict[Path, set[str]] = {}
    errors: list[str] = []
    for source, root in parsed.items():
        for element in root.iter():
            for keyref_attribute in ("keyref", "conkeyref"):
                keyref = element.attrib.get(keyref_attribute)
                if keyref and keyref.split("/", 1)[0] not in keys:
                    errors.append(f"{source}: unknown {keyref_attribute} {keyref!r}")
            href = element.attrib.get("href")
            if not href:
                continue
            try:
                target, fragment = _source_target(source, href)
            except BuildError as exc:
                errors.append(str(exc))
                continue
            if target == source and urllib.parse.urlsplit(href).scheme:
                continue
            if not target.is_file():
                errors.append(f"{source}: missing local target {href!r}")
                continue
            if fragment:
                anchor = fragment.split("/", 1)[-1]
                if anchor not in _xml_ids(target, id_cache):
                    errors.append(f"{source}: missing DITA fragment {fragment!r} in {target}")
    if errors:
        raise BuildError("source link validation failed:\n" + "\n".join(errors))


def _source_keys_from_text(sources: list[Path]) -> set[str]:
    keys: set[str] = set()
    key_attribute = re.compile(r"""\bkeys\s*=\s*(['"])(.*?)\1""", flags=re.DOTALL)
    for source in sources:
        try:
            text = source.read_text(encoding="utf-8")
        except OSError:
            continue
        for _quote, value in key_attribute.findall(text):
            keys.update(value.split())
    return keys


def validate_focused_source_links(focused_sources: list[Path]) -> None:
    sources = [source for source in focused_sources if source.suffix in SOURCE_SUFFIXES]
    if not sources:
        return
    keys = _source_keys_from_text(dita_sources())
    id_cache: dict[Path, set[str]] = {}
    errors: list[str] = []
    for source in sources:
        if not source.is_file():
            errors.append(f"{source}: changed DITA source is missing")
            continue
        try:
            root = ET.parse(source).getroot()
        except (OSError, ET.ParseError) as exc:
            errors.append(f"invalid DITA XML {source}: {exc}")
            continue
        for element in root.iter():
            for keyref_attribute in ("keyref", "conkeyref"):
                keyref = element.attrib.get(keyref_attribute)
                if keyref and keyref.split("/", 1)[0] not in keys:
                    errors.append(f"{source}: unknown {keyref_attribute} {keyref!r}")
            href = element.attrib.get("href")
            if not href:
                continue
            try:
                target, fragment = _source_target(source, href)
            except BuildError as exc:
                errors.append(str(exc))
                continue
            if target == source and urllib.parse.urlsplit(href).scheme:
                continue
            if not target.is_file():
                errors.append(f"{source}: missing local target {href!r}")
                continue
            if fragment:
                anchor = fragment.split("/", 1)[-1]
                if anchor not in _xml_ids(target, id_cache):
                    errors.append(f"{source}: missing DITA fragment {fragment!r} in {target}")
    if errors:
        raise BuildError("focused source link validation failed:\n" + "\n".join(errors))


def _resolve_changed_path(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = REPOSITORY_ROOT / path
    resolved = path.resolve()
    try:
        resolved.relative_to(REPOSITORY_ROOT.resolve())
    except ValueError as exc:
        raise BuildError(f"changed path is outside repository: {value}") from exc
    return resolved


def _git_changed_paths() -> list[Path]:
    paths: list[Path] = []
    commands = (
        ["git", "diff", "--name-only", "--", "documentation", "docs/architecture"],
        [
            "git",
            "ls-files",
            "--others",
            "--exclude-standard",
            "--",
            "documentation",
            "docs/architecture",
        ],
    )
    for command in commands:
        completed = subprocess.run(
            command,
            cwd=REPOSITORY_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode:
            raise BuildError((completed.stdout + "\n" + completed.stderr).strip())
        paths.extend(
            _resolve_changed_path(line) for line in completed.stdout.splitlines() if line.strip()
        )
    return sorted(set(paths))


def _changed_paths(arguments: list[str]) -> list[Path]:
    if arguments:
        return sorted({_resolve_changed_path(argument) for argument in arguments})
    return _git_changed_paths()


def _relative_repo_path(path: Path) -> str:
    return path.relative_to(REPOSITORY_ROOT).as_posix()


def _fast_scope(path: Path) -> dict[str, Any] | None:
    try:
        relative = path.relative_to(DOCUMENTATION_ROOT)
    except ValueError:
        try:
            architecture_relative = path.relative_to(REPOSITORY_ROOT / "docs/architecture")
        except ValueError:
            return None
        return {
            "kind": "architecture-contract",
            "locales": set(LOCALES),
            "guide_roots": set(),
            "search_indexes": set(),
            "path": architecture_relative.as_posix(),
        }
    parts = relative.parts
    if not parts:
        return None
    if parts[:2] == ("src", "dita") and len(parts) >= 4 and parts[2] in LOCALES:
        guide_root = ""
        if parts[3] == "maps":
            guide_root = GUIDE_OUTPUT_ROOT_BY_MAP.get(path.name, "")
        else:
            guide_root = GUIDE_OUTPUT_ROOT_BY_SOURCE_DIR.get(parts[3], "user")
        return {
            "kind": "dita",
            "locales": {parts[2]},
            "guide_roots": {guide_root} if guide_root else set(),
            "search_indexes": {parts[2]},
            "path": relative.as_posix(),
        }
    if parts[:2] == ("src", "shared"):
        return {
            "kind": "shared-source",
            "locales": set(LOCALES),
            "guide_roots": {url_root for *_prefix, url_root in GUIDE_MAPS},
            "search_indexes": set(LOCALES),
            "path": relative.as_posix(),
        }
    if parts[:2] == ("src", "generated"):
        guide_root = {"firefox": "firefox", "cis": "cis"}.get(
            parts[2] if len(parts) > 2 else "", ""
        )
        return {
            "kind": "generated-source",
            "locales": set(LOCALES),
            "guide_roots": {guide_root} if guide_root else set(),
            "search_indexes": set(LOCALES),
            "path": relative.as_posix(),
        }
    if parts[:2] == ("assets", "theme"):
        return {
            "kind": "theme-asset",
            "locales": set(LOCALES),
            "guide_roots": set(),
            "search_indexes": set(),
            "path": relative.as_posix(),
        }
    if parts[:2] == ("assets", "screenshots") and len(parts) >= 3 and parts[2] in LOCALES:
        return {
            "kind": "screenshot-asset",
            "locales": {parts[2]},
            "guide_roots": set(),
            "search_indexes": {parts[2]},
            "path": relative.as_posix(),
        }
    if parts[0] == "config" and path.name.startswith("search-") and path.suffix == ".json":
        return {
            "kind": "search-config",
            "locales": set(LOCALES),
            "guide_roots": set(),
            "search_indexes": set(LOCALES),
            "path": relative.as_posix(),
        }
    if parts[0] in {"config", "runbooks", "tests"}:
        return {
            "kind": f"{parts[0]}-input",
            "locales": set(),
            "guide_roots": set(),
            "search_indexes": set(),
            "path": relative.as_posix(),
        }
    return None


def _topic_id(path: Path) -> str | None:
    if path.suffix not in SOURCE_SUFFIXES or not path.is_file():
        return None
    try:
        root = ET.parse(path).getroot()
    except OSError, ET.ParseError:
        return None
    return root.attrib.get("id")


def _source_line_hint(path: Path, topic_id: str | None = None) -> int | None:
    if not path.is_file():
        return None
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError, UnicodeDecodeError:
        return None
    patterns = [f'id="{topic_id}"', f"id='{topic_id}'"] if topic_id else []
    patterns.extend(["<topic", "<map", "<section"])
    for index, line in enumerate(lines, start=1):
        if any(pattern in line for pattern in patterns):
            return index
    return 1 if lines else None


def _first_fixture_entry(path: Path, collection: str) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError, json.JSONDecodeError:
        return None
    entries = payload.get(collection)
    if isinstance(entries, list) and entries and isinstance(entries[0], dict):
        return entries[0]
    return None


def _diagnostic_context(path: Path) -> dict[str, Any]:
    scope = _fast_scope(path) or {
        "kind": "unknown",
        "locales": set(),
        "guide_roots": set(),
        "search_indexes": set(),
    }
    locales = sorted(scope["locales"])
    guide_roots = sorted(scope["guide_roots"])
    topic_id = _topic_id(path)
    locale = locales[0] if locales else None
    guide = guide_roots[0] if guide_roots else None
    target_url = (
        f"/help/{locale}/{guide}/{topic_id}.html" if locale and guide and topic_id else None
    )
    search_hint = _first_fixture_entry(SEARCH_STATE_FIXTURE, "queries")
    screenshot_hint = _first_fixture_entry(SCREENSHOT_STATE_FIXTURE, "capture_matrix")
    return {
        "source_path": _relative_repo_path(path),
        "failure_domain": scope["kind"],
        "topic_id": topic_id,
        "locale": locale,
        "guide": guide,
        "source_line": _source_line_hint(path, topic_id),
        "target_url": target_url,
        "query": search_hint.get("query") if search_hint else None,
        "query_fixture_id": search_hint.get("id") if search_hint else None,
        "screenshot_state": screenshot_hint.get("id") if screenshot_hint else None,
        "focused_rerun": f"make docs-fast-check DOCS_CHANGED={_relative_repo_path(path)}",
    }


def _diagnostic_payload(error: BaseException, changed_arguments: list[str]) -> dict[str, Any]:
    resolved_paths: list[Path] = []
    for argument in changed_arguments:
        try:
            resolved_paths.append(_resolve_changed_path(argument))
        except BuildError:
            continue
    contexts = [_diagnostic_context(path) for path in resolved_paths]
    focused_rerun = (
        "make docs-fast-check"
        if not changed_arguments
        else 'make docs-fast-check DOCS_CHANGED="' + " ".join(changed_arguments) + '"'
    )
    return {
        "schema_version": 1,
        "backlog_item": "BPM090-M11-06",
        "target_bpm_version": "0.9.1",
        "status": "failed",
        "error_summary": str(error).splitlines()[0],
        "focused_rerun": focused_rerun,
        "contexts": contexts,
        "debug_artifacts_root": "documentation/reports/diagnostics/",
        "retention": "ignored local/CI diagnostics; do not commit generated reports",
    }


def write_failure_diagnostic(error: BaseException, changed_arguments: list[str]) -> Path:
    payload = _diagnostic_payload(error, changed_arguments)
    digest = hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()[:12]
    DIAGNOSTICS_ROOT.mkdir(parents=True, exist_ok=True)
    path = DIAGNOSTICS_ROOT / f"diagnostic-{digest}.json"
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def _affected_output_paths(scopes: list[dict[str, Any]], dita_paths: list[Path]) -> list[str]:
    outputs: set[str] = set()
    topic_ids = {path: _topic_id(path) for path in dita_paths}
    for path, topic_id in topic_ids.items():
        scope = _fast_scope(path)
        if not scope:
            continue
        for locale in scope["locales"]:
            if topic_id:
                guide_roots = scope["guide_roots"] or {"index"}
                for guide_root in guide_roots:
                    if guide_root == "index":
                        outputs.add(f"documentation/build/site/{locale}/index.html")
                    else:
                        outputs.add(
                            f"documentation/build/site/{locale}/{guide_root}/{topic_id}.html"
                        )
            for search_locale in scope["search_indexes"]:
                outputs.add(f"documentation/build/site/search/{search_locale}/index.json")
    for scope in scopes:
        for locale in scope["locales"]:
            for guide_root in scope["guide_roots"]:
                outputs.add(f"documentation/build/site/{locale}/{guide_root}/")
            for search_locale in scope["search_indexes"]:
                outputs.add(f"documentation/build/site/search/{search_locale}/index.json")
    return sorted(outputs)


def _validate_changed_inputs(paths: list[Path]) -> None:
    errors: list[str] = []
    for path in paths:
        scope = _fast_scope(path)
        if scope is None:
            continue
        if not path.exists():
            errors.append(f"{_relative_repo_path(path)}: changed documentation input is missing")
            continue
        if path.is_file() and path.stat().st_size == 0:
            errors.append(f"{_relative_repo_path(path)}: changed documentation input is empty")
            continue
        if path.suffix == ".json":
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                errors.append(f"{_relative_repo_path(path)}: invalid JSON: {exc}")
    if errors:
        raise BuildError("focused input validation failed:\n" + "\n".join(errors))


def fast_check(changed_arguments: list[str] | None = None, *, emit: bool = True) -> dict[str, Any]:
    changed = _changed_paths(changed_arguments or [])
    scoped = [(path, _fast_scope(path)) for path in changed]
    relevant = [(path, scope) for path, scope in scoped if scope is not None]
    if not relevant:
        report = {
            "changed": [_relative_repo_path(path) for path in changed],
            "checked": [],
            "locales": [],
            "guide_roots": [],
            "search_indexes": [],
            "affected_outputs": [],
            "recommended_next_checks": ["make test-docs-contract"],
        }
        if emit:
            print("Documentation fast check: no changed documentation inputs detected.", flush=True)
            print("Recommended next check: make test-docs-contract", flush=True)
        return report

    paths = [path for path, _scope in relevant]
    _validate_changed_inputs(paths)
    focused_dita = [path for path in paths if path.suffix in SOURCE_SUFFIXES]
    validate_focused_source_links(focused_dita)
    scopes = [scope for _path, scope in relevant if scope is not None]
    locales = sorted({locale for scope in scopes for locale in scope["locales"]})
    guide_roots = sorted({guide_root for scope in scopes for guide_root in scope["guide_roots"]})
    search_indexes = sorted({locale for scope in scopes for locale in scope["search_indexes"]})
    affected_outputs = _affected_output_paths(scopes, focused_dita)
    recommended_next_checks = [
        "make test-docs-contract",
        "make docs-validate",
    ]
    report = {
        "changed": [_relative_repo_path(path) for path in changed],
        "checked": [_relative_repo_path(path) for path in paths],
        "locales": locales,
        "guide_roots": guide_roots,
        "search_indexes": search_indexes,
        "affected_outputs": affected_outputs,
        "recommended_next_checks": recommended_next_checks,
    }
    if emit:
        print(f"Documentation fast check: {len(paths)} changed documentation input(s).", flush=True)
        print("Checked inputs:", flush=True)
        for path in report["checked"]:
            print(f"  {path}", flush=True)
        print(f"Affected locales: {', '.join(locales) if locales else 'none'}", flush=True)
        print(
            f"Affected guide roots: {', '.join(guide_roots) if guide_roots else 'none'}", flush=True
        )
        print(
            f"Affected search indexes: {', '.join(search_indexes) if search_indexes else 'none'}",
            flush=True,
        )
        if affected_outputs:
            print("Expected outputs touched by a full docs build:", flush=True)
            for output in affected_outputs[:30]:
                print(f"  {output}", flush=True)
            if len(affected_outputs) > 30:
                print(f"  ... {len(affected_outputs) - 30} more", flush=True)
        print("Fast check passed. Full deterministic gate remains: make docs-validate.", flush=True)
    return report


class _HTMLLinks(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.links: list[str] = []
        self.tags: list[str] = []
        self.h1_count = 0
        self.html_lang = ""
        self.main_count = 0
        self.tree_host_count = 0
        self.embedded_tree_count = 0
        self.body_classes: set[str] = set()
        self.nav_labels: set[str] = set()
        self.forbidden: list[str] = []
        self._script_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        self.tags.append(tag)
        attributes = {name.lower(): value or "" for name, value in attrs}
        if tag == "html":
            self.html_lang = attributes.get("lang", "")
        if tag == "h1":
            self.h1_count += 1
        if tag == "main" and attributes.get("id") == "main-content":
            self.main_count += 1
        if "data-docs-tree-host" in attributes:
            self.tree_host_count += 1
        if attributes.get("role") == "tree" or "data-docs-tree" in attributes:
            self.embedded_tree_count += 1
        if tag == "body":
            self.body_classes.update(attributes.get("class", "").split())
        if tag == "nav" and attributes.get("aria-label"):
            self.nav_labels.add(attributes["aria-label"])
        if tag == "script":
            self._script_depth += 1
            if set(attributes) != {"src", "defer"} or not attributes.get("src"):
                self.forbidden.append("forbidden script element")
        elif tag in {"style", "iframe", "frame", "object", "embed", "applet", "form"}:
            self.forbidden.append(f"forbidden element <{tag}>")
        for name, value in attrs:
            if value is None:
                continue
            name = name.lower()
            if name == "style" or name.startswith("on"):
                self.forbidden.append(f"forbidden attribute {name!r}")
            if name == "id":
                if value in self.ids:
                    raise BuildError(f"duplicate generated HTML id: {value}")
                self.ids.add(value)
            elif name in LINK_ATTRIBUTES:
                self.links.append(value)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "script" and self._script_depth:
            self._script_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._script_depth and data.strip():
            self.forbidden.append("forbidden inline script content")


def _html_document(path: Path, cache: dict[Path, _HTMLLinks]) -> _HTMLLinks:
    if path not in cache:
        parser = _HTMLLinks()
        try:
            parser.feed(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError) as exc:
            raise BuildError(f"cannot parse generated HTML {path}: {exc}") from exc
        cache[path] = parser
    return cache[path]


def validate_output(root: Path) -> None:
    html_files = sorted(root.rglob("*.html"))
    if len(html_files) < len(LOCALES):
        raise BuildError("generated site does not contain an HTML entry point for every locale")
    cache: dict[Path, _HTMLLinks] = {}
    errors: list[str] = []
    workspace_bytes = str(REPOSITORY_ROOT).encode()
    for artifact in sorted(path for path in root.rglob("*") if path.is_file()):
        if workspace_bytes in artifact.read_bytes():
            errors.append(f"generated artifact leaks absolute workspace path: {artifact}")
    for page in html_files:
        locale = page.relative_to(root).parts[0]
        document = _html_document(page, cache)
        if locale in LOCALES:
            if document.html_lang != locale:
                errors.append(f"{page}: html lang must be {locale!r}")
            if document.h1_count != 1:
                errors.append(f"{page}: generated page must contain exactly one h1")
            if document.main_count != 1:
                errors.append(f"{page}: generated page must contain one main#main-content landmark")
            if "bpm-docs-shell" not in document.body_classes:
                errors.append(f"{page}: portal shell class is missing")
            if document.tree_host_count != 1:
                errors.append(f"{page}: portal shell must contain one navigation tree host")
            if document.embedded_tree_count:
                errors.append(f"{page}: portal shell must not embed navigation tree nodes")
            if len(document.nav_labels) < 3:
                errors.append(f"{page}: portal shell must expose distinct navigation labels")
        errors.extend(f"{page}: {issue}" for issue in document.forbidden)
        for link in document.links:
            parsed = urllib.parse.urlsplit(link)
            if parsed.scheme:
                if parsed.scheme != "https":
                    errors.append(f"{page}: forbidden generated link scheme in {link!r}")
                continue
            if parsed.netloc or parsed.path.startswith("/"):
                errors.append(f"{page}: generated link must be relative: {link!r}")
                continue
            target = page if not parsed.path else (page.parent / urllib.parse.unquote(parsed.path))
            if target.is_dir():
                target /= "index.html"
            if not target.is_file():
                errors.append(f"{page}: missing generated target {link!r}")
                continue
            if parsed.fragment and target.suffix == ".html":
                if urllib.parse.unquote(parsed.fragment) not in _html_document(target, cache).ids:
                    errors.append(f"{page}: missing generated fragment in {link!r}")
    if errors:
        raise BuildError("generated link validation failed:\n" + "\n".join(errors))


def _map_title(locale: str, filename: str) -> str:
    source = DOCUMENTATION_ROOT / f"src/dita/{locale}/maps/{filename}"
    try:
        root = ET.parse(source).getroot()
    except (OSError, ET.ParseError) as exc:
        raise BuildError(f"cannot read localized map title {source}: {exc}") from exc
    title = root.find("title")
    if title is None or not "".join(title.itertext()).strip():
        raise BuildError(f"localized map title is missing: {source}")
    return " ".join("".join(title.itertext()).split())


def _escape(value: str) -> str:
    return html.escape(value, quote=True)


def _relative_href(from_html: Path, target: Path) -> str:
    return os.path.relpath(target, from_html.parent).replace(os.sep, "/")


def _navigation_topic_order(filename: str) -> list[str]:
    topic_ids: list[str] = []
    for keyref in _guide_topic_keyrefs("en", filename):
        if not keyref.startswith("topic."):
            raise BuildError(f"guide map uses unsupported topic key: {keyref}")
        topic_ids.append(keyref.removeprefix("topic."))
    return topic_ids


def _navigation_section_labels(taxonomy: dict[str, Any]) -> dict[str, dict[str, str]]:
    catalog = _read_json_file(TOPIC_SECTION_LABELS)
    if catalog.get("locales") != list(LOCALES):
        raise BuildError("topic section label catalog must use the exact locale matrix")
    expected = {
        section["label_key"]
        for document in taxonomy["documents"]
        for section in document["sections"]
    }
    labels = catalog.get("labels", {})
    if set(labels) != expected:
        raise BuildError("topic section label catalog must match the taxonomy label keys exactly")
    for document in taxonomy["documents"]:
        for section in document["sections"]:
            label_key = section["label_key"]
            localized = labels[label_key]
            if set(localized) != set(LOCALES):
                raise BuildError(f"topic section label {label_key} must own every locale")
            if any(
                not isinstance(localized[locale], str) or not localized[locale].strip()
                for locale in LOCALES
            ):
                raise BuildError(
                    f"topic section label {label_key} must be non-empty in every locale"
                )
            if localized["en"] != section["canonical_label"]:
                raise BuildError(
                    f"topic section label {label_key} must preserve its canonical English value"
                )
            if any(localized[locale] == localized["en"] for locale in LOCALES if locale != "en"):
                raise BuildError(f"topic section label {label_key} must not fall back to English")
    return labels


def _navigation_sections() -> dict[str, list[dict[str, Any]]]:
    taxonomy = _read_json_file(TOPIC_SECTION_TAXONOMY)
    labels = _navigation_section_labels(taxonomy)
    return {
        document["guide_id"]: [
            {
                **section,
                "labels": labels[section["label_key"]],
                "node_id": (f"section:{document['guide_id']}:{section['section_id']}"),
            }
            for section in document["sections"]
        ]
        for document in taxonomy["documents"]
    }


def _navigation_model(site_root: Path) -> dict[str, Any]:
    cache_key = str(site_root.resolve())
    cached = _NAVIGATION_MODEL_CACHE.get(cache_key)
    if cached is not None:
        return cached
    model = {
        "topics": _build_topics(site_root),
        "topic_order": {
            filename: _navigation_topic_order(filename)
            for _guide_id, filename, _anchor, _url_root in GUIDE_MAPS
        },
        "sections": _navigation_sections(),
    }
    _NAVIGATION_MODEL_CACHE[cache_key] = model
    return model


def _current_navigation_topic(
    topics: dict[str, dict[str, Any]],
    page: Path,
    site_root: Path,
    locale: str,
) -> tuple[str, str] | None:
    try:
        page_output = page.relative_to(site_root).as_posix()
    except ValueError as exc:
        raise BuildError(f"documentation page is outside site root: {page}") from exc
    guide_ids = {guide_id for guide_id, *_rest in GUIDE_MAPS}
    for topic_id, topic in topics.items():
        if topic_id in guide_ids:
            continue
        if topic["output"].get(locale) == page_output:
            return topic["guide_id"], topic_id
    return None


def _locale_navigation_href(output: str, locale: str) -> str:
    prefix = f"{locale}/"
    if not output.startswith(prefix):
        raise BuildError(f"navigation output is outside locale root: {output}")
    return output.removeprefix(prefix)


def _navigation_topic_node(
    topics: dict[str, dict[str, Any]], topic_id: str, locale: str
) -> dict[str, Any]:
    topic = topics[topic_id]
    return {
        "node_id": topic_id,
        "node_type": "topic",
        "label": topic["title"][locale],
        "href": _locale_navigation_href(topic["output"][locale], locale),
        "anchor": None,
        "label_key": None,
        "children": [],
    }


def _navigation_payload(site_root: Path, locale: str) -> dict[str, Any]:
    model = _navigation_model(site_root)
    topics = model["topics"]
    guide_ids = {guide_id for guide_id, *_rest in GUIDE_MAPS}
    guide_nodes = []
    for guide_id, filename, anchor, _url_root in GUIDE_MAPS:
        guide = topics[guide_id]
        sections = model["sections"].get(guide_id, [])
        if sections:
            children = [
                {
                    "node_id": section["node_id"],
                    "node_type": "section",
                    "label": section["labels"][locale],
                    "href": None,
                    "anchor": None,
                    "label_key": section["label_key"],
                    "children": [
                        _navigation_topic_node(topics, topic_id, locale)
                        for topic_id in section["topics"]
                    ],
                }
                for section in sections
            ]
        else:
            children = [
                _navigation_topic_node(topics, topic_id, locale)
                for topic_id in model["topic_order"][filename]
                if topic_id not in guide_ids
            ]
        guide_nodes.append(
            {
                "node_id": guide_id,
                "node_type": "guide",
                "label": guide["title"][locale],
                "href": (f"{_locale_navigation_href(guide['output'][locale], locale)}#{anchor}"),
                "anchor": anchor,
                "label_key": None,
                "children": children,
            }
        )
    root = {
        "node_id": "documentation-root",
        "node_type": "root",
        "label": SHELL_LABELS[locale]["navigation_root"],
        "href": "index.html",
        "anchor": None,
        "label_key": "navigation.root",
        "children": guide_nodes,
    }

    def count_nodes(node: dict[str, Any]) -> int:
        return 1 + sum(count_nodes(child) for child in node["children"])

    return {
        "$schema": "../schemas/product-documentation-navigation-v1.schema.json",
        "schema_version": 1,
        "documentation_version": _product_version(),
        "locale": locale,
        "node_count": count_nodes(root),
        "root": root,
    }


def generate_navigation_files(site_root: Path) -> None:
    for locale in LOCALES:
        payload = _navigation_payload(site_root, locale)
        _validate_schema(payload, NAVIGATION_SCHEMA)
        _write_json(site_root / locale / "navigation.json", payload)


def _manifest_navigation_root(manifest: dict[str, Any], locale: str) -> dict[str, Any]:
    topics = manifest["topics"]
    sections_by_guide = _navigation_sections()
    guide_ids = {guide_id for guide_id, *_rest in GUIDE_MAPS}

    def topic_node(topic_id: str) -> dict[str, Any]:
        topic = topics[topic_id]
        return {
            "node_id": topic_id,
            "node_type": "topic",
            "label": topic["title"][locale],
            "href": _locale_navigation_href(topic["output"][locale], locale),
            "anchor": None,
            "label_key": None,
            "children": [],
        }

    guide_nodes = []
    for guide_id, filename, anchor, _url_root in GUIDE_MAPS:
        guide = manifest["guides"][guide_id]
        sections = sections_by_guide.get(guide_id, [])
        if sections:
            children = [
                {
                    "node_id": section["node_id"],
                    "node_type": "section",
                    "label": section["labels"][locale],
                    "href": None,
                    "anchor": None,
                    "label_key": section["label_key"],
                    "children": [topic_node(topic_id) for topic_id in section["topics"]],
                }
                for section in sections
            ]
        else:
            children = [
                topic_node(topic_id)
                for topic_id in _navigation_topic_order(filename)
                if topic_id not in guide_ids
            ]
        home_topic = topics[guide["home_topic_id"]]
        guide_nodes.append(
            {
                "node_id": guide_id,
                "node_type": "guide",
                "label": guide["title"][locale],
                "href": (
                    f"{_locale_navigation_href(home_topic['output'][locale], locale)}#{anchor}"
                ),
                "anchor": anchor,
                "label_key": None,
                "children": children,
            }
        )
    return {
        "node_id": "documentation-root",
        "node_type": "root",
        "label": SHELL_LABELS[locale]["navigation_root"],
        "href": "index.html",
        "anchor": None,
        "label_key": "navigation.root",
        "children": guide_nodes,
    }


def _validate_navigation_manifest_alignment(
    locale: str, navigation_payload: dict[str, Any], manifest: dict[str, Any]
) -> None:
    if navigation_payload.get("locale") != locale:
        raise BuildError(f"navigation locale mismatch for {locale}")
    artifact = manifest.get("artifact")
    if not isinstance(artifact, dict):
        raise BuildError("manifest artifact metadata is missing")
    bpm_version = artifact.get("bpm_version")
    documentation_version = artifact.get("documentation_version")
    if (
        not isinstance(bpm_version, str)
        or documentation_version != bpm_version
        or navigation_payload.get("documentation_version") != bpm_version
    ):
        raise BuildError(f"navigation version diverges from BPM artifact metadata for {locale}")
    expected_root = _manifest_navigation_root(manifest, locale)
    if navigation_payload.get("root") != expected_root:
        raise BuildError(f"navigation source diverges from manifest authority for {locale}")

    def count_nodes(node: dict[str, Any]) -> int:
        return 1 + sum(count_nodes(child) for child in node["children"])

    expected_count = count_nodes(expected_root)
    if navigation_payload.get("node_count") != expected_count:
        raise BuildError(f"navigation node count diverges from manifest authority for {locale}")


def _validate_navigation_artifact_record(
    locale: str,
    record: dict[str, Any],
    payload: bytes,
    manifest: dict[str, Any],
    *,
    context: str,
) -> dict[str, Any]:
    if _payload_sha256(payload) != record["sha256"]:
        raise BuildError(f"{context} navigation SHA-256 mismatch for {locale}")
    navigation_payload = _read_json_bytes(payload, record["path"])
    _validate_schema(navigation_payload, NAVIGATION_SCHEMA)
    if record["format_version"] != navigation_payload["schema_version"]:
        raise BuildError(f"{context} navigation format version mismatch for {locale}")
    if record["node_count"] != navigation_payload["node_count"]:
        raise BuildError(f"{context} navigation node count mismatch for {locale}")
    _validate_navigation_manifest_alignment(locale, navigation_payload, manifest)
    return navigation_payload


def _navigation_host(site_root: Path, page: Path, locale: str) -> str:
    labels = SHELL_LABELS[locale]
    current = _current_navigation_topic(
        _navigation_model(site_root)["topics"], page, site_root, locale
    )
    current_node_id = current[1] if current else "documentation-root"
    navigation_href = _relative_href(page, site_root / locale / "navigation.json")
    root_href = _relative_href(page, site_root / locale / "index.html")
    return f"""            <div class="bpm-docs-tree-host" data-docs-tree-host aria-busy="true" data-navigation-href="{_escape(navigation_href)}" data-navigation-locale="{_escape(locale)}" data-navigation-version="{_escape(_product_version())}" data-current-tree-node="{_escape(current_node_id)}" data-tree-storage-key="bpm-docs-tree:{_escape(locale)}:{_escape(_product_version())}" data-label-tree="{_escape(labels["navigation_tree_label"])}" data-label-expand="{_escape(labels["navigation_expand"])}" data-label-collapse="{_escape(labels["navigation_collapse"])}" data-label-current="{_escape(labels["navigation_current"])}" data-label-parent="{_escape(labels["navigation_parent"])}" data-label-back-to-root="{_escape(labels["navigation_back_to_root"])}" data-label-loading="{_escape(labels["navigation_loading"])}" data-label-unavailable="{_escape(labels["navigation_unavailable"])}" data-root-href="{_escape(root_href)}">
               <p class="bpm-docs-tree-status" role="status" aria-live="polite" data-docs-tree-status>{_escape(labels["navigation_loading"])}</p>
               <noscript><p class="bpm-docs-tree-status"><a href="{_escape(root_href)}">{_escape(labels["navigation_back_to_root"])}</a></p></noscript>
            </div>"""


def _navigation_breadcrumbs(site_root: Path, page: Path, locale: str) -> str:
    labels = SHELL_LABELS[locale]
    model = _navigation_model(site_root)
    topics = model["topics"]
    current = _current_navigation_topic(topics, page, site_root, locale)
    root_href = _relative_href(page, site_root / locale / "index.html")
    if not current:
        return f'            <li aria-current="page">{_escape(labels["navigation_root"])}</li>'
    guide_id, topic_id = current
    guide = topics[guide_id]
    topic = topics[topic_id]
    guide_anchor = next(
        anchor
        for candidate_guide_id, _filename, anchor, _url_root in GUIDE_MAPS
        if candidate_guide_id == guide_id
    )
    guide_href = f"{root_href}#{guide_anchor}"
    return "\n".join(
        [
            f'            <li><a href="{_escape(root_href)}">{_escape(labels["navigation_root"])}</a></li>',
            f'            <li><a href="{_escape(guide_href)}">{_escape(guide["title"][locale])}</a></li>',
            f'            <li aria-current="page">{_escape(topic["title"][locale])}</li>',
        ]
    )


def _normalize_locale_root_links(site_root: Path) -> None:
    for locale in LOCALES:
        locale_root = site_root / locale
        for page in sorted(locale_root.rglob("*.html")):
            content = page.read_text(encoding="utf-8")

            def replace_link(
                match: re.Match[str],
                *,
                page: Path = page,
                locale_root: Path = locale_root,
            ) -> str:
                attribute = match.group("attribute")
                quote = match.group("quote")
                value = match.group("value")
                parsed = urllib.parse.urlsplit(value)
                if parsed.scheme or parsed.netloc or not parsed.path.startswith("../"):
                    return match.group(0)
                current_target = page.parent / urllib.parse.unquote(parsed.path)
                stripped_path = parsed.path.removeprefix("../")
                locale_target = locale_root / urllib.parse.unquote(stripped_path)
                if current_target.is_file() or not locale_target.is_file():
                    return match.group(0)
                normalized = urllib.parse.urlunsplit(
                    ("", "", _relative_href(page, locale_target), parsed.query, parsed.fragment)
                )
                return f"{attribute}={quote}{_escape(normalized)}{quote}"

            updated = re.sub(
                r'(?P<attribute>href|src)=(?P<quote>["\'])(?P<value>.*?)(?P=quote)',
                replace_link,
                content,
                flags=re.IGNORECASE,
            )
            if updated != content:
                page.write_text(updated, encoding="utf-8")


def _normalize_screenshot_links(site_root: Path) -> None:
    attribute_pattern = re.compile(
        r'(?P<attribute>href|src)=(?P<quote>["\'])(?P<value>.*?)(?P=quote)',
        flags=re.IGNORECASE,
    )
    for locale in LOCALES:
        locale_root = site_root / locale
        screenshot_root = locale_root / "assets/screenshots"
        if not screenshot_root.is_dir():
            continue
        screenshot_names = {path.name for path in screenshot_root.glob("*.png")}
        for page in sorted(locale_root.rglob("*.html")):
            content = page.read_text(encoding="utf-8")

            def replace_link(
                match: re.Match[str],
                *,
                page: Path = page,
                locale: str = locale,
                screenshot_names: set[str] = screenshot_names,
                screenshot_root: Path = screenshot_root,
            ) -> str:
                attribute = match.group("attribute")
                quote = match.group("quote")
                value = match.group("value")
                parsed = urllib.parse.urlsplit(value)
                if (parsed.scheme and parsed.scheme != "file") or parsed.netloc:
                    return match.group(0)
                parts = [urllib.parse.unquote(part) for part in parsed.path.split("/") if part]
                filename = ""
                for index in range(0, len(parts) - 3):
                    if parts[index : index + 3] == ["assets", "screenshots", locale]:
                        filename = parts[index + 3]
                        break
                if filename not in screenshot_names:
                    return match.group(0)
                normalized = urllib.parse.urlunsplit(
                    (
                        "",
                        "",
                        _relative_href(page, screenshot_root / filename),
                        parsed.query,
                        parsed.fragment,
                    )
                )
                return f"{attribute}={quote}{_escape(normalized)}{quote}"

            updated = attribute_pattern.sub(replace_link, content)
            if updated != content:
                page.write_text(updated, encoding="utf-8")


def _body_with_shell_class(body_tag: str) -> str:
    class_match = re.search(r'\sclass=(["\'])(.*?)\1', body_tag, flags=re.IGNORECASE)
    if class_match:
        classes = class_match.group(2).split()
        if "bpm-docs-shell" not in classes:
            classes.append("bpm-docs-shell")
        start, end = class_match.span(2)
        return body_tag[:start] + " ".join(classes) + body_tag[end:]
    return body_tag[:-1] + ' class="bpm-docs-shell">'


def _html_with_locale(content: str, locale: str) -> str:
    html_match = re.search(r"<html\b[^>]*>", content, flags=re.IGNORECASE)
    if not html_match:
        raise BuildError("generated page lacks an html root element")
    html_tag = html_match.group(0)
    lang_match = re.search(r'\slang=(["\'])(.*?)\1', html_tag, flags=re.IGNORECASE)
    if lang_match:
        start, end = lang_match.span(2)
        html_tag = html_tag[:start] + locale + html_tag[end:]
    else:
        html_tag = html_tag[:-1] + f' lang="{locale}">'
    return content[: html_match.start()] + html_tag + content[html_match.end() :]


def _locale_peer(site_root: Path, page: Path, source_locale: str, target_locale: str) -> Path:
    try:
        locale_relative = page.relative_to(site_root / source_locale)
    except ValueError as exc:
        raise BuildError(f"generated page is outside its locale root: {page}") from exc
    peer = site_root / target_locale / locale_relative
    return peer if peer.is_file() else site_root / target_locale / "index.html"


def _portal_root_anchor_targets(site_root: Path, page: Path, locale: str, body_inner: str) -> str:
    if page != site_root / locale / "index.html":
        return ""
    anchors = []
    for _guide_id, _filename, anchor, _url_root in GUIDE_MAPS:
        if re.search(rf'\sid=(["\']){re.escape(anchor)}\1', body_inner):
            continue
        anchors.append(
            f'            <span id="{_escape(anchor)}" class="bpm-docs-guide-anchor" aria-hidden="true"></span>'
        )
    return "\n".join(anchors)


def _portal_shell(site_root: Path, page: Path, locale: str, body_inner: str) -> str:
    labels = SHELL_LABELS[locale]
    product_header_labels = _product_header_labels(locale)
    product_version = _product_version()
    guide_sidebar = _navigation_host(site_root, page, locale)
    breadcrumbs = _navigation_breadcrumbs(site_root, page, locale)
    product_locale_codes = tuple(option.code for option in PRODUCT_LOCALE_OPTIONS)
    if product_locale_codes != LOCALES:
        raise BuildError(
            "documentation locales must match the product locale picker: "
            f"expected {LOCALES}, got {product_locale_codes}"
        )
    locale_options = "\n".join(
        [
            "                  "
            f'<option value="system" data-docs-locale-system>{_escape(product_header_labels["locale_system"])}</option>'
        ]
        + [
            "                  "
            f'<option value="{_escape(option.code)}" lang="{_escape(option.bcp47)}"'
            f' data-docs-locale-href="{_escape(_relative_href(page, _locale_peer(site_root, page, locale, option.code)))}"'
            f" data-docs-locale-matches='{_escape(json.dumps(option.browser_language_matches))}'"
            f"{' selected' if option.code == locale else ''}>{_escape(product_header_labels[f'locale_option_{option.code}'])}</option>"
            for option in PRODUCT_LOCALE_OPTIONS
        ]
    )
    firefox_versions = "\n".join(
        "               "
        f'<span data-firefox-channel="{_escape(channel.value)}">'
        f'{_escape(product_header_labels[f"firefox_schema_{channel.value}"])}'
        f'{", " if index < len(HEADER_SCHEMA_CHANNELS) - 1 else ""}</span>'
        for index, channel in enumerate(HEADER_SCHEMA_CHANNELS)
    )
    search_index_href = _relative_href(page, site_root / "search" / locale / "index.json")
    root_anchor_targets = _portal_root_anchor_targets(site_root, page, locale, body_inner)
    search_shell = f"""            <section class="bpm-docs-search" role="search" aria-labelledby="bpm-docs-search-heading" data-search-locale="{_escape(locale)}" data-search-index-href="{_escape(search_index_href)}" data-label-loading="{_escape(labels["search_loading"])}" data-label-ready="{_escape(labels["search_ready"])}" data-label-no-results="{_escape(labels["search_no_results"])}" data-label-unavailable="{_escape(labels["search_unavailable"])}" data-label-result-singular="{_escape(labels["search_result_singular"])}" data-label-result-plural="{_escape(labels["search_result_plural"])}" data-label-active-filters="{_escape(labels["search_active_filters"])}">
               <h2 id="bpm-docs-search-heading" class="bpm-docs-visually-hidden">{_escape(labels["search"])}</h2>
               <div class="bpm-docs-search-form">
                  <label class="bpm-docs-visually-hidden" for="bpm-docs-search-query">{_escape(labels["search_query"])}</label>
                  <div class="bpm-docs-search-row">
                     <input id="bpm-docs-search-query" class="bpm-docs-search-input" name="q" type="search" inputmode="search" maxlength="256" autocomplete="off" placeholder="{_escape(labels["search_placeholder"])}">
                     <button class="bpm-docs-search-submit" type="button" data-search-submit>{_escape(labels["search_submit"])}</button>
                     <button class="bpm-docs-search-clear" type="button" data-search-clear>{_escape(labels["search_clear"])}</button>
                     <button class="bpm-docs-search-advanced-toggle" type="button" aria-expanded="false" aria-controls="bpm-docs-search-advanced-panel" data-search-advanced-toggle>{_escape(labels["search_filters"])}</button>
                  </div>
                  <div class="bpm-docs-search-active-filters" data-search-active-filters hidden>
                     <span role="status" aria-live="polite" aria-atomic="true" data-search-active-filters-summary></span>
                     <button class="bpm-docs-search-clear-filters" type="button" data-search-clear-filters>{_escape(labels["search_clear_filters"])}</button>
                  </div>
               </div>
               <div id="bpm-docs-search-advanced-panel" class="bpm-docs-search-advanced-panel" data-search-advanced-panel hidden>
                  <p class="bpm-docs-search-help" id="bpm-docs-search-help">{_escape(labels["search_help"])}</p>
                  <div class="bpm-docs-search-filters">
                     <h3>{_escape(labels["search_filters"])}</h3>
                     <div class="bpm-docs-search-filter-grid" data-search-filters></div>
                  </div>
                  <p class="bpm-docs-search-status" role="status" aria-live="polite" data-search-status>{_escape(labels["search_loading"])}</p>
                  <section class="bpm-docs-search-results" aria-labelledby="bpm-docs-search-results-heading">
                  <h3 id="bpm-docs-search-results-heading">{_escape(labels["search_results"])}</h3>
                  <ol class="bpm-docs-search-result-list" data-search-results></ol>
                  </section>
               </div>
            </section>"""
    discovery_shell = f"""            <div class="bpm-docs-discovery-tools">
{search_shell}
            </div>"""
    assistant_shell = f"""      <section class="bpm-docs-assistant-widget" data-documentation-assistant-widget data-assistant-locale="{_escape(locale)}" data-assistant-expanded="false" data-assistant-state="unavailable" data-assistant-label-ready="{_escape(labels["assistant_ready"])}" data-assistant-label-busy="{_escape(labels["assistant_busy_short"])}" data-assistant-label-unavailable="{_escape(labels["assistant_unavailable_short"])}" data-assistant-label-installing="{_escape(labels["assistant_installing"])}" data-assistant-label-verifying="{_escape(labels["assistant_verifying_model"])}" data-assistant-label-preparing="{_escape(labels["assistant_preparing_documentation"])}" data-assistant-label-install-failed="{_escape(labels["assistant_install_failed"])}" data-assistant-label-clarify="{_escape(labels["assistant_clarify"])}" data-assistant-label-abstain="{_escape(labels["assistant_abstain"])}" data-assistant-label-refuse="{_escape(labels["assistant_refuse"])}" data-assistant-label-cancelled="{_escape(labels["assistant_cancelled_short"])}" data-assistant-label-time-preview="{_escape(labels["assistant_time_preview"])}" data-assistant-label-answer-failed="{_escape(labels["assistant_answer_failed"])}" data-assistant-label-sources="{_escape(labels["assistant_sources"])}" data-assistant-label-external-sources="{_escape(labels["assistant_external_sources"])}">
         <button class="bpm-docs-assistant-toggle" type="button" aria-expanded="false" aria-controls="bpm-docs-assistant-panel" data-assistant-toggle>{_escape(labels["assistant"])}</button>
         <section id="bpm-docs-assistant-panel" class="bpm-docs-assistant-panel" aria-label="{_escape(labels["assistant"])}" data-assistant-panel hidden>
            <button class="bpm-docs-assistant-panel-title" type="button" aria-label="{_escape(labels["assistant_close"])}" data-assistant-collapse>{_escape(labels["assistant"])}</button>
            <ol id="bpm-docs-assistant-transcript" class="bpm-docs-assistant-transcript" role="log" aria-label="{_escape(labels["assistant_transcript"])}" aria-live="polite" aria-relevant="additions text" aria-atomic="false" data-assistant-transcript data-assistant-message-roles="user assistant system"></ol>
            <div class="bpm-docs-assistant-controls" data-assistant-controls>
               <label class="bpm-docs-visually-hidden" for="bpm-docs-assistant-question">{_escape(labels["assistant_question"])}</label>
               <textarea id="bpm-docs-assistant-question" name="question" rows="3" maxlength="4000" placeholder="{_escape(labels["assistant_question_placeholder"])}" disabled aria-disabled="true" data-assistant-question></textarea>
               <button class="bpm-docs-assistant-send" type="button" disabled aria-disabled="true" hidden data-assistant-send>{_escape(labels["assistant_send"])}</button>
            </div>
            <div class="bpm-docs-assistant-status-row">
               <p id="bpm-docs-assistant-status" class="bpm-docs-assistant-status" role="status" aria-live="polite" aria-atomic="true" data-assistant-status>{_escape(labels["assistant_unavailable_short"])}</p>
               <button class="bpm-docs-assistant-stop" type="button" disabled aria-disabled="true" hidden data-assistant-stop>{_escape(labels["assistant_stop"])}</button>
               <button class="bpm-docs-assistant-clear" type="button" hidden data-assistant-clear>{_escape(labels["assistant_clear_short"])}</button>
               <button class="bpm-docs-assistant-install" type="button" disabled aria-disabled="true" data-assistant-install>{_escape(labels["assistant_install_model"])}</button>
            </div>
         </section>
      </section>"""
    return f"""      <a class="bpm-docs-skip-link" href="#main-content">{_escape(labels["skip"])}</a>
      <header class="bpm-docs-header">
         <div class="bpm-docs-header-main">
            <p class="bpm-docs-header-title">Browser Policy Manager <span class="bpm-docs-header-version">v{_escape(product_version)}</span></p>
            <p class="bpm-docs-header-firefox-versions" data-supported-firefox-versions><span class="bpm-docs-header-firefox-versions-label">{_escape(product_header_labels["supported_firefox_versions"])}</span>
{firefox_versions}
            </p>
         </div>
         <div class="bpm-docs-header-side">
            <div class="bpm-docs-header-actions">
            <nav class="bpm-docs-header-control bpm-docs-locale-control" aria-label="{_escape(product_header_labels["locales"])}">
               <span class="bpm-docs-header-control-label">{_escape(product_header_labels["locales"])}</span>
               <select id="bpm-docs-locale" name="locale" aria-label="{_escape(product_header_labels["locales"])}" data-docs-locale-select>
{locale_options}
               </select>
            </nav>
            <label class="bpm-docs-header-control bpm-docs-theme-control" for="bpm-docs-theme">
               <span class="bpm-docs-header-control-label">{_escape(product_header_labels["theme"])}</span>
               <select id="bpm-docs-theme" name="theme" data-docs-theme-select>
                  <option value="system">{_escape(product_header_labels["theme_system"])}</option>
                  <option value="light">{_escape(product_header_labels["theme_light"])}</option>
                  <option value="dark">{_escape(product_header_labels["theme_dark"])}</option>
               </select>
            </label>
            </div>
         </div>
      </header>
      <nav class="bpm-docs-breadcrumbs" aria-label="{_escape(labels["breadcrumbs"])}">
         <ol>
{breadcrumbs}
         </ol>
      </nav>
      <div class="bpm-docs-content-grid">
         <aside class="bpm-docs-sidebar" aria-labelledby="bpm-docs-guides-heading">
            <h2 id="bpm-docs-guides-heading">{_escape(labels["guides"])}</h2>
            <nav class="bpm-docs-tree-nav" aria-label="{_escape(labels["navigation_tree_label"])}">
{guide_sidebar}
            </nav>
         </aside>
         <main id="main-content" class="bpm-docs-main" tabindex="-1">
{discovery_shell}
{root_anchor_targets}
{body_inner.rstrip()}
         </main>
      </div>
{assistant_shell}
      <footer class="bpm-docs-footer">
         <p>{_escape(labels["status"])}</p>
      </footer>
"""


def _install_theme_assets(locale_root: Path) -> None:
    assets_root = locale_root / "assets"
    assets_root.mkdir(parents=True, exist_ok=True)
    for filename in THEME_FILES:
        source = THEME_ROOT / filename
        if not source.is_file():
            raise BuildError(f"missing portal theme asset: {source}")
        shutil.copyfile(source, assets_root / filename)
    for script_name in (
        SEARCH_SCRIPT,
        MODEL_MANAGER_SCRIPT,
        ASSISTANT_RENDERER_SCRIPT,
        ASSISTANT_STATE_MACHINE_SCRIPT,
        ASSISTANT_CONVERSATION_SCRIPT,
        ASSISTANT_TRANSPORT_SCRIPT,
        ASSISTANT_SHELL_SCRIPT,
    ):
        script = THEME_ROOT / script_name
        if not script.is_file():
            raise BuildError(f"missing portal script asset: {script}")
        shutil.copyfile(script, assets_root / script_name)


def _install_screenshot_assets(locale_root: Path) -> None:
    locale = locale_root.name
    source_root = SCREENSHOT_ROOT / locale
    if not source_root.is_dir():
        raise BuildError(f"missing localized screenshot assets: {source_root}")
    target_root = locale_root / "assets/screenshots"
    target_root.mkdir(parents=True, exist_ok=True)
    for source in sorted(source_root.glob("*.png")):
        shutil.copyfile(source, target_root / source.name)


def _remove_dita_transient_screenshot_copies(site_root: Path) -> None:
    """Remove DITA-OT copies made from absolute screenshot source paths.

    Some DITA-OT transforms preserve an absolute ``file:`` screenshot path as a
    nested ``<locale>/home/.../assets/screenshots/<locale>/`` output tree.  The
    portal uses the separately installed, locale-relative screenshot assets;
    the nested copies are non-publishable and make two otherwise identical
    builds differ by their temporary-directory name.
    """

    for locale in LOCALES:
        locale_root = site_root / locale
        expected_names = {
            source.name for source in (SCREENSHOT_ROOT / locale).glob("*.png")
        }
        transient_roots: set[Path] = set()
        for copied in locale_root.rglob("*.png"):
            relative = copied.relative_to(locale_root)
            if len(relative.parts) < 5:
                continue
            if tuple(relative.parts[-4:-1]) != ("assets", "screenshots", locale):
                continue
            if copied.name not in expected_names:
                continue
            transient_roots.add(locale_root / relative.parts[0])

        for transient_root in sorted(transient_roots):
            files = [path for path in transient_root.rglob("*") if path.is_file()]
            if not files:
                continue
            if not all(
                len(path.relative_to(locale_root).parts) >= 5
                and tuple(path.relative_to(locale_root).parts[-4:-1])
                == ("assets", "screenshots", locale)
                and path.name in expected_names
                for path in files
            ):
                raise BuildError(
                    "unexpected generated files beneath transient screenshot root: "
                    f"{transient_root}"
                )
            shutil.rmtree(transient_root)


def _apply_portal_shell_to_page(site_root: Path, page: Path, locale: str) -> None:
    content = _html_with_locale(page.read_text(encoding="utf-8"), locale)
    head_end = re.search(r"</head\s*>", content, flags=re.IGNORECASE)
    body_start = re.search(r"<body\b[^>]*>", content, flags=re.IGNORECASE)
    body_end = re.search(r"</body\s*>", content, flags=re.IGNORECASE)
    if not head_end or not body_start or not body_end:
        raise BuildError(f"generated page lacks head/body shell anchors: {page}")
    css_links = (
        '      <meta name="theme-color" content="#edf2f7">\n'
        f'      <link rel="stylesheet" type="text/css" href="'
        f'{_escape(_relative_href(page, site_root / locale / "assets" / THEME_FILES[0]))}">\n'
        f'      <link rel="stylesheet" type="text/css" media="print" href="'
        f'{_escape(_relative_href(page, site_root / locale / "assets" / THEME_FILES[1]))}">\n'
        f'      <script src="{_escape(_relative_href(page, site_root / locale / "assets" / SEARCH_SCRIPT))}" defer></script>\n'
        f'      <script src="{_escape(_relative_href(page, site_root / locale / "assets" / MODEL_MANAGER_SCRIPT))}" defer></script>\n'
        f'      <script src="{_escape(_relative_href(page, site_root / locale / "assets" / ASSISTANT_RENDERER_SCRIPT))}" defer></script>\n'
        f'      <script src="{_escape(_relative_href(page, site_root / locale / "assets" / ASSISTANT_STATE_MACHINE_SCRIPT))}" defer></script>\n'
        f'      <script src="{_escape(_relative_href(page, site_root / locale / "assets" / ASSISTANT_CONVERSATION_SCRIPT))}" defer></script>\n'
        f'      <script src="{_escape(_relative_href(page, site_root / locale / "assets" / ASSISTANT_TRANSPORT_SCRIPT))}" defer></script>\n'
        f'      <script src="{_escape(_relative_href(page, site_root / locale / "assets" / ASSISTANT_SHELL_SCRIPT))}" defer></script>\n'
    )
    before_head_close = content[: head_end.start()]
    after_head_close = content[head_end.start() : body_start.start()]
    body_tag = _body_with_shell_class(body_start.group(0))
    body_inner = content[body_start.end() : body_end.start()]
    shell = _portal_shell(site_root, page, locale, body_inner)
    updated = (
        before_head_close
        + css_links
        + after_head_close
        + body_tag
        + "\n"
        + shell
        + content[body_end.start() :]
    )
    page.write_text(updated, encoding="utf-8")


def apply_portal_shell(site_root: Path) -> None:
    for locale in LOCALES:
        locale_root = site_root / locale
        if not locale_root.is_dir():
            raise BuildError(f"generated locale root is missing: {locale_root}")
        _install_theme_assets(locale_root)
        _install_screenshot_assets(locale_root)
    generate_navigation_files(site_root)
    generate_assistant_copy_files(site_root)
    for locale in LOCALES:
        for page in sorted((site_root / locale).rglob("*.html")):
            _apply_portal_shell_to_page(site_root, page, locale)


def _guide_titles(filename: str) -> dict[str, str]:
    return {locale: _map_title(locale, filename) for locale in LOCALES}


def _source_revision() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "--verify", "HEAD"],
        cwd=REPOSITORY_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    revision = completed.stdout.strip()
    if completed.returncode or not re.fullmatch(r"[a-f0-9]{40}", revision):
        raise BuildError("cannot resolve 40-character source revision for documentation manifest")
    return revision


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


_ASSISTANT_SHELL_LABEL_KEYS = (
    "assistant",
    "assistant_close",
    "assistant_unavailable_short",
    "assistant_install_model",
    "assistant_installing",
    "assistant_verifying_model",
    "assistant_preparing_documentation",
    "assistant_install_failed",
    "assistant_ready",
    "assistant_clear_short",
    "assistant_busy_short",
    "assistant_clarify",
    "assistant_abstain",
    "assistant_refuse",
    "assistant_cancelled_short",
    "assistant_time_preview",
    "assistant_answer_failed",
    "assistant_busy_short",
    "assistant_clarify",
    "assistant_abstain",
    "assistant_refuse",
    "assistant_cancelled_short",
    "assistant_description",
    "assistant_unavailable",
    "assistant_transcript",
    "assistant_question",
    "assistant_question_placeholder",
    "assistant_controls_unavailable",
    "assistant_send",
    "assistant_stop",
    "assistant_clear",
    "assistant_answer_mode",
    "assistant_sources",
    "assistant_manage_model",
    "assistant_web_title",
    "assistant_web_local_only",
    "assistant_external_sources",
)
_ASSISTANT_COPY_GROUP_KEYS = {
    "dialogue": {
        "scope",
        "out_of_scope",
        "clarification",
        "no_evidence",
        "answer",
        "incomplete",
        "citation_local",
        "citation_external",
        "citation_unavailable",
        "question_too_long",
        "source_guide",
        "source_topic",
        "source_anchor",
        "source_version",
        "source_excerpt",
    },
    "actions": {
        "send",
        "stop",
        "clear",
        "retry",
        "use_search",
        "open_settings",
        "install",
        "verify",
        "cancel",
        "remove",
    },
    "model": {
        "title",
        "optional",
        "cpu",
        "no_sla",
        "source",
        "size",
        "confirm_install",
        "verifying",
        "installed",
        "remove_confirm",
        "removed",
    },
    "resource_states": {
        "queued",
        "timeout",
        "unloading",
        "unloaded",
        "search_only",
        "duplicate",
        "resource_limit",
    },
    "web": {
        "title",
        "disabled",
        "consent_title",
        "consent_question",
        "recipient",
        "privacy",
        "accept",
        "decline",
        "external_label",
        "local_only",
        "consent_required",
        "consent_scope",
        "active",
    },
}


def _documentation_assistant_copy_contract() -> dict[str, Any]:
    contract = _read_json_file(DOCUMENTATION_ASSISTANT_COPY)
    if contract.get("contract_id") != "bpm-documentation-assistant-copy-0.9.3":
        raise BuildError("documentation assistant copy contract identifier is invalid")
    if contract.get("locales") != list(LOCALES):
        raise BuildError("documentation assistant copy locales diverge from the published locales")
    catalog = contract.get("catalog")
    templates = contract.get("state_templates")
    rules = contract.get("catalog_rules")
    if not isinstance(catalog, dict) or set(catalog) != set(LOCALES):
        raise BuildError("documentation assistant copy catalog has incomplete locale coverage")
    if not isinstance(templates, dict) or set(templates) != set(LOCALES):
        raise BuildError("documentation assistant copy templates have incomplete locale coverage")
    if not isinstance(rules, dict):
        raise BuildError("documentation assistant copy rules are missing")
    state_ids = rules.get("state_ids")
    if not isinstance(state_ids, list) or not all(isinstance(item, str) for item in state_ids):
        raise BuildError("documentation assistant copy state inventory is invalid")
    state_fields = rules.get("state_fields")
    if state_fields != ["title", "detail", "action", "live", "aria"]:
        raise BuildError("documentation assistant copy state field inventory is invalid")
    for locale in LOCALES:
        locale_catalog = catalog[locale]
        if not isinstance(locale_catalog, dict):
            raise BuildError(f"documentation assistant copy catalog is invalid for {locale}")
        states = locale_catalog.get("states")
        if not isinstance(states, dict) or list(states) != state_ids:
            raise BuildError(f"documentation assistant state catalog diverges for {locale}")
        for state_id in state_ids:
            state = states[state_id]
            if not isinstance(state, dict) or set(state) != {"title", "detail", "action"}:
                raise BuildError(f"documentation assistant state copy is invalid for {locale}/{state_id}")
            if not all(isinstance(value, str) and value.strip() for value in state.values()):
                raise BuildError(f"documentation assistant state copy is empty for {locale}/{state_id}")
        for group, expected_keys in _ASSISTANT_COPY_GROUP_KEYS.items():
            messages = locale_catalog.get(group)
            if not isinstance(messages, dict) or set(messages) != expected_keys:
                raise BuildError(f"documentation assistant {group} copy diverges for {locale}")
            if not all(isinstance(value, str) and value.strip() for value in messages.values()):
                raise BuildError(f"documentation assistant {group} copy is empty for {locale}")
        template = templates[locale]
        if not isinstance(template, dict) or set(template) != {"live", "aria"}:
            raise BuildError(f"documentation assistant state templates are invalid for {locale}")
        if "{title}" not in template["live"] or "{detail}" not in template["live"]:
            raise BuildError(f"documentation assistant live template is invalid for {locale}")
        if "{title}" not in template["aria"]:
            raise BuildError(f"documentation assistant aria template is invalid for {locale}")
    return contract


def _assistant_copy_payload(locale: str) -> dict[str, Any]:
    if locale not in LOCALES:
        raise BuildError(f"unsupported assistant copy locale: {locale}")
    contract = _documentation_assistant_copy_contract()
    source = contract["catalog"][locale]
    template = contract["state_templates"][locale]
    states = {
        state_id: {
            **state,
            "live": template["live"].format(**state),
            "aria": template["aria"].format(**state),
        }
        for state_id, state in source["states"].items()
    }
    return {
        "schema_version": contract["schema_version"],
        "contract_id": contract["contract_id"],
        "target_bpm_version": contract["target_bpm_version"],
        "locale": locale,
        "messages": {
            "shell": {key: SHELL_LABELS[locale][key] for key in _ASSISTANT_SHELL_LABEL_KEYS},
            "states": states,
            **{group: source[group] for group in _ASSISTANT_COPY_GROUP_KEYS},
        },
    }


def generate_assistant_copy_files(site_root: Path) -> None:
    for locale in LOCALES:
        locale_root = site_root / locale
        if not locale_root.is_dir():
            raise BuildError(f"generated locale root is missing: {locale_root}")
        _write_json(locale_root / "assistant-copy.json", _assistant_copy_payload(locale))


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _payload_sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _schema(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BuildError(f"cannot read documentation JSON schema {path}: {exc}") from exc


def _validate_schema(instance: dict[str, Any], schema_path: Path) -> None:
    try:
        jsonschema.Draft202012Validator(_schema(schema_path)).validate(instance)
    except jsonschema.ValidationError as exc:
        location = "/".join(str(part) for part in exc.absolute_path) or "<root>"
        raise BuildError(
            f"schema validation failed for {schema_path.name} at {location}: {exc.message}"
        ) from exc


def _read_json_file(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BuildError(f"cannot read documentation JSON {path}: {exc}") from exc


def _guide_topic_id(guide_id: str) -> str:
    return guide_id


def _guide_source_inventory(filename: str) -> str:
    return f"documentation/src/dita/en/maps/{filename}"


def _localized_map_keydefs(locale: str) -> dict[str, Path]:
    key_map = DOCUMENTATION_ROOT / f"src/dita/{locale}/maps/keys.ditamap"
    try:
        root = ET.parse(key_map).getroot()
    except (OSError, ET.ParseError) as exc:
        raise BuildError(f"cannot read localized key map {key_map}: {exc}") from exc
    keydefs: dict[str, Path] = {}
    for keydef in root.findall("keydef"):
        key = keydef.attrib.get("keys")
        href = keydef.attrib.get("href")
        if key and href:
            keydefs[key] = (key_map.parent / href).resolve()
    return keydefs


def _topicrefs(root: ET.Element) -> list[str]:
    keyrefs: list[str] = []
    for element in root.iter():
        if element.tag == "topicref":
            keyref = element.attrib.get("keyref")
            if keyref:
                keyrefs.append(keyref)
    return keyrefs


def _guide_topic_keyrefs(locale: str, filename: str) -> list[str]:
    source = DOCUMENTATION_ROOT / f"src/dita/{locale}/maps/{filename}"
    try:
        root = ET.parse(source).getroot()
    except (OSError, ET.ParseError) as exc:
        raise BuildError(f"cannot read localized guide map {source}: {exc}") from exc
    return _topicrefs(root)


def _localized_topic_roots(
    key: str, hrefs_by_locale: dict[str, dict[str, Path]]
) -> dict[str, ET.Element]:
    roots = {}
    for locale in LOCALES:
        try:
            path = hrefs_by_locale[locale][key]
        except KeyError as exc:
            raise BuildError(f"missing localized key {key!r} for {locale}") from exc
        try:
            roots[locale] = ET.parse(path).getroot()
        except (OSError, ET.ParseError) as exc:
            raise BuildError(f"cannot read localized topic {path}: {exc}") from exc
    return roots


def _element_text(element: ET.Element | None) -> str:
    if element is None:
        return ""
    return " ".join("".join(element.itertext()).split())


def _tag_name(element: ET.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def _unique_non_empty(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        normalized = " ".join(value.split())
        if normalized and normalized not in seen:
            unique.append(normalized)
            seen.add(normalized)
    return unique


def _search_normalization_aliases() -> dict[str, Any]:
    return _read_json_file(SEARCH_NORMALIZATION_ALIASES)


def _search_ranking_typo() -> dict[str, Any]:
    return _read_json_file(SEARCH_RANKING_TYPO)


def _search_facets_filters() -> dict[str, Any]:
    config = _read_json_file(SEARCH_FACETS_FILTERS)
    bpm_version = config.get("facet_fields", {}).get("bpm_version", {})
    if bpm_version.get("values") != [PRODUCT_VERSION_FACET_PLACEHOLDER]:
        raise BuildError("search BPM-version facet must derive from the product version")
    bpm_version["values"] = [_product_version()]
    return config


def _search_domain_ranking_facets() -> dict[str, Any]:
    config = _read_json_file(SEARCH_DOMAIN_RANKING_FACETS)
    if config.get("contract_id") != "bpm-doc-search-domain-ranking-facets-0.9.3":
        raise BuildError("unsupported search domain ranking/facets contract")
    return config


def _localized_search_facet_fields(
    locale: str,
    config: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    field_labels = SEARCH_FILTER_FIELD_LABELS[locale]
    value_labels = SEARCH_FILTER_VALUE_LABELS[locale]
    localized: dict[str, dict[str, Any]] = {}
    for field, definition in config["facet_fields"].items():
        field_value_labels = value_labels.get(field, {})
        localized[field] = {
            **definition,
            "label": field_labels[field],
            "value_labels": {
                str(value): field_value_labels.get(str(value), str(value))
                for value in definition["values"]
                if value is not None
            },
        }
    return localized


def _search_quality_performance() -> dict[str, Any]:
    return _read_json_file(SEARCH_QUALITY_PERFORMANCE)


def _search_integrity_drift() -> dict[str, Any]:
    return _read_json_file(SEARCH_INTEGRITY_DRIFT)


def _is_latin(character: str) -> bool:
    return "LATIN" in unicodedata.name(character, "")


def _strip_latin_diacritics(value: str) -> str:
    stripped: list[str] = []
    last_base_was_latin = False
    for character in unicodedata.normalize("NFKD", value):
        if unicodedata.combining(character):
            if not last_base_was_latin:
                stripped.append(character)
            continue
        stripped.append(character)
        last_base_was_latin = _is_latin(character)
    return unicodedata.normalize("NFC", "".join(stripped))


def _is_cjk(character: str) -> bool:
    codepoint = ord(character)
    return (
        0x3400 <= codepoint <= 0x4DBF
        or 0x4E00 <= codepoint <= 0x9FFF
        or 0xF900 <= codepoint <= 0xFAFF
    )


def _cjk_expansions(token: str) -> list[str]:
    cjk_run = "".join(character for character in token if _is_cjk(character))
    if not cjk_run:
        return []
    expansions = [cjk_run]
    expansions.extend(cjk_run[index : index + 1] for index in range(len(cjk_run)))
    expansions.extend(cjk_run[index : index + 2] for index in range(len(cjk_run) - 1))
    return expansions


def _normalize_search_text(
    locale: str, text: str, config: dict[str, Any] | None = None
) -> list[str]:
    if locale not in LOCALES:
        raise BuildError(f"unsupported search locale: {locale}")
    rules = (config or _search_normalization_aliases())["normalization"]
    normalized = unicodedata.normalize(rules["unicode_form"], text).casefold()
    if rules["strip_diacritics"]:
        normalized = _strip_latin_diacritics(normalized)
    tokens: list[str] = []
    compound_parts: list[str] = []
    for match in SEARCH_TOKEN_PATTERN.finditer(normalized):
        token = match.group(0).strip(".,;!?()[]{}<>\"'")
        if not token:
            continue
        tokens.append(token)
        tokens.extend(_cjk_expansions(token))
        if token.isalnum() and not any(_is_cjk(character) for character in token):
            compound_parts.append(token)
    tokens.extend(
        f"{left}-{right}" for left, right in zip(compound_parts, compound_parts[1:], strict=False)
    )
    return _unique_non_empty(tokens)


def _normalize_search_values(
    locale: str,
    values: list[str],
    config: dict[str, Any],
) -> list[str]:
    tokens: list[str] = []
    for value in values:
        tokens.extend(_normalize_search_text(locale, value, config))
    return _unique_non_empty(tokens)


def _alias_terms_for_locale(alias_group: dict[str, Any], locale: str) -> list[str]:
    return [
        *alias_group["terms"][locale],
        *alias_group.get("technical_identifiers", []),
    ]


def _search_alias_groups_for_document(
    locale: str,
    topic_id: str,
    identifiers: set[str],
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    matched = []
    for alias_group in config["alias_groups"]:
        target_topics = set(alias_group.get("target_topic_ids", []))
        target_ids = set(alias_group.get("target_ids", []))
        technical_identifiers = set(alias_group.get("technical_identifiers", []))
        if topic_id in target_topics or identifiers & (target_ids | technical_identifiers):
            match_sources = []
            if topic_id in target_topics:
                match_sources.append("target_topic")
            if identifiers & target_ids:
                match_sources.append("target_id")
            if identifiers & technical_identifiers:
                match_sources.append("technical_identifier")
            matched.append(
                {
                    "alias_id": alias_group["alias_id"],
                    "match_sources": match_sources,
                    "terms": _alias_terms_for_locale(alias_group, locale),
                }
            )
    return matched


def _resolve_search_query_aliases(
    locale: str,
    query: str,
    config: dict[str, Any] | None = None,
) -> list[str]:
    alias_config = config or _search_normalization_aliases()
    query_tokens = set(_normalize_search_text(locale, query, alias_config))
    matched_aliases: list[str] = []
    for alias_group in alias_config["alias_groups"]:
        for term in _alias_terms_for_locale(alias_group, locale):
            term_tokens = set(_normalize_search_text(locale, term, alias_config))
            if term_tokens and term_tokens <= query_tokens:
                matched_aliases.append(alias_group["alias_id"])
                break
    return sorted(set(matched_aliases))


def _query_fixtures_for_locale(locale: str, config: dict[str, Any]) -> list[dict[str, Any]]:
    return [fixture for fixture in config["query_fixtures"] if fixture["locale"] == locale]


def _ranking_fixtures_for_locale(locale: str, config: dict[str, Any]) -> list[dict[str, Any]]:
    return [fixture for fixture in config["ranking_fixtures"] if fixture["locale"] == locale]


def _max_typo_distance(token: str, ranking_config: dict[str, Any]) -> int:
    tolerance = ranking_config["typo_tolerance"]
    length = len(token)
    if length < tolerance["min_token_length"] or length > tolerance["max_token_length"]:
        return 0
    for rule in tolerance["max_distance_by_length"]:
        if rule["min_length"] <= length <= rule["max_length"]:
            return rule["max_distance"]
    return 0


def _is_typo_excluded(token: str, ranking_config: dict[str, Any]) -> bool:
    return any(
        re.fullmatch(pattern, token, flags=re.IGNORECASE)
        for pattern in ranking_config["typo_tolerance"]["excluded_token_patterns"]
    )


def _bounded_levenshtein(left: str, right: str, limit: int) -> int | None:
    if abs(len(left) - len(right)) > limit:
        return None
    previous = list(range(len(right) + 1))
    for left_index, left_character in enumerate(left, start=1):
        current = [left_index]
        row_min = current[0]
        for right_index, right_character in enumerate(right, start=1):
            substitution = previous[right_index - 1] + (left_character != right_character)
            insertion = current[right_index - 1] + 1
            deletion = previous[right_index] + 1
            value = min(substitution, insertion, deletion)
            current.append(value)
            row_min = min(row_min, value)
        if row_min > limit:
            return None
        previous = current
    distance = previous[-1]
    return distance if distance <= limit else None


def _bounded_typo_matches(
    query_tokens: list[str],
    document: dict[str, Any],
    ranking_config: dict[str, Any],
) -> list[dict[str, Any]]:
    fields = document["normalized"]["fields"]
    exact_pool = {token for field_tokens in fields.values() for token in field_tokens}
    matches: list[dict[str, Any]] = []
    for query_token in query_tokens:
        if query_token in exact_pool or _is_typo_excluded(query_token, ranking_config):
            continue
        limit = _max_typo_distance(query_token, ranking_config)
        if not limit:
            continue
        best: dict[str, Any] | None = None
        for field in ranking_config["typo_tolerance"]["fields"]:
            for candidate in fields.get(field, []):
                if candidate == query_token or _is_typo_excluded(candidate, ranking_config):
                    continue
                distance = _bounded_levenshtein(query_token, candidate, limit)
                if distance is None:
                    continue
                match = {
                    "query_token": query_token,
                    "matched_token": candidate,
                    "field": field,
                    "distance": distance,
                }
                if best is None or (distance, field, candidate) < (
                    best["distance"],
                    best["field"],
                    best["matched_token"],
                ):
                    best = match
        if best is not None:
            matches.append(best)
    return matches


def _score_search_document(
    locale: str,
    query: str,
    document: dict[str, Any],
    alias_config: dict[str, Any] | None = None,
    ranking_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalizer = alias_config or _search_normalization_aliases()
    ranking = ranking_config or _search_ranking_typo()
    weights = ranking["weights"]
    query_tokens = _normalize_search_text(locale, query, normalizer)
    query_token_set = set(query_tokens)
    normalized_fields = document["normalized"]["fields"]
    query_alias_ids = set(_resolve_search_query_aliases(locale, query, normalizer))
    document_alias_ids = set(document["normalized"]["alias_ids"])
    unmatched_technical_identifier = any(
        _is_typo_excluded(token, ranking) and token not in normalized_fields["identifiers"]
        for token in query_tokens
    )
    if unmatched_technical_identifier:
        return {
            "score": 0,
            "score_breakdown": {
                "exact_identifier": 0,
                "title": 0,
                "alias": 0,
                "heading": 0,
                "body": 0,
                "bounded_typo": 0,
                "recency": 0,
            },
            "matched_fields": [],
            "matches": {},
        }

    meaningful_query_tokens = {
        token
        for token in query_token_set
        if len(token) > 1 or not _is_cjk(token)
    }
    exact_identifier_matches = sorted(meaningful_query_tokens & set(normalized_fields["identifiers"]))
    title_matches = sorted(meaningful_query_tokens & set(normalized_fields["title"]))
    alias_token_matches = sorted(meaningful_query_tokens & set(normalized_fields["aliases"]))
    alias_id_matches = sorted(query_alias_ids & document_alias_ids)
    direct_alias_matches = sorted(
        alias_id
        for alias_id in alias_id_matches
        if "target_topic" in document["normalized"].get("alias_match_sources", {}).get(alias_id, [])
    )
    heading_matches = sorted(meaningful_query_tokens & set(normalized_fields["headings"]))
    body_matches = sorted(meaningful_query_tokens & set(normalized_fields["body"]))
    typo_matches = _bounded_typo_matches(query_tokens, document, ranking)

    components = {
        "exact_identifier": len(exact_identifier_matches) * weights["exact_identifier"],
        "title": len(title_matches) * weights["title"],
        "alias": (len(alias_token_matches) + len(alias_id_matches) + len(direct_alias_matches))
        * weights["alias"],
        "heading": len(heading_matches) * weights["heading"],
        "body": len(body_matches) * weights["body"],
        "bounded_typo": len(typo_matches) * weights["bounded_typo"],
        "recency": weights["recency"],
    }
    score = sum(components.values())
    return {
        "score": score,
        "score_breakdown": components,
        "matched_fields": [
            field
            for field in ("exact_identifier", "title", "alias", "heading", "body", "bounded_typo")
            if components[field] > 0
        ],
        "matches": {
            "exact_identifier": exact_identifier_matches,
            "title": title_matches,
            "alias": sorted({*alias_token_matches, *alias_id_matches, *direct_alias_matches}),
            "heading": heading_matches,
            "body": body_matches,
            "bounded_typo": typo_matches,
        },
    }


def _rank_search_documents(
    locale: str,
    query: str,
    documents: list[dict[str, Any]],
    alias_config: dict[str, Any] | None = None,
    ranking_config: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    ranking = ranking_config or _search_ranking_typo()
    scored = []
    for document in documents:
        score = _score_search_document(locale, query, document, alias_config, ranking)
        if score["score"] > 0:
            scored.append({**score, "document": document})
    return sorted(
        scored,
        key=lambda result: (
            -result["score"],
            -result["score_breakdown"]["exact_identifier"],
            -result["score_breakdown"]["title"],
            -result["score_breakdown"]["alias"],
            result["document"]["guide_id"],
            result["document"]["topic_id"],
        ),
    )


def _ranking_fixture_results(
    locale: str,
    documents: list[dict[str, Any]],
    alias_config: dict[str, Any],
    ranking_config: dict[str, Any],
) -> list[dict[str, Any]]:
    results = []
    for fixture in _ranking_fixtures_for_locale(locale, ranking_config):
        ranked = _rank_search_documents(
            locale, fixture["query"], documents, alias_config, ranking_config
        )
        top = ranked[0] if ranked else None
        results.append(
            {
                "fixture_id": fixture["fixture_id"],
                "query": fixture["query"],
                "expected_top_topic_id": fixture["expected_top_topic_id"],
                "top_topic_id": top["document"]["topic_id"] if top else None,
                "score": top["score"] if top else 0,
                "score_breakdown": top["score_breakdown"] if top else {},
                "matched_fields": top["matched_fields"] if top else [],
            }
        )
    return results


def _topic_kind(root: ET.Element) -> str:
    if root.tag in {"concept", "task", "reference"}:
        return root.tag
    if root.tag == "troubleshooting":
        return "troubleshooting"
    raise BuildError(f"unsupported publishable DITA topic type: {root.tag}")


def _topic_anchor_titles(roots: dict[str, ET.Element]) -> dict[str, dict[str, Any]]:
    anchor_ids: set[str] = set()
    titles_by_locale: dict[str, dict[str, str]] = {}
    for locale, root in roots.items():
        titles_by_locale[locale] = {}
        for element in root.iter():
            anchor_id = element.attrib.get("id")
            if not anchor_id or not re.fullmatch(r"a-[a-z0-9]+(?:-[a-z0-9]+)*", anchor_id):
                continue
            title = _element_text(element.find("title"))
            anchor_ids.add(anchor_id)
            titles_by_locale[locale][anchor_id] = title or anchor_id

    anchors = {}
    for anchor_id in sorted(anchor_ids):
        anchors[anchor_id] = {
            "title": {
                locale: titles_by_locale[locale].get(anchor_id, anchor_id) for locale in LOCALES
            },
            "aliases": [],
        }
    return anchors


def _topic_shortdesc(root: ET.Element | None) -> str:
    if root is None:
        return ""
    for child in root:
        if _tag_name(child) == "shortdesc":
            return _element_text(child)
    return ""


def _topic_headings(root: ET.Element | None, root_title: str) -> list[str]:
    if root is None:
        return []
    return _unique_non_empty(
        [
            _element_text(element)
            for element in root.iter()
            if _tag_name(element) == "title" and _element_text(element) != root_title
        ]
    )


def _topic_keywords(root: ET.Element | None) -> list[str]:
    if root is None:
        return []
    return _unique_non_empty(
        [
            _element_text(element)
            for element in root.iter()
            if _tag_name(element) in {"keyword", "indexterm"}
        ]
    )


def _topic_body(root: ET.Element | None, fallback: str) -> str:
    if root is None:
        return fallback
    return _element_text(root)


def _target_identifiers_by_topic(target_map: dict[str, Any]) -> dict[str, dict[str, list[str]]]:
    by_topic: dict[str, dict[str, list[str]]] = {}
    field_by_kind = {
        "policy": "policy_ids",
        "cis": "cis_recommendation_ids",
        "api-operation": "api_operation_ids",
        "capability": "capability_ids",
        "topic": "target_topic_ids",
    }
    for target_id, target in sorted(target_map["targets"].items()):
        topic_id = target["topic_id"]
        kind = target["kind"]
        topic_identifiers = by_topic.setdefault(
            topic_id,
            {
                "target_ids": [],
                "target_topic_ids": [],
                "policy_ids": [],
                "cis_recommendation_ids": [],
                "api_operation_ids": [],
                "capability_ids": [],
            },
        )
        topic_identifiers["target_ids"].append(target_id)
        field = field_by_kind.get(kind)
        if field:
            topic_identifiers[field].append(target["source_id"])
    return {
        topic_id: {field: sorted(set(values)) for field, values in identifiers.items()}
        for topic_id, identifiers in by_topic.items()
    }


def _api_operation_area(operation_id: str) -> str:
    if operation_id.startswith("API-SVC-"):
        return "service"
    if operation_id.startswith("API-HEALTH-"):
        return "health"
    if operation_id.startswith("API-PROFILE-"):
        return "profiles"
    if operation_id.startswith("API-VAL-"):
        return "validation"
    if operation_id.startswith("API-FF-"):
        return "import-export"
    if operation_id.startswith("WEB-"):
        return "ui"
    raise BuildError(f"cannot derive API documentation area from operation ID: {operation_id}")


def _policy_facet_metadata() -> dict[str, dict[str, list[str]]]:
    inventory = _read_json_file(FIREFOX_POLICY_INVENTORY)
    index = _read_json_file(FIREFOX_POLICY_INDEX)
    metadata: dict[str, dict[str, set[str]]] = {}
    for policy in index["policies"]:
        policy_id = policy["policy_id"]
        fields = metadata.setdefault(
            policy_id, {"firefox_channel": set(), "policy_category": set()}
        )
        channel_support = policy.get("channel_support", {})
        fields["firefox_channel"].update(channel_support.get("supported_channels", []))

    for policy in inventory["policies"]:
        policy_id = policy["policy_id"]
        fields = metadata.setdefault(
            policy_id, {"firefox_channel": set(), "policy_category": set()}
        )
        for channel_id, channel in policy.get("channels", {}).items():
            fields["firefox_channel"].add(channel_id)
            ui = channel.get("ui", {})
            if ui.get("section"):
                fields["policy_category"].add(ui["section"])
            fields["policy_category"].update(channel.get("categories", []))

    return {
        policy_id: {field: sorted(values) for field, values in fields.items()}
        for policy_id, fields in metadata.items()
    }


def _cis_facet_metadata() -> dict[str, dict[str, list[str]]]:
    inventory = _read_json_file(CIS_INVENTORY)
    index = _read_json_file(CIS_RECOMMENDATION_INDEX)
    metadata: dict[str, dict[str, set[str]]] = {}
    for topic in index["topics"]:
        recommendation_id = topic["recommendation_id"]
        fields = metadata.setdefault(
            recommendation_id, {"cis_level": set(), "cis_control_state": set()}
        )
        if topic.get("level"):
            fields["cis_level"].add(f"level-{topic['level']}")
        if topic.get("mapping_status"):
            fields["cis_control_state"].add(topic["mapping_status"])

    for record in index.get("provenance_only_records", []):
        recommendation_id = record["recommendation_id"]
        fields = metadata.setdefault(
            recommendation_id, {"cis_level": set(), "cis_control_state": set()}
        )
        if record.get("level"):
            fields["cis_level"].add(f"level-{record['level']}")
        fields["cis_control_state"].add("provenance-only")

    for recommendation in inventory["recommendations"]:
        recommendation_id = recommendation["recommendation_id"]
        fields = metadata.setdefault(
            recommendation_id, {"cis_level": set(), "cis_control_state": set()}
        )
        if recommendation.get("level"):
            fields["cis_level"].add(f"level-{recommendation['level']}")
        if recommendation.get("mapping_status"):
            fields["cis_control_state"].add(recommendation["mapping_status"])
        if recommendation.get("assessment") == "manual":
            fields["cis_control_state"].add("manual-review")

    return {
        recommendation_id: {field: sorted(values) for field, values in fields.items()}
        for recommendation_id, fields in metadata.items()
    }


def _facet_values_from_config(config: dict[str, Any], field: str) -> set[str]:
    return {value for value in config["facet_fields"][field]["values"] if value is not None}


def _target_facets_by_topic(
    target_map: dict[str, Any], config: dict[str, Any]
) -> dict[str, dict[str, list[str]]]:
    policy_metadata = _policy_facet_metadata()
    cis_metadata = _cis_facet_metadata()
    allowed_values = {
        field: _facet_values_from_config(config, field) for field in config["facet_fields"]
    }
    by_topic: dict[str, dict[str, set[str]]] = {}
    for target in target_map["targets"].values():
        topic_id = target["topic_id"]
        fields = by_topic.setdefault(
            topic_id,
            {
                "firefox_channel": set(),
                "policy_category": set(),
                "cis_level": set(),
                "cis_control_state": set(),
                "api_area": set(),
            },
        )
        kind = target["kind"]
        source_id = target["source_id"]
        if kind == "policy":
            policy_fields = policy_metadata.get(source_id, {})
            fields["firefox_channel"].update(policy_fields.get("firefox_channel", []))
            fields["policy_category"].update(policy_fields.get("policy_category", []))
        elif kind == "cis":
            cis_fields = cis_metadata.get(source_id, {})
            fields["cis_level"].update(cis_fields.get("cis_level", []))
            fields["cis_control_state"].update(cis_fields.get("cis_control_state", []))
        elif kind == "api-operation":
            fields["api_area"].add(_api_operation_area(source_id))

    clean: dict[str, dict[str, list[str]]] = {}
    for topic_id, fields in by_topic.items():
        clean[topic_id] = {}
        for field, values in fields.items():
            unknown = values - allowed_values[field]
            if unknown:
                raise BuildError(
                    f"search facet values are not declared for {topic_id}/{field}: {sorted(unknown)}"
                )
            clean[topic_id][field] = sorted(values)
    return clean


def _document_filter_facets(document: dict[str, Any]) -> dict[str, list[str]]:
    filter_facets = document.get("filter_facets", {})
    if isinstance(filter_facets, dict):
        return {
            field: sorted(str(value) for value in values)
            for field, values in filter_facets.items()
            if isinstance(values, list)
        }
    facets = document.get("facets", {})
    values: dict[str, list[str]] = {}
    for field, value in facets.items():
        if value is None:
            values[field] = []
        elif isinstance(value, list):
            values[field] = sorted(str(item) for item in value)
        else:
            values[field] = [str(value)]
    return values


def _facet_counts(
    documents: list[dict[str, Any]], config: dict[str, Any]
) -> dict[str, dict[str, int]]:
    counts = {
        field: {str(value): 0 for value in definition["values"] if value is not None}
        for field, definition in config["facet_fields"].items()
    }
    for document in documents:
        filter_facets = _document_filter_facets(document)
        for field in counts:
            for value in set(filter_facets.get(field, [])):
                if value in counts[field]:
                    counts[field][value] += 1
    return counts


def _filter_search_documents(
    documents: list[dict[str, Any]],
    filters: dict[str, list[str]],
) -> list[dict[str, Any]]:
    active_filters = {field: set(values) for field, values in filters.items() if values}
    if not active_filters:
        return documents
    filtered = []
    for document in documents:
        filter_facets = _document_filter_facets(document)
        if all(
            set(filter_facets.get(field, [])) & values for field, values in active_filters.items()
        ):
            filtered.append(document)
    return filtered


def _filter_url_query(filters: dict[str, list[str]], config: dict[str, Any]) -> str:
    parameters = config["url_state"]["parameters"]
    pairs: list[tuple[str, str]] = []
    for field in sorted(filters):
        parameter = parameters[field]
        for value in sorted(filters[field]):
            pairs.append((parameter, value))
    return urllib.parse.urlencode(pairs)


def _filter_fixture_results(
    locale: str,
    documents: list[dict[str, Any]],
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    results = []
    for fixture in config["filter_fixtures"]:
        if fixture["locale"] != locale:
            continue
        filters = {field: sorted(values) for field, values in fixture["filters"].items()}
        filtered = _filter_search_documents(documents, filters)
        results.append(
            {
                "fixture_id": fixture["fixture_id"],
                "locale": locale,
                "filters": filters,
                "url_query": _filter_url_query(filters, config),
                "result_count": len(filtered),
                "result_topic_ids": [document["topic_id"] for document in filtered],
                "empty_result_message": config["empty_result"]["messages"][locale]
                if not filtered
                else None,
            }
        )
    return results


def _quality_fixtures_for_locale(locale: str, config: dict[str, Any]) -> list[dict[str, Any]]:
    return [fixture for fixture in config["quality_fixtures"] if fixture["locale"] == locale]


def _quality_fixture_results(
    locale: str,
    documents: list[dict[str, Any]],
    alias_config: dict[str, Any],
    ranking_config: dict[str, Any],
    quality_config: dict[str, Any],
) -> list[dict[str, Any]]:
    visible_limit = quality_config["performance_budget"]["max_visible_results_per_query"]
    results = []
    for fixture in _quality_fixtures_for_locale(locale, quality_config):
        filters = {field: sorted(values) for field, values in fixture.get("filters", {}).items()}
        filtered_documents = _filter_search_documents(documents, filters)
        ranked = _rank_search_documents(
            locale,
            fixture["query"],
            filtered_documents,
            alias_config,
            ranking_config,
        )
        visible_ranked = ranked[:visible_limit]
        top = ranked[0] if ranked else None
        required_component = fixture.get("required_score_component")
        results.append(
            {
                "fixture_id": fixture["fixture_id"],
                "locale": locale,
                "category": fixture["category"],
                "query": fixture["query"],
                "filters": filters,
                "expected_top_topic_id": fixture.get("expected_top_topic_id"),
                "top_topic_id": top["document"]["topic_id"] if top else None,
                "expected_count": fixture.get("expected_count"),
                "result_count": len(ranked),
                "visible_result_count": len(visible_ranked),
                "top_topic_ids": [result["document"]["topic_id"] for result in visible_ranked[:5]],
                "required_score_component": required_component,
                "required_score_component_value": top["score_breakdown"].get(required_component, 0)
                if top and required_component
                else 0,
                "top_score": top["score"] if top else 0,
                "top_score_breakdown": top["score_breakdown"] if top else {},
                "matched_fields": top["matched_fields"] if top else [],
            }
        )
    return results


def _quality_performance_report(
    documents: list[dict[str, Any]],
    fixture_results: list[dict[str, Any]],
    quality_config: dict[str, Any],
) -> dict[str, Any]:
    budget = quality_config["performance_budget"]
    return {
        "latency_budget_proxy": budget["latency_budget_proxy"],
        "document_count": len(documents),
        "quality_fixture_count": len(fixture_results),
        "deterministic_scan_units": len(documents) * len(fixture_results),
        "max_visible_results_per_query": budget["max_visible_results_per_query"],
        "max_observed_visible_results": max(
            (result["visible_result_count"] for result in fixture_results),
            default=0,
        ),
        "budget": budget,
    }


def _validate_quality_fixture_coverage(config: dict[str, Any]) -> None:
    coverage = config["coverage_requirements"]
    if coverage["locales"] != list(LOCALES):
        raise BuildError("search quality fixture locale matrix mismatch")
    categories = set(coverage["categories"])
    fixture_categories = {fixture["category"] for fixture in config["quality_fixtures"]}
    if not categories <= fixture_categories:
        raise BuildError("search quality fixture categories are incomplete")
    common_categories = categories - {"cjk"}
    cjk_required_locales = set(coverage["cjk_required_locales"])
    for locale in LOCALES:
        locale_categories = {
            fixture["category"]
            for fixture in config["quality_fixtures"]
            if fixture["locale"] == locale
        }
        if (
            len(_quality_fixtures_for_locale(locale, config))
            < coverage["minimum_locale_fixture_count"]
        ):
            raise BuildError(f"search quality fixture count is too low for {locale}")
        if not common_categories <= locale_categories:
            raise BuildError(f"search quality fixture categories are incomplete for {locale}")
        if locale in cjk_required_locales and "cjk" not in locale_categories:
            raise BuildError(f"search quality CJK fixture is missing for {locale}")


def _duplicates(values: list[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return sorted(duplicates)


def _contains_control_character(value: str) -> bool:
    return any(ord(character) < 32 and character not in "\n\r\t" for character in value)


def _snippet_source(document: dict[str, Any], config: dict[str, Any]) -> str:
    searchable = document.get("searchable", {})
    for field in config["snippet_integrity"]["source_fields"]:
        value = searchable.get(field, "")
        if isinstance(value, list):
            value = " ".join(str(item) for item in value)
        value = str(value)
        if value.strip():
            return value
    return ""


def _inventory_gap_report(
    expected_source_ids: set[str],
    target_source_ids: set[str],
) -> dict[str, Any]:
    return {
        "inventory_count": len(expected_source_ids),
        "target_count": len(target_source_ids),
        "missing_source_ids": sorted(expected_source_ids - target_source_ids),
        "extra_source_ids": sorted(target_source_ids - expected_source_ids),
    }


def _search_integrity_report(
    locale: str,
    documents: list[dict[str, Any]],
    topics: dict[str, dict[str, Any]],
    target_map: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    topic_ids = set(topics)
    document_topic_ids = {str(document.get("topic_id", "")) for document in documents}
    document_ids = [str(document.get("document_id", "")) for document in documents]

    wrong_locale_document_ids: list[str] = []
    wrong_url_document_ids: list[str] = []
    wrong_output_document_ids: list[str] = []
    broken_snippet_document_ids: list[str] = []
    control_character_document_ids: list[str] = []
    for document in documents:
        document_id = str(document.get("document_id", ""))
        topic_id = document.get("topic_id")
        topic = topics.get(str(topic_id), {})
        expected_output = topic.get("output", {}).get(locale)
        if document.get("locale") != locale:
            wrong_locale_document_ids.append(document_id)
        if not str(document.get("url", "")).startswith(f"/help/{locale}/"):
            wrong_url_document_ids.append(document_id)
        if expected_output and document.get("source", {}).get("output_path") != expected_output:
            wrong_output_document_ids.append(document_id)
        snippet_source = _snippet_source(document, config)
        if not snippet_source:
            broken_snippet_document_ids.append(document_id)
        searchable_values = [
            value
            for value in document.get("searchable", {}).values()
            for value in (value if isinstance(value, list) else [value])
        ]
        if any(
            _contains_control_character(str(value))
            for value in [snippet_source, *searchable_values]
        ):
            control_character_document_ids.append(document_id)

    stale_target_anchors = []
    target_topic_mismatches = []
    for target_id, target in sorted(target_map["targets"].items()):
        topic_id = target["topic_id"]
        topic = topics.get(topic_id)
        if topic is None:
            target_topic_mismatches.append(target_id)
            continue
        anchor_id = target.get("anchor_id")
        if anchor_id and anchor_id not in topic["anchors"]:
            stale_target_anchors.append(
                {
                    "target_id": target_id,
                    "topic_id": topic_id,
                    "anchor_id": anchor_id,
                }
            )

    source_ids_by_kind: dict[str, set[str]] = {
        "policy": set(),
        "cis": set(),
        "api-operation": set(),
    }
    for target in target_map["targets"].values():
        kind = target["kind"]
        if kind in source_ids_by_kind:
            source_ids_by_kind[kind].add(target["source_id"])

    inventory_gap_integrity = {
        "firefox_policy": _inventory_gap_report(_policy_ids(), source_ids_by_kind["policy"]),
        "cis": _inventory_gap_report(_cis_recommendation_ids(), source_ids_by_kind["cis"]),
        "api": _inventory_gap_report(
            set(_api_operation_topic_ids()), source_ids_by_kind["api-operation"]
        ),
    }

    document_integrity = {
        "missing_topic_ids": sorted(topic_ids - document_topic_ids),
        "extra_topic_ids": sorted(document_topic_ids - topic_ids),
        "duplicate_document_ids": _duplicates(document_ids),
        "wrong_locale_document_ids": sorted(wrong_locale_document_ids),
        "wrong_url_document_ids": sorted(wrong_url_document_ids),
        "wrong_output_document_ids": sorted(wrong_output_document_ids),
    }
    anchor_integrity = {
        "stale_target_anchors": stale_target_anchors,
        "target_topic_mismatches": sorted(target_topic_mismatches),
    }
    snippet_integrity = {
        "broken_snippet_document_ids": sorted(broken_snippet_document_ids),
        "control_character_document_ids": sorted(control_character_document_ids),
        "max_snippet_characters": config["snippet_integrity"]["max_characters"],
        "source_fields": config["snippet_integrity"]["source_fields"],
    }

    failure_count = (
        sum(len(values) for values in document_integrity.values())
        + len(anchor_integrity["stale_target_anchors"])
        + len(anchor_integrity["target_topic_mismatches"])
        + len(snippet_integrity["broken_snippet_document_ids"])
        + len(snippet_integrity["control_character_document_ids"])
        + sum(
            len(report["missing_source_ids"]) + len(report["extra_source_ids"])
            for report in inventory_gap_integrity.values()
        )
    )

    return {
        "schema_version": config["schema_version"],
        "contract_id": config["contract_id"],
        "locale": locale,
        "status": "pass" if failure_count == 0 else "fail",
        "failure_count": failure_count,
        "check_categories": config["check_categories"],
        "counts": {
            "manifest_topics": len(topics),
            "search_documents": len(documents),
            "target_map_targets": len(target_map["targets"]),
            "firefox_policy_inventory": len(_policy_ids()),
            "cis_inventory": len(_cis_recommendation_ids()),
            "api_inventory": len(_api_operation_topic_ids()),
        },
        "document_integrity": document_integrity,
        "anchor_integrity": anchor_integrity,
        "snippet_integrity": snippet_integrity,
        "inventory_gap_integrity": inventory_gap_integrity,
    }


def _topic_search_document(
    locale: str,
    topic_id: str,
    topic: dict[str, Any],
    identifiers_by_topic: dict[str, dict[str, list[str]]],
    facets_by_topic: dict[str, dict[str, list[str]]],
    source_revision: str,
    alias_config: dict[str, Any],
    product_version: str,
) -> dict[str, Any]:
    root = topic.get("_roots", {}).get(locale)
    title = topic["title"][locale]
    output_path = topic["output"][locale]
    identifier_groups = identifiers_by_topic.get(topic_id, {})
    anchor_ids = sorted(topic["anchors"])
    identifiers = sorted(
        {
            topic_id,
            topic["guide_id"],
            topic["dita_key"],
            *anchor_ids,
            *identifier_groups.get("target_ids", []),
            *identifier_groups.get("target_topic_ids", []),
            *identifier_groups.get("policy_ids", []),
            *identifier_groups.get("cis_recommendation_ids", []),
            *identifier_groups.get("api_operation_ids", []),
            *identifier_groups.get("capability_ids", []),
        }
    )
    identifier_set = set(identifiers)
    document_alias_groups = _search_alias_groups_for_document(
        locale,
        topic_id,
        identifier_set,
        alias_config,
    )
    aliases = sorted(
        {alias for anchor in topic["anchors"].values() for alias in anchor.get("aliases", [])}
        | {alias for alias_group in document_alias_groups for alias in alias_group["terms"]}
    )
    searchable = {
        "title": title,
        "shortdesc": _topic_shortdesc(root),
        "headings": _topic_headings(root, title)
        or [topic["anchors"][anchor_id]["title"][locale] for anchor_id in anchor_ids],
        "body": _topic_body(root, title),
        "keywords": _topic_keywords(root),
        "identifiers": identifiers,
        "aliases": aliases,
    }
    normalized_fields = {
        field: _normalize_search_values(
            locale,
            value if isinstance(value, list) else [value],
            alias_config,
        )
        for field, value in searchable.items()
    }
    target_facets = facets_by_topic.get(topic_id, {})
    filter_facets = {
        "locale": [locale],
        "guide_id": [topic["guide_id"]],
        "topic_kind": [topic["kind"]],
        "firefox_channel": target_facets.get("firefox_channel", []),
        "policy_category": target_facets.get("policy_category", []),
        "cis_level": target_facets.get("cis_level", []),
        "cis_control_state": target_facets.get("cis_control_state", []),
        "api_area": target_facets.get("api_area", []),
        "bpm_version": [product_version],
    }
    return {
        "document_id": f"{locale}:{topic_id}",
        "locale": locale,
        "guide_id": topic["guide_id"],
        "topic_id": topic_id,
        "topic_kind": topic["kind"],
        "url": f"/help/{output_path}",
        "source": {
            "topic_id": topic_id,
            "anchor_id": None,
            "dita_key": topic["dita_key"],
            "source_slug": topic["source_slug"],
            "output_path": output_path,
        },
        "searchable": searchable,
        "normalized": {
            "alias_ids": sorted({group["alias_id"] for group in document_alias_groups}),
            "alias_match_sources": {
                group["alias_id"]: group["match_sources"] for group in document_alias_groups
            },
            "fields": normalized_fields,
        },
        "identifier_groups": identifier_groups,
        "facets": {
            "locale": locale,
            "guide_id": topic["guide_id"],
            "topic_kind": topic["kind"],
            "firefox_channel": filter_facets["firefox_channel"] or None,
            "policy_category": filter_facets["policy_category"] or None,
            "cis_level": filter_facets["cis_level"] or None,
            "cis_control_state": filter_facets["cis_control_state"] or None,
            "api_area": filter_facets["api_area"] or None,
            "bpm_version": product_version,
        },
        "filter_facets": filter_facets,
        "versions": {
            "bpm_version": product_version,
            "documentation_version": product_version,
            "source_revision": source_revision,
        },
    }


def _search_document(
    locale: str,
    topics: dict[str, dict[str, Any]],
    target_map: dict[str, Any],
) -> dict[str, Any]:
    contract = _read_json_file(SEARCH_CORPUS_CONTRACT)
    alias_config = _search_normalization_aliases()
    ranking_config = _search_ranking_typo()
    facets_config = _search_facets_filters()
    domain_ranking_config = _search_domain_ranking_facets()
    quality_config = _search_quality_performance()
    integrity_config = _search_integrity_drift()
    _validate_quality_fixture_coverage(quality_config)
    identifiers_by_topic = _target_identifiers_by_topic(target_map)
    facets_by_topic = _target_facets_by_topic(target_map, facets_config)
    source_revision = _source_revision()
    product_version = _product_version()
    documents = [
        _topic_search_document(
            locale,
            topic_id,
            topic,
            identifiers_by_topic,
            facets_by_topic,
            source_revision,
            alias_config,
            product_version,
        )
        for topic_id, topic in sorted(topics.items())
    ]
    locale_fixtures = _query_fixtures_for_locale(locale, alias_config)
    ranking_fixture_results = _ranking_fixture_results(
        locale,
        documents,
        alias_config,
        ranking_config,
    )
    filter_fixture_results = _filter_fixture_results(locale, documents, facets_config)
    quality_fixture_results = _quality_fixture_results(
        locale,
        documents,
        alias_config,
        ranking_config,
        quality_config,
    )
    integrity_report = _search_integrity_report(
        locale,
        documents,
        topics,
        target_map,
        integrity_config,
    )
    return {
        "schema_version": 1,
        "contract_id": contract["contract_id"],
        "contract_schema_version": contract["schema_version"],
        "normalization_contract_id": alias_config["contract_id"],
        "normalization_schema_version": alias_config["schema_version"],
        "ranking_contract_id": ranking_config["contract_id"],
        "ranking_schema_version": ranking_config["schema_version"],
        "facets_contract_id": facets_config["contract_id"],
        "facets_schema_version": facets_config["schema_version"],
        "domain_ranking_contract_id": domain_ranking_config["contract_id"],
        "domain_ranking_schema_version": domain_ranking_config["schema_version"],
        "quality_contract_id": quality_config["contract_id"],
        "quality_schema_version": quality_config["schema_version"],
        "integrity_contract_id": integrity_config["contract_id"],
        "integrity_schema_version": integrity_config["schema_version"],
        "result_schema_version": contract["result_schema"]["schema_version"],
        "target_bpm_version": product_version,
        "locale": locale,
        "format_version": 1,
        "generated_by": "documentation/tools/build_docs.py",
        "status": "ready",
        "index_kind": "dita-document-corpus-v1",
        "search_mode": contract["search_mode"],
        "non_ai_boundary": contract["non_ai_boundary"]["mode"],
        "allowlisted_cross_locale_fields": ["identifiers"],
        "normalization": {
            **alias_config["normalization"],
            "alias_groups": [
                {
                    "alias_id": alias_group["alias_id"],
                    "terms": _alias_terms_for_locale(alias_group, locale),
                }
                for alias_group in alias_config["alias_groups"]
            ],
            "alias_group_count": len(alias_config["alias_groups"]),
            "query_fixture_count": len(locale_fixtures),
        },
        "ranking": {
            "ranking_order": ranking_config["ranking_order"],
            "weights": ranking_config["weights"],
            "typo_tolerance": ranking_config["typo_tolerance"],
            "tie_breakers": ranking_config["tie_breakers"],
            "ranking_fixture_count": len(_ranking_fixtures_for_locale(locale, ranking_config)),
        },
        "filtering": {
            "facet_fields": _localized_search_facet_fields(locale, facets_config),
            "composition": facets_config["filter_contract"]["composition"],
            "url_state": facets_config["url_state"],
            "empty_result": facets_config["empty_result"]["messages"][locale],
            "filter_fixture_count": len(
                [
                    fixture
                    for fixture in facets_config["filter_fixtures"]
                    if fixture["locale"] == locale
                ]
            ),
        },
        "domain_ranking": {
            "preserved_sources": domain_ranking_config["ranking"]["preserved_sources"],
            "evidence_fields": domain_ranking_config["ranking"]["evidence_fields"],
            "preserved_facets": domain_ranking_config["facets"]["preserved_fields"],
            "maximum_evidence_rows": domain_ranking_config["adapter_projection"][
                "maximum_evidence_rows"
            ],
        },
        "quality": {
            "categories": quality_config["coverage_requirements"]["categories"],
            "fixture_count": len(_quality_fixtures_for_locale(locale, quality_config)),
            "thresholds": quality_config["quality_thresholds"],
        },
        "performance_report": _quality_performance_report(
            documents,
            quality_fixture_results,
            quality_config,
        ),
        "integrity_report": integrity_report,
        "facet_counts": _facet_counts(documents, facets_config),
        "query_fixtures": locale_fixtures,
        "ranking_fixture_results": ranking_fixture_results,
        "filter_fixture_results": filter_fixture_results,
        "quality_fixture_results": quality_fixture_results,
        "document_required_fields": contract["document_schema"]["required_fields"],
        "searchable_fields": [field["field"] for field in contract["corpus"]["searchable_fields"]],
        "result_required_fields": contract["result_schema"]["required_fields"],
        "documents": documents,
    }


def _policy_ids() -> set[str]:
    index = _read_json_file(FIREFOX_POLICY_INDEX)
    return {policy["policy_id"] for policy in index["policies"]}


def _managed_preference_ids() -> set[str]:
    inventory = _read_json_file(FIREFOX_POLICY_INVENTORY)
    return {preference["preference_id"] for preference in inventory["managed_preferences"]}


def _all_settings_help_target_contract() -> dict[str, Any]:
    contract = _read_json_file(ALL_SETTINGS_HELP_TARGET_MAP)
    if contract.get("schema_version") != 1:
        raise BuildError("unsupported All Settings help target map contract schema")
    if contract.get("target_bpm_version") != "0.9.1":
        raise BuildError("All Settings help target map contract has the wrong BPM version")
    return contract


def _validate_all_settings_help_target_coverage(targets: dict[str, dict[str, Any]]) -> None:
    expected_policy_targets = {f"policy:{policy_id}" for policy_id in _policy_ids()}
    expected_preference_targets = {
        f"known-preference:{preference_id}" for preference_id in _managed_preference_ids()
    }
    actual_policy_targets = {target_id for target_id in targets if target_id.startswith("policy:")}
    actual_preference_targets = {
        target_id for target_id in targets if target_id.startswith("known-preference:")
    }
    for kind, expected, actual in (
        ("policy", expected_policy_targets, actual_policy_targets),
        ("known preference", expected_preference_targets, actual_preference_targets),
    ):
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        if missing:
            raise BuildError(f"All Settings help target map is missing {kind} targets: {missing}")
        if extra:
            raise BuildError(f"All Settings help target map has unknown {kind} targets: {extra}")


def _cis_recommendation_ids() -> set[str]:
    index = _read_json_file(CIS_RECOMMENDATION_INDEX)
    topic_ids = {topic["recommendation_id"] for topic in index["topics"]}
    provenance_only_ids = {
        record["recommendation_id"] for record in index["provenance_only_records"]
    }
    return topic_ids | provenance_only_ids


def _api_operation_topic_ids() -> dict[str, str]:
    text = API_INVENTORY.read_text(encoding="utf-8")
    operations: dict[str, str] = {}
    for line in text.splitlines():
        if not line.startswith("| `API-"):
            continue
        parts = [part.strip() for part in line.strip("|").split("|")]
        if len(parts) >= 8:
            operations[parts[0].strip("`")] = parts[7].strip("`")
    return operations


def _capability_topic_ids() -> dict[str, str]:
    text = CAPABILITY_INVENTORY.read_text(encoding="utf-8")
    capabilities: dict[str, str] = {}
    for line in text.splitlines():
        if not line.startswith("| `CAP-"):
            continue
        parts = [part.strip() for part in line.strip("|").split("|")]
        if len(parts) >= 5:
            capabilities[parts[0].strip("`")] = parts[3].strip("`")
    return capabilities


def _policy_context_assignments(context: dict[str, Any] | None = None) -> dict[str, dict[str, Any]]:
    context = context or _read_json_file(FIREFOX_POLICY_CONTEXT_TARGETS)
    if context.get("schema_version") != 1:
        raise BuildError("unsupported Firefox policy context target schema")
    known_policy_ids = _policy_ids()
    known_api_operation_ids = set(_api_operation_topic_ids())
    known_capability_topics = set(_capability_topic_ids().values())
    assignments: dict[str, dict[str, Any]] = {}
    context_targets = [context["default_policy_target"], *context["family_targets"]]
    for target in context_targets:
        if target["topic_id"] not in known_capability_topics and not target["topic_id"].startswith(
            "fx-"
        ):
            raise BuildError(f"policy context references unknown user topic: {target['topic_id']}")
        validation_topic_id = target.get("validation_topic_id")
        if validation_topic_id and validation_topic_id not in known_capability_topics:
            raise BuildError(
                f"policy context references unknown validation topic: {validation_topic_id}"
            )
        for task_topic_id in target.get("user_task_topic_ids", []):
            if task_topic_id not in known_capability_topics:
                raise BuildError(
                    f"policy context references unknown user task topic: {task_topic_id}"
                )
        for operation_id in target.get("api_operation_ids", []):
            if operation_id not in known_api_operation_ids:
                raise BuildError(f"policy context references unknown API operation: {operation_id}")

    for family in context["family_targets"]:
        family_policy_ids = family.get("policy_ids", [])
        if not family_policy_ids:
            raise BuildError(f"policy context family has no policy IDs: {family.get('family_id')}")
        for policy_id in family_policy_ids:
            if policy_id not in known_policy_ids:
                raise BuildError(f"policy context references unknown policy: {policy_id}")
            if policy_id in assignments:
                raise BuildError(f"policy context assigns policy more than once: {policy_id}")
            assignments[policy_id] = family
        for related_policy_id in family.get("related_policy_ids", []):
            if related_policy_id not in known_policy_ids:
                raise BuildError(
                    f"policy context references unknown related policy: {related_policy_id}"
                )
    return assignments


def _target(
    topic_id: str, kind: str, source_id: str, source_inventory: str, anchor_id: str | None = None
) -> dict[str, Any]:
    target = {
        "kind": kind,
        "source_id": source_id,
        "source_inventory": source_inventory,
        "topic_id": topic_id,
    }
    if anchor_id:
        target["anchor_id"] = anchor_id
    return target


def _build_target_map(topics: dict[str, dict[str, Any]]) -> dict[str, Any]:
    targets = {}
    policy_context = _read_json_file(FIREFOX_POLICY_CONTEXT_TARGETS)
    help_target_contract = _all_settings_help_target_contract()
    policy_assignments = _policy_context_assignments(policy_context)
    default_policy_target = policy_context["default_policy_target"]

    for topic_id in sorted(topics):
        targets[f"topic:{topic_id}"] = _target(
            topic_id,
            "topic",
            topic_id,
            "documentation/src/dita",
        )

    for guide_id, filename, anchor, _url_root in GUIDE_MAPS:
        topic_id = _guide_topic_id(guide_id)
        if topic_id not in topics:
            raise BuildError(f"cannot create target for missing guide topic: {topic_id}")
        targets[f"topic:{topic_id}"] = _target(
            topic_id,
            "topic",
            topic_id,
            _guide_source_inventory(filename),
            anchor,
        )

    for policy_id in sorted(_policy_ids()):
        assignment = policy_assignments.get(policy_id, default_policy_target)
        targets[f"policy:{policy_id}"] = _target(
            assignment["topic_id"],
            "policy",
            policy_id,
            "documentation/config/firefox-policy-context-targets-0.9.0.json",
            assignment["anchor_id"],
        )

    preference_target = help_target_contract["known_preference_targets"]
    for preference_id in sorted(_managed_preference_ids()):
        targets[f"known-preference:{preference_id}"] = _target(
            preference_target["topic_id"],
            "known-preference",
            preference_id,
            help_target_contract["source_inventory"],
            preference_target["anchor_id"],
        )

    for recommendation_id in sorted(_cis_recommendation_ids()):
        targets[f"cis:{recommendation_id}"] = _target(
            "cis-settings-guide",
            "cis",
            recommendation_id,
            "docs/architecture/cis-documentation-inventory-0.9.0.json",
            "a-cis-settings-guide",
        )

    for operation_id, planned_topic_id in sorted(_api_operation_topic_ids().items()):
        if planned_topic_id not in topics:
            raise BuildError(
                "API operation target is missing its Administrator Guide topic: "
                f"{operation_id} -> {planned_topic_id}"
            )
        targets[f"api-operation:{operation_id}"] = _target(
            planned_topic_id,
            "api-operation",
            operation_id,
            "docs/architecture/api-documentation-inventory-0.9.0.md",
        )

    for capability_id, topic_id in sorted(_capability_topic_ids().items()):
        targets[f"capability:{capability_id}"] = _target(
            topic_id,
            "capability",
            capability_id,
            "docs/architecture/product-user-capability-inventory-0.9.0.md",
        )

    _validate_all_settings_help_target_coverage(targets)
    return {
        "$schema": "schemas/product-documentation-ui-target-map-v1.schema.json",
        "schema_version": 1,
        "manifest_schema_version": 1,
        "bpm_version": _product_version(),
        "locales": list(LOCALES),
        "targets": targets,
    }


def _build_topics(site_root: Path) -> dict[str, dict[str, Any]]:
    topics: dict[str, dict[str, Any]] = {}
    hrefs_by_locale = {locale: _localized_map_keydefs(locale) for locale in LOCALES}
    for guide_id, filename, anchor, url_root in GUIDE_MAPS:
        title = _guide_titles(filename)
        topic_id = _guide_topic_id(guide_id)
        output = {}
        for locale in LOCALES:
            page = site_root / locale / "index.html"
            if not page.is_file():
                raise BuildError(f"missing guide landing output for {locale}: {page}")
            output[locale] = page.relative_to(site_root).as_posix()
        topics[topic_id] = {
            "guide_id": guide_id,
            "dita_key": f"topic.{topic_id}",
            "source_slug": guide_id,
            "url_path": "home",
            "kind": "landing",
            "title": title,
            "anchors": {
                anchor: {
                    "title": title,
                    "aliases": [],
                }
            },
            "output": output,
            "_url_root": url_root,
        }

        keyrefs = _guide_topic_keyrefs("en", filename)
        for keyref in keyrefs:
            if not keyref.startswith("topic."):
                raise BuildError(f"guide map uses unsupported topic key: {keyref}")
            child_topic_id = keyref.removeprefix("topic.")
            if child_topic_id in topics:
                raise BuildError(f"topic is present in more than one guide map: {child_topic_id}")
            roots = _localized_topic_roots(keyref, hrefs_by_locale)
            child_output = {}
            for locale in LOCALES:
                topic_path = hrefs_by_locale[locale][keyref]
                output_path = site_root / locale / topic_path.parent.name / f"{child_topic_id}.html"
                if not output_path.is_file():
                    raise BuildError(
                        f"missing topic output for {locale}/{child_topic_id}: {output_path}"
                    )
                child_output[locale] = output_path.relative_to(site_root).as_posix()
            topics[child_topic_id] = {
                "guide_id": guide_id,
                "dita_key": keyref,
                "source_slug": child_topic_id,
                "url_path": child_topic_id,
                "kind": _topic_kind(roots["en"]),
                "title": {
                    locale: _element_text(root.find("title")) for locale, root in roots.items()
                },
                "anchors": _topic_anchor_titles(roots),
                "output": child_output,
                "_url_root": url_root,
                "_roots": roots,
                "_source_paths": {locale: hrefs_by_locale[locale][keyref] for locale in LOCALES},
            }
    return topics


def _build_guides(topics: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    guides = {}
    for guide_id, filename, _anchor, url_root in GUIDE_MAPS:
        topic_id = _guide_topic_id(guide_id)
        if topic_id not in topics:
            raise BuildError(f"guide home topic is missing: {topic_id}")
        guides[guide_id] = {
            "url_root": url_root,
            "home_topic_id": topic_id,
            "title": _guide_titles(filename),
        }
    return guides


def _manifest_build_id(site_root: Path) -> str:
    excluded = {"manifest.json", "artifact-integrity.json"}
    digest = hashlib.sha256()
    for path in sorted(path for path in site_root.rglob("*") if path.is_file()):
        relative = path.relative_to(site_root).as_posix()
        if relative in excluded:
            continue
        digest.update(relative.encode())
        digest.update(b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def generate_manifest_files(site_root: Path) -> None:
    topics_with_private = _build_topics(site_root)
    topics = {
        topic_id: {key: value for key, value in topic.items() if not key.startswith("_")}
        for topic_id, topic in topics_with_private.items()
    }
    target_map = _build_target_map(topics)
    _validate_schema(target_map, UI_TARGET_SCHEMA)
    _write_json(site_root / "ui-target-map.json", target_map)

    navigation = {}
    for locale in LOCALES:
        navigation_path = site_root / locale / "navigation.json"
        if not navigation_path.is_file():
            raise BuildError(f"generated navigation source is missing for {locale}")
        navigation_payload = json.loads(navigation_path.read_text(encoding="utf-8"))
        _validate_schema(navigation_payload, NAVIGATION_SCHEMA)
        if navigation_payload != _navigation_payload(site_root, locale):
            raise BuildError(
                f"generated navigation source diverges from manifest topics for {locale}"
            )
        navigation[locale] = {
            "path": navigation_path.relative_to(site_root).as_posix(),
            "sha256": _file_sha256(navigation_path),
            "format_version": 1,
            "node_count": navigation_payload["node_count"],
        }

    search = {}
    for locale in LOCALES:
        search_payload = _search_document(locale, topics_with_private, target_map)
        search_path = site_root / "search" / locale / "index.json"
        _write_json(search_path, search_payload)
        search[locale] = {
            "path": search_path.relative_to(site_root).as_posix(),
            "sha256": _file_sha256(search_path),
            "format_version": 1,
            "document_count": len(search_payload["documents"]),
        }

    manifest = {
        "$schema": "schemas/product-documentation-manifest-v1.schema.json",
        "schema_version": 1,
        "artifact": {
            "bpm_version": _product_version(),
            "documentation_version": _product_version(),
            "build_id": _manifest_build_id(site_root),
            "source_revision": _source_revision(),
            "dita_ot_version": _load_lock()["components"]["dita_ot"]["version"],
        },
        "locales": list(LOCALES),
        "default_locale": "en",
        "guides": _build_guides(topics),
        "topics": topics,
        "assets": {},
        "navigation": navigation,
        "search": search,
        "aliases": {},
        "tombstones": {},
        "ui_target_map": {
            "path": "ui-target-map.json",
            "sha256": _file_sha256(site_root / "ui-target-map.json"),
            "schema_version": 1,
        },
    }
    _validate_schema(manifest, MANIFEST_SCHEMA)
    _write_json(site_root / "manifest.json", manifest)
    validate_manifest_files(site_root)


def _read_json_bytes(payload: bytes, name: str) -> dict[str, Any]:
    try:
        return json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BuildError(f"cannot parse generated JSON {name}: {exc}") from exc


def _safe_artifact_path(root: Path, relative: str) -> Path:
    parsed = urllib.parse.urlsplit(relative)
    if parsed.scheme or parsed.netloc or relative.startswith("/") or "\\" in relative:
        raise BuildError(f"artifact path is not relative and local: {relative}")
    candidate = (root / urllib.parse.unquote(parsed.path)).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise BuildError(f"artifact path escapes root: {relative}") from exc
    return candidate


def _validate_target_map_semantics(target_map: dict[str, Any], manifest: dict[str, Any]) -> None:
    topics = manifest["topics"]
    policy_ids = _policy_ids()
    preference_ids = _managed_preference_ids()
    cis_recommendation_ids = _cis_recommendation_ids()
    api_operation_ids = set(_api_operation_topic_ids())
    capability_ids = set(_capability_topic_ids())
    for target_id, target in target_map["targets"].items():
        expected_key = f"{target['kind']}:{target['source_id']}"
        if target_id != expected_key:
            raise BuildError(f"target key does not match kind/source_id: {target_id}")
        source_id = target["source_id"]
        if target["kind"] == "topic" and source_id not in topics:
            raise BuildError(f"target references unknown topic source: {target_id}")
        if target["kind"] == "policy" and source_id not in policy_ids:
            raise BuildError(f"target references unknown policy source: {target_id}")
        if target["kind"] == "known-preference" and source_id not in preference_ids:
            raise BuildError(f"target references unknown known-preference source: {target_id}")
        if target["kind"] == "cis" and source_id not in cis_recommendation_ids:
            raise BuildError(f"target references unknown CIS recommendation source: {target_id}")
        if target["kind"] == "api-operation" and source_id not in api_operation_ids:
            raise BuildError(f"target references unknown API operation source: {target_id}")
        if target["kind"] == "capability" and source_id not in capability_ids:
            raise BuildError(f"target references unknown capability source: {target_id}")
        topic_id = target["topic_id"]
        if topic_id not in topics:
            raise BuildError(f"target references unknown topic: {target_id}")
        anchor_id = target.get("anchor_id")
        if anchor_id and anchor_id not in topics[topic_id]["anchors"]:
            raise BuildError(f"target references unknown anchor: {target_id} -> {anchor_id}")


def _validate_manifest_semantics(manifest: dict[str, Any], target_map: dict[str, Any]) -> None:
    if manifest["locales"] != list(LOCALES) or target_map["locales"] != list(LOCALES):
        raise BuildError("manifest and target map must use the exact locale matrix")
    if target_map["manifest_schema_version"] != manifest["schema_version"]:
        raise BuildError("target map schema version does not match manifest schema version")
    topics = manifest["topics"]
    for guide_id, guide in manifest["guides"].items():
        home_topic_id = guide["home_topic_id"]
        if home_topic_id not in topics:
            raise BuildError(f"guide {guide_id} references missing home topic {home_topic_id}")
        if topics[home_topic_id]["guide_id"] != guide_id:
            raise BuildError(f"guide {guide_id} home topic is owned by another guide")
    seen_paths: set[str] = set()
    seen_slugs: set[str] = set()
    for topic_id, topic in topics.items():
        if topic["dita_key"] != f"topic.{topic_id}":
            raise BuildError(f"topic {topic_id} has inconsistent DITA key")
        slug_key = topic["source_slug"].casefold()
        if slug_key in seen_slugs:
            raise BuildError(
                f"duplicate topic source slug after case-folding: {topic['source_slug']}"
            )
        seen_slugs.add(slug_key)
        guide_root = manifest["guides"][topic["guide_id"]]["url_root"]
        public_path = f"{guide_root}/{topic['url_path']}".casefold()
        if public_path in seen_paths:
            raise BuildError(f"duplicate topic public path: {public_path}")
        seen_paths.add(public_path)
        for locale in LOCALES:
            if locale not in topic["title"] or locale not in topic["output"]:
                raise BuildError(f"topic {topic_id} lacks locale data for {locale}")
    _validate_target_map_semantics(target_map, manifest)


def _validate_search_index_semantics(
    locale: str,
    search_payload: dict[str, Any],
    manifest: dict[str, Any],
    target_map: dict[str, Any],
) -> None:
    contract = _read_json_file(SEARCH_CORPUS_CONTRACT)
    alias_config = _search_normalization_aliases()
    ranking_config = _search_ranking_typo()
    facets_config = _search_facets_filters()
    domain_ranking_config = _search_domain_ranking_facets()
    quality_config = _search_quality_performance()
    integrity_config = _search_integrity_drift()
    _validate_quality_fixture_coverage(quality_config)
    if search_payload.get("contract_id") != contract["contract_id"]:
        raise BuildError(f"search index contract mismatch for {locale}")
    if search_payload.get("normalization_contract_id") != alias_config["contract_id"]:
        raise BuildError(f"search index normalization contract mismatch for {locale}")
    if search_payload.get("normalization_schema_version") != alias_config["schema_version"]:
        raise BuildError(f"search index normalization schema mismatch for {locale}")
    if search_payload.get("ranking_contract_id") != ranking_config["contract_id"]:
        raise BuildError(f"search index ranking contract mismatch for {locale}")
    if search_payload.get("ranking_schema_version") != ranking_config["schema_version"]:
        raise BuildError(f"search index ranking schema mismatch for {locale}")
    if search_payload.get("facets_contract_id") != facets_config["contract_id"]:
        raise BuildError(f"search index facets contract mismatch for {locale}")
    if search_payload.get("facets_schema_version") != facets_config["schema_version"]:
        raise BuildError(f"search index facets schema mismatch for {locale}")
    if search_payload.get("domain_ranking_contract_id") != domain_ranking_config["contract_id"]:
        raise BuildError(f"search index domain ranking contract mismatch for {locale}")
    if search_payload.get("domain_ranking_schema_version") != domain_ranking_config["schema_version"]:
        raise BuildError(f"search index domain ranking schema mismatch for {locale}")
    if search_payload.get("quality_contract_id") != quality_config["contract_id"]:
        raise BuildError(f"search index quality contract mismatch for {locale}")
    if search_payload.get("quality_schema_version") != quality_config["schema_version"]:
        raise BuildError(f"search index quality schema mismatch for {locale}")
    if search_payload.get("integrity_contract_id") != integrity_config["contract_id"]:
        raise BuildError(f"search index integrity contract mismatch for {locale}")
    if search_payload.get("integrity_schema_version") != integrity_config["schema_version"]:
        raise BuildError(f"search index integrity schema mismatch for {locale}")
    if search_payload.get("status") != "ready":
        raise BuildError(f"search index is not ready for {locale}")
    if search_payload.get("locale") != locale:
        raise BuildError(f"search index locale mismatch for {locale}")
    if search_payload.get("search_mode") != "deterministic-local-static":
        raise BuildError(f"search index mode mismatch for {locale}")
    if search_payload.get("non_ai_boundary") != "no-ai-no-rag-no-embeddings-no-generative-answers":
        raise BuildError(f"search index non-AI boundary mismatch for {locale}")
    if search_payload.get("allowlisted_cross_locale_fields") != ["identifiers"]:
        raise BuildError(f"search index cross-locale allowlist mismatch for {locale}")

    fixtures = search_payload.get("query_fixtures")
    expected_fixtures = _query_fixtures_for_locale(locale, alias_config)
    if fixtures != expected_fixtures:
        raise BuildError(f"search index query fixtures mismatch for {locale}")
    normalization = search_payload.get("normalization", {})
    expected_browser_alias_groups = [
        {
            "alias_id": alias_group["alias_id"],
            "terms": _alias_terms_for_locale(alias_group, locale),
        }
        for alias_group in alias_config["alias_groups"]
    ]
    if normalization.get("alias_groups") != expected_browser_alias_groups:
        raise BuildError(f"search index browser alias groups mismatch for {locale}")
    if normalization.get("alias_group_count") != len(alias_config["alias_groups"]):
        raise BuildError(f"search index alias group count mismatch for {locale}")
    if normalization.get("query_fixture_count") != len(expected_fixtures):
        raise BuildError(f"search index query fixture count mismatch for {locale}")
    ranking = search_payload.get("ranking", {})
    expected_ranking_fixtures = _ranking_fixtures_for_locale(locale, ranking_config)
    if ranking.get("ranking_order") != ranking_config["ranking_order"]:
        raise BuildError(f"search index ranking order mismatch for {locale}")
    if ranking.get("weights") != ranking_config["weights"]:
        raise BuildError(f"search index ranking weights mismatch for {locale}")
    if ranking.get("typo_tolerance") != ranking_config["typo_tolerance"]:
        raise BuildError(f"search index typo tolerance mismatch for {locale}")
    if ranking.get("ranking_fixture_count") != len(expected_ranking_fixtures):
        raise BuildError(f"search index ranking fixture count mismatch for {locale}")
    filtering = search_payload.get("filtering", {})
    expected_filter_fixtures = [
        fixture for fixture in facets_config["filter_fixtures"] if fixture["locale"] == locale
    ]
    if filtering.get("facet_fields") != _localized_search_facet_fields(locale, facets_config):
        raise BuildError(f"search index facet fields mismatch for {locale}")
    if filtering.get("composition") != facets_config["filter_contract"]["composition"]:
        raise BuildError(f"search index filter composition mismatch for {locale}")
    if filtering.get("url_state") != facets_config["url_state"]:
        raise BuildError(f"search index filter URL state mismatch for {locale}")
    if filtering.get("empty_result") != facets_config["empty_result"]["messages"][locale]:
        raise BuildError(f"search index empty result message mismatch for {locale}")
    if filtering.get("filter_fixture_count") != len(expected_filter_fixtures):
        raise BuildError(f"search index filter fixture count mismatch for {locale}")
    quality = search_payload.get("quality", {})
    expected_quality_fixtures = _quality_fixtures_for_locale(locale, quality_config)
    if quality.get("categories") != quality_config["coverage_requirements"]["categories"]:
        raise BuildError(f"search index quality categories mismatch for {locale}")
    if quality.get("fixture_count") != len(expected_quality_fixtures):
        raise BuildError(f"search index quality fixture count mismatch for {locale}")
    if quality.get("thresholds") != quality_config["quality_thresholds"]:
        raise BuildError(f"search index quality thresholds mismatch for {locale}")
    for fixture in expected_fixtures:
        query_tokens = _normalize_search_text(locale, fixture["query"], alias_config)
        if not set(fixture["expected_tokens"]) <= set(query_tokens):
            raise BuildError(
                f"search fixture expected tokens are not resolved: {fixture['fixture_id']}"
            )
        resolved_aliases = set(
            _resolve_search_query_aliases(locale, fixture["query"], alias_config)
        )
        if not set(fixture["expected_alias_ids"]) <= resolved_aliases:
            raise BuildError(
                f"search fixture expected aliases are not resolved: {fixture['fixture_id']}"
            )

    documents = search_payload.get("documents")
    if not isinstance(documents, list) or len(documents) != len(manifest["topics"]):
        raise BuildError(f"search index document count mismatch for {locale}")

    document_ids: set[str] = set()
    required_searchable = set(contract["document_schema"]["searchable"]["required_fields"])
    required_facets = set(contract["document_schema"]["facets"]["required_fields"])
    known_alias_ids = {alias_group["alias_id"] for alias_group in alias_config["alias_groups"]}
    for document in documents:
        topic_id = document.get("topic_id")
        if topic_id not in manifest["topics"]:
            raise BuildError(f"search index references unknown topic for {locale}: {topic_id}")
        topic = manifest["topics"][topic_id]
        expected_output = topic["output"][locale]
        expected_url = f"/help/{expected_output}"
        document_id = document.get("document_id")
        if document_id in document_ids:
            raise BuildError(f"duplicate search document ID for {locale}: {document_id}")
        document_ids.add(document_id)
        if document_id != f"{locale}:{topic_id}" or document.get("locale") != locale:
            raise BuildError(f"search document identity mismatch for {locale}/{topic_id}")
        if (
            document.get("guide_id") != topic["guide_id"]
            or document.get("topic_kind") != topic["kind"]
        ):
            raise BuildError(f"search document manifest metadata mismatch for {locale}/{topic_id}")
        if document.get("url") != expected_url or not expected_url.startswith(f"/help/{locale}/"):
            raise BuildError(f"search document URL mismatch for {locale}/{topic_id}")

        source = document.get("source", {})
        if source.get("topic_id") != topic_id or source.get("output_path") != expected_output:
            raise BuildError(f"search document source mismatch for {locale}/{topic_id}")
        searchable = document.get("searchable", {})
        if set(searchable) != required_searchable:
            raise BuildError(f"search document searchable fields mismatch for {locale}/{topic_id}")
        if not isinstance(searchable.get("title"), str) or not searchable["title"]:
            raise BuildError(f"search document title is missing for {locale}/{topic_id}")
        if not isinstance(searchable.get("body"), str) or not searchable["body"]:
            raise BuildError(f"search document body is missing for {locale}/{topic_id}")
        for field in ("headings", "keywords", "identifiers", "aliases"):
            if not isinstance(searchable.get(field), list):
                raise BuildError(f"search document {field} is not a list for {locale}/{topic_id}")
        if (
            topic_id not in searchable["identifiers"]
            or topic["guide_id"] not in searchable["identifiers"]
        ):
            raise BuildError(f"search document identifiers are incomplete for {locale}/{topic_id}")
        normalized = document.get("normalized", {})
        normalized_fields = normalized.get("fields", {})
        alias_ids = normalized.get("alias_ids", [])
        if set(normalized_fields) != required_searchable:
            raise BuildError(f"search document normalized fields mismatch for {locale}/{topic_id}")
        if "tokens" in normalized:
            raise BuildError(f"search document has obsolete normalized tokens for {locale}/{topic_id}")
        if not set(alias_ids) <= known_alias_ids:
            raise BuildError(
                f"search document aliases reference unknown group for {locale}/{topic_id}"
            )

        facets = document.get("facets", {})
        if set(facets) != required_facets:
            raise BuildError(f"search document facets mismatch for {locale}/{topic_id}")
        if facets["locale"] != locale or facets["guide_id"] != topic["guide_id"]:
            raise BuildError(f"search document facet values mismatch for {locale}/{topic_id}")
        filter_facets = document.get("filter_facets", {})
        if set(filter_facets) != set(facets_config["facet_fields"]):
            raise BuildError(f"search document filter facets mismatch for {locale}/{topic_id}")
        for field, values in filter_facets.items():
            if not isinstance(values, list):
                raise BuildError(
                    f"search document filter facet is not a list for {locale}/{topic_id}/{field}"
                )
            allowed_values = _facet_values_from_config(facets_config, field)
            unknown_values = set(values) - allowed_values
            if unknown_values:
                raise BuildError(
                    f"search document filter facet has undeclared values for {locale}/{topic_id}/{field}: "
                    f"{sorted(unknown_values)}"
                )
        if filter_facets["locale"] != [locale] or filter_facets["guide_id"] != [topic["guide_id"]]:
            raise BuildError(
                f"search document filter identity facets mismatch for {locale}/{topic_id}"
            )

    if search_payload.get("facet_counts") != _facet_counts(documents, facets_config):
        raise BuildError(f"search index facet counts mismatch for {locale}")
    if search_payload.get("domain_ranking") != {
        "preserved_sources": domain_ranking_config["ranking"]["preserved_sources"],
        "evidence_fields": domain_ranking_config["ranking"]["evidence_fields"],
        "preserved_facets": domain_ranking_config["facets"]["preserved_fields"],
        "maximum_evidence_rows": domain_ranking_config["adapter_projection"][
            "maximum_evidence_rows"
        ],
    }:
        raise BuildError(f"search index domain ranking projection mismatch for {locale}")

    expected_integrity_report = _search_integrity_report(
        locale,
        documents,
        manifest["topics"],
        target_map,
        integrity_config,
    )
    if search_payload.get("integrity_report") != expected_integrity_report:
        raise BuildError(f"search index integrity report mismatch for {locale}")
    if (
        expected_integrity_report["status"] != "pass"
        or expected_integrity_report["failure_count"] != 0
    ):
        raise BuildError(f"search index integrity drift detected for {locale}")

    expected_results = _ranking_fixture_results(
        locale,
        documents,
        alias_config,
        ranking_config,
    )
    if search_payload.get("ranking_fixture_results") != expected_results:
        raise BuildError(f"search index ranking fixture results mismatch for {locale}")
    result_by_id = {result["fixture_id"]: result for result in expected_results}
    for fixture in expected_ranking_fixtures:
        result = result_by_id.get(fixture["fixture_id"])
        if result is None:
            raise BuildError(f"missing ranking fixture result: {fixture['fixture_id']}")
        if result["top_topic_id"] != fixture["expected_top_topic_id"]:
            raise BuildError(f"ranking fixture top result mismatch: {fixture['fixture_id']}")
        component = fixture["required_score_component"]
        if result["score_breakdown"].get(component, 0) <= 0:
            raise BuildError(
                f"ranking fixture component missing: {fixture['fixture_id']}/{component}"
            )

    expected_filter_results = _filter_fixture_results(locale, documents, facets_config)
    if search_payload.get("filter_fixture_results") != expected_filter_results:
        raise BuildError(f"search index filter fixture results mismatch for {locale}")
    filter_results_by_id = {result["fixture_id"]: result for result in expected_filter_results}
    for fixture in expected_filter_fixtures:
        result = filter_results_by_id.get(fixture["fixture_id"])
        if result is None:
            raise BuildError(f"missing filter fixture result: {fixture['fixture_id']}")
        if "expected_count" in fixture and result["result_count"] != fixture["expected_count"]:
            raise BuildError(f"filter fixture count mismatch: {fixture['fixture_id']}")
        if result["result_count"] < fixture.get("expected_min_count", 0):
            raise BuildError(f"filter fixture minimum count mismatch: {fixture['fixture_id']}")
        if not set(fixture.get("must_include_topic_ids", [])) <= set(result["result_topic_ids"]):
            raise BuildError(f"filter fixture missing expected topics: {fixture['fixture_id']}")
        if fixture.get("expected_empty") and (
            result["result_count"] != 0 or not result["empty_result_message"]
        ):
            raise BuildError(
                f"filter fixture empty-result recovery mismatch: {fixture['fixture_id']}"
            )
        if fixture["filters"] and not result["url_query"]:
            raise BuildError(f"filter fixture URL state is missing: {fixture['fixture_id']}")

    expected_quality_results = _quality_fixture_results(
        locale,
        documents,
        alias_config,
        ranking_config,
        quality_config,
    )
    if search_payload.get("quality_fixture_results") != expected_quality_results:
        raise BuildError(f"search index quality fixture results mismatch for {locale}")
    quality_results_by_id = {result["fixture_id"]: result for result in expected_quality_results}
    for fixture in expected_quality_fixtures:
        result = quality_results_by_id.get(fixture["fixture_id"])
        if result is None:
            raise BuildError(f"missing quality fixture result: {fixture['fixture_id']}")
        if "expected_count" in fixture and result["result_count"] != fixture["expected_count"]:
            raise BuildError(f"quality fixture count mismatch: {fixture['fixture_id']}")
        if (
            fixture.get("expected_top_topic_id")
            and result["top_topic_id"] != fixture["expected_top_topic_id"]
        ):
            raise BuildError(f"quality fixture top result mismatch: {fixture['fixture_id']}")
        component = fixture.get("required_score_component")
        if component and result["required_score_component_value"] <= 0:
            raise BuildError(
                f"quality fixture score component missing: {fixture['fixture_id']}/{component}"
            )
        if (
            result["visible_result_count"]
            > quality_config["performance_budget"]["max_visible_results_per_query"]
        ):
            raise BuildError(
                f"quality fixture visible result budget exceeded: {fixture['fixture_id']}"
            )

    expected_performance = _quality_performance_report(
        documents, expected_quality_results, quality_config
    )
    if search_payload.get("performance_report") != expected_performance:
        raise BuildError(f"search index performance report mismatch for {locale}")
    budget = quality_config["performance_budget"]
    if expected_performance["document_count"] > budget["max_documents_per_locale"]:
        raise BuildError(f"search index document performance budget exceeded for {locale}")
    if expected_performance["quality_fixture_count"] > budget["max_quality_fixtures_per_locale"]:
        raise BuildError(f"search index quality fixture budget exceeded for {locale}")
    if (
        expected_performance["deterministic_scan_units"]
        > budget["max_deterministic_scan_units_per_locale"]
    ):
        raise BuildError(f"search index deterministic scan budget exceeded for {locale}")


def validate_manifest_files(site_root: Path) -> None:
    manifest_path = site_root / "manifest.json"
    target_map_path = site_root / "ui-target-map.json"
    if not manifest_path.is_file() or not target_map_path.is_file():
        raise BuildError("manifest.json or ui-target-map.json is missing")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    target_map = json.loads(target_map_path.read_text(encoding="utf-8"))
    _validate_schema(target_map, UI_TARGET_SCHEMA)
    _validate_schema(manifest, MANIFEST_SCHEMA)
    _validate_manifest_semantics(manifest, target_map)
    if _file_sha256(target_map_path) != manifest["ui_target_map"]["sha256"]:
        raise BuildError("ui-target-map.json SHA-256 does not match manifest")
    quality_config = _search_quality_performance()
    for locale, navigation in manifest["navigation"].items():
        navigation_path = _safe_artifact_path(site_root, navigation["path"])
        if not navigation_path.is_file():
            raise BuildError(
                f"manifest navigation source is missing for {locale}: {navigation['path']}"
            )
        navigation_payload = _validate_navigation_artifact_record(
            locale,
            navigation,
            navigation_path.read_bytes(),
            manifest,
            context="manifest",
        )
        if navigation_payload != _navigation_payload(site_root, locale):
            raise BuildError(f"manifest navigation source diverges for {locale}")
    max_search_index_bytes = quality_config["performance_budget"]["max_index_bytes_per_locale"]
    for locale, search in manifest["search"].items():
        search_path = _safe_artifact_path(site_root, search["path"])
        if not search_path.is_file():
            raise BuildError(f"manifest search file is missing for {locale}: {search['path']}")
        if search_path.stat().st_size > max_search_index_bytes:
            raise BuildError(f"manifest search index size budget exceeded for {locale}")
        if _file_sha256(search_path) != search["sha256"]:
            raise BuildError(f"manifest search SHA-256 mismatch for {locale}")
        search_payload = json.loads(search_path.read_text(encoding="utf-8"))
        if search["document_count"] != len(search_payload.get("documents", [])):
            raise BuildError(f"manifest search document count mismatch for {locale}")
        _validate_search_index_semantics(locale, search_payload, manifest, target_map)
    for topic_id, topic in manifest["topics"].items():
        for locale, output in topic["output"].items():
            output_path = _safe_artifact_path(site_root, output)
            if not output_path.is_file():
                raise BuildError(f"manifest topic output is missing for {topic_id}/{locale}")


def validate_manifest_payloads(payloads: dict[str, bytes]) -> None:
    try:
        manifest = _read_json_bytes(payloads["manifest.json"], "manifest.json")
        target_map = _read_json_bytes(payloads["ui-target-map.json"], "ui-target-map.json")
    except KeyError as exc:
        raise BuildError("manifest.json or ui-target-map.json is missing from artifact") from exc
    _validate_schema(target_map, UI_TARGET_SCHEMA)
    _validate_schema(manifest, MANIFEST_SCHEMA)
    _validate_manifest_semantics(manifest, target_map)
    if _payload_sha256(payloads["ui-target-map.json"]) != manifest["ui_target_map"]["sha256"]:
        raise BuildError("archived ui-target-map.json SHA-256 does not match manifest")
    quality_config = _search_quality_performance()
    for locale, navigation in manifest["navigation"].items():
        path = navigation["path"]
        if path not in payloads:
            raise BuildError(f"archived navigation source is missing for {locale}: {path}")
        _validate_navigation_artifact_record(
            locale,
            navigation,
            payloads[path],
            manifest,
            context="archived",
        )
    max_search_index_bytes = quality_config["performance_budget"]["max_index_bytes_per_locale"]
    for locale, search in manifest["search"].items():
        path = search["path"]
        if path not in payloads:
            raise BuildError(f"archived search file is missing for {locale}: {path}")
        if len(payloads[path]) > max_search_index_bytes:
            raise BuildError(f"archived search index size budget exceeded for {locale}")
        if _payload_sha256(payloads[path]) != search["sha256"]:
            raise BuildError(f"archived search SHA-256 mismatch for {locale}")
        search_payload = _read_json_bytes(payloads[path], path)
        if search["document_count"] != len(search_payload.get("documents", [])):
            raise BuildError(f"archived search document count mismatch for {locale}")
        _validate_search_index_semantics(locale, search_payload, manifest, target_map)
    for topic_id, topic in manifest["topics"].items():
        for locale, output in topic["output"].items():
            if output not in payloads:
                raise BuildError(f"archived topic output is missing for {topic_id}/{locale}")


def _run(command: list[str], env: dict[str, str]) -> None:
    completed = subprocess.run(command, env=env, text=True, capture_output=True, check=False)
    if completed.returncode:
        output = (completed.stdout + "\n" + completed.stderr).strip()
        raise BuildError(f"DITA command failed ({' '.join(command)}):\n{output[-12000:]}")


def _dita_environment(java_home: Path) -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "JAVA_HOME": str(java_home),
            "PATH": f"{java_home / 'bin'}:{env.get('PATH', '')}",
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            "TZ": "UTC",
            "SOURCE_DATE_EPOCH": "0",
        }
    )
    return env


def _run_pdf(command: list[str], env: dict[str, str]) -> None:
    """Run DITA PDF conversion and fail on errors emitted with a zero exit code."""

    completed = subprocess.run(command, env=env, text=True, capture_output=True, check=False)
    output = (completed.stdout + "\n" + completed.stderr).strip()
    has_transform_error = "[DOTJ088E]" in output or "BUILD FAILED" in output
    if completed.returncode or has_transform_error:
        raise BuildError(
            f"DITA PDF command failed ({' '.join(command)}):\n{output[-12000:]}"
        )


def build_tree(destination: Path) -> None:
    dita, java_home = toolchain()
    source_before = source_hashes()
    destination.mkdir(parents=True, exist_ok=False)
    temp_root = destination.parent / f".{destination.name}-dita-temp"
    temp_root.mkdir(parents=True, exist_ok=False)
    env = _dita_environment(java_home)
    try:
        for locale in LOCALES:
            maintained_source = DOCUMENTATION_ROOT / f"src/dita/{locale}/maps/portal.ditamap"
            if not maintained_source.is_file():
                raise BuildError(f"missing locale portal map: {maintained_source}")
            locale_workspace = temp_root / locale
            input_root = locale_workspace / "input"
            shutil.copytree(DOCUMENTATION_ROOT / "src", input_root / "src")
            shutil.copytree(DOCUMENTATION_ROOT / "assets", input_root / "assets")
            source = input_root / f"src/dita/{locale}/maps/portal.ditamap"
            print(f"DITA publish: {locale}", flush=True)
            _run(
                [
                    str(dita),
                    "--input",
                    str(source),
                    "--format",
                    "html5",
                    "--output",
                    str(destination / locale),
                    "--temp",
                    str(locale_workspace / "work"),
                ],
                env,
            )
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)
    if source_hashes() != source_before:
        raise BuildError("DITA transform mutated maintained documentation source or assets")
    _normalize_locale_root_links(destination)
    _remove_dita_transient_screenshot_copies(destination)
    apply_portal_shell(destination)
    _normalize_screenshot_links(destination)
    generate_manifest_files(destination)
    validate_output(destination)


def _pdf_layout() -> dict[str, Any]:
    layout = _read_json_file(PDF_LAYOUT_CONTRACT)
    if layout.get("schema_version") != 1:
        raise BuildError("unsupported future PDF delivery layout schema")
    if layout.get("target_bpm_version") != _product_version():
        raise BuildError("future PDF delivery layout version does not match BPM version")
    if layout.get("locales") != list(LOCALES):
        raise BuildError("future PDF delivery layout locales do not match the BPM locale matrix")
    guides = layout.get("guides")
    if not isinstance(guides, list) or [guide.get("id") for guide in guides] != [
        guide_id for guide_id, _map_name in PDF_GUIDE_MAPS
    ]:
        raise BuildError("future PDF delivery layout guide order is invalid")
    for guide in guides:
        filename = guide.get("filename")
        if not isinstance(filename, str) or "{locale}" not in filename or "{bpm_version}" not in filename:
            raise BuildError("future PDF delivery layout guide filename is invalid")
    return layout


def _pdf_generation_policy() -> dict[str, Any]:
    policy = _read_json_file(PDF_GENERATION_CONTRACT)
    if policy.get("schema_version") != 1 or policy.get("backlog_item") != "BPM093-M14-08":
        raise BuildError("unsupported PDF generation contract")
    if policy.get("candidate_root") != "documentation/build/pdf":
        raise BuildError("PDF generation contract candidate root is invalid")
    if policy.get("candidate_path_layout") != "{locale}/{filename}":
        raise BuildError("PDF generation contract candidate path layout is invalid")
    if policy.get("dita_format") != "html5":
        raise BuildError("PDF generation contract DITA format is invalid")
    if policy.get("pdf_renderer") != "chromium":
        raise BuildError("PDF generation contract renderer is invalid")
    expected_maps = [map_name for _guide_id, map_name in PDF_GUIDE_MAPS]
    if policy.get("source_maps") != expected_maps:
        raise BuildError("PDF generation contract source maps are invalid")
    return policy


def _pdf_guide_filename(layout: dict[str, Any], guide_id: str, locale: str) -> str:
    guides = {guide["id"]: guide for guide in layout["guides"]}
    try:
        filename = guides[guide_id]["filename"].format(
            locale=locale, bpm_version=_product_version()
        )
    except (KeyError, AttributeError) as exc:
        raise BuildError(f"cannot format PDF filename for {guide_id}/{locale}") from exc
    if Path(filename).name != filename or not filename.endswith(".pdf"):
        raise BuildError(f"unsafe PDF filename for {guide_id}/{locale}: {filename!r}")
    return filename


def _expected_pdf_paths(layout: dict[str, Any]) -> set[str]:
    return {
        (Path(locale) / _pdf_guide_filename(layout, guide_id, locale)).as_posix()
        for locale in LOCALES
        for guide_id, _map_name in PDF_GUIDE_MAPS
    }


def _normalize_pdf_metadata(path: Path) -> None:
    """Remove renderer wall-clock metadata and canonically rewrite the PDF."""

    payload = path.read_bytes()

    def normalize_creation_date(match: re.Match[bytes]) -> bytes:
        fixed_date = (
            PDF_FIXED_UTC_CREATION_DATE
            if match.group(2).endswith(b"Z")
            else PDF_FIXED_CREATION_DATE
        )
        if len(match.group(2)) != len(fixed_date):
            raise BuildError(f"unsupported PDF creation-date format in {path}")
        return match.group(1) + fixed_date + match.group(3)

    payload, creation_dates = PDF_CREATION_DATE_PATTERN.subn(normalize_creation_date, payload)
    payload, modification_dates = PDF_MODIFICATION_DATE_PATTERN.subn(
        normalize_creation_date, payload
    )
    payload, document_ids = PDF_DOCUMENT_ID_PATTERN.subn(
        b"/ID [<" + PDF_FIXED_DOCUMENT_ID + b"> <" + PDF_FIXED_DOCUMENT_ID + b">]",
        payload,
    )
    if creation_dates != 1 or modification_dates not in {0, 1} or document_ids not in {0, 1}:
        raise BuildError(
            f"cannot deterministically normalize PDF metadata for {path}: "
            f"creation_dates={creation_dates}, modification_dates={modification_dates}, "
            f"document_ids={document_ids}"
        )
    path.write_bytes(payload)
    _canonicalize_pdf(path)


def _canonicalize_pdf(path: Path) -> None:
    qpdf = shutil.which("qpdf")
    if qpdf is None:
        raise BuildError("qpdf is required for deterministic PDF generation; install qpdf")
    qdf_path = path.with_name(f".{path.stem}.qdf.pdf")
    canonical_path = path.with_name(f".{path.stem}.canonical.pdf")
    try:
        _run_pdf_tool(
            [qpdf, "--qdf", "--object-streams=disable", str(path), str(qdf_path)],
            "expand PDF metadata",
        )
        qdf_payload = qdf_path.read_bytes()
        def normalize_xmp_timestamp(match: re.Match[bytes]) -> bytes:
            fixed_timestamp = (
                PDF_FIXED_UTC_XMP_TIMESTAMP
                if match.group(2).endswith(b"Z")
                else PDF_FIXED_XMP_TIMESTAMP
            )
            if len(match.group(2)) != len(fixed_timestamp):
                raise BuildError(f"unsupported PDF XMP timestamp format in {path}")
            return match.group(1) + fixed_timestamp + match.group(3)

        qdf_payload, xmp_timestamps = PDF_XMP_TIMESTAMP_PATTERN.subn(
            normalize_xmp_timestamp, qdf_payload
        )
        if xmp_timestamps not in {0, 3}:
            raise BuildError(
                f"cannot deterministically normalize PDF XMP metadata for {path}: "
                f"timestamps={xmp_timestamps}"
            )
        qdf_path.write_bytes(qdf_payload)
        _run_pdf_tool(
            [
                qpdf,
                "--static-id",
                "--object-streams=generate",
                "--recompress-flate",
                "--compression-level=9",
                str(qdf_path),
                str(canonical_path),
            ],
            "canonicalize PDF",
        )
        canonical_path.replace(path)
        # qpdf writes a new trailer ID while canonicalizing.  Replacing it after
        # that rewrite keeps the byte-level reproducibility promise without
        # changing any cross-reference offsets: the replacement is the same
        # fixed-width value.
        canonical_payload = path.read_bytes()
        canonical_payload, canonical_document_ids = PDF_DOCUMENT_ID_PATTERN.subn(
            b"/ID [<" + PDF_FIXED_DOCUMENT_ID + b"> <" + PDF_FIXED_DOCUMENT_ID + b">]",
            canonical_payload,
        )
        if canonical_document_ids != 1:
            raise BuildError(
                f"cannot deterministically normalize canonical PDF ID for {path}: "
                f"document_ids={canonical_document_ids}"
            )
        path.write_bytes(canonical_payload)
    finally:
        qdf_path.unlink(missing_ok=True)
        canonical_path.unlink(missing_ok=True)


def _run_pdf_tool(command: list[str], operation: str) -> None:
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    if completed.returncode:
        output = (completed.stdout + "\n" + completed.stderr).strip()
        raise BuildError(f"cannot {operation} ({' '.join(command)}):\n{output[-12000:]}")


def _pdf_keydefs(keys_path: Path) -> dict[str, str]:
    """Return local DITA map keys needed to assemble a print-only guide HTML file."""

    try:
        root = ET.parse(keys_path).getroot()
    except ET.ParseError as exc:
        raise BuildError(f"cannot parse PDF keys map {keys_path}: {exc}") from exc
    keydefs: dict[str, str] = {}
    for keydef in root.findall(".//keydef"):
        href = keydef.get("href")
        for key in keydef.get("keys", "").split():
            if href:
                keydefs[key] = href
    return keydefs


def _pdf_html_path_for_topic(map_path: Path, href: str) -> Path:
    """Resolve a local DITA topic href to its DITA-OT HTML5 output path."""

    topic_href = urllib.parse.unquote(href.split("#", 1)[0])
    if not topic_href:
        raise BuildError(f"PDF topic reference has no local target: {map_path}")
    locale_root = map_path.parents[1]
    target = (map_path.parent / topic_href).resolve()
    try:
        return target.relative_to(locale_root).with_suffix(".html")
    except ValueError as exc:
        raise BuildError(f"PDF topic target leaves locale source root: {href!r}") from exc


def _pdf_print_navigation(map_path: Path) -> tuple[str, list[tuple[str, list[Path]]]]:
    """Read the reviewed map order so the PDF has the same logical hierarchy as the web guide."""

    try:
        root = ET.parse(map_path).getroot()
    except ET.ParseError as exc:
        raise BuildError(f"cannot parse PDF source map {map_path}: {exc}") from exc
    title = " ".join(root.findtext("title", default="").split())
    if not title:
        raise BuildError(f"PDF source map has no title: {map_path}")
    keydefs = _pdf_keydefs(map_path.parent / "keys.ditamap")

    def topic_path(topicref: ET.Element) -> Path:
        href = topicref.get("href") or keydefs.get(topicref.get("keyref", ""))
        if href is None:
            raise BuildError(
                f"PDF topic reference cannot resolve keyref {topicref.get('keyref')!r} in {map_path}"
            )
        return _pdf_html_path_for_topic(map_path, href)

    sections: list[tuple[str, list[Path]]] = []
    direct_topics: list[Path] = []
    for child in root:
        if child.tag == "topichead":
            heading = " ".join(child.findtext("./topicmeta/navtitle", default="").split())
            if not heading:
                raise BuildError(f"PDF topic section has no navigation title: {map_path}")
            topics = [topic_path(topicref) for topicref in child.findall("./topicref")]
            if not topics:
                raise BuildError(f"PDF topic section has no topics: {heading!r} in {map_path}")
            sections.append((heading, topics))
        elif child.tag == "topicref":
            direct_topics.append(topic_path(child))
    if direct_topics:
        sections.insert(0, ("", direct_topics))
    if not sections:
        raise BuildError(f"PDF source map has no printable topics: {map_path}")
    return title, sections


def _pdf_article_from_html(path: Path) -> str:
    """Keep DITA-OT semantic HTML while dropping portal-only related-topic navigation."""

    try:
        rendered = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise BuildError(f"cannot read generated PDF topic HTML {path}: {exc}") from exc
    match = re.search(r"(<article\b.*?</article>)", rendered, flags=re.DOTALL)
    if match is None:
        raise BuildError(f"generated PDF topic has no article element: {path}")
    article = re.sub(
        r"<nav\b(?=[^>]*\brelated-links\b)[^>]*>.*?</nav>",
        "",
        match.group(1),
        flags=re.DOTALL,
    )
    # DITA-OT can resolve an intra-guide xref to the temporary output directory
    # when Chromium prints this combined HTML file. It has no stable PDF target;
    # omit local topic links while preserving external reader links.
    return re.sub(
        r"\s+href=(['\"])(?:file:.*?)?[^/'\"]+\.html(?:#[^'\"]*)?\1",
        "",
        article,
        flags=re.IGNORECASE,
    )


def _generated_pdf_topic_html(output_root: Path, topic_html: Path) -> Path | None:
    """Find one map topic in DITA-OT output, accepting its locale prefix.

    DITA-OT normally preserves the locale-relative path, but it can prepend the
    locale directory for a key-resolved map topic.  The basename and trailing
    locale-relative path remain stable, which is sufficient to select the
    generated article without deriving an invalid web-link path.
    """

    expected = output_root / topic_html
    if expected.is_file():
        return expected
    trailing_parts = topic_html.parts
    matches = [
        candidate
        for candidate in output_root.rglob(topic_html.name)
        if candidate.is_file() and candidate.parts[-len(trailing_parts) :] == trailing_parts
    ]
    if len(matches) == 1:
        return matches[0]
    return None


def _wait_for_pdf_topic_html(
    *,
    locale: str,
    guide_id: str,
    map_path: Path,
    output_root: Path,
    timeout_seconds: float = 120.0,
) -> None:
    """Wait until DITA-OT has materialized every map topic HTML file.

    Some DITA-OT runs return control slightly before every topic file is visible
    on disk.  The PDF printer must consume one complete map transformation, not
    launch independent topic transformations that could diverge from map output.
    """

    _title, sections = _pdf_print_navigation(map_path)
    expected = [
        topic_html
        for _section_title, topics in sections
        for topic_html in topics
    ]
    deadline = time.monotonic() + timeout_seconds
    reported_pending = False
    while True:
        pending = [
            topic_html
            for topic_html in expected
            if _generated_pdf_topic_html(output_root, topic_html) is None
        ]
        if not pending:
            return
        if not reported_pending:
            print(
                f"PDF source wait: {locale}/{guide_id} "
                f"({len(pending)} topic HTML pending)",
                flush=True,
            )
            reported_pending = True
        if time.monotonic() >= deadline:
            samples = ", ".join(
                topic_html.as_posix() for topic_html in pending[:5]
            )
            raise BuildError(
                "DITA HTML5 output did not become ready for "
                f"{locale}/{guide_id}: {samples}"
            )
        time.sleep(0.25)


def _write_pdf_print_guide(
    *,
    locale: str,
    guide_id: str,
    map_path: Path,
    output_root: Path,
) -> Path:
    """Compose one A4-ready guide from DITA HTML5 topic output in reviewed map order."""

    title, sections = _pdf_print_navigation(map_path)
    guide_directory = output_root / ("user" if guide_id == "user-guide" else "admin")
    guide_directory.mkdir(parents=True, exist_ok=True)
    print_path = guide_directory / f".{guide_id}-print.html"
    toc: list[str] = []
    content: list[str] = []
    for section_title, topics in sections:
        if section_title:
            toc.append(f"<h2>{html.escape(section_title)}</h2>")
            content.append(
                '<section class="bpm-pdf-section">'
                f"<h2>{html.escape(section_title)}</h2>"
            )
        toc.append("<ul>")
        for topic in topics:
            topic_path = _generated_pdf_topic_html(output_root, topic)
            if topic_path is None:
                raise BuildError(f"generated PDF topic is missing: {output_root / topic}")
            article = _pdf_article_from_html(topic_path)
            topic_title_match = re.search(r"<h1\b[^>]*>(.*?)</h1>", article, flags=re.DOTALL)
            if topic_title_match is None:
                raise BuildError(f"generated PDF topic has no title: {topic_path}")
            topic_title = re.sub(r"<[^>]+>", "", topic_title_match.group(1)).strip()
            toc.append(f"<li>{html.escape(topic_title)}</li>")
            content.append(article)
        toc.append("</ul>")
        if section_title:
            content.append("</section>")
    version = _product_version()
    print_path.write_text(
        "<!doctype html>\n"
        f'<html lang="{html.escape(locale)}"><head><meta charset="utf-8">'
        f"<title>{html.escape(title)}</title>"
        '<link rel="stylesheet" href="../bpm-guide-print.css"></head><body>'
        '<section class="bpm-pdf-cover">'
        '<img class="bpm-pdf-cover__logo" src="../assets/branding/bpm-logo.png" alt="">'
        f"<h1>{html.escape(title)}</h1>"
        f'<p class="bpm-pdf-cover__product">Browser Policy Manager {html.escape(version)}</p>'
        "</section>"
        f'<nav class="bpm-pdf-toc"><h1>{html.escape(_pdf_contents_title(locale))}</h1>'
        + "".join(toc)
        + "</nav>"
        + "".join(content)
        + "</body></html>\n",
        encoding="utf-8",
    )
    return print_path


def _pdf_contents_title(locale: str) -> str:
    return {
        "en": "Contents",
        "ru": "Содержание",
        "de": "Inhalt",
        "zh-CN": "目录",
        "fr": "Sommaire",
        "es-ES": "Contenido",
    }[locale]


def _chromium_pdf_renderer() -> str:
    for executable in ("chromium", "chromium-browser", "google-chrome"):
        resolved = shutil.which(executable)
        if resolved:
            return resolved
    raise BuildError(
        "Chromium is required for Unicode-safe PDF generation; install the chromium executable"
    )


def _render_pdf_with_chromium(source: Path, target: Path, env: dict[str, str]) -> None:
    renderer = _chromium_pdf_renderer()
    completed = subprocess.run(
        [
            renderer,
            "--headless",
            "--no-sandbox",
            "--disable-gpu",
            "--disable-background-networking",
            "--disable-component-update",
            "--disable-sync",
            "--no-first-run",
            "--no-pdf-header-footer",
            f"--print-to-pdf={target}",
            source.resolve().as_uri(),
        ],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        output = (completed.stdout + "\n" + completed.stderr).strip()
        raise BuildError(f"Chromium PDF rendering failed for {source}:\n{output[-12000:]}")
    _validate_pdf_file(target)


def _validate_pdf_file(path: Path) -> None:
    if not path.is_file() or path.is_symlink():
        raise BuildError(f"generated PDF is missing or unsafe: {path}")
    payload = path.read_bytes()
    if len(payload) < 1024 or not payload.startswith(b"%PDF-") or b"%%EOF" not in payload[-2048:]:
        raise BuildError(f"generated file is not a complete PDF: {path}")


def _pdf_build_manifest(layout: dict[str, Any], policy: dict[str, Any], root: Path) -> dict[str, Any]:
    files = {
        path: _file_sha256(root / path)
        for path in sorted(_expected_pdf_paths(layout))
    }
    lock = _load_lock()
    return {
        "schema_version": 1,
        "contract_id": policy["contract_id"],
        "backlog_item": policy["backlog_item"],
        "bpm_version": _product_version(),
        "source_revision": _source_revision(),
        "source_fingerprint": _source_fingerprint(),
        "dita_ot_version": lock["components"]["dita_ot"]["version"],
        "files": files,
    }


def validate_pdf_tree(root: Path) -> None:
    layout = _pdf_layout()
    policy = _pdf_generation_policy()
    if not root.is_dir() or root.is_symlink():
        raise BuildError(f"PDF candidate root is missing or unsafe: {root}")
    expected_pdf_paths = _expected_pdf_paths(layout)
    expected_files = expected_pdf_paths | {PDF_BUILD_MANIFEST}
    actual_files = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and not path.is_symlink()
    }
    unsafe_paths = [path for path in root.rglob("*") if path.is_symlink()]
    if unsafe_paths:
        raise BuildError(f"PDF candidate contains a symbolic link: {unsafe_paths[0]}")
    if actual_files != expected_files:
        missing = sorted(expected_files - actual_files)
        unexpected = sorted(actual_files - expected_files)
        raise BuildError(
            "PDF candidate file set does not match the contract: "
            f"missing={missing}, unexpected={unexpected}"
        )
    for path in sorted(expected_pdf_paths):
        _validate_pdf_file(root / path)
    manifest = _read_json_file(root / PDF_BUILD_MANIFEST)
    if (
        manifest.get("schema_version") != 1
        or manifest.get("contract_id") != policy["contract_id"]
        or manifest.get("backlog_item") != policy["backlog_item"]
        or manifest.get("bpm_version") != _product_version()
        or manifest.get("source_fingerprint") != _source_fingerprint()
    ):
        raise BuildError("PDF candidate manifest does not match the current generation contract")
    expected_hashes = {path: _file_sha256(root / path) for path in sorted(expected_pdf_paths)}
    if manifest.get("files") != expected_hashes:
        raise BuildError("PDF candidate manifest SHA-256 values do not match generated PDFs")


def build_pdf_tree(destination: Path) -> None:
    """Generate the two source guides for every supported locale into a candidate tree."""

    layout = _pdf_layout()
    policy = _pdf_generation_policy()
    for required_asset in (PDF_PRINT_CSS, PDF_COVER_LOGO):
        if not required_asset.is_file():
            raise BuildError(f"PDF asset is missing: {required_asset}")
    validate_sources()
    dita, java_home = toolchain()
    source_before = source_hashes()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.mkdir(parents=True, exist_ok=False)
    temp_root = destination.parent / f".{destination.name}-dita-temp"
    temp_root.mkdir(parents=True, exist_ok=False)
    env = _dita_environment(java_home)
    total = len(LOCALES) * len(PDF_GUIDE_MAPS)
    completed = 0
    try:
        for locale in LOCALES:
            locale_workspace = temp_root / locale
            input_root = locale_workspace / "input"
            shutil.copytree(DOCUMENTATION_ROOT / "src", input_root / "src")
            shutil.copytree(DOCUMENTATION_ROOT / "assets", input_root / "assets")
            for guide_id, map_name in PDF_GUIDE_MAPS:
                completed += 1
                source = input_root / f"src/dita/{locale}/maps/{map_name}"
                if not source.is_file():
                    raise BuildError(f"missing PDF source map: {source}")
                output = locale_workspace / "output" / guide_id
                print(
                    f"PDF source: {locale}/{guide_id} ({completed}/{total}) DITA HTML5",
                    flush=True,
                )
                _run_pdf(
                    [
                        str(dita),
                        "--input",
                        str(source),
                        "--format",
                        policy["dita_format"],
                        "--output",
                        str(output),
                        "--temp",
                        str(locale_workspace / "work" / guide_id),
                    ],
                    env,
                )
                _wait_for_pdf_topic_html(
                    locale=locale,
                    guide_id=guide_id,
                    map_path=source,
                    output_root=output,
                )
                css = input_root / "assets/pdf/bpm-guide-print.css"
                logo = input_root / "assets/branding/bpm-logo.png"
                if not css.is_file() or not logo.is_file():
                    raise BuildError("isolated PDF print assets are missing")
                shutil.copyfile(css, output / "bpm-guide-print.css")
                logo_destination = output / "assets/branding/bpm-logo.png"
                logo_destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(logo, logo_destination)
                print_source = _write_pdf_print_guide(
                    locale=locale,
                    guide_id=guide_id,
                    map_path=source,
                    output_root=output,
                )
                target = destination / locale / _pdf_guide_filename(layout, guide_id, locale)
                target.parent.mkdir(parents=True, exist_ok=True)
                print(
                    f"PDF render: {locale}/{guide_id} ({completed}/{total}) Chromium",
                    flush=True,
                )
                _render_pdf_with_chromium(print_source, target, env)
                _normalize_pdf_metadata(target)
                _validate_pdf_file(target)
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)
    if source_hashes() != source_before:
        raise BuildError("DITA PDF transform mutated maintained documentation source or assets")
    _write_json(destination / PDF_BUILD_MANIFEST, _pdf_build_manifest(layout, policy, destination))
    validate_pdf_tree(destination)


def publish_pdfs() -> None:
    BUILD_ROOT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".pdf-build-", dir=BUILD_ROOT) as temporary:
        candidate = Path(temporary) / "pdf"
        build_pdf_tree(candidate)
        previous = BUILD_ROOT / ".pdf-previous"
        _remove_path(previous)
        if PDF_BUILD_ROOT.exists():
            PDF_BUILD_ROOT.replace(previous)
        try:
            candidate.replace(PDF_BUILD_ROOT)
        except OSError:
            if previous.exists():
                previous.replace(PDF_BUILD_ROOT)
            raise
        finally:
            _remove_path(previous)
    print(f"Published PDF candidate to {PDF_BUILD_ROOT.relative_to(REPOSITORY_ROOT)}", flush=True)


def verify_pdfs() -> None:
    validate_pdf_tree(PDF_BUILD_ROOT)
    print(f"Verified PDF candidate: {PDF_BUILD_ROOT.relative_to(REPOSITORY_ROOT)}", flush=True)


def pdf_reproducibility_check() -> None:
    validate_pdf_tree(PDF_BUILD_ROOT)
    published_hashes = tree_hashes(PDF_BUILD_ROOT)
    BUILD_ROOT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".pdf-reproducibility-", dir=BUILD_ROOT) as temporary:
        candidate = Path(temporary) / "candidate"
        build_pdf_tree(candidate)
        candidate_hashes = tree_hashes(candidate)
        if published_hashes != candidate_hashes:
            differing = sorted(
                path
                for path in set(published_hashes) | set(candidate_hashes)
                if published_hashes.get(path) != candidate_hashes.get(path)
            )
            raise BuildError("non-deterministic PDF files:\n" + "\n".join(differing))
    print(f"PDF reproducibility check passed for {len(published_hashes)} files.", flush=True)


def tree_hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def source_hashes() -> dict[str, str]:
    roots = (DOCUMENTATION_ROOT / "src", DOCUMENTATION_ROOT / "assets")
    paths = [
        *(path for root in roots for path in sorted(root.rglob("*")) if path.is_file()),
        TOPIC_SECTION_TAXONOMY,
        TOPIC_SECTION_LABELS,
    ]
    return {
        path.relative_to(DOCUMENTATION_ROOT).as_posix(): hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path in paths
    }


def _artifact_policy() -> dict[str, Any]:
    try:
        policy = json.loads(ARTIFACT_POLICY.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BuildError(f"cannot read artifact policy: {exc}") from exc
    if policy.get("schema_version") != 1:
        raise BuildError("unsupported artifact policy schema")
    return policy


def _source_fingerprint() -> str:
    inputs = [
        *dita_sources(),
        *sorted((DOCUMENTATION_ROOT / "src/shared/filters").glob("*.ditaval")),
        *sorted(THEME_ROOT.glob("*.css")),
        THEME_ROOT / SEARCH_SCRIPT,
        THEME_ROOT / MODEL_MANAGER_SCRIPT,
        THEME_ROOT / ASSISTANT_RENDERER_SCRIPT,
        THEME_ROOT / ASSISTANT_STATE_MACHINE_SCRIPT,
        THEME_ROOT / ASSISTANT_CONVERSATION_SCRIPT,
        THEME_ROOT / ASSISTANT_TRANSPORT_SCRIPT,
        THEME_ROOT / ASSISTANT_SHELL_SCRIPT,
        DOCUMENTATION_ASSISTANT_COPY,
        PDF_THEME,
        PDF_PRINT_CSS,
        PDF_COVER_LOGO,
        PDF_COVER_BRANDING,
        PDF_LAYOUT_CONTRACT,
        PDF_GENERATION_CONTRACT,
        MANIFEST_SCHEMA,
        UI_TARGET_SCHEMA,
        NAVIGATION_SCHEMA,
        DOCUMENTATION_ROOT / "config/metadata-vocabulary.json",
        DOCUMENTATION_ROOT / "config/user-guide-map-0.9.0.json",
        SEARCH_CORPUS_CONTRACT,
        SEARCH_NORMALIZATION_ALIASES,
        SEARCH_RANKING_TYPO,
        SEARCH_FACETS_FILTERS,
        SEARCH_DOMAIN_RANKING_FACETS,
        SEARCH_QUALITY_PERFORMANCE,
        SEARCH_INTEGRITY_DRIFT,
        TOPIC_SECTION_TAXONOMY,
        TOPIC_SECTION_LABELS,
        LOCK_PATH,
        REPOSITORY_ROOT / "pyproject.toml",
        Path(__file__),
    ]
    digest = hashlib.sha256()
    for path in sorted(set(inputs)):
        digest.update(path.relative_to(REPOSITORY_ROOT).as_posix().encode())
        digest.update(b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def _write_integrity(root: Path, policy: dict[str, Any]) -> None:
    lock = _load_lock()
    runtime = policy["current_runtime_contract"]
    integrity = {
        "schema_version": 1,
        "bpm_version": _product_version(),
        "documentation_version": _product_version(),
        "dita_ot_version": lock["components"]["dita_ot"]["version"],
        "locales": list(LOCALES),
        "source_fingerprint": _source_fingerprint(),
        "runtime_ready": runtime["runtime_ready"],
        "runtime_blockers": runtime["required_before_shipping"],
        "files": tree_hashes(root),
    }
    (root / "artifact-integrity.json").write_text(
        json.dumps(integrity, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _tar_filter(info: tarfile.TarInfo) -> tarfile.TarInfo:
    info.uid = 0
    info.gid = 0
    info.uname = ""
    info.gname = ""
    info.mtime = 0
    if info.isdir():
        info.mode = 0o755
    elif info.isfile():
        info.mode = 0o644
    return info


def create_archive(root: Path, archive: Path) -> None:
    with archive.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as bundle:
                paths = [root, *sorted(root.rglob("*"), key=lambda path: path.as_posix().lower())]
                for path in paths:
                    arcname = path.relative_to(root.parent).as_posix()
                    bundle.add(path, arcname=arcname, recursive=False, filter=_tar_filter)


def verify_archive(archive: Path, policy: dict[str, Any] | None = None) -> str:
    policy = policy or _artifact_policy()
    expected_root = policy["archive"]["root"]
    payloads: dict[str, bytes] = {}
    with tarfile.open(archive, "r:gz") as bundle:
        for member in bundle.getmembers():
            parts = Path(member.name).parts
            if not parts or parts[0] != expected_root or ".." in parts:
                raise BuildError(f"archive member escapes artifact root: {member.name}")
            if member.issym() or member.islnk() or member.isdev():
                raise BuildError(f"special archive member is forbidden: {member.name}")
            if member.isfile():
                stream = bundle.extractfile(member)
                if stream is None:
                    raise BuildError(f"cannot read archive member: {member.name}")
                payloads[Path(*parts[1:]).as_posix()] = stream.read()
    try:
        integrity = json.loads(payloads.pop("artifact-integrity.json").decode("utf-8"))
    except (KeyError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BuildError("archive has no valid artifact-integrity.json") from exc
    if integrity.get("runtime_ready") is not False:
        raise BuildError("artifact runtime status does not match the current blocked contract")
    expected_files = integrity.get("files")
    actual_files = {name: hashlib.sha256(content).hexdigest() for name, content in payloads.items()}
    if expected_files != actual_files:
        raise BuildError("artifact integrity file list or SHA-256 values do not match archive")
    if set(LOCALES) - {Path(name).parts[0] for name in payloads}:
        raise BuildError("artifact does not contain every locale root")
    validate_manifest_payloads(payloads)
    return hashlib.sha256(archive.read_bytes()).hexdigest()


def artifact_paths(policy: dict[str, Any] | None = None) -> tuple[Path, Path]:
    policy = policy or _artifact_policy()
    return (
        REPOSITORY_ROOT / policy["paths"]["release_archive"],
        REPOSITORY_ROOT / policy["paths"]["release_checksum"],
    )


def _metadata_validation() -> None:
    validator = DOCUMENTATION_ROOT / "tools/validate_metadata.py"
    completed = subprocess.run(
        [sys.executable, str(validator)], text=True, capture_output=True, check=False
    )
    if completed.returncode:
        raise BuildError((completed.stdout + "\n" + completed.stderr).strip())


def validate_sources() -> None:
    _metadata_validation()
    validate_source_links()


def publish() -> None:
    validate_sources()
    BUILD_ROOT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".publish-", dir=BUILD_ROOT) as temporary:
        candidate = Path(temporary) / "site"
        build_tree(candidate)
        destination = BUILD_ROOT / "site"
        previous = BUILD_ROOT / ".site-previous"
        shutil.rmtree(previous, ignore_errors=True)
        if destination.exists():
            destination.replace(previous)
        try:
            candidate.replace(destination)
        except OSError:
            if previous.exists():
                previous.replace(destination)
            raise
        shutil.rmtree(previous, ignore_errors=True)
    print(f"Published documentation to {destination.relative_to(REPOSITORY_ROOT)}", flush=True)


def _remove_path(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink(missing_ok=True)


def _dev_site_is_current(source_fingerprint: str) -> bool:
    if not DEV_SITE_ROOT.is_dir() or not DEV_SITE_METADATA.is_file():
        return False
    try:
        metadata = json.loads(DEV_SITE_METADATA.read_text(encoding="utf-8"))
    except OSError, json.JSONDecodeError:
        return False
    if metadata.get("source_fingerprint") != source_fingerprint:
        return False
    try:
        validate_manifest_files(DEV_SITE_ROOT)
    except BuildError:
        return False
    return True


def _promote_dev_site(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    candidate = destination.parent / f".{destination.name}-candidate"
    previous = destination.parent / f".{destination.name}-previous"
    _remove_path(candidate)
    _remove_path(previous)
    shutil.copytree(source, candidate)
    validate_manifest_files(candidate)
    if destination.exists():
        destination.replace(previous)
    try:
        candidate.replace(destination)
    except OSError:
        if previous.exists():
            previous.replace(destination)
        raise
    finally:
        _remove_path(candidate)
        _remove_path(previous)


def install_dev_site() -> None:
    """Install the locally built documentation site into the BPM dev runtime path."""

    source_fingerprint = _source_fingerprint()
    if _dev_site_is_current(source_fingerprint):
        print(
            f"Installed dev documentation is current at {DEV_SITE_ROOT.relative_to(REPOSITORY_ROOT)}",
            flush=True,
        )
        return

    publish()
    source = BUILD_ROOT / "site"
    _promote_dev_site(source, DEV_SITE_ROOT)
    metadata = {
        "schema_version": 1,
        "bpm_version": _product_version(),
        "source_fingerprint": source_fingerprint,
        "source_site": source.relative_to(REPOSITORY_ROOT).as_posix(),
        "installed_site": DEV_SITE_ROOT.relative_to(REPOSITORY_ROOT).as_posix(),
    }
    DEV_SITE_METADATA.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        f"Installed dev documentation to {DEV_SITE_ROOT.relative_to(REPOSITORY_ROOT)}",
        flush=True,
    )


def validate_build() -> None:
    validate_sources()
    BUILD_ROOT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".validate-", dir=BUILD_ROOT) as temporary:
        build_tree(Path(temporary) / "site")
    print("DITA, metadata, source links, and generated links are valid.", flush=True)


def reproducibility_check() -> None:
    validate_sources()
    BUILD_ROOT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".reproducibility-", dir=BUILD_ROOT) as temporary:
        root = Path(temporary)
        first = root / "first"
        second = root / "second"
        build_tree(first)
        build_tree(second)
        first_hashes = tree_hashes(first)
        second_hashes = tree_hashes(second)
        if first_hashes != second_hashes:
            differing = sorted(
                path
                for path in set(first_hashes) | set(second_hashes)
                if first_hashes.get(path) != second_hashes.get(path)
            )
            raise BuildError("non-deterministic publishable files:\n" + "\n".join(differing))
    print(f"Reproducibility check passed for {len(first_hashes)} files.", flush=True)


def package() -> None:
    policy = _artifact_policy()
    archive, checksum_file = artifact_paths(policy)
    DIST_ROOT.mkdir(parents=True, exist_ok=True)
    archive.unlink(missing_ok=True)
    checksum_file.unlink(missing_ok=True)
    try:
        validate_sources()
        with tempfile.TemporaryDirectory(prefix=".package-", dir=DIST_ROOT) as temporary:
            staging = Path(temporary)
            root = staging / policy["archive"]["root"]
            build_tree(root)
            licenses = root / "licenses"
            licenses.mkdir()
            shutil.copyfile(REPOSITORY_ROOT / "LICENSE", licenses / "BPM-MPL-2.0.txt")
            shutil.copyfile(
                DOCUMENTATION_ROOT / "config/THIRD_PARTY_NOTICES.md",
                licenses / "THIRD_PARTY_NOTICES.md",
            )
            _write_integrity(root, policy)
            candidate = staging / archive.name
            create_archive(root, candidate)
            digest = verify_archive(candidate, policy)
            candidate_checksum = staging / checksum_file.name
            candidate_checksum.write_text(f"{digest}  {archive.name}\n", encoding="ascii")
            candidate.replace(archive)
            candidate_checksum.replace(checksum_file)
    except Exception:
        archive.unlink(missing_ok=True)
        checksum_file.unlink(missing_ok=True)
        raise
    print(f"Packaged documentation candidate: {archive.relative_to(REPOSITORY_ROOT)}", flush=True)


def verify_package() -> None:
    policy = _artifact_policy()
    archive, checksum_file = artifact_paths(policy)
    if not archive.is_file() or not checksum_file.is_file():
        raise BuildError("documentation package or checksum is absent; run make docs-package")
    digest = verify_archive(archive, policy)
    expected_checksum = f"{digest}  {archive.name}\n"
    if checksum_file.read_text(encoding="ascii") != expected_checksum:
        raise BuildError("documentation package checksum file does not match archive")
    print(f"Verified documentation package SHA-256: {digest}", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=(
            "validate",
            "build",
            "install-dev",
            "fast-check",
            "reproducibility",
            "package",
            "package-verify",
            "pdf-build",
            "pdf-verify",
            "pdf-reproducibility",
        ),
    )
    parser.add_argument("paths", nargs="*", help="changed documentation paths for fast-check")
    args = parser.parse_args()
    try:
        {
            "validate": validate_build,
            "build": publish,
            "install-dev": install_dev_site,
            "fast-check": lambda: fast_check(args.paths),
            "reproducibility": reproducibility_check,
            "package": package,
            "package-verify": verify_package,
            "pdf-build": publish_pdfs,
            "pdf-verify": verify_pdfs,
            "pdf-reproducibility": pdf_reproducibility_check,
        }[args.command]()
    except (BuildError, OSError) as exc:
        print(f"documentation build failed: {exc}", file=sys.stderr)
        if args.command == "fast-check":
            diagnostic = write_failure_diagnostic(exc, args.paths)
            print(
                f"diagnostic artifact: {diagnostic.relative_to(REPOSITORY_ROOT)}",
                file=sys.stderr,
            )
            print(
                f"focused rerun: {_diagnostic_payload(exc, args.paths)['focused_rerun']}",
                file=sys.stderr,
            )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
