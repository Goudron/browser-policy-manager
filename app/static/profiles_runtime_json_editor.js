(() => {
    function createHeadlessEditorAdapter(initialValue = "{}") {
        let value = String(initialValue ?? "");
        let language = "json";
        const listeners = new Set();
        const model = {
            getValue() {
                return value;
            },
            setValue(nextValue) {
                value = String(nextValue ?? "");
                listeners.forEach((listener) => listener({}));
            },
            onDidChangeContent(listener) {
                listeners.add(listener);
                return {
                    dispose() {
                        listeners.delete(listener);
                    },
                };
            },
            getLanguageId() {
                return language;
            },
            _setLanguage(nextLanguage) {
                language = String(nextLanguage || "json");
            },
            dispose() {
                listeners.clear();
            },
        };
        return {
            getValue() {
                return model.getValue();
            },
            setValue(value) {
                model.setValue(String(value ?? ""));
            },
            getModel() {
                return model;
            },
            onDidChangeModelContent(listener) {
                return model.onDidChangeContent(listener);
            },
            layout() {},
            dispose() {
                model.dispose();
            },
        };
    }

    function setEditorModelLanguage(monacoRef, editorInstance, language) {
        if (!editorInstance?.getModel) return;
        const model = editorInstance.getModel();
        if (monacoRef?.editor?.setModelLanguage) {
            monacoRef.editor.setModelLanguage(model, language);
            return;
        }
        if (typeof model?._setLanguage === "function") {
            model._setLanguage(language);
        }
    }

    function getMonacoThemeName(resolvedTheme) {
        return resolvedTheme === "dark" ? "bpm-vs-dark" : "bpm-vs-light";
    }

    function ensureMonacoThemes(monacoRef) {
        if (!monacoRef?.editor?.defineTheme) return;

        monacoRef.editor.defineTheme("bpm-vs-light", {
            base: "vs",
            inherit: true,
            rules: [
                { token: "string.key.json", foreground: "0f4c81" },
                { token: "string.value.json", foreground: "a16207" },
                { token: "string", foreground: "a16207" },
                { token: "number", foreground: "7c3aed" },
                { token: "keyword", foreground: "0f766e" },
                { token: "keyword.json", foreground: "0f766e" },
                { token: "delimiter.bracket", foreground: "334155" },
                { token: "delimiter.array", foreground: "334155" },
                { token: "delimiter.comma", foreground: "64748b" },
            ],
            colors: {
                "editor.background": "#f8fafc",
                "editor.foreground": "#122033",
                "editor.lineHighlightBackground": "#e2e8f066",
                "editor.selectionBackground": "#14b8a626",
                "editor.inactiveSelectionBackground": "#cbd5e166",
                "editorCursor.foreground": "#0f766e",
                "editorWhitespace.foreground": "#cbd5e180",
                "editorIndentGuide.background1": "#dbe3ee",
                "editorIndentGuide.activeBackground1": "#14b8a670",
                "editorLineNumber.foreground": "#94a3b8",
                "editorLineNumber.activeForeground": "#122033",
                "editorLineNumber.dimmedForeground": "#cbd5e1",
                "editorGutter.background": "#f8fafc",
                "editorBracketHighlight.foreground1": "#0f766e",
                "editorBracketHighlight.foreground2": "#7c3aed",
                "editorBracketHighlight.foreground3": "#2563eb",
                "scrollbar.shadow": "#ffffff00",
                "scrollbarSlider.background": "#94a3b899",
                "scrollbarSlider.hoverBackground": "#64748bcc",
                "scrollbarSlider.activeBackground": "#334155dd",
            },
        });

        monacoRef.editor.defineTheme("bpm-vs-dark", {
            base: "vs-dark",
            inherit: true,
            rules: [
                { token: "string.key.json", foreground: "7dd3fc" },
                { token: "string.value.json", foreground: "fbbf24" },
                { token: "string", foreground: "fbbf24" },
                { token: "number", foreground: "c084fc" },
                { token: "keyword", foreground: "34d399" },
                { token: "keyword.json", foreground: "34d399" },
                { token: "delimiter.bracket", foreground: "e2e8f0" },
                { token: "delimiter.array", foreground: "e2e8f0" },
                { token: "delimiter.comma", foreground: "94a3b8" },
            ],
            colors: {
                "editor.background": "#0b1324",
                "editor.foreground": "#e2e8f0",
                "editor.lineHighlightBackground": "#1e293b66",
                "editor.selectionBackground": "#14b8a633",
                "editor.inactiveSelectionBackground": "#33415588",
                "editorCursor.foreground": "#5eead4",
                "editorWhitespace.foreground": "#334155bb",
                "editorIndentGuide.background1": "#1f2937",
                "editorIndentGuide.activeBackground1": "#2dd4bf88",
                "editorLineNumber.foreground": "#64748b",
                "editorLineNumber.activeForeground": "#f8fafc",
                "editorLineNumber.dimmedForeground": "#475569",
                "editorGutter.background": "#0b1324",
                "editorBracketHighlight.foreground1": "#2dd4bf",
                "editorBracketHighlight.foreground2": "#c084fc",
                "editorBracketHighlight.foreground3": "#7dd3fc",
                "scrollbar.shadow": "#02061700",
                "scrollbarSlider.background": "#64748baa",
                "scrollbarSlider.hoverBackground": "#94a3b8cc",
                "scrollbarSlider.activeBackground": "#cbd5e1dd",
            },
        });
    }

    window.BPMProfilesJsonEditorRuntime = {
        createHeadlessEditorAdapter,
        ensureMonacoThemes,
        getMonacoThemeName,
        setEditorModelLanguage,
    };
})();
