from __future__ import annotations

from ..domain import ParsedProject
from .environment import DEFAULT_LANGUAGE, render_template


def render_metrics_glossary(
    project: ParsedProject,
    model_filenames: dict[str, str],
    language: str = DEFAULT_LANGUAGE,
) -> str:
    """Render ``metrics.md`` — a business glossary of every metric in the project."""
    metrics = sorted(project.metrics, key=lambda m: m.display_label.lower())

    def built_on(metric) -> str:
        return _built_on(metric, project, model_filenames)

    return render_template(
        "metrics.md.jinja", language=language, metrics=metrics, built_on=built_on
    )


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
