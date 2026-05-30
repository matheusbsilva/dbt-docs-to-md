"""Render ``metrics.md`` — a business glossary of every metric in the project."""

from __future__ import annotations

from ..domain import ParsedProject
from .renderer import _cell


def render_metrics_glossary(project: ParsedProject, model_filenames: dict[str, str]) -> str:
    lines = ["# Metrics Glossary", ""]
    lines.append("Every metric defined in the dbt Semantic Layer, in business terms.")
    lines.append("")
    lines.append("| Metric | Type | How it's calculated | Description | Built on |")
    lines.append("| --- | --- | --- | --- | --- |")

    for metric in sorted(project.metrics, key=lambda m: m.display_label.lower()):
        built_on = _built_on(metric, project, model_filenames)
        lines.append(
            "| {label} | {type} | {calc} | {desc} | {built} |".format(
                label=_cell(metric.display_label),
                type=_cell(metric.type or "—"),
                calc=_cell(metric.type_params_summary or "—"),
                desc=_cell(metric.description or "—"),
                built=built_on,
            )
        )

    lines.append("")
    lines.append(f"*Total metrics: {len(project.metrics)}.*")
    lines.append("")
    return "\n".join(lines)


def _built_on(metric, project: ParsedProject, model_filenames: dict[str, str]) -> str:
    models = project.model_by_id()
    links = []
    for model_id in metric.model_ids:
        model = models.get(model_id)
        if model is None:
            continue
        filename = model_filenames.get(model_id)
        label = model.display_label
        links.append(f"[{label}]({filename})" if filename else label)
    return ", ".join(links) if links else "—"
