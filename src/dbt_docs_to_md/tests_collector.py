"""Collect dbt test nodes and associate them back to models and columns.

dbt represents data tests as separate nodes (``resource_type == "test"``). Each
test depends on the model it validates and may carry a ``column_name`` (column
test) or not (model-level test). We build a map::

    {model_unique_id: {column_name | None: [ColumnTest, ...]}}

which the adapter merges into the parsed models.
"""

from __future__ import annotations

from typing import Any

from .domain import ColumnTest


def collect_tests(nodes: dict[str, Any]) -> dict[str, dict[str | None, list[ColumnTest]]]:
    result: dict[str, dict[str | None, list[ColumnTest]]] = {}

    for node in nodes.values():
        rt = getattr(node, "resource_type", None)
        if str(getattr(rt, "value", rt) or "") != "test":
            continue

        target = _target_model(node)
        if target is None:
            continue

        column_name = getattr(node, "column_name", None)
        test = _build_test(node)
        result.setdefault(target, {}).setdefault(column_name, []).append(test)

    return result


def _target_model(node: Any) -> str | None:
    """Find the model this test validates.

    Prefer ``attached_node`` (set for tests defined on a model in recent dbt
    versions); otherwise fall back to the first ``model.*``/``snapshot.*`` in
    ``depends_on.nodes``.
    """
    attached = getattr(node, "attached_node", None)
    if attached:
        return attached

    depends_on = getattr(node, "depends_on", None)
    for dep in _as_list(getattr(depends_on, "nodes", None)):
        if isinstance(dep, str) and dep.split(".", 1)[0] in {"model", "snapshot"}:
            return dep
    return None


def _build_test(node: Any) -> ColumnTest:
    test_metadata = getattr(node, "test_metadata", None)
    if test_metadata is not None:
        name = getattr(test_metadata, "name", None)
        kwargs = getattr(test_metadata, "kwargs", None)
        if name:
            return ColumnTest(name=str(name), kwargs=_as_dict(kwargs))

    # Singular / custom tests have no test_metadata; use a readable name.
    return ColumnTest(name=str(getattr(node, "name", "custom")))


def _as_dict(value: Any) -> dict[str, object]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return dict(value)
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
