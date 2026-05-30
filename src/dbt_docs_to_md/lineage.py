"""Resolve upstream lineage and business labels for models.

Lineage scope (per project decision): the *full transitive* upstream tree,
including raw sources and seeds, so business stakeholders get the complete origin
story of a model's data. Upstream nodes are named by their ``label`` meta key
when available.
"""

from __future__ import annotations

from .domain import ParsedNodeRef, ParsedProject


def direct_parents(model_id: str, project: ParsedProject) -> list[ParsedNodeRef]:
    """Immediate upstream nodes (models/sources/seeds) of a model."""
    model = project.model_by_id().get(model_id)
    if model is None:
        return []
    refs = [project.nodes_by_id[p] for p in model.parents if p in project.nodes_by_id]
    return _dedup(refs)


def upstream_tree(model_id: str, project: ParsedProject) -> list[ParsedNodeRef]:
    """All transitive upstream nodes, de-duplicated.

    Traversal follows model parents recursively; sources and seeds are leaves
    (they have no parents in the manifest's node graph).
    """
    models = project.model_by_id()
    seen: set[str] = set()
    order: list[ParsedNodeRef] = []
    stack = list(_parent_ids(model_id, models))

    while stack:
        current = stack.pop(0)
        if current in seen:
            continue
        seen.add(current)
        ref = project.nodes_by_id.get(current)
        if ref is not None:
            order.append(ref)
        # Recurse only into nodes that are themselves models with parents.
        stack.extend(_parent_ids(current, models))

    return order


def _parent_ids(node_id: str, models: dict) -> list[str]:
    model = models.get(node_id)
    return list(model.parents) if model is not None else []


def _dedup(refs: list[ParsedNodeRef]) -> list[ParsedNodeRef]:
    seen: set[str] = set()
    out: list[ParsedNodeRef] = []
    for ref in refs:
        if ref.unique_id not in seen:
            seen.add(ref.unique_id)
            out.append(ref)
    return out
