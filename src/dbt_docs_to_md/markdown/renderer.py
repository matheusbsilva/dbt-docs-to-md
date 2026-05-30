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


def _sanitize(text: str) -> str:
    """Filesystem-safe token: lowercase, drop unsafe chars, collapse separators."""
    base = text.strip().lower()
    base = re.sub(r"[^\w\s-]", "", base)
    base = re.sub(r"[\s_]+", "_", base).strip("_-")
    return base


def model_relpath(model: ParsedModel) -> str:
    """Output path for a model's Markdown, relative to the output root.

    Models are organized by their dbt layer (warehouse schema): a model in
    schema ``analytics`` is written to ``analytics/<name>.md``. The file is named
    after the technical model name. Models without a schema land at the root.
    """
    filename = f"{_sanitize(model.name) or model.name}.md"
    folder = _sanitize(model.schema_name) if model.schema_name else ""
    return f"{folder}/{filename}" if folder else filename


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

    # Semantic models (entities / dimensions / measures)
    if model.semantic_models:
        lines.append("## Semantic Model")
        for sm in model.semantic_models:
            lines.extend(_semantic_model_section(sm))

    # Metrics built on this model
    if model.metrics:
        lines.append("## Metrics You Can Measure")
        lines.append(
            "**Available metrics:** "
            + ", ".join(m.display_label for m in model.metrics)
        )
        lines.append("")
        lines.extend(_metrics_table(model.metrics))
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


def _semantic_model_section(sm) -> list[str]:
    lines: list[str] = [f"### {sm.display_label}"]
    if sm.description:
        lines.append(sm.description)
    if sm.primary_entity:
        lines.append(f"_Primary entity:_ `{sm.primary_entity}`")
    lines.append("")

    if sm.entities:
        lines.append("**Entities** (how this data joins to other models)")
        lines.append("")
        lines.append("| Entity | Type | Description |")
        lines.append("| --- | --- | --- |")
        for e in sm.entities:
            lines.append(
                f"| {_cell(e.display_label)} | {_cell(e.type or '—')} | {_cell(e.description or '—')} |"
            )
        lines.append("")

    if sm.dimensions:
        lines.append("**Dimensions** (ways to slice the metrics)")
        lines.append("")
        lines.append("| Dimension | Type | Description |")
        lines.append("| --- | --- | --- |")
        for d in sm.dimensions:
            lines.append(
                f"| {_cell(d.display_label)} | {_cell(d.type or '—')} | {_cell(d.description or '—')} |"
            )
        lines.append("")

    if sm.measures:
        lines.append("**Measures** (the quantities that can be aggregated)")
        lines.append("")
        lines.append("| Measure | Aggregation | Description |")
        lines.append("| --- | --- | --- |")
        for m in sm.measures:
            lines.append(
                f"| {_cell(m.display_label)} | {_cell(m.agg or '—')} | {_cell(m.description or '—')} |"
            )
        lines.append("")

    return lines


def _metrics_table(metrics) -> list[str]:
    rows = [
        "| Metric | Type | How it's calculated | Description |",
        "| --- | --- | --- | --- |",
    ]
    for m in metrics:
        rows.append(
            "| {label} | {type} | {calc} | {desc} |".format(
                label=_cell(m.display_label),
                type=_cell(m.type or "—"),
                calc=_cell(m.type_params_summary or "—"),
                desc=_cell(m.description or "—"),
            )
        )
    return rows


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
