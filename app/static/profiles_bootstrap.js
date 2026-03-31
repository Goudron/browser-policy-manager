(() => {
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
