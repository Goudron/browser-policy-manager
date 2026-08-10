    function create({
        initCoreModules,
        initFeatureModules,
        startRuntimeModule,
    }) {
        return {
            initCoreModules,
            initFeatureModules,
            startRuntimeModule,
        };
    }

    export { create };
