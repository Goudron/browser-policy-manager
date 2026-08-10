/** Navigation policy with all browser APIs supplied explicitly. */
export function isGuardedProfileRouteHref(anchorEl, origin) {
    const href = anchorEl?.getAttribute?.("href") || "";
    if (!href || href.startsWith("#")) return false;
    try {
        const url = new URL(href, origin);
        return url.origin === new URL(origin).origin && (url.pathname === "/profiles" || url.pathname.startsWith("/profiles/"));
    } catch {
        return false;
    }
}

export function isCrossTabProfileRouteIntent(event, anchorEl) {
    if (anchorEl?.target && anchorEl.target !== "_self") return true;
    if (!event) return false;
    return Boolean(event.metaKey || event.ctrlKey || event.shiftKey || (typeof event.button === "number" && event.button !== 0));
}

export function createDirtyRouteGuard({ windowRef, currentSnapshotState = () => ({ dirty: false }), confirmDiscard = () => "" } = {}) {
    if (!windowRef?.location || typeof windowRef.confirm !== "function") {
        throw new TypeError("createDirtyRouteGuard requires a windowRef with location and confirm.");
    }
    function confirmRouteNavigationIfDirty() {
        return !currentSnapshotState().dirty || windowRef.confirm(confirmDiscard());
    }
    function guardProfileRouteNavigation(event) {
        const anchorEl = event.target?.closest?.("a[href]");
        if (!anchorEl || !isGuardedProfileRouteHref(anchorEl, windowRef.location.origin)) return false;
        if (isCrossTabProfileRouteIntent(event, anchorEl) || confirmRouteNavigationIfDirty()) return false;
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
    return { bindBeforeUnload, confirmRouteNavigationIfDirty, guardProfileRouteNavigation, isCrossTabProfileRouteIntent, isGuardedProfileRouteHref: (anchorEl) => isGuardedProfileRouteHref(anchorEl, windowRef.location.origin) };
}
