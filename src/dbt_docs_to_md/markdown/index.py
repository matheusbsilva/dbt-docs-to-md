from __future__ import annotations

from ..domain import ParsedProject
from .environment import render_template
from .renderer import model_relpath


def render_index(project: ParsedProject, filenames: dict[str, str]) -> str:
    """Render the index, grouping models by dbt layer (warehouse schema).

    ``filenames`` maps ``model.unique_id`` -> output path so links match the
    (collision-resolved) names actually written to disk.
    """
    grouped: dict[str, list] = {}
    for model in project.models:
        grouped.setdefault(model.schema_name or "(no schema)", []).append(model)

    layers = [
        (layer, sorted(grouped[layer], key=lambda m: m.display_label.lower()))
        for layer in sorted(grouped)
    ]
    links = {m.unique_id: filenames.get(m.unique_id, model_relpath(m)) for m in project.models}

    return render_template(
        "index.md.jinja",
        project=project,
        layers=layers,
        filenames=links,
        version=project.dbt_schema_version or "unknown",
    )
