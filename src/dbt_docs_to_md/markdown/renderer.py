from __future__ import annotations

import re

from ..domain import ParsedModel
from ..lineage import direct_parents
from .environment import render_template


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
    """Render a model's Markdown document from the ``model.md.jinja`` template.

    Two prose sections — Upstream Lineage and What This Model Does — are emitted
    as placeholder regions bracketed by the markers in :mod:`.markers`, which
    Claude fills in afterwards using the per-model context bundle.
    """
    version = schema_version or project.dbt_schema_version or "unknown"
    return render_template(
        "model.md.jinja",
        model=model,
        parents=direct_parents(model.unique_id, project),
        version=version,
    )
