    function create({ components = {}, ...config }) {
        const { createSections } = components;
        return createSections(config);
    }

    export { create };
