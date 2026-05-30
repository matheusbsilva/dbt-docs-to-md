"""Version-agnostic domain models.

These are the only models the renderer, lineage and bundle layers touch. The
:mod:`dbt_docs_to_md.adapter` module is responsible for mapping the many
version-specific objects produced by ``dbt-artifacts-parser`` (manifest v1..v12)
onto this stable shape, so the rest of the codebase never needs to care about
which dbt schema version generated the artifacts.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

# The custom meta key that carries the descriptive, business-friendly name of a
# model or column. Documented in the project README and SKILL.md.
LABEL_META_KEY = "label"


class ColumnTest(BaseModel):
    """A data test applied to a column or to a whole model."""

    name: str  # not_null, unique, relationships, accepted_values, custom, ...
    kwargs: dict[str, object] = Field(default_factory=dict)

    def describe(self) -> str:
        """Human-readable one-liner, e.g. ``accepted_values (values: a, b)``."""
        if not self.kwargs:
            return self.name
        # Keep only the stakeholder-relevant kwargs; drop dbt internals.
        shown = {
            k: v
            for k, v in self.kwargs.items()
            if k not in {"model", "column_name"} and v is not None
        }
        if not shown:
            return self.name
        parts = ", ".join(f"{k}: {_fmt(v)}" for k, v in shown.items())
        return f"{self.name} ({parts})"


class ParsedColumn(BaseModel):
    name: str
    description: str | None = None
    data_type: str | None = None
    meta: dict[str, object] = Field(default_factory=dict)
    tests: list[ColumnTest] = Field(default_factory=list)

    @property
    def label(self) -> str | None:
        value = self.meta.get(LABEL_META_KEY)
        return str(value) if value is not None else None

    @property
    def display_label(self) -> str:
        return self.label or self.name


class ParsedNodeRef(BaseModel):
    """A lightweight reference to any upstream node (model, source or seed).

    Used so lineage can name sources/seeds with their business ``label`` without
    carrying their full content.
    """

    unique_id: str
    name: str
    resource_type: str
    label: str | None = None

    @property
    def display_label(self) -> str:
        return self.label or self.name


class _Labelled(BaseModel):
    """Mixin for semantic objects that carry their own ``label`` field."""

    name: str
    label: str | None = None

    @property
    def display_label(self) -> str:
        return self.label or self.name


class SemanticEntity(_Labelled):
    """An entity (join key) of a semantic model, e.g. a primary/foreign key."""

    type: str | None = None  # primary, foreign, unique, natural
    description: str | None = None
    expr: str | None = None


class SemanticDimension(_Labelled):
    """A dimension — how a measure can be sliced (categorical or time)."""

    type: str | None = None  # categorical, time
    description: str | None = None
    is_partition: bool = False
    expr: str | None = None


class SemanticMeasure(_Labelled):
    """A measure — an aggregatable quantity defined on a semantic model."""

    agg: str | None = None  # sum, count, count_distinct, average, ...
    description: str | None = None
    expr: str | None = None
    agg_time_dimension: str | None = None
    create_metric: bool = False


class SemanticModel(_Labelled):
    unique_id: str
    description: str | None = None
    model_id: str | None = None  # unique_id of the dbt model it is built on
    primary_entity: str | None = None
    entities: list[SemanticEntity] = Field(default_factory=list)
    dimensions: list[SemanticDimension] = Field(default_factory=list)
    measures: list[SemanticMeasure] = Field(default_factory=list)


class Metric(_Labelled):
    unique_id: str
    description: str | None = None
    type: str | None = None  # simple, ratio, cumulative, derived, conversion
    type_params_summary: str | None = None
    filter: str | None = None
    meta: dict[str, object] = Field(default_factory=dict)
    semantic_model_ids: list[str] = Field(default_factory=list)
    model_ids: list[str] = Field(default_factory=list)


class ParsedModel(BaseModel):
    unique_id: str
    name: str
    description: str | None = None
    schema_name: str | None = None
    database: str | None = None
    relation_name: str | None = None
    resource_type: str = "model"
    meta: dict[str, object] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    columns: list[ParsedColumn] = Field(default_factory=list)
    model_tests: list[ColumnTest] = Field(default_factory=list)
    parents: list[str] = Field(default_factory=list)  # direct upstream unique_ids
    raw_code: str | None = None
    compiled_code: str | None = None
    semantic_models: list[SemanticModel] = Field(default_factory=list)
    metrics: list[Metric] = Field(default_factory=list)

    @property
    def label(self) -> str | None:
        value = self.meta.get(LABEL_META_KEY)
        return str(value) if value is not None else None

    @property
    def display_label(self) -> str:
        return self.label or self.name

    @property
    def transformation_sql(self) -> str | None:
        """SQL used to summarise transformations: compiled first, then raw."""
        return self.compiled_code or self.raw_code


class ParsedProject(BaseModel):
    dbt_schema_version: str | None = None
    models: list[ParsedModel] = Field(default_factory=list)
    # All upstream-referenceable nodes keyed by unique_id (models + sources + seeds).
    nodes_by_id: dict[str, ParsedNodeRef] = Field(default_factory=dict)
    # Project-wide semantic layer (for the metrics glossary).
    semantic_models: list[SemanticModel] = Field(default_factory=list)
    metrics: list[Metric] = Field(default_factory=list)

    def model_by_id(self) -> dict[str, ParsedModel]:
        return {m.unique_id: m for m in self.models}


def _fmt(value: object) -> str:
    if isinstance(value, (list, tuple)):
        return ", ".join(str(v) for v in value)
    return str(value)
