from __future__ import annotations

from collections import Counter
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.compliance.firefox.cis.generation import GeneratedCisLayer
from app.compliance.firefox.cis.validation import BASE_DIR, load_yaml_file

PathKey = tuple[str, ...]


@dataclass(frozen=True)
class CisMergeDecision:
    path: PathKey
    decision: str
    selected_source: str
    base_value: Any
    cis_value: Any
    selected_value: Any
    recommendation_ids: tuple[str, ...] = ()
    merge_rule: str | None = None
    review_required: bool = False
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": list(self.path),
            "decision": self.decision,
            "selected_source": self.selected_source,
            "base_value": self.base_value,
            "cis_value": self.cis_value,
            "selected_value": self.selected_value,
            "recommendation_ids": list(self.recommendation_ids),
            "merge_rule": self.merge_rule,
            "review_required": self.review_required,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class CisMergeResult:
    effective_policies: dict[str, Any]
    decisions: tuple[CisMergeDecision, ...]
    summary: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        return {
            "effective_policies": self.effective_policies,
            "decisions": [decision.to_dict() for decision in self.decisions],
            "summary": dict(self.summary),
        }


def merge_base_with_cis_layer(
    base_policies: dict[str, Any],
    cis_layer: GeneratedCisLayer,
    *,
    base_label: str = "base",
    cis_label: str = "cis",
    base_dir: Path = BASE_DIR,
) -> CisMergeResult:
    metadata = _load_target_metadata(base_dir)
    manual_review = _load_manual_review_rules(base_dir)
    decisions: list[CisMergeDecision] = []
    effective = _merge_node(
        deepcopy(base_policies),
        cis_layer.policies,
        path=(),
        decisions=decisions,
        metadata=metadata,
        manual_review=manual_review,
        base_label=base_label,
        cis_label=cis_label,
    )
    counts = Counter(decision.decision for decision in decisions)
    counts["review_required"] = sum(1 for decision in decisions if decision.review_required)
    return CisMergeResult(
        effective_policies=effective,
        decisions=tuple(decisions),
        summary=dict(sorted(counts.items())),
    )


def _merge_node(
    base_value: Any,
    cis_value: Any,
    *,
    path: PathKey,
    decisions: list[CisMergeDecision],
    metadata: dict[PathKey, dict[str, Any]],
    manual_review: dict[PathKey, str],
    base_label: str,
    cis_label: str,
) -> Any:
    if isinstance(base_value, dict) and isinstance(cis_value, dict):
        merged: dict[str, Any] = {}
        for key in sorted(set(base_value) | set(cis_value)):
            child_path = (*path, key)
            if key not in base_value:
                merged[key] = deepcopy(cis_value[key])
                _append_decision(
                    decisions,
                    child_path,
                    "added_from_cis",
                    cis_label,
                    None,
                    cis_value[key],
                    cis_value[key],
                    metadata,
                    review_required=False,
                    reason="CIS defines this setting and the base scenario does not.",
                )
            elif key not in cis_value:
                merged[key] = deepcopy(base_value[key])
                _append_decision(
                    decisions,
                    child_path,
                    "kept_base_only",
                    base_label,
                    base_value[key],
                    None,
                    base_value[key],
                    metadata,
                    review_required=False,
                    reason="The base scenario defines this setting and CIS does not.",
                )
            else:
                merged[key] = _merge_node(
                    base_value[key],
                    cis_value[key],
                    path=child_path,
                    decisions=decisions,
                    metadata=metadata,
                    manual_review=manual_review,
                    base_label=base_label,
                    cis_label=cis_label,
                )
        return merged

    if base_value == cis_value:
        _append_decision(
            decisions,
            path,
            "already_satisfied",
            base_label,
            base_value,
            cis_value,
            base_value,
            metadata,
            review_required=False,
            reason="The base scenario already matches the CIS value.",
        )
        return deepcopy(base_value)

    if path in manual_review:
        _append_decision(
            decisions,
            path,
            "manual_review_kept_base",
            base_label,
            base_value,
            cis_value,
            base_value,
            metadata,
            review_required=True,
            reason=manual_review[path],
        )
        return deepcopy(base_value)

    rule = metadata.get(path, {}).get("merge_rule")
    selected = _select_by_rule(rule, base_value, cis_value)
    if selected == "cis":
        _append_decision(
            decisions,
            path,
            "cis_replaced_base",
            cis_label,
            base_value,
            cis_value,
            cis_value,
            metadata,
            review_required=False,
            reason="CIS value is stricter according to the path merge rule.",
        )
        return deepcopy(cis_value)
    if selected == "base":
        _append_decision(
            decisions,
            path,
            "kept_base_stricter",
            base_label,
            base_value,
            cis_value,
            base_value,
            metadata,
            review_required=False,
            reason="Base scenario value is stricter according to the path merge rule.",
        )
        return deepcopy(base_value)

    _append_decision(
        decisions,
        path,
        "manual_review_kept_base",
        base_label,
        base_value,
        cis_value,
        base_value,
        metadata,
        review_required=True,
        reason="No safe automatic strictness comparison is available for this path.",
    )
    return deepcopy(base_value)


def _append_decision(
    decisions: list[CisMergeDecision],
    path: PathKey,
    decision: str,
    selected_source: str,
    base_value: Any,
    cis_value: Any,
    selected_value: Any,
    metadata: dict[PathKey, dict[str, Any]],
    *,
    review_required: bool,
    reason: str,
) -> None:
    target_metadata = metadata.get(path, {})
    decisions.append(
        CisMergeDecision(
            path=path,
            decision=decision,
            selected_source=selected_source,
            base_value=deepcopy(base_value),
            cis_value=deepcopy(cis_value),
            selected_value=deepcopy(selected_value),
            recommendation_ids=tuple(target_metadata.get("recommendation_ids", ())),
            merge_rule=target_metadata.get("merge_rule"),
            review_required=review_required,
            reason=reason,
        )
    )


def _select_by_rule(rule: str | None, base_value: Any, cis_value: Any) -> str | None:
    if rule == "boolean_true_is_stricter":
        return _select_boolean_rank(base_value, cis_value, {False: 0, True: 1})
    if rule == "boolean_false_is_stricter":
        return _select_boolean_rank(base_value, cis_value, {True: 0, False: 1})
    if rule == "empty_allowlist_is_stricter":
        if isinstance(base_value, list) and isinstance(cis_value, list):
            if len(cis_value) < len(base_value):
                return "cis"
            if len(base_value) < len(cis_value):
                return "base"
    if rule == "cookie_behavior_rank":
        order = {
            "accept": 0,
            "reject-tracker": 1,
            "reject-tracker-and-partition-foreign": 2,
            "reject": 3,
        }
        return _select_rank(base_value, cis_value, order)
    if rule == "tls_version_min_rank":
        return _select_rank(base_value, cis_value, {"tls1": 0, "tls1.1": 1, "tls1.2": 2, "tls1.3": 3})
    if rule == "tls_version_max_rank":
        return _select_rank(base_value, cis_value, {"tls1": 0, "tls1.1": 1, "tls1.2": 2, "tls1.3": 3})
    if rule == "preference_locked_value":
        return _select_preference(base_value, cis_value)
    return None


def _select_boolean_rank(base_value: Any, cis_value: Any, order: dict[bool, int]) -> str | None:
    if isinstance(base_value, bool) and isinstance(cis_value, bool):
        return "cis" if order[cis_value] > order[base_value] else "base"
    return None


def _select_rank(base_value: Any, cis_value: Any, order: dict[Any, int]) -> str | None:
    if base_value in order and cis_value in order:
        return "cis" if order[cis_value] > order[base_value] else "base"
    return None


def _select_preference(base_value: Any, cis_value: Any) -> str | None:
    if not isinstance(base_value, dict) or not isinstance(cis_value, dict):
        return None
    if base_value.get("Value") == cis_value.get("Value") and cis_value.get("Status") == "locked":
        if base_value.get("Status") == "locked":
            return "base"
        return "cis"
    return None


def _load_target_metadata(base_dir: Path) -> dict[PathKey, dict[str, Any]]:
    mappings = load_yaml_file(base_dir / "mappings.yaml").get("mappings", [])
    metadata: dict[PathKey, dict[str, Any]] = {}
    for mapping in mappings:
        recommendation_id = mapping.get("recommendation_id")
        for target in mapping.get("targets") or []:
            path = _target_effective_path(target)
            if not path:
                continue
            entry = metadata.setdefault(
                path,
                {
                    "recommendation_ids": [],
                    "merge_rule": target.get("merge_rule"),
                },
            )
            entry["recommendation_ids"].append(recommendation_id)
            if target.get("merge_rule"):
                entry["merge_rule"] = target["merge_rule"]
    return metadata


def _target_effective_path(target: dict[str, Any]) -> PathKey | None:
    path = target.get("path") or []
    if target.get("kind") == "preference" and path:
        return ("Preferences", path[0])
    if target.get("kind") == "policy" and path:
        return tuple(path)
    return None


def _load_manual_review_rules(base_dir: Path) -> dict[PathKey, str]:
    rules_path = base_dir / "merge_rules.yaml"
    if not rules_path.exists():
        return {}
    data = load_yaml_file(rules_path)
    manual_review: dict[PathKey, str] = {}
    for dotted_path, rule in (data.get("manual_review_paths") or {}).items():
        reason_value = rule.get("reason") if isinstance(rule, dict) else rule
        reason = str(reason_value) if reason_value is not None else ""
        manual_review[tuple(dotted_path.split("."))] = reason
    return manual_review
