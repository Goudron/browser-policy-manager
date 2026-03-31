browser.runtime.onInstalled.addListener(() => {
  browser.storage.local.set({
    installedBy: "browser-policy-manager-live-tests",
    signal: "BPM_TEST_EXTENSION_READY",
  });
});
