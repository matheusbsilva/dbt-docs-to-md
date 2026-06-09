from __future__ import annotations

from .domain import ParsedModel, ParsedProject
from .lineage import direct_parents, upstream_tree
from .markdown.environment import DEFAULT_LANGUAGE


def build_bundle(
    model: ParsedModel,
    project: ParsedProject,
    language: str = DEFAULT_LANGUAGE,
) -> dict:
    direct_ids = {r.unique_id for r in direct_parents(model.unique_id, project)}
    return {
        "unique_id": model.unique_id,
        "name": model.name,
        "label": model.label,
        "description": model.description,
        "language": language,
        "upstream": [
            _ref(r, direct=r.unique_id in direct_ids)
            for r in upstream_tree(model.unique_id, project)
        ],
        "sql": model.transformation_sql,
        "semantic_models": [_semantic_model(sm) for sm in model.semantic_models],
        "metrics": [_metric(m) for m in model.metrics],
    }


def _ref(ref, direct: bool = False) -> dict:
    return {
        "name": ref.name,
        "label": ref.label,
        "display_label": ref.display_label,
        "resource_type": ref.resource_type,
        "direct": direct,
    }


def _semantic_model(sm) -> dict:
    return {
        "name": sm.display_label,
        "dimensions": [d.display_label for d in sm.dimensions],
        "measures": [m.display_label for m in sm.measures],
    }


def _metric(metric) -> dict:
    return {
        "name": metric.display_label,
        "type": metric.type,
        "description": metric.description,
    }
