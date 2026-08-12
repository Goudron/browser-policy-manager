"""Bounded, immutable conversion-recipe registry for the M4 planner.

The production registry is deliberately empty.  This module provides the
smallest reviewable mechanism needed to publish a future lossless recipe: one
exact source atom to one exact target atom, tied to the exact two artifacts and
their normalized validator digests.  It has no catalog, I/O, or policy-schema
loader dependency.
"""

from __future__ import annotations

import copy
import hashlib
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field

from app.core.profile_conversion_json import canonical_json, strict_json_copy

type JsonValue = str | int | float | bool | None | list[JsonValue] | dict[str, JsonValue]
type JsonPredicate = Callable[[JsonValue], bool]
type JsonTransform = Callable[[JsonValue], JsonValue]

_SHA256 = re.compile(r"^[a-f0-9]{64}$")
_RECIPE_ID = re.compile(r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$")


class ConversionRecipeError(ValueError):
    """A construction-time registry violation with a stable code."""


def _digest(value: JsonValue) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def _is_pointer(value: str) -> bool:
    if not value.startswith("/"):
        return False
    index = 0
    while index < len(value):
        if value[index] == "~":
            if index + 1 == len(value) or value[index + 1] not in "01":
                return False
            index += 2
        else:
            index += 1
    return True


@dataclass(frozen=True, slots=True)
class ConversionRecipe:
    """One reviewed reversible exact-atom transformation.

    Callables are intentionally excluded from identity.  Their behavior is
    still checked on every use by source immutability, target constraint, and
    executable inverse equality.  A behaviour change therefore requires a
    changed reviewed descriptor/evidence and a new version before publication.
    """

    recipe_id: str
    recipe_version: int
    source_artifact_id: str
    target_artifact_id: str
    source_validation_schema_sha256: str
    target_validation_schema_sha256: str
    source_path: str
    target_path: str
    input_predicate_id: str
    target_constraint_id: str
    evidence_digest: str
    predicate: JsonPredicate = field(repr=False, compare=False)
    transform: JsonTransform = field(repr=False, compare=False)
    inverse: JsonTransform = field(repr=False, compare=False)
    target_constraint: JsonPredicate = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        if not _RECIPE_ID.fullmatch(self.recipe_id) or self.recipe_version < 1:
            raise ConversionRecipeError("transform_recipe_identity_invalid")
        if not self.source_artifact_id or not self.target_artifact_id:
            raise ConversionRecipeError("transform_recipe_artifact_invalid")
        if not all(
            _SHA256.fullmatch(value)
            for value in (
                self.source_validation_schema_sha256,
                self.target_validation_schema_sha256,
                self.evidence_digest,
            )
        ):
            raise ConversionRecipeError("transform_recipe_digest_invalid")
        if not _is_pointer(self.source_path) or not _is_pointer(self.target_path):
            raise ConversionRecipeError("transform_recipe_path_invalid")
        if not _RECIPE_ID.fullmatch(self.input_predicate_id) or not _RECIPE_ID.fullmatch(
            self.target_constraint_id
        ):
            raise ConversionRecipeError("transform_recipe_predicate_invalid")
        if not all(
            callable(value)
            for value in (self.predicate, self.transform, self.inverse, self.target_constraint)
        ):
            raise ConversionRecipeError("transform_recipe_callable_invalid")

    def definition(self) -> dict[str, JsonValue]:
        return {
            "recipe_id": self.recipe_id,
            "recipe_version": self.recipe_version,
            "source_artifact_id": self.source_artifact_id,
            "target_artifact_id": self.target_artifact_id,
            "source_validation_schema_sha256": self.source_validation_schema_sha256,
            "target_validation_schema_sha256": self.target_validation_schema_sha256,
            "source_path": self.source_path,
            "target_path": self.target_path,
            "input_predicate_id": self.input_predicate_id,
            "target_constraint_id": self.target_constraint_id,
            "evidence_digest": self.evidence_digest,
            "evidence_kind": "reversible",
        }

    @property
    def definition_digest(self) -> str:
        return _digest(self.definition())

    def as_identity(self) -> dict[str, JsonValue]:
        return {
            "recipe_id": self.recipe_id,
            "recipe_version": self.recipe_version,
            "definition_digest": self.definition_digest,
            "evidence_digest": self.evidence_digest,
            "evidence_kind": "reversible",
        }

    def domain_key(self) -> tuple[str, str, str, str, str]:
        return (
            self.source_artifact_id,
            self.target_artifact_id,
            self.source_validation_schema_sha256,
            self.target_validation_schema_sha256,
            self.source_path,
        )


@dataclass(frozen=True, slots=True)
class RecipeApplication:
    recipe: ConversionRecipe
    output: JsonValue | None
    failure_code: str | None


@dataclass(frozen=True, slots=True)
class ConversionRecipeRegistry:
    """Order-independent exact-domain registry; overlaps are invalid at build."""

    registry_id: str = "firefox-profile-conversion"
    registry_version: int = 1
    recipes: tuple[ConversionRecipe, ...] = ()

    def __post_init__(self) -> None:
        if self.registry_id != "firefox-profile-conversion" or self.registry_version < 1:
            raise ConversionRecipeError("transform_recipe_registry_identity_invalid")
        recipes = tuple(self.recipes)
        if not all(isinstance(recipe, ConversionRecipe) for recipe in recipes):
            raise ConversionRecipeError("transform_recipe_registry_member_invalid")
        identities = [(recipe.recipe_id, recipe.recipe_version) for recipe in recipes]
        if len(identities) != len(set(identities)):
            raise ConversionRecipeError("transform_recipe_duplicate")
        domains = [recipe.domain_key() for recipe in recipes]
        # Predicate overlap cannot be proved from arbitrary pure callables.  A
        # shared exact domain is consequently rejected conservatively.
        if len(domains) != len(set(domains)):
            raise ConversionRecipeError("transform_recipe_domain_overlap")
        object.__setattr__(self, "recipes", tuple(sorted(recipes, key=_recipe_sort_key)))

    def as_identity(self) -> dict[str, JsonValue]:
        projection: dict[str, JsonValue] = {
            "registry_id": self.registry_id,
            "registry_version": self.registry_version,
            "recipes": [recipe.as_identity() for recipe in self.recipes],
        }
        return {**projection, "registry_digest": _digest(projection)}

    def apply(
        self,
        *,
        source_artifact: Mapping[str, JsonValue],
        target_artifact: Mapping[str, JsonValue],
        source_path: str,
        source_value: JsonValue,
    ) -> RecipeApplication | None:
        source_digest = source_artifact.get("validation_schema_sha256")
        target_digest = target_artifact.get("validation_schema_sha256")
        matches = [
            recipe
            for recipe in self.recipes
            if recipe.domain_key()
            == (
                source_artifact.get("artifact_id"),
                target_artifact.get("artifact_id"),
                source_digest,
                target_digest,
                source_path,
            )
        ]
        if not matches:
            return None
        if len(matches) != 1:  # Defensive: construction already forbids this.
            return RecipeApplication(matches[0], None, "transform_recipe_ambiguous")
        recipe = matches[0]
        original = strict_json_copy(source_value)
        try:
            if not recipe.predicate(copy.deepcopy(original)):
                return RecipeApplication(recipe, None, "transform_predicate_mismatch")
            output = strict_json_copy(recipe.transform(copy.deepcopy(original)))
            if canonical_json(original) != canonical_json(strict_json_copy(source_value)):
                return RecipeApplication(recipe, None, "transform_source_mutated")
            if not recipe.target_constraint(copy.deepcopy(output)):
                return RecipeApplication(recipe, None, "transform_output_invalid")
            reversed_value = strict_json_copy(recipe.inverse(copy.deepcopy(output)))
            if canonical_json(reversed_value) != canonical_json(original):
                return RecipeApplication(recipe, None, "transform_lossless_evidence_missing")
        except Exception:  # Recipe code is untrusted until it proves itself on this input.
            return RecipeApplication(recipe, None, "transform_exception")
        return RecipeApplication(recipe, output, None)


def _recipe_sort_key(recipe: ConversionRecipe) -> tuple[str, int, str]:
    return (recipe.recipe_id, recipe.recipe_version, recipe.definition_digest)


EMPTY_CONVERSION_RECIPE_REGISTRY = ConversionRecipeRegistry()
