"""Build the catalog ``index.md`` listing every model."""

from __future__ import annotations

from ..domain import ParsedProject
from .renderer import _cell, model_relpath


def render_index(project: ParsedProject, filenames: dict[str, str]) -> str:
    """Render the index, grouping models by dbt layer (warehouse schema).

    ``filenames`` maps ``model.unique_id`` -> output path so links match the
    (collision-resolved) names actually written to disk.
    """
    lines = ["# Data Catalog Index", ""]
    lines.append(
        "Business-readable documentation for every dbt model in the project, "
        "organized by layer."
    )
    lines.append("")
    if project.metrics:
        lines.append(
            f"See the [Metrics Glossary](metrics.md) for the {len(project.metrics)} "
            "metric(s) available in the semantic layer."
        )
        lines.append("")

    layers: dict[str, list] = {}
    for model in project.models:
        layers.setdefault(model.schema_name or "(no schema)", []).append(model)

    for layer in sorted(layers):
        lines.append(f"## {layer}")
        lines.append("")
        lines.append("| Model | Description | Documentation |")
        lines.append("| --- | --- | --- |")
        for model in sorted(layers[layer], key=lambda m: m.display_label.lower()):
            name = model.display_label
            if model.label and model.label != model.name:
                name = f"{model.label} (`{model.name}`)"
            desc = model.description or "—"
            filename = filenames.get(model.unique_id, model_relpath(model))
            link = f"[View]({filename})"
            lines.append(f"| {_cell(name)} | {_cell(desc)} | {link} |")
        lines.append("")

    version = project.dbt_schema_version or "unknown"
    lines.append(
        f"*Total models: {len(project.models)}. Generated from dbt schema: {version}.*"
    )
    lines.append("")
    return "\n".join(lines)
