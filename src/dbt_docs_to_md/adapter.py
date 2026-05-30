from __future__ import annotations

from typing import Any

from .domain import (
    LABEL_META_KEY,
    ColumnTest,
    ParsedColumn,
    ParsedModel,
    ParsedNodeRef,
    ParsedProject,
)
from .semantic_collector import collect_semantic_layer
from .tests_collector import collect_tests

MODEL_RESOURCE_TYPES = {"model", "snapshot"}
REFERENCEABLE_RESOURCE_TYPES = MODEL_RESOURCE_TYPES | {"source", "seed"}


def build_project(manifest_obj: Any, catalog_obj: Any | None = None) -> ParsedProject:
    """Build a :class:`ParsedProject` from parsed manifest/catalog objects."""
    nodes = _as_dict(getattr(manifest_obj, "nodes", {}))
    sources = _as_dict(getattr(manifest_obj, "sources", {}))
    catalog_nodes = _as_dict(getattr(catalog_obj, "nodes", {})) if catalog_obj else {}

    tests_by_model = collect_tests(nodes)
    semantic = collect_semantic_layer(manifest_obj)

    nodes_by_id: dict[str, ParsedNodeRef] = {}
    models: list[ParsedModel] = []

    for unique_id, node in nodes.items():
        rtype = _resource_type(node)
        if rtype in REFERENCEABLE_RESOURCE_TYPES:
            nodes_by_id[unique_id] = _node_ref(unique_id, node, rtype)
        if rtype in MODEL_RESOURCE_TYPES:
            models.append(
                _build_model(
                    unique_id, node, rtype, catalog_nodes, tests_by_model, semantic
                )
            )

    for unique_id, src in sources.items():
        nodes_by_id[unique_id] = _node_ref(unique_id, src, "source")

    return ParsedProject(
        dbt_schema_version=_schema_version(manifest_obj),
        models=sorted(models, key=lambda m: m.display_label.lower()),
        nodes_by_id=nodes_by_id,
        semantic_models=semantic.semantic_models,
        metrics=semantic.metrics,
    )


def _build_model(
    unique_id: str,
    node: Any,
    rtype: str,
    catalog_nodes: dict[str, Any],
    tests_by_model: dict[str, dict[str | None, list[ColumnTest]]],
    semantic: Any,
) -> ParsedModel:
    meta = _merged_meta(node)
    catalog_cols = _as_dict(getattr(catalog_nodes.get(unique_id), "columns", {}))
    model_tests = tests_by_model.get(unique_id, {})

    columns: list[ParsedColumn] = []
    for col_name, col in _as_dict(getattr(node, "columns", {})).items():
        columns.append(
            ParsedColumn(
                name=getattr(col, "name", col_name) or col_name,
                description=_clean(getattr(col, "description", None)),
                data_type=_column_type(col, col_name, catalog_cols),
                meta=_as_meta(getattr(col, "meta", None)),
                tests=model_tests.get(col_name, []),
            )
        )

    sem = semantic.by_model_id.get(unique_id, {})

    return ParsedModel(
        unique_id=unique_id,
        name=getattr(node, "name", unique_id),
        description=_clean(getattr(node, "description", None)),
        schema_name=getattr(node, "schema_", None) or getattr(node, "schema", None),
        database=getattr(node, "database", None),
        relation_name=getattr(node, "relation_name", None),
        resource_type=rtype,
        meta=meta,
        tags=_as_list(getattr(node, "tags", None)),
        columns=columns,
        model_tests=model_tests.get(None, []),
        parents=_depends_on_nodes(node),
        raw_code=getattr(node, "raw_code", None),
        compiled_code=getattr(node, "compiled_code", None),
        semantic_models=sem.get("semantic_models", []),
        metrics=sem.get("metrics", []),
    )


def _node_ref(unique_id: str, node: Any, rtype: str) -> ParsedNodeRef:
    meta = _merged_meta(node)
    label = meta.get(LABEL_META_KEY)
    return ParsedNodeRef(
        unique_id=unique_id,
        name=getattr(node, "name", unique_id),
        resource_type=rtype,
        label=str(label) if label is not None else None,
    )


def _resource_type(node: Any) -> str:
    rt = getattr(node, "resource_type", None)
    return str(getattr(rt, "value", rt) or "")


def _schema_version(manifest_obj: Any) -> str | None:
    metadata = getattr(manifest_obj, "metadata", None)
    return getattr(metadata, "dbt_schema_version", None)


def _merged_meta(node: Any) -> dict[str, object]:
    """Merge ``config.meta`` then top-level ``meta`` (resolved value wins)."""
    config = getattr(node, "config", None)
    merged: dict[str, object] = {}
    merged.update(_as_meta(getattr(config, "meta", None)))
    merged.update(_as_meta(getattr(node, "meta", None)))
    return merged


def _column_type(col: Any, col_name: str, catalog_cols: dict[str, Any]) -> str | None:
    declared = getattr(col, "data_type", None)
    if declared:
        return declared
    entry = catalog_cols.get(col_name)
    if entry is None:
        lowered = {k.lower(): v for k, v in catalog_cols.items()}
        entry = lowered.get(col_name.lower())
    return getattr(entry, "type", None) if entry is not None else None


def _depends_on_nodes(node: Any) -> list[str]:
    depends_on = getattr(node, "depends_on", None)
    return _as_list(getattr(depends_on, "nodes", None))


def _as_meta(value: Any) -> dict[str, object]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return dict(value)
    if hasattr(value, "model_dump"):
        return value.model_dump()
    return {}


def _as_dict(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        dumped = value.model_dump()
        return dumped if isinstance(dumped, dict) else {}
    return {}


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


def _clean(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
