from __future__ import annotations

from ..domain import ParsedProject
from .environment import DEFAULT_LANGUAGE, render_template
from .renderer import model_relpath


def render_index(
    project: ParsedProject,
    filenames: dict[str, str],
    language: str = DEFAULT_LANGUAGE,
) -> str:
    """Render the index, grouping models by dbt layer (warehouse schema).

    ``filenames`` maps ``model.unique_id`` -> output path so links match the
    (collision-resolved) names actually written to disk. The layer label (a
    possibly-``None`` schema name) is localized in the template.
    """
    grouped: dict[str | None, list] = {}
    for model in project.models:
        grouped.setdefault(model.schema_name, []).append(model)

    layers = [
        (schema, sorted(grouped[schema], key=lambda m: m.display_label.lower()))
        for schema in sorted(grouped, key=lambda s: s or "(no schema)")
    ]
    links = {m.unique_id: filenames.get(m.unique_id, model_relpath(m)) for m in project.models}

    return render_template(
        "index.md.jinja",
        language=language,
        project=project,
        layers=layers,
        filenames=links,
        version=project.dbt_schema_version or "unknown",
    )
