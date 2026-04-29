import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_profiles_data_editor_adapters_use_firefox_policies_document_shape():
    source = (REPO_ROOT / "app/static/profiles_data.js").read_text()
    script = f"""
const vm = require("node:vm");
const source = {json.dumps(source)};
const context = {{
  window: {{
    jsyaml: {{
      dump: (obj) => JSON.stringify(obj),
      load: (text) => JSON.parse(text),
    }},
  }},
}};
vm.createContext(context);
vm.runInContext(source, context);
const data = context.window.BPMProfilesData;

const editorJson = data.toEditorValue({{ DisableTelemetry: true }}, "json");
const editorDocument = JSON.parse(editorJson);
if (JSON.stringify(editorDocument) !== JSON.stringify({{ policies: {{ DisableTelemetry: true }} }})) {{
  throw new Error(`unexpected editor document: ${{editorJson}}`);
}}

const parsedFlags = data.fromEditorValue(
  JSON.stringify({{ policies: {{ BlockAboutConfig: true }} }}),
  "json",
);
if (JSON.stringify(parsedFlags) !== JSON.stringify({{ BlockAboutConfig: true }})) {{
  throw new Error(`unexpected parsed flags: ${{JSON.stringify(parsedFlags)}}`);
}}

const doubleWrapped = JSON.parse(data.toEditorValue(
  {{ policies: {{ DisableAppUpdate: true }} }},
  "json",
));
if (JSON.stringify(doubleWrapped) !== JSON.stringify({{ policies: {{ DisableAppUpdate: true }} }})) {{
  throw new Error(`unexpected double wrapper: ${{JSON.stringify(doubleWrapped)}}`);
}}

try {{
  data.fromEditorValue("[]", "json");
  throw new Error("array root did not fail");
}} catch (error) {{
  if (!String(error.message).includes("Expected policies.json root object")) {{
    throw error;
  }}
}}

const parsedEditorDocument = data.parseEditorPolicyDocument(
  JSON.stringify({{ policies: {{ DisableFirefoxStudies: true }} }}),
  "json",
);
if (JSON.stringify(parsedEditorDocument) !== JSON.stringify({{ policies: {{ DisableFirefoxStudies: true }} }})) {{
  throw new Error(`unexpected parsed editor document: ${{JSON.stringify(parsedEditorDocument)}}`);
}}

const policyValue = data.getPolicyValue(
  {{ policies: {{ DisableFirefoxStudies: true }} }},
  "DisableFirefoxStudies",
);
if (policyValue !== true) {{
  throw new Error(`unexpected policy value: ${{policyValue}}`);
}}

const withPolicy = data.setPolicyValue(
  {{ policies: {{ DisableFirefoxStudies: true }} }},
  "DisableTelemetry",
  true,
);
if (JSON.stringify(withPolicy) !== JSON.stringify({{
  DisableFirefoxStudies: true,
  DisableTelemetry: true,
}})) {{
  throw new Error(`unexpected set policy value: ${{JSON.stringify(withPolicy)}}`);
}}

let validationBody = null;
(async () => {{
  await data.validateFlags("release-150", {{ policies: {{ DisableTelemetry: true }} }}, async (_url, options) => {{
    validationBody = JSON.parse(options.body);
    return {{
      ok: true,
      json: async () => ({{ ok: true }}),
      text: async () => "{{}}",
    }};
  }});
  if (JSON.stringify(validationBody) !== JSON.stringify({{ document: {{ policies: {{ DisableTelemetry: true }} }} }})) {{
    throw new Error(`unexpected validation body: ${{JSON.stringify(validationBody)}}`);
  }}
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""

    subprocess.run(
        ["node", "-e", script],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
