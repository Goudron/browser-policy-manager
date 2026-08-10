"""Typed, stable diagnostics for documentation artifact validation.

The build contract deliberately fails on the first invalid artifact.  Keeping
the issue object separate from its rendered message gives every validation
stage a machine-readable owner without changing the established CLI output.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import TypeVar


class ValidationStage(StrEnum):
    """Owned semantic validation stages for published documentation artifacts."""

    MANIFEST_MATRIX = "manifest-matrix"
    MANIFEST_GUIDES = "manifest-guides"
    MANIFEST_TOPICS = "manifest-topics"
    TARGET_MAP = "target-map"
    SEARCH_CONTRACT = "search-contract"
    SEARCH_FIXTURES = "search-fixtures"
    SEARCH_DOCUMENTS = "search-documents"
    SEARCH_PROJECTIONS = "search-projections"
    SEARCH_RANKING = "search-ranking"
    SEARCH_FILTERS = "search-filters"
    SEARCH_QUALITY = "search-quality"
    SEARCH_BUDGETS = "search-budgets"


@dataclass(frozen=True)
class ValidationIssue:
    """A stable semantic failure with optional artifact and locale context."""

    stage: ValidationStage
    message: str
    artifact: str | None = None
    locale: str | None = None

    def diagnostic(self) -> str:
        """Return the established human-facing diagnostic without hidden context."""

        return self.message


Failure = TypeVar("Failure", bound=Exception)
Result = TypeVar("Result")


class ValidationReporter:
    """Attach typed stage ownership while preserving fail-closed diagnostics."""

    def __init__(
        self,
        failure_type: type[Failure],
        *,
        artifact: str | None = None,
        locale: str | None = None,
    ) -> None:
        self._failure_type = failure_type
        self._artifact = artifact
        self._locale = locale
        self.issues: list[ValidationIssue] = []

    def fail(self, stage: ValidationStage, message: str) -> None:
        issue = ValidationIssue(stage, message, self._artifact, self._locale)
        self.issues.append(issue)
        raise self._failure_type(issue.diagnostic())

    def require(self, stage: ValidationStage, condition: bool, message: str) -> None:
        if not condition:
            self.fail(stage, message)

    def stage(self, stage: ValidationStage, action: Callable[[], Result]) -> Result:
        """Run one explicit stage and classify a legacy semantic ``BuildError``."""

        try:
            return action()
        except self._failure_type as exc:
            self.fail(stage, str(exc))
