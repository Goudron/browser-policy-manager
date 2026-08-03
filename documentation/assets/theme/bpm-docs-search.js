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

  const unique = (items) => [...new Set(items.filter(Boolean))];

  const isCjk = (character) => {
    const codepoint = character.codePointAt(0) || 0;
    return (
      (codepoint >= 0x3400 && codepoint <= 0x4dbf) ||
      (codepoint >= 0x4e00 && codepoint <= 0x9fff) ||
      (codepoint >= 0xf900 && codepoint <= 0xfaff)
    );
  };

  const isLatin = (character) => /\p{Script=Latin}/u.test(character);

  const casefold = (value) =>
    String(value || "")
      .normalize("NFKC")
      .toLocaleLowerCase("und")
      .replace(/ß/g, "ss")
      .replace(/ς/g, "σ");

  const stripLatinDiacritics = (value) => {
    let result = "";
    let previousBaseWasLatin = false;
    for (const character of String(value || "").normalize("NFD")) {
      if (/\p{Mark}/u.test(character)) {
        if (!previousBaseWasLatin) {
          result += character;
        }
        continue;
      }
      result += character;
      previousBaseWasLatin = isLatin(character);
    }
    return result.normalize("NFC");
  };

  const normalizedText = (value, normalization = {}) => {
    let normalized = casefold(value);
    if (normalization.strip_diacritics) {
      normalized = stripLatinDiacritics(normalized);
    }
    return normalized;
  };

  const cjkExpansions = (token) => {
    const run = [...token].filter(isCjk).join("");
    if (!run) {
      return [];
    }
    return [
      run,
      ...[...run],
      ...[...run].slice(0, -1).map((character, index) => character + [...run][index + 1]),
    ];
  };

  const searchTokens = (value, normalization = {}) => {
    const tokens = [];
    const compoundParts = [];
    const expression = /\/[^\s"'<>]+|[\p{Letter}\p{Number}]+(?:[-._:/][\p{Letter}\p{Number}]+)+|[\p{Letter}\p{Number}]+/gu;
    const normalized = normalizedText(value, normalization);
    for (const match of normalized.matchAll(expression)) {
      const token = match[0].replace(/^[.,;!?()[\]{}<>"']+|[.,;!?()[\]{}<>"']+$/gu, "");
      if (token) {
        tokens.push(token, ...cjkExpansions(token));
        if (/^[\p{Letter}\p{Number}]+$/u.test(token) && ![...token].some(isCjk)) {
          compoundParts.push(token);
        }
      }
    }
    tokens.push(
      ...compoundParts.slice(0, -1).map((part, index) => `${part}-${compoundParts[index + 1]}`),
    );
    return unique(tokens);
  };

  const queryTokens = (query, index) => searchTokens(query, index.normalization).slice(0, 24);

  const normalizedComparableText = (value, normalization = {}) =>
    normalizedText(value, normalization)
      .replace(/[^\p{Letter}\p{Number}._:/-]+/gu, " ")
      .trim();

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

  const appendMarkedText = (parent, text, tokens, normalization) => {
    const source = String(text || "");
    const folded = normalizedComparableText(source, normalization);
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

  const tokenSet = (values) => new Set(Array.isArray(values) ? values : []);

  const queryAliasIds = (tokens, index) => {
    const queryTokenSet = new Set(tokens);
    return (index.normalization?.alias_groups || [])
      .filter((group) => {
        return (group.terms || []).some((term) => {
          const termTokens = searchTokens(term, index.normalization);
          return termTokens.length && termTokens.every((token) => queryTokenSet.has(token));
        });
      })
      .map((group) => group.alias_id)
      .sort();
  };

  const maxTypoDistance = (token, ranking) => {
    const tolerance = ranking.typo_tolerance || {};
    if (token.length < tolerance.min_token_length || token.length > tolerance.max_token_length) {
      return 0;
    }
    const rule = (tolerance.max_distance_by_length || []).find(
      (candidate) => token.length >= candidate.min_length && token.length <= candidate.max_length,
    );
    return rule ? rule.max_distance : 0;
  };

  const typoExcluded = (token, ranking) =>
    (ranking.typo_tolerance?.excluded_token_patterns || []).some((pattern) =>
      new RegExp(pattern, "iu").test(token),
    );

  const boundedLevenshtein = (left, right, limit) => {
    if (Math.abs(left.length - right.length) > limit) {
      return null;
    }
    let previous = Array.from({ length: right.length + 1 }, (_value, index) => index);
    for (let leftIndex = 1; leftIndex <= left.length; leftIndex += 1) {
      const current = [leftIndex];
      let rowMinimum = leftIndex;
      for (let rightIndex = 1; rightIndex <= right.length; rightIndex += 1) {
        const substitution = previous[rightIndex - 1] + (left[leftIndex - 1] !== right[rightIndex - 1]);
        const insertion = current[rightIndex - 1] + 1;
        const deletion = previous[rightIndex] + 1;
        const value = Math.min(substitution, insertion, deletion);
        current.push(value);
        rowMinimum = Math.min(rowMinimum, value);
      }
      if (rowMinimum > limit) {
        return null;
      }
      previous = current;
    }
    return previous.at(-1) <= limit ? previous.at(-1) : null;
  };

  const boundedTypoMatches = (tokens, fields, ranking) => {
    const exactPool = new Set(Object.values(fields).flat());
    return tokens.flatMap((token) => {
      if (exactPool.has(token) || typoExcluded(token, ranking)) {
        return [];
      }
      const limit = maxTypoDistance(token, ranking);
      if (!limit) {
        return [];
      }
      const matches = [];
      for (const field of ranking.typo_tolerance?.fields || []) {
        for (const candidate of fields[field] || []) {
          if (candidate === token || typoExcluded(candidate, ranking)) {
            continue;
          }
          const distance = boundedLevenshtein(token, candidate, limit);
          if (distance !== null) {
            matches.push({ field, candidate, distance });
          }
        }
      }
      matches.sort((left, right) =>
        left.distance - right.distance || left.field.localeCompare(right.field) || left.candidate.localeCompare(right.candidate),
      );
      return matches.length ? [matches[0]] : [];
    });
  };

  const scoreDocument = (documentRecord, tokens, index) => {
    if (!tokens.length) {
      return { score: 1, breakdown: {} };
    }
    const ranking = index.ranking || {};
    const weights = ranking.weights || {};
    const fields = documentRecord.normalized?.fields || {};
    const unmatchedTechnicalIdentifier = tokens.some(
      (token) => typoExcluded(token, ranking) && !tokenSet(fields.identifiers).has(token),
    );
    if (unmatchedTechnicalIdentifier) {
      return { score: 0, breakdown: {} };
    }
    const queryTokenSet = new Set(tokens);
    const meaningfulQueryTokens = [...queryTokenSet].filter(
      (token) => token.length > 1 || !isCjk(token),
    );
    const matches = (field) => meaningfulQueryTokens.filter((token) => tokenSet(fields[field]).has(token));
    const documentAliasIds = new Set(documentRecord.normalized?.alias_ids || []);
    const aliasIds = queryAliasIds(tokens, index).filter((aliasId) => documentAliasIds.has(aliasId));
    const directAliasIds = aliasIds.filter(
      (aliasId) => documentRecord.normalized?.alias_match_sources?.[aliasId]?.includes("target_topic"),
    );
    const exactIdentifiers = matches("identifiers");
    const title = matches("title");
    const aliases = matches("aliases");
    const headings = matches("headings");
    const body = matches("body");
    const typos = boundedTypoMatches(tokens, fields, ranking);
    const breakdown = {
      exact_identifier: exactIdentifiers.length * (weights.exact_identifier || 0),
      title: title.length * (weights.title || 0),
      alias: (aliases.length + aliasIds.length + directAliasIds.length) * (weights.alias || 0),
      heading: headings.length * (weights.heading || 0),
      body: body.length * (weights.body || 0),
      bounded_typo: typos.length * (weights.bounded_typo || 0),
      recency: weights.recency || 0,
    };
    return { score: Object.values(breakdown).reduce((total, value) => total + value, 0), breakdown };
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
    const origin = window.location?.origin || "https://bpm.invalid";
    try {
      const resolved = new URL(String(url || ""), origin);
      const localeRoot = `/help/${locale}/`;
      if (resolved.origin !== origin || !resolved.pathname.startsWith(localeRoot)) {
        return "";
      }
      return `${resolved.pathname}${resolved.search}${resolved.hash}`;
    } catch {
      return "";
    }
  };

  const snippetText = (documentRecord, tokens, normalization) => {
    const searchable = documentRecord.searchable || {};
    const source = searchable.shortdesc || searchable.body || searchable.title || "";
    const folded = normalizedComparableText(source, normalization);
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

  const filterEntries = (filters) => {
    if (filters instanceof Map) {
      return [...filters.entries()];
    }
    return Object.entries(filters || {});
  };

  const filterValues = (value) => (value instanceof Set ? [...value] : values(value));

  const normalizeFilters = (index, filters) => {
    const normalized = new Map();
    const definitions = index.filtering?.facet_fields || {};
    for (const [field, selected] of filterEntries(filters)) {
      const allowed = new Set(values(definitions[field]?.values));
      if (!allowed.size) {
        continue;
      }
      const accepted = new Set(filterValues(selected).filter((value) => allowed.has(value)));
      if (accepted.size) {
        normalized.set(field, accepted);
      }
    }
    return normalized;
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

  const updateUrlState = (root, state, index) => {
    const queryString = BrowserSearchAdapter.serialize(index, state);
    const nextUrl = `${window.location.pathname}${queryString ? `?${queryString}` : ""}${window.location.hash}`;
    window.history.replaceState(null, "", nextUrl);
  };

  const currentUrlState = (index, recentQuery = "") =>
    BrowserSearchAdapter.hydrate(index, window.location.search, recentQuery);

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

  const renderResults = (root, locale, documents, tokens, index) => {
    const results = root.querySelector("[data-search-results]");
    if (!results) {
      return;
    }
    clearNode(results);
    for (const documentRecord of documents) {
      const item = document.createElement("li");
      const article = document.createElement("article");
      const heading = document.createElement("h4");
      const href = safeResultUrl(locale, documentRecord.url);
      const title = href ? document.createElement("a") : document.createElement("span");
      if (href) {
        title.href = href;
      }
      appendMarkedText(
        title,
        documentRecord.searchable?.title || documentRecord.topic_id,
        tokens,
        index.normalization,
      );
      heading.appendChild(title);

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
      appendMarkedText(snippet, snippetText(documentRecord, tokens, index.normalization), tokens, index.normalization);

      article.appendChild(heading);
      article.appendChild(metadata);
      article.appendChild(snippet);
      item.appendChild(article);
      results.appendChild(item);
    }
  };

  const compareRankedDocuments = (left, right, locale) => {
    if (right.score !== left.score) {
      return right.score - left.score;
    }
    for (const field of ["exact_identifier", "title", "alias"]) {
      if (right.breakdown[field] !== left.breakdown[field]) {
        return right.breakdown[field] - left.breakdown[field];
      }
    }
    return (
      String(left.documentRecord.guide_id || "").localeCompare(String(right.documentRecord.guide_id || ""), locale)
      || String(left.documentRecord.topic_id || "").localeCompare(String(right.documentRecord.topic_id || ""), locale)
    );
  };

  const rankDocuments = (index, query, documents = index.documents || []) => {
    const tokens = queryTokens(query, index);
    return documents
      .map((documentRecord) => ({ documentRecord, ...scoreDocument(documentRecord, tokens, index) }))
      .filter((result) => result.score > 0)
      .sort((left, right) => compareRankedDocuments(left, right, index.locale || "en"));
  };

  const BrowserSearchAdapter = Object.freeze({
    contractId: "bpm-doc-search-browser-adapter-0.9.3",
    schemaVersion: 1,
    hydrate(index, search, recentQuery = "") {
      const parameters = new URLSearchParams(String(search || "").replace(/^\?/u, ""));
      const urlParameters = index.filtering?.url_state?.parameters || {};
      const fieldByParameter = new Map(
        Object.entries(urlParameters).map(([field, parameter]) => [parameter, field]),
      );
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
        query: (parameters.has("q") ? parameters.get("q") : recentQuery || "")
          .slice(0, MAX_QUERY_LENGTH)
          .trim(),
        filters: normalizeFilters(index, filters),
      };
    },
    serialize(index, state) {
      const parameters = new URLSearchParams();
      const query = String(state?.query || "").slice(0, MAX_QUERY_LENGTH).trim();
      const filters = normalizeFilters(index, state?.filters);
      const urlParameters = index.filtering?.url_state?.parameters || {};
      if (query) {
        parameters.set("q", query);
      }
      for (const [field, selected] of filters.entries()) {
        const parameter = urlParameters[field] || field;
        [...selected].sort().forEach((value) => parameters.append(parameter, value));
      }
      return parameters.toString();
    },
    query(index, state) {
      const query = String(state?.query || "").slice(0, MAX_QUERY_LENGTH).trim();
      const filters = normalizeFilters(index, state?.filters);
      const tokens = queryTokens(query, index);
      if (!tokens.length && !filters.size) {
        return {
          query,
          filters,
          tokens,
          documents: [],
          rankingEvidence: [],
          facetCounts: index.facet_counts || {},
          resultCount: 0,
          statusKind: "ready",
        };
      }
      const ranked = rankDocuments(
        index,
        query,
        (index.documents || []).filter((documentRecord) => documentMatchesFilters(documentRecord, filters)),
      );
      const visible = ranked.slice(0, MAX_RESULTS);
      const documents = visible.map((item) => item.documentRecord);
      return {
        query,
        filters,
        tokens,
        documents,
        rankingEvidence: visible.map((item) => ({
          topic_id: item.documentRecord.topic_id,
          document_id: item.documentRecord.document_id || "",
          score: item.score,
          score_breakdown: item.breakdown,
          matched_fields: Object.entries(item.breakdown)
            .filter(([field, value]) => field !== "recency" && value > 0)
            .map(([field]) => field),
          identifiers: values(item.documentRecord.searchable?.identifiers),
          filter_facets: item.documentRecord.filter_facets || {},
        })),
        facetCounts: index.facet_counts || {},
        resultCount: documents.length,
        statusKind: documents.length === 0
          ? "no-results"
          : documents.length === 1
            ? "result-singular"
            : "result-plural",
      };
    },
    safeResultUrl,
  });

  window.BpmDocsSearchRanking = Object.freeze({
    queryTokens,
    rankDocuments,
  });
  window.BpmDocsSearchAdapter = BrowserSearchAdapter;

  const runSearch = (root, index, options = {}) => {
    const locale = root.dataset.searchLocale || index.locale || "en";
    const input = root.querySelector("#bpm-docs-search-query");
    const status = root.querySelector("[data-search-status]");
    if (!(input instanceof HTMLInputElement) || !status) {
      return;
    }
    const result = BrowserSearchAdapter.query(index, {
      query: input.value,
      filters: selectedFilters(root),
    });
    updateActiveFilterSummary(root, result.filters);
    if (result.statusKind === "ready") {
      const results = root.querySelector("[data-search-results]");
      if (results) {
        clearNode(results);
      }
      status.textContent = root.dataset.labelReady || "Search ready.";
      if (!options.skipState) {
        writeRecentQuery(locale, "");
        updateUrlState(root, result, index);
      }
      return;
    }
    renderResults(root, locale, result.documents, result.tokens, index);
    if (result.statusKind === "no-results") {
      status.textContent = root.dataset.labelNoResults || "No results.";
    } else if (result.statusKind === "result-singular") {
      status.textContent = root.dataset.labelResultSingular || "1 result";
    } else {
      status.textContent = `${result.resultCount} ${root.dataset.labelResultPlural || "results"}`;
    }
    if (!options.skipState) {
      writeRecentQuery(locale, result.query);
      updateUrlState(root, result, index);
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
    const state = currentUrlState(index, readRecentQuery(locale));
    buildFilters(root, index, state.filters);
    input.value = state.query;
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
    root.addEventListener("keydown", (event) => {
      const panel = root.querySelector("[data-search-advanced-panel]");
      if (event.key !== "Escape" || !panel || panel.hidden || !root.contains(document.activeElement)) {
        return;
      }
      event.preventDefault();
      setSearchExpanded(root, false);
      root.querySelector("[data-search-advanced-toggle]")?.focus();
    });
    window.addEventListener("popstate", () => {
      const restored = currentUrlState(index);
      input.value = restored.query;
      root.querySelectorAll("[data-search-filter]").forEach((checkbox) => {
        if (checkbox instanceof HTMLInputElement) {
          checkbox.checked = Boolean(restored.filters.get(checkbox.dataset.searchFilter || "")?.has(checkbox.value));
        }
      });
      runSearch(root, index, { skipState: true });
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
