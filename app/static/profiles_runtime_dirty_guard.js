(() => {
    function create({
        windowRef = window,
        currentSnapshotState = () => ({ dirty: false }),
        confirmDiscard = () => "",
    } = {}) {
        function isGuardedProfileRouteHref(anchorEl) {
            const href = anchorEl?.getAttribute?.("href") || "";
            if (!href || href.startsWith("#")) return false;
            try {
                const url = new URL(href, windowRef.location.origin);
                if (url.origin !== windowRef.location.origin) return false;
                return url.pathname === "/profiles" || url.pathname.startsWith("/profiles/");
            } catch {
                return false;
            }
        }

        function isCrossTabProfileRouteIntent(event, anchorEl) {
            if (anchorEl?.target && anchorEl.target !== "_self") return true;
            if (!event) return false;
            if (event.metaKey || event.ctrlKey || event.shiftKey) return true;
            if (typeof event.button === "number" && event.button !== 0) return true;
            return false;
        }

        function confirmRouteNavigationIfDirty() {
            if (!currentSnapshotState().dirty) return true;
            return windowRef.confirm(confirmDiscard());
        }

        function guardProfileRouteNavigation(event) {
            const anchorEl = event.target.closest?.("a[href]");
            if (!anchorEl || !isGuardedProfileRouteHref(anchorEl)) return false;
            if (isCrossTabProfileRouteIntent(event, anchorEl)) return false;
            if (confirmRouteNavigationIfDirty()) return false;
            event.preventDefault();
            event.stopPropagation();
            return true;
        }

        function bindBeforeUnload() {
            windowRef.addEventListener("beforeunload", (event) => {
                if (!currentSnapshotState().dirty) return;
                event.preventDefault();
                event.returnValue = "";
            });
        }

        return {
            bindBeforeUnload,
            confirmRouteNavigationIfDirty,
            guardProfileRouteNavigation,
            isCrossTabProfileRouteIntent,
            isGuardedProfileRouteHref,
        };
    }

    window.BPMProfilesDirtyRouteGuard = { create };
})();
