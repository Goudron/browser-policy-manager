"""Portal HTML, theme assets, and assistant-copy publishing."""

# ruff: noqa: F403, F405
from .catalog import (
    _escape,
    _navigation_breadcrumbs,
    _navigation_host,
    _read_json_file,
    _relative_href,
    _write_json,
    generate_navigation_files,
)
from .shared import *
from .shared import _product_header_labels, _product_version


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
        f"{_escape(product_header_labels[f'firefox_schema_{channel.value}'])}"
        f"{', ' if index < len(HEADER_SCHEMA_CHANNELS) - 1 else ''}</span>"
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
        expected_names = {source.name for source in (SCREENSHOT_ROOT / locale).glob("*.png")}
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
                raise BuildError(
                    f"documentation assistant state copy is invalid for {locale}/{state_id}"
                )
            if not all(isinstance(value, str) and value.strip() for value in state.values()):
                raise BuildError(
                    f"documentation assistant state copy is empty for {locale}/{state_id}"
                )
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
