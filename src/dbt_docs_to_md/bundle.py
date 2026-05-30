"""Per-model context bundles — the contract between the script and Claude.

For each model the script writes ``_bundles/<slug>.json`` containing exactly the
information Claude needs to author the two prose sections:

* the model's identity and description,
* its direct parents and full upstream tree, each resolved to a business
  ``label`` (so lineage prose can speak in stakeholder terms),
* the SQL used to summarise transformations (compiled, falling back to raw),
* the target Markdown filename and the placeholder markers to replace.

Keeping this compact bounds Claude's token usage and makes the LLM phase
deterministic and resumable.
"""

from __future__ import annotations

from .domain import ParsedModel, ParsedProject
from .lineage import direct_parents, upstream_tree
from .markdown import templates


def build_bundle(model: ParsedModel, project: ParsedProject, target_md: str) -> dict:
    return {
        "unique_id": model.unique_id,
        "name": model.name,
        "label": model.label,
        "description": model.description,
        "parents": [_ref(r) for r in direct_parents(model.unique_id, project)],
        "upstream": [_ref(r) for r in upstream_tree(model.unique_id, project)],
        "sql": model.transformation_sql,
        "sql_source": "compiled" if model.compiled_code else "raw",
        "semantic_models": [_semantic_model(sm) for sm in model.semantic_models],
        "metrics": [_metric(m) for m in model.metrics],
        "target_md": target_md,
        "placeholders": {
            "lineage": {
                "open": templates.LINEAGE_OPEN,
                "close": templates.LINEAGE_CLOSE,
            },
            "transformations": {
                "open": templates.TRANSFORMATION_OPEN,
                "close": templates.TRANSFORMATION_CLOSE,
            },
        },
    }


def _ref(ref) -> dict:
    return {
        "name": ref.name,
        "label": ref.label,
        "display_label": ref.display_label,
        "resource_type": ref.resource_type,
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
