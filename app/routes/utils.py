def group_by_ui_group(policies):
    groups = {}
    for p in policies:
        g = (p.get("ui", {}) or {}).get("group_i18n", "group.advanced")
        groups.setdefault(g, []).append(p)
    return groups
