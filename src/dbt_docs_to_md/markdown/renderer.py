"""Render a :class:`ParsedModel` to Markdown (deterministic sections only).

Two prose sections — Upstream Lineage and What This Model Does — are emitted as
placeholder regions bracketed by the markers in :mod:`.templates`. Claude fills
those in afterwards, using the per-model context bundle.
"""

from __future__ import annotations

import re

from ..domain import ParsedColumn, ParsedModel, ParsedNodeRef
from ..lineage import direct_parents
from . import templates


def slugify_filename(model: ParsedModel) -> str:
    """Filesystem-safe slug derived from the model's business label."""
    base = model.display_label.strip().lower()
    base = re.sub(r"[^\w\s-]", "", base)
    base = re.sub(r"[\s_-]+", "-", base).strip("-")
    return base or model.name


def render_model_md(model: ParsedModel, project, schema_version: str | None = None) -> str:
    parents = direct_parents(model.unique_id, project)
    lines: list[str] = []

    # Header
    lines.append(f"# {model.display_label}")
    lines.append("")
    meta_line = [f"**Technical model:** `{model.name}`"]
    if model.relation_name:
        meta_line.append(f"**Table:** `{model.relation_name}`")
    if model.tags:
        meta_line.append(f"**Tags:** {', '.join(model.tags)}")
    lines.append("> " + "  ·  ".join(meta_line))
    lines.append("")

    # Description
    lines.append("## Description")
    lines.append(model.description or "_No description provided._")
    lines.append("")

    # Business context (all meta keys)
    lines.append("## Business Context")
    lines.extend(_meta_table(model.meta))
    lines.append("")

    # Upstream lineage (LLM-authored region) + deterministic direct-sources list
    lines.append("## Upstream Lineage")
    lines.append(templates.LINEAGE_OPEN)
    lines.append(templates.LINEAGE_PLACEHOLDER)
    lines.append(templates.LINEAGE_CLOSE)
    lines.append("")
    lines.append(f"**Direct sources:** {_sources_list(parents)}")
    lines.append("")

    # Transformation summary (LLM-authored region)
    lines.append("## What This Model Does")
    lines.append(templates.TRANSFORMATION_OPEN)
    lines.append(templates.TRANSFORMATION_PLACEHOLDER)
    lines.append(templates.TRANSFORMATION_CLOSE)
    lines.append("")

    # Columns
    lines.append("## Columns")
    lines.extend(_columns_table(model.columns))
    lines.append("")

    # Model-level tests
    if model.model_tests:
        lines.append("## Tests Applied (model level)")
        for test in model.model_tests:
            lines.append(f"- {test.describe()}")
        lines.append("")

    # Footer
    version = schema_version or project.dbt_schema_version or "unknown"
    lines.append("---")
    lines.append(f"*Generated from dbt artifacts (schema: {version}).*")
    lines.append("")

    return "\n".join(lines)


def _meta_table(meta: dict[str, object]) -> list[str]:
    if not meta:
        return ["_No metadata provided._"]
    rows = ["| Key | Value |", "| --- | --- |"]
    for key in sorted(meta):
        rows.append(f"| {_cell(key)} | {_cell(meta[key])} |")
    return rows


def _columns_table(columns: list[ParsedColumn]) -> list[str]:
    if not columns:
        return ["_No columns documented._"]
    rows = [
        "| Column | Type | Description | Tests | Meta |",
        "| --- | --- | --- | --- | --- |",
    ]
    for col in columns:
        tests = ", ".join(t.describe() for t in col.tests) or "—"
        meta = _inline_meta(col.meta) or "—"
        rows.append(
            "| {name} | {dtype} | {desc} | {tests} | {meta} |".format(
                name=_cell(col.name),
                dtype=_cell(col.data_type or "—"),
                desc=_cell(col.description or "—"),
                tests=_cell(tests),
                meta=_cell(meta),
            )
        )
    return rows


def _sources_list(parents: list[ParsedNodeRef]) -> str:
    if not parents:
        return "_None (this model reads directly from raw data or has no tracked sources)._"
    return ", ".join(p.display_label for p in parents)


def _inline_meta(meta: dict[str, object]) -> str:
    return "; ".join(f"{k}: {_stringify(v)}" for k, v in sorted(meta.items()))


def _stringify(value: object) -> str:
    if isinstance(value, (list, tuple)):
        return ", ".join(str(v) for v in value)
    return str(value)


def _cell(value: object) -> str:
    """Escape a value for safe inclusion in a Markdown table cell."""
    text = _stringify(value)
    text = text.replace("\n", " ").replace("|", "\\|")
    return text.strip()
