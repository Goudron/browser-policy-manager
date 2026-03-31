import * as monaco from "monaco-editor/esm/vs/editor/editor.api.js";
import "monaco-editor/esm/vs/language/json/monaco.contribution.js";
import "monaco-editor/esm/vs/basic-languages/yaml/yaml.contribution.js";

(function bootstrapProfilesMonaco() {
    const globalRef = globalThis;

    globalRef.MonacoEnvironment = globalRef.MonacoEnvironment || {};
    globalRef.MonacoEnvironment.getWorker = function (_workerId, label) {
        if (label === "json") {
            return new Worker("/static/vendor/monaco-json.worker.js");
        }
        return new Worker("/static/vendor/monaco-editor.worker.js");
    };

    globalRef.monaco = monaco;
    globalRef.__BPM_MONACO_READY__ = Promise.resolve(monaco);
})();
