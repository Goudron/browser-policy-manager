(() => {
    window.BPMProfilesBootstrapSections = {
        initCoreModules: (...args) => window.BPMProfilesBootstrapCore.initCoreModules(...args),
        initFeatureModules: (...args) => window.BPMProfilesBootstrapFeatures.initFeatureModules(...args),
        startRuntimeModule: (...args) => window.BPMProfilesBootstrapRuntime.startRuntimeModule(...args),
    };
})();
