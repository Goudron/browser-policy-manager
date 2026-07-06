(() => {
  "use strict";

  const MAX_QUERY_LENGTH = 256;
  const MAX_RESULTS = 50;
  const SEARCH_ROOT_SELECTOR = ".bpm-docs-search";
  const STORAGE_PREFIX = "bpm-docs-search:";

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
    try {
      return window.localStorage.getItem(storageKey(locale)) || "";
    } catch {
      return "";
    }
  };

  const writeRecentQuery = (locale, query) => {
    try {
      if (query) {
        window.localStorage.setItem(storageKey(locale), query);
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
        appendText(label, ` ${value} (${count})`);
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
    if (!(input instanceof HTMLInputElement) || !status || !submit || !clear) {
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
    root.querySelectorAll("[data-search-filter]").forEach((checkbox) => {
      checkbox.addEventListener("change", () => runSearch(root, index));
    });
    input.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        runSearch(root, index);
      }
    });
    submit.addEventListener("click", () => runSearch(root, index));
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
    status.textContent = root.dataset.labelReady || "Search ready.";
    if (state.query || state.filters.size) {
      runSearch(root, index, { skipState: true });
    }
  };

  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(SEARCH_ROOT_SELECTOR).forEach((root) => {
      setupSearch(root);
    });
  });
})();
