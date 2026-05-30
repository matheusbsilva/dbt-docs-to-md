from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from .domain import (
    Metric,
    SemanticDimension,
    SemanticEntity,
    SemanticMeasure,
    SemanticModel,
)


class SemanticLayer(BaseModel):
    semantic_models: list[SemanticModel] = []
    metrics: list[Metric] = []
    by_model_id: dict[str, dict[str, list]] = {}


def collect_semantic_layer(manifest_obj: Any) -> SemanticLayer:
    raw_semantic = _as_dict(getattr(manifest_obj, "semantic_models", None))
    raw_metrics = _as_dict(getattr(manifest_obj, "metrics", None))

    semantic_models = [
        _build_semantic_model(uid, node) for uid, node in raw_semantic.items()
    ]
    sm_to_model = {sm.unique_id: sm.model_id for sm in semantic_models}

    metrics = [_build_metric(uid, node, sm_to_model) for uid, node in raw_metrics.items()]

    by_model: dict[str, dict[str, list]] = {}
    for sm in semantic_models:
        if sm.model_id:
            by_model.setdefault(sm.model_id, _empty())["semantic_models"].append(sm)
    for metric in metrics:
        for model_id in metric.model_ids:
            by_model.setdefault(model_id, _empty())["metrics"].append(metric)

    return SemanticLayer(
        semantic_models=semantic_models, metrics=metrics, by_model_id=by_model
    )


def _build_semantic_model(unique_id: str, node: Any) -> SemanticModel:
    return SemanticModel(
        unique_id=unique_id,
        name=getattr(node, "name", unique_id),
        label=getattr(node, "label", None),
        description=_clean(getattr(node, "description", None)),
        model_id=_underlying_model(node),
        primary_entity=getattr(node, "primary_entity", None),
        entities=[_entity(e) for e in _as_list(getattr(node, "entities", None))],
        dimensions=[_dimension(d) for d in _as_list(getattr(node, "dimensions", None))],
        measures=[_measure(m) for m in _as_list(getattr(node, "measures", None))],
    )


def _build_metric(unique_id: str, node: Any, sm_to_model: dict[str, str | None]) -> Metric:
    dep_nodes = _as_list(getattr(getattr(node, "depends_on", None), "nodes", None))
    semantic_ids = [d for d in dep_nodes if isinstance(d, str) and d.startswith("semantic_model.")]
    model_ids = {d for d in dep_nodes if isinstance(d, str) and d.startswith("model.")}
    for sid in semantic_ids:
        mid = sm_to_model.get(sid)
        if mid:
            model_ids.add(mid)

    return Metric(
        unique_id=unique_id,
        name=getattr(node, "name", unique_id),
        label=getattr(node, "label", None),
        description=_clean(getattr(node, "description", None)),
        type=_enum_str(getattr(node, "type", None)),
        type_params_summary=_type_params_summary(node),
        filter=_filter_str(getattr(node, "filter", None)),
        meta=_as_meta(getattr(node, "meta", None)),
        semantic_model_ids=semantic_ids,
        model_ids=sorted(model_ids),
    )


def _entity(e: Any) -> SemanticEntity:
    return SemanticEntity(
        name=getattr(e, "name", ""),
        label=getattr(e, "label", None),
        type=_enum_str(getattr(e, "type", None)),
        description=_clean(getattr(e, "description", None)),
        expr=getattr(e, "expr", None),
    )


def _dimension(d: Any) -> SemanticDimension:
    return SemanticDimension(
        name=getattr(d, "name", ""),
        label=getattr(d, "label", None),
        type=_enum_str(getattr(d, "type", None)),
        description=_clean(getattr(d, "description", None)),
        is_partition=bool(getattr(d, "is_partition", False)),
        expr=getattr(d, "expr", None),
    )


def _measure(m: Any) -> SemanticMeasure:
    return SemanticMeasure(
        name=getattr(m, "name", ""),
        label=getattr(m, "label", None),
        agg=_enum_str(getattr(m, "agg", None)),
        description=_clean(getattr(m, "description", None)),
        expr=getattr(m, "expr", None),
        agg_time_dimension=getattr(m, "agg_time_dimension", None),
        create_metric=bool(getattr(m, "create_metric", False)),
    )


def _underlying_model(node: Any) -> str | None:
    """Resolve the dbt model a semantic model is built on."""
    dep_nodes = _as_list(getattr(getattr(node, "depends_on", None), "nodes", None))
    for dep in dep_nodes:
        if isinstance(dep, str) and dep.startswith("model."):
            return dep
    return None


def _type_params_summary(node: Any) -> str | None:
    """A short, readable description of how a metric is computed."""
    mtype = _enum_str(getattr(node, "type", None))
    tp = getattr(node, "type_params", None)
    if tp is None:
        return None

    if mtype == "ratio":
        num = _named(getattr(tp, "numerator", None))
        den = _named(getattr(tp, "denominator", None))
        if num or den:
            return f"{num or '?'} ÷ {den or '?'}"
    if mtype == "derived":
        expr = getattr(tp, "expr", None)
        if expr:
            return str(expr)
    if mtype == "cumulative":
        measure = _named(getattr(tp, "measure", None))
        window = getattr(tp, "window", None)
        if window is not None:
            count = getattr(window, "count", None)
            grain = _enum_str(getattr(window, "granularity", None))
            win = " ".join(str(x) for x in (count, grain) if x)
            return f"{measure or 'measure'} over {win}".strip()
        return measure

    return _named(getattr(tp, "measure", None))


def _named(obj: Any) -> str | None:
    if obj is None:
        return None
    return getattr(obj, "name", None)


def _filter_str(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    filters = getattr(value, "where_filters", None)
    if filters:
        parts = [getattr(f, "where_sql_template", None) for f in _as_list(filters)]
        joined = " AND ".join(p for p in parts if p)
        return joined or None
    return None


def _enum_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(getattr(value, "value", value))


def _empty() -> dict[str, list]:
    return {"semantic_models": [], "metrics": []}


def _as_meta(value: Any) -> dict[str, object]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return dict(value)
    if hasattr(value, "model_dump"):
        dumped = value.model_dump()
        return dumped if isinstance(dumped, dict) else {}
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
