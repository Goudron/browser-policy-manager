(() => {
    const WIZARD_REVIEW_FILTERS = [
        { value: "changed", key: "profiles.wizard_review_filter_changed", fallback: "Changed" },
        { value: "attention", key: "profiles.wizard_review_filter_attention", fallback: "Needs attention" },
        { value: "settings", key: "profiles.wizard_review_filter_settings", fallback: "Outside Guided editor" },
        { value: "all", key: "profiles.wizard_review_filter_all", fallback: "All" },
    ];
    const WIZARD_LONG_LIST_LIMIT = 5;
    const WIZARD_LONG_LIST_SELECTOR = [
        ".wizard-panel .wizard-export-plan-list",
        ".wizard-panel .wizard-baseline-summary-list",
        ".wizard-panel .wizard-search-engine-list:not([data-schema-array-list]):not([data-schema-dict-list]):not([data-schema-nested-dict-list]):not([data-schema-nested-array-list])",
        ".wizard-panel .wizard-shell-list",
        ".wizard-panel .wizard-checklist",
    ].join(", ");

    function initWizardDisclosures(documentRef, t) {
        function labelFor(button, expanded) {
            const key = expanded
                ? button.dataset.wizardDisclosureHideKey
                : button.dataset.wizardDisclosureShowKey;
            const fallback = expanded ? button.dataset.wizardDisclosureHide : button.dataset.wizardDisclosureShow;
            return t(key, fallback || button.textContent || "");
        }

        function setExpanded(button, panel, expanded) {
            if (panel) {
                panel.hidden = !expanded;
            }
            button.setAttribute("aria-expanded", expanded ? "true" : "false");
            button.setAttribute(
                "data-i18n",
                expanded
                    ? button.dataset.wizardDisclosureHideKey
                    : button.dataset.wizardDisclosureShowKey,
            );
            button.textContent = labelFor(button, expanded);
        }

        Array.from(documentRef.querySelectorAll("[data-wizard-disclosure-toggle]")).forEach((button) => {
            if (button.dataset.wizardDisclosureReady === "true") return;
            const panelId = button.getAttribute("aria-controls");
            const panel = panelId ? documentRef.getElementById(panelId) : null;
            const expanded = button.getAttribute("aria-expanded") === "true" && panel?.hidden === false;

            button.dataset.wizardDisclosureReady = "true";
            setExpanded(button, panel, expanded);
            button.addEventListener("click", () => {
                const nextExpanded = button.getAttribute("aria-expanded") !== "true";
                setExpanded(button, panel, nextExpanded);
            });
        });
    }

    function initWizardLongLists(documentRef, t) {
        function listItems(list) {
            return Array.from(list.children).filter((child) => (
                child.nodeType === 1
                && child.tagName !== "TEMPLATE"
                && child.dataset.wizardLongListControl !== "true"
            ));
        }

        function managedVisibleItems(list) {
            return listItems(list).filter((child) => (
                child.dataset.wizardLongListHidden === "true" || child.hidden !== true
            ));
        }

        function setButtonLabel(button, expanded, totalCount) {
            const key = expanded ? "profiles.wizard_long_list_show_fewer" : "profiles.wizard_long_list_show_all";
            const fallback = expanded ? "Show fewer" : "Show all {count}";
            button.textContent = t(key, fallback).replace("{count}", String(totalCount));
            button.dataset.i18n = key;
        }

        function showManagedItem(child) {
            if (child.dataset.wizardLongListHidden === "true") {
                child.hidden = false;
                delete child.dataset.wizardLongListHidden;
            }
        }

        function applyBudget(list, button) {
            const expanded = list.dataset.wizardLongListExpanded === "true";
            const items = managedVisibleItems(list);

            if (items.length <= WIZARD_LONG_LIST_LIMIT) {
                items.forEach(showManagedItem);
                button.hidden = true;
                return;
            }

            button.hidden = false;
            setButtonLabel(button, expanded, items.length);
            button.setAttribute("aria-expanded", expanded ? "true" : "false");

            if (expanded) {
                items.forEach(showManagedItem);
                return;
            }

            items.forEach((child, index) => {
                if (index < WIZARD_LONG_LIST_LIMIT) {
                    showManagedItem(child);
                    return;
                }
                if (child.hidden !== true || child.dataset.wizardLongListHidden === "true") {
                    child.hidden = true;
                    child.dataset.wizardLongListHidden = "true";
                }
            });
        }

        function renderControl(list) {
            const control = documentRef.createElement("div");
            control.className = "wizard-long-list-control";
            control.dataset.wizardLongListControl = "true";

            const button = documentRef.createElement("button");
            button.type = "button";
            button.className = "button-base ghost-button wizard-long-list-toggle";
            button.hidden = true;
            control.appendChild(button);
            list.after(control);

            button.addEventListener("click", () => {
                list.dataset.wizardLongListExpanded = list.dataset.wizardLongListExpanded === "true" ? "false" : "true";
                applyBudget(list, button);
            });

            return button;
        }

        Array.from(documentRef.querySelectorAll(WIZARD_LONG_LIST_SELECTOR)).forEach((list) => {
            if (list.dataset.wizardLongListReady === "true") return;
            list.dataset.wizardLongListReady = "true";
            list.dataset.wizardLongListExpanded = "false";
            const button = renderControl(list);
            const observer = new MutationObserver(() => applyBudget(list, button));
            observer.observe(list, { childList: true });
            applyBudget(list, button);
        });
    }

    function initWizardHomeSurfaceGroups(documentRef, t) {
        const groups = Array.from(documentRef.querySelectorAll("[data-home-surface-group]"));
        if (!groups.length) return;

        function setGroupOpen(targetGroup, open) {
            const toggle = targetGroup.querySelector("[data-home-surface-toggle]");
            targetGroup.dataset.homeSurfaceCollapsed = open ? "false" : "true";
            if (toggle) {
                toggle.setAttribute("aria-expanded", open ? "true" : "false");
                toggle.textContent = open
                    ? t("profiles.wizard_home_surface_active")
                    : t("profiles.wizard_home_surface_open");
                toggle.dataset.i18n = open
                    ? "profiles.wizard_home_surface_active"
                    : "profiles.wizard_home_surface_open";
            }
        }

        function openGroup(groupKey) {
            groups.forEach((group) => {
                setGroupOpen(group, group.dataset.homeSurfaceGroup === groupKey);
            });
        }

        groups.forEach((group) => {
            const toggle = group.querySelector("[data-home-surface-toggle]");
            const isOpen = group.dataset.homeSurfaceCollapsed !== "true";
            setGroupOpen(group, isOpen);
            if (!toggle || toggle.dataset.homeSurfaceReady === "true") return;
            toggle.dataset.homeSurfaceReady = "true";
            toggle.addEventListener("click", () => {
                openGroup(toggle.dataset.homeSurfaceToggle || group.dataset.homeSurfaceGroup || "");
            });
        });

    }

    function initWizardReviewFilters(documentRef, t) {
        function isAdvancedOnlyRow(row) {
            return Boolean(
                row.closest('[data-workspace-scope-panel="settings"]')
                || row.closest("[data-settings-compatibility-panel]")
                || row.querySelector('[data-final-review-jump="raw"], [data-final-review-jump="deprecated"], [data-final-review-jump="unknown"]')
            );
        }

        function rowMatches(row, filterValue) {
            if (filterValue === "all") return true;
            const tone = row.dataset.summaryTone || "default";
            if (filterValue === "attention") {
                return tone === "attention" || tone === "strict";
            }
            if (filterValue === "settings") {
                return isAdvancedOnlyRow(row) && tone !== "default";
            }
            return tone !== "default";
        }

        function emptyLabel(filterValue) {
            const labels = {
                changed: ["profiles.wizard_review_empty_changed", "No changed items here yet."],
                attention: ["profiles.wizard_review_empty_attention", "Nothing needs attention here right now."],
                advanced: ["profiles.wizard_review_empty_settings", "No items outside Guided editor are listed here right now."],
                all: ["profiles.wizard_review_empty_all", "No review rows here yet."],
            };
            const [key, fallback] = labels[filterValue] || labels.changed;
            return t(key, fallback);
        }

        function applyFilter(list, filterValue, emptyEl = null) {
            const rows = Array.from(list.querySelectorAll(".wizard-summary-row"));
            if (!rows.length) return;
            const hasMatch = rows.some((row) => rowMatches(row, filterValue));
            rows.forEach((row) => {
                row.hidden = !rowMatches(row, filterValue);
            });
            list.querySelectorAll(".wizard-summary-group").forEach((group) => {
                const groupRows = Array.from(group.querySelectorAll(".wizard-summary-row"));
                group.hidden = groupRows.length > 0 && groupRows.every((row) => row.hidden);
            });
            if (emptyEl) {
                emptyEl.hidden = hasMatch;
                emptyEl.textContent = emptyLabel(filterValue);
                emptyEl.dataset.i18n = {
                    changed: "profiles.wizard_review_empty_changed",
                    attention: "profiles.wizard_review_empty_attention",
                    advanced: "profiles.wizard_review_empty_settings",
                    all: "profiles.wizard_review_empty_all",
                }[filterValue] || "profiles.wizard_review_empty_changed";
            }
            list.dataset.reviewFilter = filterValue;
        }

        function renderControls(list) {
            const controls = documentRef.createElement("div");
            controls.className = "wizard-review-filters";
            controls.dataset.wizardReviewFilters = "true";

            WIZARD_REVIEW_FILTERS.forEach((filter, index) => {
                const button = documentRef.createElement("button");
                button.type = "button";
                button.className = `button-base ghost-button wizard-review-filter${index === 0 ? " is-active" : ""}`;
                button.dataset.wizardReviewFilter = filter.value;
                button.dataset.i18n = filter.key;
                button.textContent = t(filter.key, filter.fallback);
                button.setAttribute("aria-pressed", index === 0 ? "true" : "false");
                controls.appendChild(button);
            });

            controls.addEventListener("click", (event) => {
                const button = event.target.closest("[data-wizard-review-filter]");
                if (!button || !controls.contains(button)) return;
                const filterValue = button.dataset.wizardReviewFilter || "changed";
                controls.querySelectorAll("[data-wizard-review-filter]").forEach((item) => {
                    const isActive = item === button;
                    item.classList.toggle("is-active", isActive);
                    item.setAttribute("aria-pressed", isActive ? "true" : "false");
                });
                applyFilter(list, filterValue);
            });

            list.before(controls);
            return controls;
        }

        function renderEmptyState(list) {
            const emptyEl = documentRef.createElement("div");
            emptyEl.className = "wizard-review-filter-empty wizard-input-hint";
            emptyEl.dataset.wizardReviewEmpty = "true";
            emptyEl.hidden = true;
            list.after(emptyEl);
            return emptyEl;
        }

        Array.from(documentRef.querySelectorAll(".wizard-summary-list--cards")).forEach((list) => {
            if (list.dataset.wizardReviewListReady === "true") return;
            list.dataset.wizardReviewListReady = "true";
            const controls = renderControls(list);
            const emptyEl = renderEmptyState(list);
            const getActiveFilter = () => controls.querySelector(".is-active")?.dataset.wizardReviewFilter || "changed";
            const observer = new MutationObserver(() => applyFilter(list, getActiveFilter(), emptyEl));
            observer.observe(list, {
                subtree: true,
                childList: true,
                attributes: true,
                attributeFilter: ["data-summary-tone"],
            });
            applyFilter(list, getActiveFilter(), emptyEl);
        });
    }

    function start() {
        const utils = window.BPMProfilesUtils;
        const platform = window.BPMProfilesPlatform;
        const data = window.BPMProfilesData;
        const dom = window.BPMProfilesDom.read(document);
        const shared = window.BPMProfilesShared.create({
            documentRef: document,
            elements: {
                statusEl: dom.elements.statusEl,
                workspaceHelperTitleEl: dom.elements.workspaceHelperTitleEl,
                workspaceHelperCopyEl: dom.elements.workspaceHelperCopyEl,
                wizardSchemaEl: dom.elements.wizardSchemaEl,
            },
            dependencies: {
                fromEditorValue: data.fromEditorValue,
                formatBooleanSelectValue: utils.formatBooleanSelectValue,
                parseBooleanSelectValue: utils.parseBooleanSelectValue,
                getDefaultSchemaVersion: utils.getDefaultSchemaVersion,
            },
        });

        initWizardDisclosures(document, shared.t);
        initWizardReviewFilters(document, shared.t);
        initWizardLongLists(document, shared.t);
        initWizardHomeSurfaceGroups(document, shared.t);

        const core = window.BPMProfilesBootstrapSections.initCoreModules({
            documentRef: document,
            windowRef: window,
            elements: dom.elements,
            catalogs: dom.catalogs,
            shared,
            utils,
            platform,
            data,
            managedExtensionFields: dom.managedExtensionFields,
            managedExtensionStatusEls: dom.managedExtensionStatusEls,
            wizardSchemaShellViews: dom.wizardSchemaShellViews,
        });

        const features = window.BPMProfilesBootstrapSections.initFeatureModules({
            documentRef: document,
            elements: dom.elements,
            catalogs: dom.catalogs,
            shared,
            utils,
            data,
            core,
        });

        core.setSyncWizardNetworkFromEditor(features.syncWizardNetworkFromEditor);
        core.setSyncWizardPreferencesFromEditor(features.syncWizardPreferencesFromEditor);

        window.BPMProfilesBootstrapSections.startRuntimeModule({
            documentRef: document,
            windowRef: window,
            shared,
            utils,
            platform,
            data,
            core,
            features,
        });
    }

    window.BPMProfilesBootstrap = { start };
})();
