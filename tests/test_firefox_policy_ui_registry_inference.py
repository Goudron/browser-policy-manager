from app.services.firefox_policy_ui_registry import inference


def test_infer_widget_falls_back_to_raw_json_for_unknown_types():
    assert inference.infer_widget("mystery", {}) == "raw-json"
