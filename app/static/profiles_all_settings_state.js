(() => {
    const DEFAULT_FILTER = "all";
    const DEFAULT_CATEGORY = "all";
    const DEFAULT_MODE = "review";
    const VALID_MODES = new Set(["review", "configured", "catalog"]);

    function normalizeText(value, fallback = "") {
        const normalized = String(value || "").trim();
        return normalized || fallback;
    }

    function defaultEntryKey(entry) {
        return entry ? `${entry.kind || ""}:${entry.id || ""}` : "";
    }

    function normalizeMode(mode) {
        const normalized = normalizeText(mode, DEFAULT_MODE);
        return VALID_MODES.has(normalized) ? normalized : DEFAULT_MODE;
    }

    function uniqueList(values) {
        return Array.from(new Set(
            (Array.isArray(values) ? values : [])
                .map((value) => normalizeText(value))
                .filter(Boolean),
        ));
    }

    function copyCounts(counts) {
        return {
            total: counts.total || 0,
            mode: counts.mode || 0,
            visible: counts.visible || 0,
            category: counts.category || 0,
            configured: counts.configured || 0,
            policies: counts.policies || 0,
            preferences: counts.preferences || 0,
            filters: { ...(counts.filters || {}) },
        };
    }

    function create(initialState = {}) {
        const state = {
            activeCategory: normalizeText(initialState.activeCategory, DEFAULT_CATEGORY),
            activeMode: normalizeMode(initialState.activeMode),
            activeFilter: normalizeText(initialState.activeFilter, DEFAULT_FILTER),
            searchQuery: normalizeText(initialState.searchQuery),
            selectedEntryKey: normalizeText(initialState.selectedEntryKey),
            focusedTarget: normalizeText(initialState.focusedTarget),
            expandedGroups: new Set(uniqueList(initialState.expandedGroups)),
            entries: [],
            modeEntries: [],
            categoryEntries: [],
            visibleEntries: [],
            counts: copyCounts({}),
        };

        function getSnapshot() {
            return {
                activeCategory: state.activeCategory,
                activeMode: state.activeMode,
                activeFilter: state.activeFilter,
                searchQuery: state.searchQuery,
                selectedEntryKey: state.selectedEntryKey,
                focusedTarget: state.focusedTarget,
                expandedGroups: Array.from(state.expandedGroups),
                counts: copyCounts(state.counts),
            };
        }

        function setActiveCategory(categoryId) {
            state.activeCategory = normalizeText(categoryId, DEFAULT_CATEGORY);
            return getSnapshot();
        }

        function setActiveMode(mode) {
            state.activeMode = normalizeMode(mode);
            return getSnapshot();
        }

        function setActiveFilter(filterValue) {
            state.activeFilter = normalizeText(filterValue, DEFAULT_FILTER);
            return getSnapshot();
        }

        function setSearchQuery(query) {
            state.searchQuery = normalizeText(query);
            return getSnapshot();
        }

        function setFocusedTarget(target) {
            state.focusedTarget = normalizeText(target);
            return getSnapshot();
        }

        function setSelectedEntryKey(entryKey, metadata = {}) {
            state.selectedEntryKey = normalizeText(entryKey);
            if (metadata.updateCategory && metadata.categoryId) {
                state.activeCategory = normalizeText(metadata.categoryId, state.activeCategory);
            }
            if (metadata.target) {
                state.focusedTarget = normalizeText(metadata.target);
            }
            return getSnapshot();
        }

        function setExpanded(groupId, expanded) {
            const normalizedGroupId = normalizeText(groupId);
            if (!normalizedGroupId) return getSnapshot();
            if (expanded) {
                state.expandedGroups.add(normalizedGroupId);
            } else {
                state.expandedGroups.delete(normalizedGroupId);
            }
            return getSnapshot();
        }

        function toggleExpanded(groupId) {
            const normalizedGroupId = normalizeText(groupId);
            if (!normalizedGroupId) return getSnapshot();
            return setExpanded(normalizedGroupId, !state.expandedGroups.has(normalizedGroupId));
        }

        function buildCounts(entries, modeEntries, visibleEntries, filterValues, matchesFilter) {
            const filters = {};
            uniqueList(filterValues).forEach((filterValue) => {
                filters[filterValue] = visibleEntries.categoryEntries.filter((entry) => matchesFilter(entry, filterValue)).length;
            });

            return {
                total: entries.length,
                mode: modeEntries.length,
                category: visibleEntries.categoryEntries.length,
                visible: visibleEntries.filteredEntries.length,
                configured: entries.filter((entry) => entry.configured).length,
                policies: entries.filter((entry) => entry.kind === "policy").length,
                preferences: entries.filter((entry) => entry.kind === "preference").length,
                filters,
            };
        }

        function updateEntries(entries = [], options = {}) {
            const nextEntries = Array.isArray(entries) ? entries : [];
            const matchesFilter = typeof options.matchesFilter === "function"
                ? options.matchesFilter
                : () => true;
            const matchesMode = typeof options.matchesMode === "function"
                ? options.matchesMode
                : () => true;
            const matchesCategory = typeof options.matchesCategory === "function"
                ? options.matchesCategory
                : () => true;
            const makeEntryKey = typeof options.entryKey === "function"
                ? options.entryKey
                : defaultEntryKey;
            const entryKeys = new Set(nextEntries.map((entry) => makeEntryKey(entry)));
            const nextModeEntries = nextEntries.filter((entry) => matchesMode(entry, state.activeMode));
            const nextCategoryEntries = nextModeEntries.filter((entry) =>
                matchesCategory(entry, state.activeCategory, state.activeMode)
            );
            const nextVisibleEntries = nextCategoryEntries.filter((entry) => matchesFilter(entry, state.activeFilter));
            const selectedEntry = nextEntries.find((entry) => makeEntryKey(entry) === state.selectedEntryKey) || null;
            const selectedVisible = selectedEntry && nextVisibleEntries.some((entry) => makeEntryKey(entry) === state.selectedEntryKey);

            if (!state.selectedEntryKey || !entryKeys.has(state.selectedEntryKey) || !selectedVisible) {
                const fallbackEntry = nextVisibleEntries.find((entry) => entry.configured)
                    || nextVisibleEntries[0]
                    || nextModeEntries[0]
                    || nextEntries.find((entry) => entry.configured)
                    || nextEntries[0]
                    || null;
                state.selectedEntryKey = fallbackEntry ? makeEntryKey(fallbackEntry) : "";
                const fallbackVisible = fallbackEntry
                    && nextVisibleEntries.some((entry) => makeEntryKey(entry) === makeEntryKey(fallbackEntry));
                if (fallbackEntry?.categoryId && fallbackVisible && state.activeCategory !== DEFAULT_CATEGORY) {
                    state.activeCategory = normalizeText(fallbackEntry.categoryId, state.activeCategory);
                }
                if (fallbackEntry?.target) {
                    state.focusedTarget = normalizeText(fallbackEntry.target);
                }
            }

            state.entries = nextEntries;
            state.modeEntries = nextModeEntries;
            state.categoryEntries = nextCategoryEntries;
            state.visibleEntries = nextVisibleEntries;
            state.counts = buildCounts(
                state.entries,
                state.modeEntries,
                {
                    categoryEntries: state.categoryEntries,
                    filteredEntries: state.visibleEntries,
                },
                options.filterValues,
                matchesFilter,
            );

            return getSnapshot();
        }

        function getEntries() {
            return state.entries.slice();
        }

        function getVisibleEntries() {
            return state.visibleEntries.slice();
        }

        function getCategoryEntries() {
            return state.categoryEntries.slice();
        }

        function getModeEntries() {
            return state.modeEntries.slice();
        }

        function getSelectedEntry(entries = state.entries, entryKey = defaultEntryKey) {
            return (Array.isArray(entries) ? entries : [])
                .find((entry) => entryKey(entry) === state.selectedEntryKey) || null;
        }

        return {
            getSnapshot,
            setActiveCategory,
            setActiveMode,
            setActiveFilter,
            setSearchQuery,
            setFocusedTarget,
            setSelectedEntryKey,
            setExpanded,
            toggleExpanded,
            updateEntries,
            getEntries,
            getModeEntries,
            getCategoryEntries,
            getVisibleEntries,
            getSelectedEntry,
        };
    }

    window.BPMProfilesAllSettingsState = { create };
})();
