function createFakeElement(tagName = "div", { query = {}, queryAll = {} } = {}) {
    const listeners = new Map();
    const state = {
        attrs: {},
        classes: {},
        focused: false,
        scrolled: false,
    };
    const element = {
        tagName,
        type: "",
        value: "",
        hidden: false,
        disabled: false,
        className: "",
        textContent: "",
        dataset: {},
        children: [],
        attrs: state.attrs,
        state,
        classList: {
            toggle(name, active) {
                state.classes[name] = Boolean(active);
            },
            add(name) {
                state.classes[name] = true;
            },
            remove(name) {
                state.classes[name] = false;
            },
        },
        addEventListener(eventName, handler) {
            listeners.set(eventName, handler);
        },
        emit(eventName, event = {}) {
            return listeners.get(eventName)?.(event);
        },
        appendChild(child) {
            this.children.push(child);
            return child;
        },
        setAttribute(name, value) {
            this.attrs[name] = String(value);
        },
        dispatchEvent(event) {
            return this.emit(event.type, event);
        },
        focus() {
            state.focused = true;
        },
        scrollIntoView() {
            state.scrolled = true;
        },
        click() {
            return this.emit("click", { target: this });
        },
        closest() {
            return null;
        },
        matches() {
            return false;
        },
        querySelector(selector) {
            if (Object.hasOwn(query, selector)) {
                const result = query[selector];
                return typeof result === "function" ? result() : result;
            }
            const stack = [...this.children];
            while (stack.length) {
                const item = stack.shift();
                if (selector === "[data-settings-search-target]" && item.dataset?.settingsSearchTarget) {
                    return item;
                }
                stack.push(...(item.children || []));
            }
            return null;
        },
        querySelectorAll(selector) {
            if (Object.hasOwn(queryAll, selector)) {
                const result = queryAll[selector];
                return typeof result === "function" ? result() : result;
            }
            return [];
        },
    };
    let innerHTML = "";
    Object.defineProperty(element, "innerHTML", {
        configurable: true,
        get() {
            return innerHTML;
        },
        set(value) {
            innerHTML = String(value);
            element.children = [];
        },
    });
    return element;
}

function eventTargetFor(selector) {
    return {
        closest(candidate) {
            return candidate === selector ? {} : null;
        },
    };
}

function installImmediateWindow() {
    const previousWindow = globalThis.window;
    globalThis.window = {
        Event: class {
            constructor(type) {
                this.type = type;
            }
        },
        setTimeout(callback) {
            callback();
        },
    };
    return () => {
        if (previousWindow === undefined) {
            delete globalThis.window;
        } else {
            globalThis.window = previousWindow;
        }
    };
}

export { createFakeElement, eventTargetFor, installImmediateWindow };
