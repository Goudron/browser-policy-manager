import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

globalThis.window = {};
const data = await import("../../../../app/static/profiles_data.js");

test("editor adapters use the complete Firefox policies document shape", async () => {
    const editorJson = data.toEditorValue({ DisableTelemetry: true });
    assert.deepEqual(JSON.parse(editorJson), { policies: { DisableTelemetry: true } });

    assert.deepEqual(
        data.fromEditorValue(JSON.stringify({ policies: { BlockAboutConfig: true } })),
        { BlockAboutConfig: true },
    );
    assert.deepEqual(
        JSON.parse(data.toEditorValue({ policies: { DisableAppUpdate: true } })),
        { policies: { DisableAppUpdate: true } },
    );
    assert.throws(() => data.fromEditorValue("[]"), /Expected policies\.json root object/);
    assert.deepEqual(
        data.parseEditorPolicyDocument(
            JSON.stringify({ policies: { DisableFirefoxStudies: true } }),
        ),
        { policies: { DisableFirefoxStudies: true } },
    );
    assert.equal(
        data.getPolicyValue(
            { policies: { DisableFirefoxStudies: true } },
            "DisableFirefoxStudies",
        ),
        true,
    );
    assert.deepEqual(
        data.setPolicyValue(
            { policies: { DisableFirefoxStudies: true } },
            "DisableTelemetry",
            true,
        ),
        { DisableFirefoxStudies: true, DisableTelemetry: true },
    );

    let validationBody = null;
    await data.validateFlags(
        "release-152",
        { policies: { DisableTelemetry: true } },
        async (_url, options) => {
            validationBody = JSON.parse(options.body);
            return {
                ok: true,
                json: async () => ({ ok: true }),
                text: async () => "{}",
            };
        },
    );
    assert.deepEqual(validationBody, {
        document: { policies: { DisableTelemetry: true } },
    });
});

test("common API errors are localized through the runtime catalog", async () => {
    const ruCatalog = JSON.parse(await readFile(
        new URL("../../../../app/i18n/ru.json", import.meta.url),
        "utf8",
    ));
    globalThis.window.__BPM_INITIAL_LOCALE__ = ruCatalog;

    assert.throws(
        () => data.fromEditorValue("[]"),
        /Ожидался корневой объект policies\.json/,
    );
    assert.equal(
        await data.readError({
            text: async () => JSON.stringify({
                detail: "Profile with this name already exists",
            }),
        }),
        "Профиль с таким именем уже существует.",
    );
    assert.equal(
        await data.readError({
            text: async () => JSON.stringify({
                detail: "Schema for profile 'release-999' is not available",
            }),
        }),
        "Схема для профиля release-999 недоступна.",
    );
});
