(() => {
  "use strict";

  const MAX_QUERY_LENGTH = 256;
  const MAX_RESULTS = 50;
  const SEARCH_ROOT_SELECTOR = ".bpm-docs-search";
  const TREE_SELECTOR = "[data-docs-tree]";
  const TREE_HOST_SELECTOR = "[data-docs-tree-host]";
  const STORAGE_PREFIX = "bpm-docs-search:";
  const LOCALE_STORAGE_KEY = "bpm-lang-mode";
  const THEME_STORAGE_KEY = "bpm-theme-mode";
  const THEME_MODES = new Set(["system", "light", "dark"]);
  const THEME_COLORS = {
    light: "#edf2f7",
    dark: "#07111a",
  };

  const safeStorageGet = (key, fallback = "") => {
    try {
      return window.localStorage.getItem(key) || fallback;
    } catch {
      return fallback;
    }
  };

  const safeStorageSet = (key, value) => {
    try {
      window.localStorage.setItem(key, value);
    } catch {
      /* Browser storage may be disabled; the current page still keeps the selected mode. */
    }
  };

  const selectorEscape = (value) => {
    if (window.CSS && typeof window.CSS.escape === "function") {
      return window.CSS.escape(value);
    }
    return String(value).replace(/["\\]/g, "\\$&");
  };

  const normalizeThemeMode = (mode) => (THEME_MODES.has(mode) ? mode : "system");

  const themeMediaQuery = () => {
    if (typeof window.matchMedia !== "function") {
      return { matches: false };
    }
    return window.matchMedia("(prefers-color-scheme: dark)");
  };

  const resolveTheme = (mode, mediaQuery) => {
    if (mode === "dark" || mode === "light") {
      return mode;
    }
    return mediaQuery.matches ? "dark" : "light";
  };

  const updateThemeColorMeta = (resolvedTheme) => {
    const metaThemeColor = document.querySelector('meta[name="theme-color"]');
    if (metaThemeColor) {
      metaThemeColor.setAttribute("content", THEME_COLORS[resolvedTheme] || THEME_COLORS.light);
    }
  };

  const applyDocsThemeMode = (mode, mediaQuery, persist = true) => {
    const normalizedMode = normalizeThemeMode(mode);
    const resolvedTheme = resolveTheme(normalizedMode, mediaQuery);
    const html = document.documentElement;
    const themeSelect = document.querySelector("[data-docs-theme-select]");

    html.dataset.themeMode = normalizedMode;
    html.dataset.theme = resolvedTheme;
    updateThemeColorMeta(resolvedTheme);

    if (themeSelect instanceof HTMLSelectElement) {
      themeSelect.value = normalizedMode;
    }
    if (persist) {
      safeStorageSet(THEME_STORAGE_KEY, normalizedMode);
    }
  };

  const setupThemeMode = () => {
    const mediaQuery = themeMediaQuery();
    const themeSelect = document.querySelector("[data-docs-theme-select]");
    const savedMode = normalizeThemeMode(safeStorageGet(THEME_STORAGE_KEY, "system"));

    applyDocsThemeMode(savedMode, mediaQuery, false);

    if (themeSelect instanceof HTMLSelectElement) {
      themeSelect.addEventListener("change", () => {
        applyDocsThemeMode(themeSelect.value, mediaQuery);
      });
    }

    const handleSystemThemeChange = () => {
      const activeMode = normalizeThemeMode(safeStorageGet(THEME_STORAGE_KEY, "system"));
      if (activeMode === "system") {
        applyDocsThemeMode("system", mediaQuery, false);
      }
    };

    if (typeof mediaQuery.addEventListener === "function") {
      mediaQuery.addEventListener("change", handleSystemThemeChange);
    } else if (typeof mediaQuery.addListener === "function") {
      mediaQuery.addListener(handleSystemThemeChange);
    }
  };

  const setupLocaleSelect = () => {
    const localeSelect = document.querySelector("[data-docs-locale-select]");
    if (!(localeSelect instanceof HTMLSelectElement)) {
      return;
    }

    const languageMatchesRule = (languageTag, rule) => {
      const language = String(languageTag || "").trim().replace(/_/g, "-").toLowerCase();
      const normalizedRule = String(rule || "").trim().replace(/_/g, "-").toLowerCase();
      if (!language || !normalizedRule) {
        return false;
      }
      return normalizedRule.endsWith("-*")
        ? language.startsWith(`${normalizedRule.slice(0, -2)}-`)
        : language === normalizedRule;
    };

    const systemLocaleOption = () => {
      const options = Array.from(localeSelect.options).filter(
        (option) => option.value !== "system"
      );
      const languages = [
        ...(Array.isArray(window.navigator.languages) ? window.navigator.languages : []),
        window.navigator.language,
      ].filter(Boolean);
      for (const language of languages.length ? languages : ["en"]) {
        const matched = options.find((option) => {
          try {
            return JSON.parse(option.dataset.docsLocaleMatches || "[]").some((rule) =>
              languageMatchesRule(language, rule)
            );
          } catch {
            return false;
          }
        });
        if (matched) {
          return matched;
        }
      }
      return options.find((option) => option.value === "en") || options[0] || null;
    };

    const savedMode = safeStorageGet(
      LOCALE_STORAGE_KEY,
      safeStorageGet("bpm-lang", "system")
    );
    const availableModes = new Set(Array.from(localeSelect.options).map((option) => option.value));
    localeSelect.value = availableModes.has(savedMode) ? savedMode : "system";

    localeSelect.addEventListener("change", () => {
      const mode = availableModes.has(localeSelect.value) ? localeSelect.value : "system";
      safeStorageSet(LOCALE_STORAGE_KEY, mode);
      const option = mode === "system"
        ? systemLocaleOption()
        : localeSelect.selectedOptions[0];
      const href = option?.dataset.docsLocaleHref;
      if (href) {
        window.location.assign(href);
      }
    });
  };

  const normalize = (value) =>
    String(value || "")
      .normalize("NFKC")
      .toLocaleLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/[^\p{Letter}\p{Number}._:/-]+/gu, " ")
      .trim();

  const queryTokens = (query) =>
    normalize(query)
      .split(/\s+/u)
      .filter(Boolean)
      .slice(0, 24);

  const values = (value) => {
    if (Array.isArray(value)) {
      return value.map(String).filter(Boolean);
    }
    return value ? [String(value)] : [];
  };

  const clearNode = (node) => {
    while (node.firstChild) {
      node.removeChild(node.firstChild);
    }
  };

  const appendText = (parent, text) => {
    parent.appendChild(document.createTextNode(text));
  };

  const appendMarkedText = (parent, text, tokens) => {
    const source = String(text || "");
    const folded = normalize(source);
    const token = tokens.find((candidate) => candidate && folded.includes(candidate));
    if (!token) {
      appendText(parent, source);
      return;
    }
    const start = folded.indexOf(token);
    const end = Math.min(source.length, start + token.length);
    appendText(parent, source.slice(0, start));
    const mark = document.createElement("mark");
    mark.textContent = source.slice(start, end);
    parent.appendChild(mark);
    appendText(parent, source.slice(end));
  };

  const searchableText = (documentRecord) => {
    const searchable = documentRecord.searchable || {};
    return [
      searchable.title,
      searchable.shortdesc,
      ...(searchable.headings || []),
      searchable.body,
      ...(searchable.keywords || []),
      ...(searchable.identifiers || []),
      ...(searchable.aliases || []),
    ]
      .map((part) => (Array.isArray(part) ? part.join(" ") : String(part || "")))
      .join(" ");
  };

  const scoreDocument = (documentRecord, tokens) => {
    if (!tokens.length) {
      return 1;
    }
    const searchable = documentRecord.searchable || {};
    const title = normalize(searchable.title);
    const identifiers = normalize((searchable.identifiers || []).join(" "));
    const aliases = normalize((searchable.aliases || []).join(" "));
    const body = normalize(searchableText(documentRecord));
    let score = 0;
    for (const token of tokens) {
      if (identifiers.split(/\s+/u).includes(token)) {
        score += 80;
      }
      if (title.includes(token)) {
        score += 40;
      }
      if (aliases.includes(token)) {
        score += 30;
      }
      if (body.includes(token)) {
        score += 10;
      }
    }
    return score;
  };

  const documentMatchesFilters = (documentRecord, activeFilters) => {
    const facets = documentRecord.filter_facets || {};
    for (const [field, selected] of activeFilters.entries()) {
      if (!selected.size) {
        continue;
      }
      const documentValues = new Set(values(facets[field]));
      if (![...selected].some((value) => documentValues.has(value))) {
        return false;
      }
    }
    return true;
  };

  const safeResultUrl = (locale, url) => {
    const value = String(url || "");
    return value.startsWith(`/help/${locale}/`) ? value : "";
  };

  const snippetText = (documentRecord, tokens) => {
    const searchable = documentRecord.searchable || {};
    const source = searchable.shortdesc || searchable.body || searchable.title || "";
    const folded = normalize(source);
    const token = tokens.find((candidate) => folded.includes(candidate));
    if (!token) {
      return String(source).slice(0, 220);
    }
    const start = Math.max(0, folded.indexOf(token) - 72);
    const end = Math.min(String(source).length, folded.indexOf(token) + token.length + 148);
    const prefix = start > 0 ? "…" : "";
    const suffix = end < String(source).length ? "…" : "";
    return `${prefix}${String(source).slice(start, end)}${suffix}`;
  };

  const storageKey = (locale) => `${STORAGE_PREFIX}${locale}:recent-query`;

  const readRecentQuery = (locale) => {
    return safeStorageGet(storageKey(locale));
  };

  const writeRecentQuery = (locale, query) => {
    try {
      if (query) {
        safeStorageSet(storageKey(locale), query);
      } else {
        window.localStorage.removeItem(storageKey(locale));
      }
    } catch {
      /* Browser storage may be disabled; search remains usable for this session. */
    }
  };

  const selectedFilters = (root) => {
    const filters = new Map();
    root.querySelectorAll("[data-search-filter]").forEach((checkbox) => {
      if (!(checkbox instanceof HTMLInputElement) || !checkbox.checked) {
        return;
      }
      const field = checkbox.dataset.searchFilter || "";
      const value = checkbox.value;
      if (!filters.has(field)) {
        filters.set(field, new Set());
      }
      filters.get(field).add(value);
    });
    return filters;
  };

  function updateActiveFilterSummary(root, filters = selectedFilters(root)) {
    const state = root.querySelector("[data-search-active-filters]");
    const summary = root.querySelector("[data-search-active-filters-summary]");
    const panel = root.querySelector("[data-search-advanced-panel]");
    if (!state || !summary) {
      return;
    }
    const count = [...filters.values()].reduce((total, values) => total + values.size, 0);
    const panelIsCollapsed = !panel || panel.hidden;
    state.hidden = !count || !panelIsCollapsed;
    summary.textContent = (root.dataset.labelActiveFilters || "Active filters: {count}")
      .replace("{count}", String(count));
  }

  const setSearchExpanded = (root, expanded) => {
    const panel = root.querySelector("[data-search-advanced-panel]");
    const toggle = root.querySelector("[data-search-advanced-toggle]");
    if (panel) {
      panel.hidden = !expanded;
    }
    if (toggle) {
      toggle.setAttribute("aria-expanded", expanded ? "true" : "false");
    }
    updateActiveFilterSummary(root);
  };

  const updateUrlState = (root, query, filters, index) => {
    const parameters = new URLSearchParams();
    const urlParameters = index.filtering?.url_state?.parameters || {};
    if (query) {
      parameters.set("q", query);
    }
    for (const [field, selected] of filters.entries()) {
      const parameter = urlParameters[field] || field;
      [...selected].sort().forEach((value) => parameters.append(parameter, value));
    }
    const queryString = parameters.toString();
    const nextUrl = `${window.location.pathname}${queryString ? `?${queryString}` : ""}${window.location.hash}`;
    window.history.replaceState(null, "", nextUrl);
  };

  const currentUrlState = (index) => {
    const parameters = new URLSearchParams(window.location.search);
    const urlParameters = index.filtering?.url_state?.parameters || {};
    const fieldByParameter = new Map(Object.entries(urlParameters).map(([field, parameter]) => [parameter, field]));
    const filters = new Map();
    for (const [parameter, value] of parameters.entries()) {
      if (parameter === "q") {
        continue;
      }
      const field = fieldByParameter.get(parameter);
      if (!field) {
        continue;
      }
      if (!filters.has(field)) {
        filters.set(field, new Set());
      }
      filters.get(field).add(value);
    }
    return {
      query: parameters.get("q") || "",
      filters,
    };
  };

  const buildFilters = (root, index, initialFilters) => {
    const container = root.querySelector("[data-search-filters]");
    if (!container) {
      return;
    }
    clearNode(container);
    const fields = index.filtering?.facet_fields || {};
    const counts = index.facet_counts || {};
    const skipped = new Set(["locale", "bpm_version"]);
    for (const [field, definition] of Object.entries(fields)) {
      if (skipped.has(field)) {
        continue;
      }
      const fieldset = document.createElement("fieldset");
      const legend = document.createElement("legend");
      legend.textContent = definition.label || field;
      fieldset.appendChild(legend);
      const valueLabels = definition.value_labels || {};
      for (const value of definition.values || []) {
        const count = counts[field]?.[value] || 0;
        if (!count && !initialFilters.get(field)?.has(value)) {
          continue;
        }
        const label = document.createElement("label");
        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.value = value;
        checkbox.dataset.searchFilter = field;
        checkbox.checked = Boolean(initialFilters.get(field)?.has(value));
        label.appendChild(checkbox);
        appendText(label, ` ${valueLabels[value] || value} (${count})`);
        fieldset.appendChild(label);
      }
      container.appendChild(fieldset);
    }
  };

  const renderResults = (root, locale, documents, tokens) => {
    const results = root.querySelector("[data-search-results]");
    if (!results) {
      return;
    }
    clearNode(results);
    for (const documentRecord of documents) {
      const item = document.createElement("li");
      const article = document.createElement("article");
      const heading = document.createElement("h4");
      const link = document.createElement("a");
      const href = safeResultUrl(locale, documentRecord.url);
      if (href) {
        link.href = href;
      }
      appendMarkedText(link, documentRecord.searchable?.title || documentRecord.topic_id, tokens);
      heading.appendChild(link);

      const metadata = document.createElement("p");
      metadata.className = "bpm-docs-search-result-meta";
      metadata.textContent = [
        documentRecord.guide_id,
        documentRecord.topic_kind,
        ...(documentRecord.filter_facets?.firefox_channel || []),
        ...(documentRecord.filter_facets?.api_area || []),
        ...(documentRecord.filter_facets?.cis_level || []),
      ]
        .filter(Boolean)
        .join(" · ");

      const snippet = document.createElement("p");
      snippet.className = "bpm-docs-search-snippet";
      appendMarkedText(snippet, snippetText(documentRecord, tokens), tokens);

      article.appendChild(heading);
      article.appendChild(metadata);
      article.appendChild(snippet);
      item.appendChild(article);
      results.appendChild(item);
    }
  };

  const runSearch = (root, index, options = {}) => {
    const locale = root.dataset.searchLocale || index.locale || "en";
    const input = root.querySelector("#bpm-docs-search-query");
    const status = root.querySelector("[data-search-status]");
    if (!(input instanceof HTMLInputElement) || !status) {
      return;
    }
    const query = input.value.slice(0, MAX_QUERY_LENGTH).trim();
    const tokens = queryTokens(query);
    const filters = selectedFilters(root);
    updateActiveFilterSummary(root, filters);
    if (!tokens.length && !filters.size) {
      const results = root.querySelector("[data-search-results]");
      if (results) {
        clearNode(results);
      }
      status.textContent = root.dataset.labelReady || "Search ready.";
      if (!options.skipState) {
        writeRecentQuery(locale, "");
        updateUrlState(root, "", filters, index);
      }
      return;
    }
    const ranked = [];
    for (const documentRecord of index.documents || []) {
      if (!documentMatchesFilters(documentRecord, filters)) {
        continue;
      }
      const score = scoreDocument(documentRecord, tokens);
      if (score > 0) {
        ranked.push({ documentRecord, score });
      }
    }
    ranked.sort((left, right) => {
      if (right.score !== left.score) {
        return right.score - left.score;
      }
      return String(left.documentRecord.searchable?.title || "").localeCompare(
        String(right.documentRecord.searchable?.title || ""),
        locale,
      );
    });
    const visible = ranked.slice(0, MAX_RESULTS).map((item) => item.documentRecord);
    renderResults(root, locale, visible, tokens);
    if (!visible.length) {
      status.textContent = root.dataset.labelNoResults || "No results.";
    } else if (visible.length === 1) {
      status.textContent = root.dataset.labelResultSingular || "1 result";
    } else {
      status.textContent = `${visible.length} ${root.dataset.labelResultPlural || "results"}`;
    }
    if (!options.skipState) {
      writeRecentQuery(locale, query);
      updateUrlState(root, query, filters, index);
    }
  };

  const setupSearch = async (root) => {
    const status = root.querySelector("[data-search-status]");
    const input = root.querySelector("#bpm-docs-search-query");
    const submit = root.querySelector("[data-search-submit]");
    const clear = root.querySelector("[data-search-clear]");
    const clearFilters = root.querySelector("[data-search-clear-filters]");
    if (!(input instanceof HTMLInputElement) || !status || !submit || !clear || !clearFilters) {
      return;
    }
    status.textContent = root.dataset.labelLoading || status.textContent;
    let index;
    try {
      const response = await fetch(root.dataset.searchIndexHref || "", { credentials: "same-origin" });
      if (!response.ok) {
        throw new Error("search index unavailable");
      }
      index = await response.json();
    } catch {
      status.textContent = root.dataset.labelUnavailable || "Search unavailable.";
      return;
    }
    const locale = root.dataset.searchLocale || index.locale || "en";
    const state = currentUrlState(index);
    input.value = (state.query || readRecentQuery(locale)).slice(0, MAX_QUERY_LENGTH);
    buildFilters(root, index, state.filters);
    updateActiveFilterSummary(root);
    root.querySelectorAll("[data-search-filter]").forEach((checkbox) => {
      checkbox.addEventListener("change", () => {
        runSearch(root, index);
      });
    });
    input.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        runSearch(root, index);
      }
    });
    submit.addEventListener("click", () => {
      runSearch(root, index);
    });
    clear.addEventListener("click", () => {
      input.value = "";
      root.querySelectorAll("[data-search-filter]").forEach((checkbox) => {
        if (checkbox instanceof HTMLInputElement) {
          checkbox.checked = false;
        }
      });
      runSearch(root, index);
      input.focus();
    });
    clearFilters.addEventListener("click", () => {
      root.querySelectorAll("[data-search-filter]").forEach((checkbox) => {
        if (checkbox instanceof HTMLInputElement) {
          checkbox.checked = false;
        }
      });
      runSearch(root, index);
      root.querySelector("[data-search-advanced-toggle]")?.focus();
    });
    root.querySelector("[data-search-advanced-toggle]")?.addEventListener("click", () => {
      const toggle = root.querySelector("[data-search-advanced-toggle]");
      const expanded = toggle?.getAttribute("aria-expanded") === "true";
      setSearchExpanded(root, !expanded);
    });
    status.textContent = root.dataset.labelReady || "Search ready.";
    if (state.query || state.filters.size) {
      runSearch(root, index, { skipState: true });
    }
  };

  const navigationUrl = (host, href, baseUrl) => {
    if (typeof href !== "string" || !href || href.startsWith("/") || href.includes("\\")) {
      return "";
    }
    const base = new URL(baseUrl, window.location.href);
    const resolved = new URL(href, base);
    const localeRoot = new URL("./", base);
    if (
      resolved.origin !== window.location.origin ||
      !resolved.pathname.startsWith(localeRoot.pathname)
    ) {
      return "";
    }
    return resolved.href;
  };

  const validatedNavigationNodes = (payload, expectedLocale, expectedVersion, baseUrl) => {
    if (
      !payload ||
      payload.schema_version !== 1 ||
      payload.documentation_version !== expectedVersion ||
      payload.locale !== expectedLocale ||
      !payload.root ||
      payload.root.node_id !== "documentation-root" ||
      payload.root.node_type !== "root"
    ) {
      throw new Error("navigation source identity mismatch");
    }
    const seen = new Set();
    const allowedTypes = new Set(["root", "guide", "section", "topic"]);
    const visit = (node, parentType = "") => {
      if (
        !node ||
        typeof node.node_id !== "string" ||
        !node.node_id ||
        !allowedTypes.has(node.node_type) ||
        typeof node.label !== "string" ||
        !node.label ||
        !Array.isArray(node.children) ||
        seen.has(node.node_id)
      ) {
        throw new Error("navigation node is invalid");
      }
      if (
        (node.node_type === "root" && parentType) ||
        (node.node_type === "guide" && parentType !== "root") ||
        (node.node_type === "section" && parentType !== "guide") ||
        (node.node_type === "topic" && !new Set(["guide", "section"]).has(parentType))
      ) {
        throw new Error("navigation hierarchy is invalid");
      }
      if (node.node_type === "section") {
        if (node.href !== null || typeof node.label_key !== "string" || !node.label_key) {
          throw new Error("navigation section is invalid");
        }
      } else if (!navigationUrl(null, node.href, baseUrl)) {
        throw new Error("navigation URL is invalid");
      }
      if (node.node_type === "topic" && node.children.length) {
        throw new Error("navigation topic has children");
      }
      seen.add(node.node_id);
      if (seen.size > 2000) {
        throw new Error("navigation source is too large");
      }
      node.children.forEach((child) => visit(child, node.node_type));
    };
    visit(payload.root);
    if (seen.size !== payload.node_count) {
      throw new Error("navigation node count mismatch");
    }
    return seen;
  };

  const renderNavigationUnavailable = (host) => {
    clearNode(host);
    host.setAttribute("aria-busy", "false");
    const status = document.createElement("p");
    status.className = "bpm-docs-tree-status bpm-docs-tree-status--unavailable";
    status.setAttribute("role", "status");
    status.textContent = host.dataset.labelUnavailable || "";
    const rootLink = document.createElement("a");
    rootLink.href = host.dataset.rootHref || "./";
    rootLink.textContent = host.dataset.labelBackToRoot || "";
    status.appendChild(document.createTextNode(" "));
    status.appendChild(rootLink);
    host.appendChild(status);
  };

  const renderNavigationTree = (host, payload, baseUrl) => {
    const currentNodeId = host.dataset.currentTreeNode || "documentation-root";
    const tree = document.createElement("ol");
    tree.className = "bpm-docs-guide-list bpm-docs-tree";
    tree.setAttribute("role", "tree");
    tree.setAttribute("aria-label", host.dataset.labelTree || "");
    tree.dataset.docsTree = "";
    tree.dataset.treeStorageKey = host.dataset.treeStorageKey || "";
    tree.dataset.labelExpand = host.dataset.labelExpand || "";
    tree.dataset.labelCollapse = host.dataset.labelCollapse || "";
    tree.dataset.labelCurrent = host.dataset.labelCurrent || "";
    tree.dataset.labelParent = host.dataset.labelParent || "";
    tree.dataset.labelBackToRoot = host.dataset.labelBackToRoot || "";
    let groupSequence = 0;

    const renderNode = (node, parentId, level, position, setSize) => {
      const item = document.createElement("li");
      item.className = "bpm-docs-tree-item";
      item.setAttribute("role", "none");
      const row = document.createElement("div");
      row.className = "bpm-docs-tree-row";
      const expandable = node.children.length > 0;
      let group = null;
      let controlId = "";
      if (expandable) {
        groupSequence += 1;
        controlId = `bpm-docs-tree-group-${groupSequence}`;
        const toggle = document.createElement("button");
        toggle.className = "bpm-docs-tree-toggle";
        toggle.type = "button";
        toggle.tabIndex = -1;
        toggle.dataset.treeToggle = "";
        toggle.dataset.treeTarget = controlId;
        toggle.textContent = "+";
        toggle.setAttribute("aria-label", `${host.dataset.labelExpand || ""} ${node.label}`.trim());
        row.appendChild(toggle);
      } else {
        const spacer = document.createElement("span");
        spacer.className = "bpm-docs-tree-spacer";
        spacer.setAttribute("aria-hidden", "true");
        row.appendChild(spacer);
      }

      const treeItem = node.node_type === "section" ? document.createElement("span") : document.createElement("a");
      treeItem.className = "bpm-docs-tree-link";
      if (node.node_type === "section") {
        treeItem.classList.add("bpm-docs-tree-section");
        treeItem.dataset.treeBranch = "";
        treeItem.dataset.sectionLabelKey = node.label_key;
      } else {
        treeItem.href = navigationUrl(host, node.href, baseUrl);
      }
      if (node.anchor) {
        treeItem.dataset.treeAnchor = node.anchor;
      }
      treeItem.setAttribute("role", "treeitem");
      treeItem.dataset.treeNode = node.node_id;
      treeItem.dataset.treeParent = parentId;
      treeItem.setAttribute("aria-level", String(level));
      treeItem.setAttribute("aria-posinset", String(position));
      treeItem.setAttribute("aria-setsize", String(setSize));
      treeItem.tabIndex = node.node_id === currentNodeId ? 0 : -1;
      if (expandable) {
        treeItem.setAttribute("aria-expanded", "false");
        treeItem.setAttribute("aria-controls", controlId);
      }
      if (node.node_id === currentNodeId) {
        treeItem.setAttribute("aria-current", "page");
      }
      treeItem.textContent = node.label;
      row.appendChild(treeItem);
      item.appendChild(row);

      if (expandable) {
        group = document.createElement("ol");
        group.id = controlId;
        group.className = "bpm-docs-tree-group";
        group.setAttribute("role", "group");
        group.hidden = true;
        node.children.forEach((child, index) => {
          group.appendChild(renderNode(child, node.node_id, level + 1, index + 1, node.children.length));
        });
        item.appendChild(group);
      }
      return item;
    };

    tree.appendChild(renderNode(payload.root, "", 1, 1, 1));
    clearNode(host);
    host.appendChild(tree);
    host.setAttribute("aria-busy", "false");
    setupNavigationTree(tree);
  };

  const setupNavigationHost = async (host) => {
    const sourceHref = host.dataset.navigationHref || "";
    const expectedLocale = host.dataset.navigationLocale || "";
    const expectedVersion = host.dataset.navigationVersion || "";
    try {
      const sourceUrl = new URL(sourceHref, window.location.href);
      if (sourceUrl.origin !== window.location.origin) {
        throw new Error("navigation source must be same-origin");
      }
      const response = await fetch(sourceUrl.href, { credentials: "same-origin" });
      if (!response.ok) {
        throw new Error("navigation source unavailable");
      }
      const payload = await response.json();
      validatedNavigationNodes(payload, expectedLocale, expectedVersion, response.url || sourceUrl.href);
      renderNavigationTree(host, payload, response.url || sourceUrl.href);
    } catch {
      renderNavigationUnavailable(host);
    }
  };

  const treeItems = (tree) => [...tree.querySelectorAll('[role="treeitem"]')];

  const visibleTreeItems = (tree) =>
    treeItems(tree).filter((item) => !item.closest("[hidden]"));

  const expandedNodeIds = (tree) =>
    treeItems(tree)
      .filter((item) => item.getAttribute("aria-expanded") === "true")
      .map((item) => item.dataset.treeNode)
      .filter(Boolean);

  const writeExpandedTreeState = (tree) => {
    const key = tree.dataset.treeStorageKey;
    if (key) {
      safeStorageSet(key, JSON.stringify(expandedNodeIds(tree)));
    }
  };

  const readExpandedTreeState = (tree) => {
    const key = tree.dataset.treeStorageKey;
    if (!key) {
      return new Set();
    }
    try {
      const value = JSON.parse(safeStorageGet(key, "[]"));
      return new Set(Array.isArray(value) ? value.map(String) : []);
    } catch {
      return new Set();
    }
  };

  const toggleForItem = (tree, item) => {
    const controls = item.getAttribute("aria-controls");
    if (!controls) {
      return null;
    }
    return tree.querySelector(`[data-tree-target="${selectorEscape(controls)}"]`);
  };

  const setTreeItemExpanded = (tree, item, expanded, persist = true) => {
    const controls = item.getAttribute("aria-controls");
    if (!controls || !item.hasAttribute("aria-expanded")) {
      return;
    }
    if (!expanded && requiredExpandedTreeNodes(tree).has(item.dataset.treeNode || "")) {
      return;
    }
    const group = document.getElementById(controls);
    if (group) {
      group.hidden = !expanded;
    }
    item.setAttribute("aria-expanded", expanded ? "true" : "false");
    const toggle = toggleForItem(tree, item);
    if (toggle) {
      toggle.textContent = expanded ? "-" : "+";
      const action = expanded ? tree.dataset.labelCollapse : tree.dataset.labelExpand;
      toggle.setAttribute("aria-label", `${action || ""} ${item.textContent || ""}`.trim());
    }
    if (persist) {
      writeExpandedTreeState(tree);
    }
  };

  const requiredExpandedTreeNodes = (tree) => {
    const required = new Set(["documentation-root"]);
    const current = tree.querySelector('[role="treeitem"][aria-current="page"]');
    let cursor = current;
    while (cursor) {
      const parentId = cursor.dataset.treeParent;
      if (!parentId) {
        break;
      }
      required.add(parentId);
      cursor = tree.querySelector(`[role="treeitem"][data-tree-node="${selectorEscape(parentId)}"]`);
    }
    return required;
  };

  const scrollTreeItemIntoView = (tree, item) => {
    const container = tree.closest(".bpm-docs-sidebar");
    if (!container || container.scrollHeight <= container.clientHeight) {
      return;
    }
    const containerRect = container.getBoundingClientRect();
    const itemRect = item.getBoundingClientRect();
    const style = window.getComputedStyle(container);
    const topEdge = containerRect.top + (Number.parseFloat(style.paddingTop) || 0);
    const bottomEdge = containerRect.bottom - (Number.parseFloat(style.paddingBottom) || 0);
    if (itemRect.top < topEdge) {
      container.scrollTop += itemRect.top - topEdge;
    } else if (itemRect.bottom > bottomEdge) {
      container.scrollTop += itemRect.bottom - bottomEdge;
    }
  };

  const focusTreeItem = (tree, item) => {
    if (!item) {
      return;
    }
    treeItems(tree).forEach((candidate) => {
      candidate.setAttribute("tabindex", candidate === item ? "0" : "-1");
    });
    item.focus({ preventScroll: true });
    scrollTreeItemIntoView(tree, item);
  };

  const setCurrentTreeItem = (tree, item) => {
    treeItems(tree).forEach((candidate) => {
      if (candidate === item) {
        candidate.setAttribute("aria-current", "page");
      } else {
        candidate.removeAttribute("aria-current");
      }
    });
    focusTreeItem(tree, item);
  };

  const guideItemForHash = (tree) => {
    const anchor = decodeURIComponent(window.location.hash || "").replace(/^#/, "");
    if (!anchor) {
      return null;
    }
    return tree.querySelector(`[role="treeitem"][data-tree-anchor="${selectorEscape(anchor)}"]`);
  };

  const activateHashGuide = (tree) => {
    const guide = guideItemForHash(tree);
    if (!guide) {
      return false;
    }
    setTreeItemExpanded(tree, guide, true, false);
    setCurrentTreeItem(tree, guide);
    return true;
  };

  const focusRelativeTreeItem = (tree, item, offset) => {
    const visible = visibleTreeItems(tree);
    const index = visible.indexOf(item);
    if (index < 0) {
      return;
    }
    focusTreeItem(tree, visible[Math.min(Math.max(index + offset, 0), visible.length - 1)]);
  };

  const firstChildTreeItem = (tree, item) => {
    const controls = item.getAttribute("aria-controls");
    const group = controls ? document.getElementById(controls) : null;
    return group && !group.hidden ? group.querySelector('[role="treeitem"]') : null;
  };

  const parentTreeItem = (tree, item) => {
    const parentId = item.dataset.treeParent;
    return parentId
      ? tree.querySelector(`[role="treeitem"][data-tree-node="${selectorEscape(parentId)}"]`)
      : null;
  };

  const setupNavigationTree = (tree) => {
    const savedExpanded = readExpandedTreeState(tree);
    const requiredExpanded = requiredExpandedTreeNodes(tree);
    treeItems(tree).forEach((item) => {
      if (!item.hasAttribute("aria-expanded")) {
        return;
      }
      const nodeId = item.dataset.treeNode || "";
      setTreeItemExpanded(tree, item, requiredExpanded.has(nodeId) || savedExpanded.has(nodeId), false);
    });

    const current = tree.querySelector('[role="treeitem"][aria-current="page"]');
    focusTreeItem(tree, current || tree.querySelector('[role="treeitem"]'));
    activateHashGuide(tree);

    tree.querySelectorAll("[data-tree-toggle]").forEach((toggle) => {
      toggle.addEventListener("click", () => {
        const target = toggle.dataset.treeTarget || "";
        const item = tree.querySelector(`[role="treeitem"][aria-controls="${selectorEscape(target)}"]`);
        if (item) {
          setTreeItemExpanded(tree, item, item.getAttribute("aria-expanded") !== "true");
        }
      });
    });
    tree.querySelectorAll("[data-tree-branch]").forEach((branch) => {
      branch.addEventListener("click", () => {
        focusTreeItem(tree, branch);
        setTreeItemExpanded(tree, branch, branch.getAttribute("aria-expanded") !== "true");
      });
    });

    tree.addEventListener("keydown", (event) => {
      const item = event.target;
      if (!(item instanceof HTMLElement) || item.getAttribute("role") !== "treeitem") {
        return;
      }
      if (event.key === "ArrowDown") {
        event.preventDefault();
        focusRelativeTreeItem(tree, item, 1);
      } else if (event.key === "ArrowUp") {
        event.preventDefault();
        focusRelativeTreeItem(tree, item, -1);
      } else if (event.key === "Home") {
        event.preventDefault();
        focusTreeItem(tree, visibleTreeItems(tree)[0]);
      } else if (event.key === "End") {
        event.preventDefault();
        const visible = visibleTreeItems(tree);
        focusTreeItem(tree, visible[visible.length - 1]);
      } else if (event.key === "ArrowRight") {
        const isExpanded = item.getAttribute("aria-expanded") === "true";
        if (item.hasAttribute("aria-expanded") && !isExpanded) {
          event.preventDefault();
          setTreeItemExpanded(tree, item, true);
        } else {
          const child = firstChildTreeItem(tree, item);
          if (child) {
            event.preventDefault();
            focusTreeItem(tree, child);
          }
        }
      } else if (event.key === "ArrowLeft") {
        const isExpanded = item.getAttribute("aria-expanded") === "true";
        if (item.hasAttribute("aria-expanded") && isExpanded) {
          event.preventDefault();
          setTreeItemExpanded(tree, item, false);
        } else {
          const parent = parentTreeItem(tree, item);
          if (parent) {
            event.preventDefault();
            focusTreeItem(tree, parent);
          }
        }
      } else if (event.key === " ") {
        if (item.hasAttribute("aria-expanded")) {
          event.preventDefault();
          setTreeItemExpanded(tree, item, item.getAttribute("aria-expanded") !== "true");
        }
      } else if (event.key === "Enter" && item.hasAttribute("data-tree-branch")) {
        event.preventDefault();
        setTreeItemExpanded(tree, item, item.getAttribute("aria-expanded") !== "true");
      }
    });

    window.addEventListener("hashchange", () => {
      activateHashGuide(tree);
    });
  };

  setupThemeMode();
  setupLocaleSelect();

  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(TREE_HOST_SELECTOR).forEach((host) => {
      setupNavigationHost(host);
    });
    document.querySelectorAll(SEARCH_ROOT_SELECTOR).forEach((root) => {
      setupSearch(root);
    });
  });
})();
